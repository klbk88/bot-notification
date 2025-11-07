"""Notification service for processing events and sending messages."""
import json
import asyncio
import logging
from typing import Dict, Any, List
from aiogram import Bot

from ..database.db import Database
from .condition_checker import ConditionChecker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationService:
    """Service for processing events and sending notifications."""

    def __init__(self, database: Database, bot: Bot):
        self.db = database
        self.bot = bot
        self.condition_checker = ConditionChecker()
        self.is_running = False

    async def create_event(self, event_type_name: str, data: Dict[str, Any]) -> int:
        """
        Create new event that will trigger notifications.

        Args:
            event_type_name: Name of the event type
            data: Event data dictionary

        Returns:
            Event ID
        """
        # Get or create event type
        event_type = await self.db.get_event_type(event_type_name)
        if not event_type:
            event_type_id = await self.db.add_event_type(event_type_name)
        else:
            event_type_id = event_type['id']

        # Create event
        event_id = await self.db.add_event(event_type_id, data)
        logger.info(f"Created event {event_id} of type '{event_type_name}'")

        # Process immediately
        await self.process_events()

        return event_id

    async def process_events(self):
        """Process all unprocessed events and send notifications."""
        events = await self.db.get_unprocessed_events()

        for event in events:
            try:
                await self._process_single_event(event)
                await self.db.mark_event_processed(event['id'])
            except Exception as e:
                logger.error(f"Error processing event {event['id']}: {e}")

    async def _process_single_event(self, event: Dict[str, Any]):
        """Process single event and send notifications to subscribers."""
        event_id = event['id']
        event_type_id = event['event_type_id']
        event_data = json.loads(event['data'])

        logger.info(f"Processing event {event_id} ({event['event_name']})")

        # Get all subscribers for this event type
        subscribers = await self.db.get_subscribers_for_event(event_type_id)

        if not subscribers:
            logger.info(f"No subscribers for event {event_id}")
            return

        # Send notifications to matching subscribers
        tasks = []
        for subscriber in subscribers:
            # Check if conditions match
            if self.condition_checker.check(event_data, subscriber['conditions']):
                task = self._send_notification(
                    subscriber,
                    event_id,
                    event['event_name'],
                    event_data
                )
                tasks.append(task)

        # Send all notifications concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Sent {len(tasks)} notifications for event {event_id}")

    async def _send_notification(self, subscriber: Dict[str, Any], event_id: int,
                                  event_name: str, event_data: Dict[str, Any]):
        """Send notification to a single subscriber."""
        user_id = subscriber['user_id']
        telegram_id = subscriber['telegram_id']

        # Format message
        message = self._format_message(event_name, event_data)

        try:
            # Send message via Telegram
            await self.bot.send_message(telegram_id, message, parse_mode="HTML")

            # Log to database
            await self.db.add_notification(user_id, event_id, message, status='sent')
            logger.info(f"Sent notification to user {telegram_id}")

        except Exception as e:
            # Log error to database
            await self.db.add_notification(
                user_id, event_id, message,
                status='failed', error_message=str(e)
            )
            logger.error(f"Failed to send notification to user {telegram_id}: {e}")

    def _format_message(self, event_name: str, event_data: Dict[str, Any]) -> str:
        """
        Format event data into readable message.
        Override this method for custom formatting.
        """
        message = f"<b>🔔 {event_name}</b>\n\n"

        for key, value in event_data.items():
            if isinstance(value, dict):
                message += f"<b>{key}:</b>\n"
                for sub_key, sub_value in value.items():
                    message += f"  • {sub_key}: {sub_value}\n"
            else:
                message += f"<b>{key}:</b> {value}\n"

        return message

    async def start_polling(self, interval: int = 5):
        """
        Start polling for unprocessed events.

        Args:
            interval: Polling interval in seconds
        """
        self.is_running = True
        logger.info(f"Started event polling (interval: {interval}s)")

        while self.is_running:
            try:
                await self.process_events()
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")

            await asyncio.sleep(interval)

    def stop_polling(self):
        """Stop polling for events."""
        self.is_running = False
        logger.info("Stopped event polling")

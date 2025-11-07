"""Main bot application."""
import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.database.db import Database
from src.bot.handlers import router
from src.services.notification_service import NotificationService
from src.services.scheduler import ScheduledNotificationService, get_preset_schedule

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main application entry point."""
    # Get configuration
    bot_token = os.getenv("BOT_TOKEN")
    db_path = os.getenv("DATABASE_PATH", "bot_notifications.db")

    # Scheduling configuration
    schedule_mode = os.getenv("SCHEDULE_MODE", "cron")  # cron, polling, or immediate
    cron_schedule = os.getenv("CRON_SCHEDULE", "*/5 * * * *")  # Default: every 5 minutes
    polling_interval = int(os.getenv("POLLING_INTERVAL", "300"))  # Default: 5 minutes

    if not bot_token:
        raise ValueError("BOT_TOKEN not found in environment variables")

    # Initialize bot
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Initialize database
    db = Database(db_path)
    await db.connect()

    # Store database in bot data for access in handlers
    bot["db"] = db

    # Initialize notification service
    notification_service = NotificationService(db, bot)

    # Store notification service for external access
    bot["notification_service"] = notification_service

    # Initialize dispatcher
    dp = Dispatcher()
    dp.include_router(router)

    # Setup scheduler based on mode
    scheduled_service = None
    polling_task = None

    if schedule_mode == "cron":
        # Use cron scheduler
        scheduled_service = ScheduledNotificationService(notification_service)

        # Check if it's a preset
        preset_schedule = get_preset_schedule(cron_schedule)
        if preset_schedule:
            if isinstance(preset_schedule, list):
                scheduled_service.schedule_multiple(preset_schedule)
                logger.info(f"Using preset '{cron_schedule}' with schedules: {preset_schedule}")
            else:
                scheduled_service.schedule_cron(preset_schedule)
                logger.info(f"Using preset '{cron_schedule}': {preset_schedule}")
        else:
            scheduled_service.schedule_cron(cron_schedule)
            logger.info(f"Using cron schedule: {cron_schedule}")

        scheduled_service.start()

    elif schedule_mode == "polling":
        # Use simple polling
        logger.info(f"Using polling mode with interval: {polling_interval}s")
        polling_task = asyncio.create_task(
            notification_service.start_polling(interval=polling_interval)
        )

    elif schedule_mode == "immediate":
        # Events are processed immediately when created (no background task)
        logger.info("Using immediate processing mode (no background task)")

    logger.info("Bot started")

    try:
        # Start bot polling
        await dp.start_polling(bot)

    except KeyboardInterrupt:
        logger.info("Bot stopping...")
    finally:
        # Clean up
        if scheduled_service:
            scheduled_service.stop()
        if polling_task:
            notification_service.stop_polling()

        await db.close()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())

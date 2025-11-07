"""Example script for triggering events and sending notifications."""
import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot
from src.database.db import Database
from src.services.notification_service import NotificationService

load_dotenv()


async def main():
    """Example of triggering events."""
    bot_token = os.getenv("BOT_TOKEN")
    db_path = os.getenv("DATABASE_PATH", "bot_notifications.db")

    # Initialize
    bot = Bot(token=bot_token)
    db = Database(db_path)
    await db.connect()

    notification_service = NotificationService(db, bot)

    try:
        # Example 1: Simple event without conditions
        print("Creating 'price_alert' event...")
        await notification_service.create_event(
            event_type_name="price_alert",
            data={
                "product": "iPhone 15 Pro",
                "price": 999,
                "currency": "USD",
                "shop": "Apple Store"
            }
        )

        # Example 2: Event with complex data
        print("Creating 'order_status' event...")
        await notification_service.create_event(
            event_type_name="order_status",
            data={
                "order_id": "ORD-12345",
                "status": "shipped",
                "tracking_number": "TRACK123456",
                "estimated_delivery": "2024-12-01",
                "items": {
                    "count": 3,
                    "total": 1500
                }
            }
        )

        # Example 3: Event with conditions (only users with matching conditions will be notified)
        print("Creating 'stock_alert' event...")
        await notification_service.create_event(
            event_type_name="stock_alert",
            data={
                "product": "PlayStation 5",
                "stock": 10,
                "price": 499,
                "category": "gaming"
            }
        )

        # Example 4: Weather alert
        print("Creating 'weather_alert' event...")
        await notification_service.create_event(
            event_type_name="weather_alert",
            data={
                "city": "Moscow",
                "temperature": -15,
                "condition": "snow",
                "warning": "heavy snowfall expected"
            }
        )

        print("\n✅ All events created successfully!")
        print("Users subscribed to these events will receive notifications.")

    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

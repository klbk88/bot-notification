"""Example of adding subscriptions with conditions via code."""
import asyncio
import os
import json
from dotenv import load_dotenv

from src.database.db import Database

load_dotenv()


async def main():
    """Example of adding subscription with conditions."""
    db_path = os.getenv("DATABASE_PATH", "bot_notifications.db")

    db = Database(db_path)
    await db.connect()

    try:
        # Get user by telegram_id (replace with actual telegram_id)
        telegram_id = 123456789  # Replace with actual user telegram_id
        user = await db.get_user(telegram_id)

        if not user:
            print(f"❌ User with telegram_id {telegram_id} not found")
            print("User must use /start command in the bot first!")
            return

        # Get event type
        event_type = await db.get_event_type("price_alert")
        if not event_type:
            print("❌ Event type 'price_alert' not found")
            return

        # Define conditions
        # User will only be notified if price <= 500
        conditions = {
            "operator": "and",
            "rules": [
                {"field": "price", "operator": "<=", "value": 500},
                {"field": "category", "operator": "in", "value": ["electronics", "gaming"]}
            ]
        }

        # Add subscription with conditions
        await db.add_subscription(
            user_id=user['user_id'],
            event_type_id=event_type['id'],
            conditions=conditions
        )

        print(f"✅ Subscription added for user {telegram_id}")
        print(f"Event type: {event_type['name']}")
        print(f"Conditions: {json.dumps(conditions, indent=2)}")

        # Example 2: Subscribe to weather alerts for specific city
        event_type = await db.get_event_type("weather_alert")
        if event_type:
            conditions = {
                "operator": "and",
                "rules": [
                    {"field": "city", "operator": "==", "value": "Moscow"},
                    {"field": "temperature", "operator": "<", "value": -10}
                ]
            }

            await db.add_subscription(
                user_id=user['user_id'],
                event_type_id=event_type['id'],
                conditions=conditions
            )

            print(f"\n✅ Weather alert subscription added")
            print(f"Will notify only when temperature in Moscow < -10°C")

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())

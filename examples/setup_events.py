"""Example script for setting up event types."""
import asyncio
import os
from dotenv import load_dotenv

from src.database.db import Database

load_dotenv()


async def main():
    """Setup example event types."""
    db_path = os.getenv("DATABASE_PATH", "bot_notifications.db")

    db = Database(db_path)
    await db.connect()

    try:
        # Create example event types
        event_types = [
            {
                "name": "price_alert",
                "description": "Уведомления об изменении цен на товары"
            },
            {
                "name": "order_status",
                "description": "Обновления статуса заказов"
            },
            {
                "name": "stock_alert",
                "description": "Уведомления о появлении товара в наличии"
            },
            {
                "name": "weather_alert",
                "description": "Предупреждения о погоде"
            },
            {
                "name": "news_update",
                "description": "Новости и обновления"
            },
            {
                "name": "system_alert",
                "description": "Системные уведомления"
            }
        ]

        print("Creating event types...")
        for event_type in event_types:
            await db.add_event_type(event_type["name"], event_type["description"])
            print(f"✅ Created: {event_type['name']}")

        print("\n✅ All event types created successfully!")

        # Show all event types
        all_types = await db.get_all_event_types()
        print(f"\nTotal event types: {len(all_types)}")

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())

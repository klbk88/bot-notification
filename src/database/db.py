"""Database manager for bot notifications."""
import aiosqlite
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """Establish database connection."""
        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row
        await self._init_schema()

    async def close(self):
        """Close database connection."""
        if self.connection:
            await self.connection.close()

    async def _init_schema(self):
        """Initialize database schema."""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, 'r') as f:
            schema = f.read()

        await self.connection.executescript(schema)
        await self.connection.commit()

    # User methods
    async def add_user(self, telegram_id: int, username: str = None,
                       first_name: str = None, last_name: str = None) -> int:
        """Add or update user."""
        cursor = await self.connection.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name
            RETURNING user_id
            """,
            (telegram_id, username, first_name, last_name)
        )
        result = await cursor.fetchone()
        await self.connection.commit()
        return result['user_id']

    async def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by telegram_id."""
        cursor = await self.connection.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_all_active_users(self) -> List[Dict]:
        """Get all active users."""
        cursor = await self.connection.execute(
            "SELECT * FROM users WHERE is_active = 1"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # Event type methods
    async def add_event_type(self, name: str, description: str = None) -> int:
        """Add event type."""
        cursor = await self.connection.execute(
            """
            INSERT OR IGNORE INTO event_types (name, description)
            VALUES (?, ?)
            RETURNING id
            """,
            (name, description)
        )
        result = await cursor.fetchone()
        await self.connection.commit()

        if result:
            return result['id']

        # If already exists, get the id
        cursor = await self.connection.execute(
            "SELECT id FROM event_types WHERE name = ?",
            (name,)
        )
        result = await cursor.fetchone()
        return result['id']

    async def get_event_type(self, name: str) -> Optional[Dict]:
        """Get event type by name."""
        cursor = await self.connection.execute(
            "SELECT * FROM event_types WHERE name = ?",
            (name,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_all_event_types(self) -> List[Dict]:
        """Get all event types."""
        cursor = await self.connection.execute(
            "SELECT * FROM event_types ORDER BY name"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # Subscription methods
    async def add_subscription(self, user_id: int, event_type_id: int,
                               conditions: Dict = None) -> int:
        """Add or update user subscription."""
        conditions_json = json.dumps(conditions) if conditions else None
        cursor = await self.connection.execute(
            """
            INSERT INTO user_subscriptions (user_id, event_type_id, conditions)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, event_type_id) DO UPDATE SET
                conditions = excluded.conditions,
                is_active = 1
            RETURNING id
            """,
            (user_id, event_type_id, conditions_json)
        )
        result = await cursor.fetchone()
        await self.connection.commit()
        return result['id']

    async def remove_subscription(self, user_id: int, event_type_id: int):
        """Remove user subscription."""
        await self.connection.execute(
            """
            UPDATE user_subscriptions
            SET is_active = 0
            WHERE user_id = ? AND event_type_id = ?
            """,
            (user_id, event_type_id)
        )
        await self.connection.commit()

    async def get_user_subscriptions(self, user_id: int) -> List[Dict]:
        """Get all active subscriptions for a user."""
        cursor = await self.connection.execute(
            """
            SELECT us.*, et.name as event_name, et.description as event_description
            FROM user_subscriptions us
            JOIN event_types et ON us.event_type_id = et.id
            WHERE us.user_id = ? AND us.is_active = 1
            """,
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_subscribers_for_event(self, event_type_id: int) -> List[Dict]:
        """Get all users subscribed to an event type."""
        cursor = await self.connection.execute(
            """
            SELECT u.*, us.conditions
            FROM users u
            JOIN user_subscriptions us ON u.user_id = us.user_id
            WHERE us.event_type_id = ? AND us.is_active = 1 AND u.is_active = 1
            """,
            (event_type_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # Event methods
    async def add_event(self, event_type_id: int, data: Dict) -> int:
        """Add new event."""
        data_json = json.dumps(data)
        cursor = await self.connection.execute(
            """
            INSERT INTO events (event_type_id, data)
            VALUES (?, ?)
            RETURNING id
            """,
            (event_type_id, data_json)
        )
        result = await cursor.fetchone()
        await self.connection.commit()
        return result['id']

    async def get_unprocessed_events(self) -> List[Dict]:
        """Get all unprocessed events."""
        cursor = await self.connection.execute(
            """
            SELECT e.*, et.name as event_name
            FROM events e
            JOIN event_types et ON e.event_type_id = et.id
            WHERE e.processed = 0
            ORDER BY e.created_at
            """
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def mark_event_processed(self, event_id: int):
        """Mark event as processed."""
        await self.connection.execute(
            "UPDATE events SET processed = 1 WHERE id = ?",
            (event_id,)
        )
        await self.connection.commit()

    # Notification history methods
    async def add_notification(self, user_id: int, event_id: int,
                               message: str, status: str = 'sent',
                               error_message: str = None) -> int:
        """Add notification to history."""
        cursor = await self.connection.execute(
            """
            INSERT INTO notification_history
            (user_id, event_id, message, status, error_message)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id
            """,
            (user_id, event_id, message, status, error_message)
        )
        result = await cursor.fetchone()
        await self.connection.commit()
        return result['id']

    async def get_user_notifications(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user notification history."""
        cursor = await self.connection.execute(
            """
            SELECT nh.*, e.data as event_data, et.name as event_name
            FROM notification_history nh
            JOIN events e ON nh.event_id = e.id
            JOIN event_types et ON e.event_type_id = et.id
            WHERE nh.user_id = ?
            ORDER BY nh.sent_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

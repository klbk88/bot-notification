"""Notification models and types."""
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class NotificationStatus(str, Enum):
    """Notification status."""
    SENT = "sent"
    FAILED = "failed"
    PENDING = "pending"


class EventData(BaseModel):
    """Event data model."""
    event_type: str
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None


class UserSubscription(BaseModel):
    """User subscription model."""
    user_id: int
    telegram_id: int
    event_type: str
    conditions: Optional[Dict[str, Any]] = None


class NotificationMessage(BaseModel):
    """Notification message model."""
    user_id: int
    telegram_id: int
    message: str
    event_id: int

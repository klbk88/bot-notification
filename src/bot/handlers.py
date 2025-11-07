"""Telegram bot handlers."""
import json
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..database.db import Database

router = Router()


async def get_db(message: Message) -> Database:
    """Get database instance from bot data."""
    return message.bot.get("db")


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    db = await get_db(message)

    # Register user
    await db.add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    await message.answer(
        "👋 Привет! Я бот уведомлений.\n\n"
        "Я могу отправлять вам уведомления на основе событий и условий.\n\n"
        "Доступные команды:\n"
        "/subscribe - Подписаться на события\n"
        "/unsubscribe - Отписаться от событий\n"
        "/my_subscriptions - Мои подписки\n"
        "/events - Доступные типы событий\n"
        "/history - История уведомлений"
    )


@router.message(Command("events"))
async def cmd_events(message: Message):
    """Show available event types."""
    db = await get_db(message)
    event_types = await db.get_all_event_types()

    if not event_types:
        await message.answer("📭 Пока нет доступных типов событий.")
        return

    text = "📋 <b>Доступные типы событий:</b>\n\n"
    for event_type in event_types:
        text += f"• <b>{event_type['name']}</b>"
        if event_type['description']:
            text += f"\n  {event_type['description']}"
        text += "\n\n"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    """Show subscription menu."""
    db = await get_db(message)
    event_types = await db.get_all_event_types()

    if not event_types:
        await message.answer("📭 Пока нет доступных типов событий.")
        return

    # Get user
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Пожалуйста, сначала используйте /start")
        return

    # Get current subscriptions
    subscriptions = await db.get_user_subscriptions(user['user_id'])
    subscribed_ids = {sub['event_type_id'] for sub in subscriptions}

    # Create keyboard
    builder = InlineKeyboardBuilder()
    for event_type in event_types:
        is_subscribed = event_type['id'] in subscribed_ids
        text = f"{'✅' if is_subscribed else '➕'} {event_type['name']}"
        callback_data = f"unsub:{event_type['id']}" if is_subscribed else f"sub:{event_type['id']}"
        builder.button(text=text, callback_data=callback_data)

    builder.adjust(1)

    await message.answer(
        "📝 <b>Управление подписками:</b>\n\n"
        "Выберите события для подписки/отписки:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("sub:"))
async def callback_subscribe(callback: CallbackQuery):
    """Handle subscription."""
    db = callback.bot.get("db")
    event_type_id = int(callback.data.split(":")[1])

    # Get user
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Ошибка: пользователь не найден")
        return

    # Add subscription
    await db.add_subscription(user['user_id'], event_type_id)

    # Get event type name
    event_types = await db.get_all_event_types()
    event_name = next((et['name'] for et in event_types if et['id'] == event_type_id), "Unknown")

    await callback.answer(f"✅ Подписка на '{event_name}' активирована")

    # Update keyboard
    await cmd_subscribe(callback.message)


@router.callback_query(F.data.startswith("unsub:"))
async def callback_unsubscribe(callback: CallbackQuery):
    """Handle unsubscription."""
    db = callback.bot.get("db")
    event_type_id = int(callback.data.split(":")[1])

    # Get user
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Ошибка: пользователь не найден")
        return

    # Remove subscription
    await db.remove_subscription(user['user_id'], event_type_id)

    # Get event type name
    event_types = await db.get_all_event_types()
    event_name = next((et['name'] for et in event_types if et['id'] == event_type_id), "Unknown")

    await callback.answer(f"❌ Подписка на '{event_name}' отменена")

    # Update keyboard
    await cmd_subscribe(callback.message)


@router.message(Command("my_subscriptions"))
async def cmd_my_subscriptions(message: Message):
    """Show user's subscriptions."""
    db = await get_db(message)

    # Get user
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Пожалуйста, сначала используйте /start")
        return

    # Get subscriptions
    subscriptions = await db.get_user_subscriptions(user['user_id'])

    if not subscriptions:
        await message.answer("📭 У вас пока нет активных подписок.\n\nИспользуйте /subscribe для подписки.")
        return

    text = "📌 <b>Ваши подписки:</b>\n\n"
    for sub in subscriptions:
        text += f"• <b>{sub['event_name']}</b>"
        if sub['event_description']:
            text += f"\n  {sub['event_description']}"
        if sub['conditions']:
            text += f"\n  <i>С условиями</i>"
        text += "\n\n"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("history"))
async def cmd_history(message: Message):
    """Show notification history."""
    db = await get_db(message)

    # Get user
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Пожалуйста, сначала используйте /start")
        return

    # Get history
    history = await db.get_user_notifications(user['user_id'], limit=10)

    if not history:
        await message.answer("📭 История уведомлений пуста.")
        return

    text = "📜 <b>История уведомлений:</b>\n\n"
    for notif in history:
        status_emoji = "✅" if notif['status'] == 'sent' else "❌"
        text += f"{status_emoji} <b>{notif['event_name']}</b>\n"
        text += f"  {notif['sent_at']}\n\n"

    await message.answer(text, parse_mode="HTML")

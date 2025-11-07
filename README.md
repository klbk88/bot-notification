# Telegram Bot Notification System

Система уведомлений для Telegram бота с поддержкой событий и условий из базы данных.

## Возможности

- ✅ Отправка уведомлений пользователям по событиям из БД
- ✅ Гибкая система условий для фильтрации уведомлений
- ✅ Подписки пользователей на типы событий
- ✅ Поддержка сложных условий (AND/OR логика)
- ✅ Асинхронная обработка событий
- ✅ История уведомлений
- ✅ SQLite база данных

## Архитектура

```
bot-notification/
├── src/
│   ├── bot/
│   │   ├── __init__.py
│   │   └── handlers.py          # Обработчики команд бота
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                # Менеджер базы данных
│   │   └── schema.sql           # Схема БД
│   ├── services/
│   │   ├── __init__.py
│   │   ├── notification_service.py  # Сервис уведомлений
│   │   └── condition_checker.py     # Проверка условий
│   └── models/
│       ├── __init__.py
│       └── notification.py      # Модели данных
├── examples/
│   ├── setup_events.py          # Настройка типов событий
│   ├── trigger_events.py        # Примеры создания событий
│   └── add_subscription_with_conditions.py  # Подписки с условиями
├── main.py                      # Главный файл запуска
├── requirements.txt
├── .env.example
└── README.md
```

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repo-url>
cd bot-notification
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте `.env` файл:
```bash
cp .env.example .env
```

4. Добавьте токен бота в `.env`:
```
BOT_TOKEN=your_telegram_bot_token_here
DATABASE_PATH=bot_notifications.db
```

## Быстрый старт

### 1. Настройка типов событий

Создайте типы событий, на которые пользователи смогут подписаться:

```bash
python examples/setup_events.py
```

### 2. Запуск бота

```bash
python main.py
```

### 3. Использование бота

Пользователи могут использовать следующие команды:

- `/start` - Регистрация в боте
- `/subscribe` - Подписаться на события
- `/unsubscribe` - Отписаться от событий
- `/my_subscriptions` - Список подписок
- `/events` - Доступные типы событий
- `/history` - История уведомлений

### 4. Отправка событий

Создайте события программно:

```bash
python examples/trigger_events.py
```

## Примеры использования

### Создание события из кода

```python
from src.services.notification_service import NotificationService

# Создать событие
await notification_service.create_event(
    event_type_name="price_alert",
    data={
        "product": "iPhone 15 Pro",
        "price": 999,
        "currency": "USD",
        "shop": "Apple Store"
    }
)
```

### Подписка с условиями

Пользователи будут получать уведомления только если данные события соответствуют условиям:

```python
# Подписка на уведомления о ценах <= 500
conditions = {
    "operator": "and",
    "rules": [
        {"field": "price", "operator": "<=", "value": 500},
        {"field": "category", "operator": "in", "value": ["electronics"]}
    ]
}

await db.add_subscription(
    user_id=user_id,
    event_type_id=event_type_id,
    conditions=conditions
)
```

### Операторы условий

Поддерживаются следующие операторы:

- `==` - равно
- `!=` - не равно
- `>` - больше
- `>=` - больше или равно
- `<` - меньше
- `<=` - меньше или равно
- `in` - входит в список
- `not_in` - не входит в список
- `contains` - содержит подстроку
- `starts_with` - начинается с
- `ends_with` - заканчивается на

### Сложные условия

Можно комбинировать условия с AND/OR логикой:

```python
conditions = {
    "operator": "or",  # OR логика
    "rules": [
        {
            "operator": "and",  # AND логика для первой группы
            "rules": [
                {"field": "price", "operator": "<=", "value": 500},
                {"field": "category", "operator": "==", "value": "electronics"}
            ]
        },
        {
            "operator": "and",  # AND логика для второй группы
            "rules": [
                {"field": "discount", "operator": ">=", "value": 50},
                {"field": "brand", "operator": "==", "value": "Apple"}
            ]
        }
    ]
}
```

### Вложенные поля

Поддерживается dot-нотация для вложенных полей:

```python
# Данные события
event_data = {
    "product": "iPhone",
    "details": {
        "price": 999,
        "stock": 10
    }
}

# Условие для вложенного поля
conditions = {
    "operator": "and",
    "rules": [
        {"field": "details.price", "operator": "<=", "value": 1000},
        {"field": "details.stock", "operator": ">", "value": 0}
    ]
}
```

## API

### Database

```python
db = Database("bot_notifications.db")
await db.connect()

# Пользователи
await db.add_user(telegram_id, username, first_name, last_name)
await db.get_user(telegram_id)
await db.get_all_active_users()

# Типы событий
await db.add_event_type(name, description)
await db.get_event_type(name)
await db.get_all_event_types()

# Подписки
await db.add_subscription(user_id, event_type_id, conditions)
await db.remove_subscription(user_id, event_type_id)
await db.get_user_subscriptions(user_id)

# События
await db.add_event(event_type_id, data)
await db.get_unprocessed_events()
await db.mark_event_processed(event_id)

# История
await db.get_user_notifications(user_id, limit)
```

### NotificationService

```python
service = NotificationService(db, bot)

# Создать событие (автоматически отправит уведомления)
await service.create_event("price_alert", {"price": 100})

# Обработать все необработанные события
await service.process_events()

# Запустить polling событий
await service.start_polling(interval=5)
```

## Интеграция в существующее приложение

```python
from aiogram import Bot
from src.database.db import Database
from src.services.notification_service import NotificationService

# Инициализация
bot = Bot(token="YOUR_TOKEN")
db = Database("bot_notifications.db")
await db.connect()

notification_service = NotificationService(db, bot)

# Использование в вашем коде
async def on_price_change(product, new_price):
    await notification_service.create_event(
        event_type_name="price_alert",
        data={
            "product": product,
            "price": new_price,
            "timestamp": datetime.now().isoformat()
        }
    )
```

## Структура базы данных

- `users` - Пользователи бота
- `event_types` - Типы событий
- `user_subscriptions` - Подписки пользователей
- `events` - События для обработки
- `notification_history` - История отправленных уведомлений

## Требования

- Python 3.8+
- aiogram 3.4.1
- aiosqlite 0.19.0
- python-dotenv 1.0.0
- pydantic 2.5.3

## Лицензия

MIT

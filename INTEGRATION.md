# Руководство по интеграции системы уведомлений

Это руководство поможет интегрировать систему уведомлений в ваш существующий проект.

## Вариант 1: Интеграция в существующий Telegram бот

### Шаг 1: Копирование файлов

Скопируйте следующие директории в ваш проект:

```bash
# Из bot-notification в ваш проект
cp -r src/database/* your_project/src/database/
cp -r src/services/notification_service.py your_project/src/services/
cp -r src/services/condition_checker.py your_project/src/services/
cp -r src/services/scheduler.py your_project/src/services/
cp -r src/models/notification.py your_project/src/models/
```

### Шаг 2: Установка зависимостей

Добавьте в `requirements.txt` вашего проекта:

```txt
aiosqlite==0.19.0
aiocron==1.8
```

Установите:

```bash
pip install -r requirements.txt
```

### Шаг 3: Инициализация в вашем боте

В вашем главном файле бота (например, `main.py` или `bot.py`):

```python
from aiogram import Bot, Dispatcher
from src.database.db import Database
from src.services.notification_service import NotificationService
from src.services.scheduler import ScheduledNotificationService

# ... ваш существующий код ...

async def main():
    # Ваша инициализация бота
    bot = Bot(token=YOUR_TOKEN)
    dp = Dispatcher()

    # ДОБАВИТЬ: Инициализация БД уведомлений
    notification_db = Database("notifications.db")
    await notification_db.connect()

    # ДОБАВИТЬ: Инициализация сервиса уведомлений
    notification_service = NotificationService(notification_db, bot)

    # ДОБАВИТЬ: Настройка расписания (опционально)
    scheduled_service = ScheduledNotificationService(notification_service)
    scheduled_service.schedule_cron('*/10 * * * *')  # Каждые 10 минут
    scheduled_service.start()

    # Сохраняем для доступа из других частей приложения
    bot["notification_service"] = notification_service
    bot["notification_db"] = notification_db

    # ... ваш существующий код запуска бота ...

    try:
        await dp.start_polling(bot)
    finally:
        # ДОБАВИТЬ: Очистка
        scheduled_service.stop()
        await notification_db.close()
```

### Шаг 4: Добавление handlers (опционально)

Если хотите добавить команды управления подписками:

```python
# В вашем файле с handlers
from src.bot.handlers import router as notification_router

# В main()
dp.include_router(notification_router)
```

Или создайте свои handlers:

```python
from aiogram import Router
from aiogram.filters import Command

router = Router()

@router.message(Command("subscribe"))
async def subscribe_handler(message: Message):
    db = message.bot.get("notification_db")
    # ... ваша логика подписки
```

### Шаг 5: Использование в коде

Теперь в любом месте вашего проекта можете создавать события:

```python
# Пример: при изменении цены товара
async def on_price_changed(product_id, old_price, new_price):
    notification_service = bot.get("notification_service")

    await notification_service.create_event(
        event_type_name="price_change",
        data={
            "product_id": product_id,
            "old_price": old_price,
            "new_price": new_price,
            "discount_percent": round((old_price - new_price) / old_price * 100, 2)
        }
    )
```

## Вариант 2: Интеграция как отдельный модуль

### Структура проекта

```
your_project/
├── your_existing_code/
│   └── ...
├── notifications/              # <-- Добавить эту папку
│   ├── __init__.py
│   ├── database/
│   ├── services/
│   └── models/
└── main.py
```

### Создание модуля notifications

```python
# notifications/__init__.py
from .services.notification_service import NotificationService
from .services.scheduler import ScheduledNotificationService
from .database.db import Database

__all__ = ['NotificationService', 'ScheduledNotificationService', 'Database']
```

### Использование

```python
from notifications import NotificationService, ScheduledNotificationService, Database

# Инициализация
db = Database("notifications.db")
await db.connect()

notification_service = NotificationService(db, your_bot)
```

## Вариант 3: Интеграция как микросервис

### Запуск как отдельный сервис

Можно запустить бот уведомлений отдельно и общаться через API или очередь сообщений.

#### Создание API endpoint

```python
# api.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class EventCreate(BaseModel):
    event_type: str
    data: dict

@app.post("/events")
async def create_event(event: EventCreate):
    await notification_service.create_event(
        event_type_name=event.event_type,
        data=event.data
    )
    return {"status": "created"}

# Запуск: uvicorn api:app --port 8000
```

#### Использование из основного приложения

```python
import httpx

async def send_notification(event_type: str, data: dict):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://localhost:8000/events",
            json={"event_type": event_type, "data": data}
        )
```

## Примеры интеграции для разных сценариев

### Пример 1: E-commerce проект

```python
# В вашем коде обработки заказов
async def process_order(order_id):
    # ... ваша логика обработки заказа ...

    # Отправить уведомление
    await notification_service.create_event(
        event_type_name="order_status",
        data={
            "order_id": order_id,
            "status": "processing",
            "customer_id": order.customer_id
        }
    )

# При отгрузке
async def ship_order(order_id, tracking_number):
    # ... ваша логика отгрузки ...

    await notification_service.create_event(
        event_type_name="order_shipped",
        data={
            "order_id": order_id,
            "tracking_number": tracking_number,
            "estimated_delivery": delivery_date
        }
    )
```

### Пример 2: Мониторинг системы

```python
# В вашем коде мониторинга
async def check_system_health():
    cpu_usage = get_cpu_usage()
    memory_usage = get_memory_usage()

    if cpu_usage > 80:
        await notification_service.create_event(
            event_type_name="system_alert",
            data={
                "type": "high_cpu",
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "severity": "warning"
            }
        )
```

### Пример 3: CRM система

```python
# При создании нового лида
async def create_lead(lead_data):
    # ... создание лида ...

    await notification_service.create_event(
        event_type_name="new_lead",
        data={
            "lead_id": lead.id,
            "source": lead.source,
            "value": lead.estimated_value,
            "assigned_to": lead.manager_id
        }
    )
```

### Пример 4: Новостной портал

```python
# При публикации новости
async def publish_article(article):
    # ... публикация статьи ...

    await notification_service.create_event(
        event_type_name="new_article",
        data={
            "article_id": article.id,
            "title": article.title,
            "category": article.category,
            "tags": article.tags,
            "author": article.author
        }
    )
```

## Настройка условий подписки

Пользователи могут подписаться с условиями программно:

```python
# Настройка подписки для администратора
async def setup_admin_subscriptions(admin_telegram_id):
    db = Database("notifications.db")
    await db.connect()

    # Получить пользователя
    user = await db.get_user(admin_telegram_id)

    # Подписаться на критические алерты
    event_type = await db.get_event_type("system_alert")
    await db.add_subscription(
        user_id=user['user_id'],
        event_type_id=event_type['id'],
        conditions={
            "operator": "and",
            "rules": [
                {"field": "severity", "operator": "==", "value": "critical"}
            ]
        }
    )

    await db.close()
```

## Расширенная интеграция

### Добавление кастомного форматирования сообщений

```python
from src.services.notification_service import NotificationService

class CustomNotificationService(NotificationService):
    def _format_message(self, event_name: str, event_data: dict) -> str:
        """Кастомное форматирование сообщений."""

        if event_name == "order_status":
            return (
                f"📦 <b>Обновление заказа #{event_data['order_id']}</b>\n\n"
                f"Статус: {event_data['status']}\n"
                f"Трек-номер: {event_data.get('tracking_number', 'N/A')}"
            )

        elif event_name == "price_alert":
            return (
                f"💰 <b>Изменение цены!</b>\n\n"
                f"Товар: {event_data['product']}\n"
                f"Новая цена: {event_data['price']} {event_data['currency']}\n"
                f"Скидка: {event_data.get('discount', 0)}%"
            )

        # Fallback на стандартное форматирование
        return super()._format_message(event_name, event_data)

# Использование
notification_service = CustomNotificationService(db, bot)
```

### Добавление middleware для фильтрации

```python
class FilteredNotificationService(NotificationService):
    async def create_event(self, event_type_name: str, data: dict) -> int:
        # Фильтрация перед созданием события
        if self._should_process_event(event_type_name, data):
            return await super().create_event(event_type_name, data)
        return -1

    def _should_process_event(self, event_type: str, data: dict) -> bool:
        # Ваша логика фильтрации
        if event_type == "price_alert" and data.get("price", 0) < 10:
            return False  # Игнорировать дешевые товары
        return True
```

## Тестирование интеграции

```python
# test_integration.py
import asyncio
from aiogram import Bot
from notifications import Database, NotificationService

async def test_notifications():
    bot = Bot(token="YOUR_TEST_TOKEN")
    db = Database("test_notifications.db")
    await db.connect()

    service = NotificationService(db, bot)

    # Создать тестовое событие
    event_id = await service.create_event(
        event_type_name="test_event",
        data={"message": "Test notification"}
    )

    print(f"Created test event: {event_id}")

    await db.close()
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_notifications())
```

## Миграция существующих данных

Если у вас уже есть система пользователей:

```python
async def migrate_users_to_notifications():
    """Миграция пользователей из существующей БД."""

    # Ваша существующая БД
    your_db = YourDatabase()
    users = await your_db.get_all_users()

    # БД уведомлений
    notification_db = Database("notifications.db")
    await notification_db.connect()

    for user in users:
        await notification_db.add_user(
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

    print(f"Migrated {len(users)} users")
    await notification_db.close()
```

## Мониторинг и логирование

```python
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('notifications.log'),
        logging.StreamHandler()
    ]
)

# Логи будут автоматически записываться NotificationService
```

## Troubleshooting

### Проблема: События не обрабатываются

Проверьте, что scheduler запущен:

```python
scheduled_service.start()
```

### Проблема: Уведомления не отправляются

1. Проверьте, что пользователи подписаны на события
2. Проверьте условия подписки
3. Проверьте логи на ошибки отправки

```python
# Проверить подписки пользователя
subscriptions = await db.get_user_subscriptions(user_id)
print(subscriptions)
```

### Проблема: Дублирование уведомлений

Убедитесь, что не запущено несколько экземпляров scheduler:

```python
# Запускать только один раз!
scheduled_service.start()
```

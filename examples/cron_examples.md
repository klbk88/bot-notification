# Примеры настройки Cron расписания

## Формат Cron выражений

```
* * * * *
│ │ │ │ │
│ │ │ │ └─── день недели (0-6, 0=Воскресенье)
│ │ │ └───── месяц (1-12)
│ │ └─────── день месяца (1-31)
│ └───────── час (0-23)
└─────────── минута (0-59)
```

## Часто используемые расписания

### Каждые N минут

```bash
# Каждую минуту
CRON_SCHEDULE="* * * * *"

# Каждые 5 минут
CRON_SCHEDULE="*/5 * * * *"

# Каждые 10 минут
CRON_SCHEDULE="*/10 * * * *"

# Каждые 15 минут
CRON_SCHEDULE="*/15 * * * *"

# Каждые 30 минут
CRON_SCHEDULE="*/30 * * * *"
```

### Почасовые расписания

```bash
# Каждый час в 0 минут (9:00, 10:00, 11:00...)
CRON_SCHEDULE="0 * * * *"

# Каждый час в 15 минут (9:15, 10:15, 11:15...)
CRON_SCHEDULE="15 * * * *"

# Каждые 2 часа
CRON_SCHEDULE="0 */2 * * *"

# Каждые 6 часов
CRON_SCHEDULE="0 */6 * * *"
```

### Ежедневные расписания

```bash
# Каждый день в 9:00
CRON_SCHEDULE="0 9 * * *"

# Каждый день в 9:30
CRON_SCHEDULE="30 9 * * *"

# Каждый день в полночь
CRON_SCHEDULE="0 0 * * *"

# Дважды в день (9:00 и 18:00)
CRON_SCHEDULE="0 9,18 * * *"

# Трижды в день (9:00, 14:00, 20:00)
CRON_SCHEDULE="0 9,14,20 * * *"
```

### Еженедельные расписания

```bash
# По понедельникам в 9:00
CRON_SCHEDULE="0 9 * * 1"

# По пятницам в 17:00
CRON_SCHEDULE="0 17 * * 5"

# Рабочие дни (пн-пт) в 9:00
CRON_SCHEDULE="0 9 * * 1-5"

# Выходные дни (сб-вс) в 10:00
CRON_SCHEDULE="0 10 * * 0,6"

# Каждую среду и субботу в 12:00
CRON_SCHEDULE="0 12 * * 3,6"
```

### Ежемесячные расписания

```bash
# 1-го числа каждого месяца в 9:00
CRON_SCHEDULE="0 9 1 * *"

# 15-го числа каждого месяца в 12:00
CRON_SCHEDULE="0 12 15 * *"

# Последний день месяца невозможен в cron
# (используйте скрипт с проверкой даты)
```

## Готовые пресеты

В `.env` можно использовать готовые пресеты вместо cron выражений:

```bash
# Каждые 5 минут
CRON_SCHEDULE=frequent

# Каждые 15 минут
CRON_SCHEDULE=moderate

# Каждый час
CRON_SCHEDULE=hourly

# Дважды в день (9:00 и 18:00)
CRON_SCHEDULE=twice_daily

# Каждый день в 9:00
CRON_SCHEDULE=daily

# Рабочие дни в 9:00
CRON_SCHEDULE=weekdays

# Выходные в 10:00
CRON_SCHEDULE=weekends
```

## Примеры использования в .env

### Пример 1: Частая проверка (каждые 5 минут)

```env
BOT_TOKEN=your_token_here
DATABASE_PATH=bot_notifications.db
SCHEDULE_MODE=cron
CRON_SCHEDULE=*/5 * * * *
```

### Пример 2: Умеренная проверка (каждые 30 минут)

```env
BOT_TOKEN=your_token_here
DATABASE_PATH=bot_notifications.db
SCHEDULE_MODE=cron
CRON_SCHEDULE=*/30 * * * *
```

### Пример 3: Рабочие часы (каждый час с 9 до 18)

```env
BOT_TOKEN=your_token_here
DATABASE_PATH=bot_notifications.db
SCHEDULE_MODE=cron
CRON_SCHEDULE=0 9-18 * * 1-5
```

### Пример 4: Использование пресета

```env
BOT_TOKEN=your_token_here
DATABASE_PATH=bot_notifications.db
SCHEDULE_MODE=cron
CRON_SCHEDULE=moderate
```

### Пример 5: Режим polling (простой)

```env
BOT_TOKEN=your_token_here
DATABASE_PATH=bot_notifications.db
SCHEDULE_MODE=polling
POLLING_INTERVAL=300
```

### Пример 6: Немедленная обработка

```env
BOT_TOKEN=your_token_here
DATABASE_PATH=bot_notifications.db
SCHEDULE_MODE=immediate
```

## Программное создание расписаний

Вы можете создавать сложные расписания программно:

```python
from src.services.scheduler import ScheduledNotificationService
from src.services.notification_service import NotificationService

# Инициализация
notification_service = NotificationService(db, bot)
scheduled_service = ScheduledNotificationService(notification_service)

# Добавить одно расписание
scheduled_service.schedule_cron('*/10 * * * *')

# Добавить несколько расписаний
scheduled_service.schedule_multiple([
    '0 9 * * *',    # Каждый день в 9:00
    '0 18 * * *',   # Каждый день в 18:00
    '*/30 9-18 * * 1-5'  # Каждые 30 минут в рабочие часы
])

# Запустить
scheduled_service.start()

# Получить информацию о расписаниях
info = scheduled_service.get_schedule_info()
print(info)
```

## Тестирование расписания

Чтобы проверить, когда сработает ваше расписание, используйте онлайн-инструменты:
- https://crontab.guru/ - визуализация cron выражений
- https://crontab-generator.org/ - генератор cron выражений

## Часто задаваемые вопросы

### Как запустить каждые X секунд?

Cron не поддерживает секунды. Минимальная единица - минута.
Для интервалов менее минуты используйте режим `polling`:

```env
SCHEDULE_MODE=polling
POLLING_INTERVAL=30  # 30 секунд
```

### Как запустить в определенное время UTC?

Cron использует системное время сервера. Убедитесь, что время сервера настроено правильно:

```bash
# Проверить текущее время сервера
date

# Проверить часовой пояс
timedatectl
```

### Можно ли использовать несколько расписаний одновременно?

Да, используйте пресет `twice_daily` или создайте программно:

```python
scheduled_service.schedule_multiple([
    '0 9 * * *',
    '0 14 * * *',
    '0 20 * * *'
])
```

### Как отключить фоновую обработку?

Используйте режим `immediate` - события будут обрабатываться только при явном вызове:

```env
SCHEDULE_MODE=immediate
```

Затем вызывайте обработку вручную:

```python
await notification_service.process_events()
```

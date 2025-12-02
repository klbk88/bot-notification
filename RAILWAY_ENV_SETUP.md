# 🚂 Railway Environment Variables Setup

## Обязательные переменные для Railway

### 1️⃣ Database (Railway предоставит автоматически)

Railway автоматически создаст PostgreSQL и предоставит:

```bash
DATABASE_URL=postgresql://user:pass@host.railway.app:5432/railway
```

✅ **Ничего делать не нужно** - Railway сам добавит при подключении PostgreSQL service.

---

### 2️⃣ Redis (Railway предоставит автоматически)

Railway автоматически создаст Redis и предоставит:

```bash
REDIS_URL=redis://default:pass@redis.railway.app:6379
```

✅ **Ничего делать не нужно** - Railway сам добавит при подключении Redis service.

---

### 3️⃣ JWT Secrets (обязательно!)

**Нужно создать случайные секретные ключи:**

```bash
# Генерация на MacOS/Linux:
openssl rand -hex 32

# Или Python:
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Добавить на Railway:**

```bash
SECRET_KEY=ваш_случайный_ключ_32_символа
JWT_SECRET_KEY=другой_случайный_ключ_32_символа
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

### 4️⃣ Admin Bot Token (обязательно!)

**Получить от @BotFather:**

1. Открыть @BotFather в Telegram
2. Отправить `/newbot`
3. Назвать бота: "My UTM Admin Bot"
4. Username: `your_utm_admin_bot`
5. Скопировать токен

**Добавить на Railway:**

```bash
ADMIN_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

---

### 5️⃣ Admin User IDs (обязательно!)

**Получить свой Telegram ID:**

1. Открыть @userinfobot в Telegram
2. Отправить `/start`
3. Бот пришлет ваш ID (например: 123456789)

**Добавить на Railway:**

```bash
ADMIN_IDS=123456789
# Если несколько админов: 123456789,987654321
```

---

### 6️⃣ Tracking API URL (обязательно!)

**После первого деплоя на Railway:**

1. Railway предоставит URL типа: `https://your-app-name.up.railway.app`
2. Добавить эту переменную

**Добавить на Railway:**

```bash
TRACKING_API_URL=https://your-app-name.up.railway.app
```

⚠️ **Сначала задеплойте**, потом добавьте эту переменную и **редеплойте**.

---

### 7️⃣ Telegram Bot Username (обязательно!)

**Username вашего LOOTBOX бота** (не admin бота!):

```bash
TELEGRAM_BOT_USERNAME=your_lootbox_bot
# Без @!
```

---

### 8️⃣ Landing Settings (обязательно!)

```bash
# URL лендингов (будет тот же что и TRACKING_API_URL)
LANDING_BASE_URL=https://your-app-name.up.railway.app/api/v1/landing/l

# Тип редиректа (рекомендуется bot)
LANDING_REDIRECT_TYPE=bot

# Название канала для лендингов
CHANNEL_NAME=Your Lootbox Game
CHANNEL_DESCRIPTION=Open lootboxes and win prizes!
```

---

## 🔧 Опциональные переменные

### AI Services (для creative analysis)

**Anthropic Claude (рекомендуется):**

Получить на https://console.anthropic.com/

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

**Без этого:**
- ✅ Трекинг работает
- ✅ ML модели работают
- ❌ Автоматический анализ видео через AI не работает (будет fallback)

---

### Storage для видео (опционально)

**По умолчанию: local storage (достаточно для MVP)**

```bash
STORAGE_TYPE=local
STORAGE_LOCAL_PATH=/tmp/utm-videos
```

**Для production - Cloudflare R2 (рекомендуется):**

Получить на https://dash.cloudflare.com/

```bash
STORAGE_TYPE=r2
STORAGE_ENDPOINT=https://[account-id].r2.cloudflarestorage.com
STORAGE_ACCESS_KEY=your_r2_access_key
STORAGE_SECRET_KEY=your_r2_secret_key
STORAGE_REGION=auto
STORAGE_BUCKET=utm-videos
```

**Преимущества R2:**
- $0.015/GB/month (дешевле S3)
- FREE egress (не платите за отдачу видео)

---

## 📋 Полный чеклист для Railway

### Обязательные (минимум для работы):

- [ ] `DATABASE_URL` - Railway добавит автоматически ✅
- [ ] `REDIS_URL` - Railway добавит автоматически ✅
- [ ] `SECRET_KEY` - генерируете случайный ключ
- [ ] `JWT_SECRET_KEY` - генерируете случайный ключ
- [ ] `JWT_ALGORITHM=HS256`
- [ ] `ADMIN_BOT_TOKEN` - от @BotFather
- [ ] `ADMIN_IDS` - ваш Telegram ID
- [ ] `TELEGRAM_BOT_USERNAME` - username lootbox бота
- [ ] `TRACKING_API_URL` - после первого деплоя
- [ ] `LANDING_BASE_URL` - после первого деплоя
- [ ] `LANDING_REDIRECT_TYPE=bot`

### Опциональные (для расширенного функционала):

- [ ] `ANTHROPIC_API_KEY` - для AI анализа видео
- [ ] `STORAGE_TYPE=r2` - для production хранения видео
- [ ] `STORAGE_*` - credentials для R2/S3

---

## 🚀 Пошаговая инструкция

### Шаг 1: Создать сервисы на Railway

1. Зайти на https://railway.app/dashboard
2. Создать новый проект
3. Добавить PostgreSQL service
4. Добавить Redis service
5. Добавить GitHub repo

Railway автоматически добавит `DATABASE_URL` и `REDIS_URL`.

### Шаг 2: Добавить обязательные переменные

Во вкладке **Variables** добавить:

```bash
# JWT
SECRET_KEY=<генерируете openssl rand -hex 32>
JWT_SECRET_KEY=<генерируете openssl rand -hex 32>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Admin Bot
ADMIN_BOT_TOKEN=<от @BotFather>
ADMIN_IDS=<ваш Telegram ID>

# Telegram Bot
TELEGRAM_BOT_USERNAME=your_lootbox_bot

# Landing
LANDING_REDIRECT_TYPE=bot
CHANNEL_NAME=Your Lootbox Game
CHANNEL_DESCRIPTION=Open lootboxes and win prizes!

# Storage (для начала local)
STORAGE_TYPE=local
STORAGE_LOCAL_PATH=/tmp/utm-videos
```

### Шаг 3: Первый деплой

Railway автоматически задеплоит из GitHub.

**Получите URL:** `https://your-app-name.up.railway.app`

### Шаг 4: Добавить URL переменные

Добавить во **Variables**:

```bash
TRACKING_API_URL=https://your-app-name.up.railway.app
LANDING_BASE_URL=https://your-app-name.up.railway.app/api/v1/landing/l
```

### Шаг 5: Редеплой

Railway автоматически редеплоится при изменении переменных.

### Шаг 6: Проверка

Открыть:
```
https://your-app-name.up.railway.app/docs
```

Должна открыться Swagger UI документация API! ✅

---

## 🧪 Тестирование

### 1. Проверить API

```bash
curl https://your-app-name.up.railway.app/api/v1/health

# Ответ:
{"status": "healthy"}
```

### 2. Проверить Admin бота

Открыть бота в Telegram и отправить `/start`

Должен ответить с меню! ✅

### 3. Создать первый креатив

В боте: `/create_creative`

Должен создаться креатив с `utm_id`! ✅

---

## 🔒 Безопасность

### ⚠️ НЕ добавляйте в Railway:

- ❌ `.env` файл - не коммитить!
- ❌ Секретные ключи в код
- ❌ Токены в публичный GitHub

### ✅ Правильно:

- ✅ Все секреты только в Railway Variables
- ✅ `.env` в `.gitignore`
- ✅ `.env.example` (без реальных значений) в git

---

## 📊 Monitoring

### Проверить логи на Railway:

1. Открыть ваш проект на Railway
2. Вкладка **Deployments**
3. Кликнуть на последний деплой
4. Вкладка **Logs**

Должны видеть:
```
✅ Database connected
✅ Redis connected
✅ Admin bot started
✅ API server started on port 8000
```

---

## 🐛 Troubleshooting

### Проблема: DATABASE_URL not found

**Решение:**
1. Проверьте что PostgreSQL service добавлен
2. Проверьте что он подключен к вашему проекту
3. Railway должен автоматически добавить переменную

### Проблема: Admin bot не отвечает

**Решение:**
1. Проверьте `ADMIN_BOT_TOKEN` корректный
2. Проверьте `ADMIN_IDS` содержит ваш ID
3. Проверьте логи: бот должен стартовать без ошибок

### Проблема: 502 Bad Gateway

**Решение:**
1. Проверьте логи на Railway
2. Убедитесь что приложение слушает на `PORT` из env
3. Railway автоматически предоставляет `PORT` переменную

---

## ✅ Готово!

После настройки всех переменных у вас будет:

- ✅ API работает на Railway
- ✅ PostgreSQL подключена
- ✅ Redis работает
- ✅ Admin бот отвечает
- ✅ Можно создавать креативы
- ✅ Трекинг работает
- ✅ ML модели готовы

**Система готова к работе! 🚀**

---

## 📝 Шпаргалка команд

```bash
# Генерация JWT секрета
openssl rand -hex 32

# Проверка API
curl https://your-app.railway.app/api/v1/health

# Проверка документации
open https://your-app.railway.app/docs

# Проверка логов (в Railway dashboard)
Railway → Deployments → Latest → Logs
```

---

## 🔗 Полезные ссылки

- Railway Dashboard: https://railway.app/dashboard
- @BotFather: https://t.me/BotFather
- @userinfobot: https://t.me/userinfobot
- Anthropic Console: https://console.anthropic.com/
- Cloudflare R2: https://dash.cloudflare.com/

---

**Следующий шаг:** Настроить переменные на Railway и проверить что все работает! ✅

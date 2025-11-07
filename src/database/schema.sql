-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица типов событий
CREATE TABLE IF NOT EXISTS event_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица подписок пользователей на события
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_type_id INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    conditions TEXT, -- JSON с условиями
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (event_type_id) REFERENCES event_types(id),
    UNIQUE(user_id, event_type_id)
);

-- Таблица событий
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type_id INTEGER NOT NULL,
    data TEXT NOT NULL, -- JSON с данными события
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT 0,
    FOREIGN KEY (event_type_id) REFERENCES event_types(id)
);

-- Таблица истории уведомлений
CREATE TABLE IF NOT EXISTS notification_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'sent', -- sent, failed, pending
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (event_id) REFERENCES events(id)
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_events_processed ON events(processed);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_active ON user_subscriptions(is_active);
CREATE INDEX IF NOT EXISTS idx_notification_history_user ON notification_history(user_id);

#!/bin/bash

# Start FastAPI in background
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2 &

# Wait a bit for API to start
sleep 5

# Start Telegram Bot in foreground
python bots/admin_bot.py

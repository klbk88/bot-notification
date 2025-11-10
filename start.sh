#!/bin/bash

# Start FastAPI in background
cd utm-tracking
uvicorn api.main:app --host 0.0.0.0 --port 8000 &

# Start Telegram Bot
python bots/admin_bot.py

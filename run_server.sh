#!/bin/bash
source venv/bin/activate
export FLASK_APP=ai_assistant/server.py
export FLASK_ENV=production
export CLAUDE_API_KEY=${CLAUDE_API_KEY:-"YOUR_CLAUDE_API_KEY"}
export PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY:-"YOUR_PERPLEXITY_API_KEY"}
export TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")

# Убиваем существующие процессы на порту 5000
lsof -ti:5000 | xargs kill -9 2>/dev/null

# Запускаем сервер с перенаправлением логов
gunicorn -w 4 -b 0.0.0.0:5000 'ai_assistant.server:app' > server.log 2>&1 &
echo "Сервер запущен. Логи в server.log" 
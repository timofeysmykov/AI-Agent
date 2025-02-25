# AI Assistant с Claude API

Интеллектуальный ассистент на базе Claude API с веб-интерфейсом.

## Особенности

- 🧠 Использует Claude API для генерации ответов
- 🔍 Интеграция с Perplexity API для поиска актуальной информации
- 💬 Удобный веб-интерфейс для общения с ассистентом
- 🌙 Поддержка светлой и темной темы
- 📱 Адаптивный дизайн для мобильных устройств
- 🔄 Сохранение истории диалогов

## Требования

- Python 3.8+
- Node.js 14+
- API ключи для Claude и Perplexity (опционально)

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/YOUR_USERNAME/ai-assistant.git
cd ai-assistant
```

### 2. Настройка бэкенда

```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

### 3. Настройка фронтенда

```bash
cd frontend
npm install
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корневой директории проекта:

```
CLAUDE_API_KEY=your_claude_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
```

## Запуск

### Запуск всего приложения

```bash
./run_app.sh
```

### Запуск только бэкенда

```bash
./run_server.sh
```

### Запуск только фронтенда

```bash
cd frontend
./run_frontend.sh
```

## Структура проекта

```
ai-assistant/
├── ai_assistant/           # Бэкенд на Python
│   ├── ai_agent.py         # Основной класс для работы с Claude API
│   ├── server.py           # Flask сервер
│   ├── tools/              # Инструменты для расширения функциональности
│   └── prompts/            # Системные промпты
├── frontend/               # Фронтенд на Next.js
│   ├── src/                # Исходный код
│   │   ├── app/            # Страницы приложения
│   │   └── components/     # React компоненты
│   └── public/             # Статические файлы
├── venv/                   # Виртуальное окружение Python
├── run_server.sh           # Скрипт для запуска бэкенда
├── run_app.sh              # Скрипт для запуска всего приложения
└── requirements.txt        # Зависимости Python
```

## Устранение неполадок

### Проблема: Сервер не запускается

1. Проверьте, что порт 5000 не занят другим процессом:
   ```bash
   lsof -i :5000
   ```

2. Убедитесь, что API ключи правильно настроены в файле `.env`

3. Проверьте логи сервера:
   ```bash
   cat server.log
   ```

### Проблема: Фронтенд не подключается к бэкенду

1. Убедитесь, что бэкенд запущен и доступен по адресу `http://localhost:5000`

2. Проверьте настройки прокси в `next.config.js`

## Лицензия

MIT

## Автор

Ваше имя 
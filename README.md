# AI Assistant

AI Assistant - это интеллектуальный помощник, построенный на основе Claude API и Perplexity API.

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/ai-assistant.git
cd ai-assistant
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -e .
```

4. Создайте файл `.env` в корневой директории проекта со следующими переменными:
```
CLAUDE_API_KEY=your_claude_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
```

## Запуск

1. Активируйте виртуальное окружение (если еще не активировано):
```bash
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
```

2. Запустите приложение:
```bash
cd ai_assistant
streamlit run frontend.py
```

## Systemd сервис (для Linux)

1. Создайте файл сервиса:
```bash
sudo nano /etc/systemd/system/ai_assistant.service
```

2. Добавьте следующее содержимое:
```ini
[Unit]
Description=AI Assistant Service
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/ai-assistant/ai_assistant
Environment="PATH=/path/to/ai-assistant/venv/bin"
ExecStart=/path/to/ai-assistant/venv/bin/streamlit run frontend.py

[Install]
WantedBy=multi-user.target
```

3. Включите и запустите сервис:
```bash
sudo systemctl enable ai_assistant
sudo systemctl start ai_assistant
``` 
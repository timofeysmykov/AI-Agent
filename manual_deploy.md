# Пошаговые инструкции для деплоя на VPS

## Шаг 1: Подключение к серверу

```bash
# Подключитесь к серверу по SSH
ssh root@88.218.93.213
# Введите пароль: 1126512
```

## Шаг 2: Клонирование репозитория

```bash
# Клонируйте репозиторий
git clone https://github.com/timofeysmykov/AI-Agent.git
cd AI-Agent
```

## Шаг 3: Установка зависимостей

```bash
# Установка Python и Node.js (если не установлены)
apt update
apt install -y python3 python3-venv python3-pip nodejs npm

# Установка PM2 глобально
npm install -g pm2

# Создание виртуального окружения Python
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей Python
pip install -r requirements.txt

# Установка зависимостей фронтенда
cd frontend
npm install
```

## Шаг 4: Настройка переменных окружения

```bash
# Вернитесь в корневую директорию проекта
cd ..

# Создайте файл .env
cat > .env << EOF
CLAUDE_API_KEY=ваш_claude_api_key
EOF
```

## Шаг 5: Настройка скрипта деплоя

```bash
# Отредактируйте скрипт деплоя
sed -i 's|/path/to/AI-Agent|/root/AI-Agent|g' deploy.sh
chmod +x deploy.sh
```

## Шаг 6: Сборка и запуск приложения

```bash
# Сборка фронтенда
cd frontend
npm run build

# Запуск приложения с помощью PM2
cd ..
pm2 start ecosystem.config.js

# Сохранение конфигурации PM2
pm2 save

# Настройка автозапуска PM2 при перезагрузке сервера
pm2 startup
# Выполните команду, которую выдаст предыдущая команда
```

## Шаг 7: Проверка работоспособности

Откройте в браузере:
- http://88.218.93.213:3000

## Шаг 8: Обновление приложения в будущем

Для обновления приложения просто запустите:

```bash
cd /root/AI-Agent
./deploy.sh
```

## Решение проблем

1. Если приложение не запускается, проверьте логи:
```bash
pm2 logs
```

2. Если порт 3000 занят:
```bash
# Найдите процесс, использующий порт
lsof -i :3000
# Завершите процесс
kill -9 PID
```

3. Для перезапуска приложения:
```bash
pm2 restart all
``` 
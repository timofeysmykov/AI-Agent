# Инструкции по деплою AI Assistant на VPS

## Шаг 1: Подключение к серверу

```bash
# Подключитесь к серверу по SSH
ssh пользователь@ваш_ip
# Введите пароль при запросе
```

## Шаг 2: Клонирование репозитория

```bash
# Создайте директорию для проекта (если нужно)
mkdir -p ~/projects
cd ~/projects

# Клонируйте репозиторий
git clone https://github.com/timofeysmykov/AI-Agent.git
cd AI-Agent
```

## Шаг 3: Установка зависимостей

```bash
# Установка Python и Node.js (если не установлены)
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm

# Установка PM2 глобально
sudo npm install -g pm2

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
cd ~/projects/AI-Agent

# Создайте файл .env
cat > .env << EOF
CLAUDE_API_KEY=ваш_claude_api_key
EOF
```

## Шаг 5: Настройка скрипта деплоя

```bash
# Отредактируйте скрипт деплоя
nano deploy.sh

# Измените переменную PROJECT_DIR на реальный путь
# PROJECT_DIR="/home/пользователь/projects/AI-Agent"

# Сохраните файл (Ctrl+O, затем Enter) и выйдите (Ctrl+X)

# Сделайте скрипт исполняемым
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

## Шаг 7: Настройка Nginx (опционально)

Если вы хотите использовать доменное имя и HTTPS:

```bash
# Установка Nginx
sudo apt install -y nginx certbot python3-certbot-nginx

# Создание конфигурации Nginx
sudo nano /etc/nginx/sites-available/ai-assistant

# Вставьте следующую конфигурацию:
# server {
#     listen 80;
#     server_name ваш_домен.com;
#
#     location / {
#         proxy_pass http://localhost:3000;
#         proxy_http_version 1.1;
#         proxy_set_header Upgrade $http_upgrade;
#         proxy_set_header Connection 'upgrade';
#         proxy_set_header Host $host;
#         proxy_cache_bypass $http_upgrade;
#     }
# }

# Создайте символическую ссылку
sudo ln -s /etc/nginx/sites-available/ai-assistant /etc/nginx/sites-enabled/

# Проверьте конфигурацию Nginx
sudo nginx -t

# Перезапустите Nginx
sudo systemctl restart nginx

# Настройка SSL (если у вас есть домен)
sudo certbot --nginx -d ваш_домен.com
```

## Шаг 8: Проверка работоспособности

Откройте в браузере:
- http://ваш_ip:3000 (если без Nginx)
- http://ваш_домен.com (если с Nginx)

## Шаг 9: Обновление приложения в будущем

Для обновления приложения просто запустите:

```bash
cd ~/projects/AI-Agent
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
sudo lsof -i :3000
# Завершите процесс
sudo kill -9 PID
```

3. Для перезапуска приложения:
```bash
pm2 restart all
``` 
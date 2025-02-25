#!/bin/bash

# Скрипт для автоматизированного деплоя AI Assistant на VPS
# ВНИМАНИЕ: Этот скрипт содержит учетные данные и должен использоваться только локально

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
  echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
  echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ОШИБКА: $1${NC}"
  exit 1
}

warning() {
  echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ВНИМАНИЕ: $1${NC}"
}

# Параметры подключения к VPS
VPS_USER="root"
VPS_IP="88.218.93.213"
VPS_PASSWORD="1126512"
PROJECT_DIR="/root/AI-Agent"

# Проверка наличия необходимых команд
check_command() {
  if ! command -v $1 &> /dev/null; then
    error "Команда $1 не найдена. Пожалуйста, установите ее."
  fi
}

check_command ssh
check_command sshpass

# Функция для выполнения команд на удаленном сервере
run_remote() {
  log "Выполнение команды на сервере: $1"
  sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "$1"
  if [ $? -ne 0 ]; then
    error "Ошибка при выполнении команды на сервере"
  fi
}

# Проверка соединения с сервером
log "Проверка соединения с сервером $VPS_IP..."
if ! sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "echo 'Соединение установлено'"; then
  error "Не удалось подключиться к серверу. Проверьте IP-адрес и учетные данные."
fi

# Проверка наличия репозитория на сервере
log "Проверка наличия репозитория на сервере..."
if run_remote "[ -d $PROJECT_DIR ]"; then
  log "Репозиторий найден, обновляем..."
  run_remote "cd $PROJECT_DIR && git pull"
else
  log "Репозиторий не найден, клонируем..."
  run_remote "git clone https://github.com/timofeysmykov/AI-Agent.git $PROJECT_DIR"
fi

# Установка необходимых пакетов
log "Установка необходимых пакетов..."
run_remote "apt update && apt install -y python3 python3-venv python3-pip nodejs npm"
run_remote "npm install -g pm2"

# Настройка виртуального окружения Python
log "Настройка виртуального окружения Python..."
run_remote "cd $PROJECT_DIR && [ ! -d venv ] && python3 -m venv venv"
run_remote "cd $PROJECT_DIR && source venv/bin/activate && pip install -r requirements.txt"

# Настройка переменных окружения
log "Настройка переменных окружения..."
run_remote "cd $PROJECT_DIR && [ ! -f .env ] && echo 'CLAUDE_API_KEY=ваш_claude_api_key' > .env"
warning "Не забудьте заменить 'ваш_claude_api_key' на реальный ключ API в файле .env на сервере"

# Установка зависимостей фронтенда и сборка
log "Установка зависимостей фронтенда и сборка..."
run_remote "cd $PROJECT_DIR/frontend && npm install && npm run build"

# Настройка скрипта деплоя
log "Настройка скрипта деплоя..."
run_remote "cd $PROJECT_DIR && sed -i 's|/path/to/AI-Agent|$PROJECT_DIR|g' deploy.sh && chmod +x deploy.sh"

# Запуск приложения с помощью PM2
log "Запуск приложения с помощью PM2..."
run_remote "cd $PROJECT_DIR && pm2 start ecosystem.config.js"
run_remote "cd $PROJECT_DIR && pm2 save"

# Настройка автозапуска PM2
log "Настройка автозапуска PM2..."
run_remote "pm2 startup | tail -n 1 > /tmp/pm2_startup.sh && chmod +x /tmp/pm2_startup.sh && /tmp/pm2_startup.sh"

# Проверка статуса приложения
log "Проверка статуса приложения..."
run_remote "pm2 list"

log "Деплой успешно завершен! Приложение доступно по адресу http://$VPS_IP:3000"
log "Для проверки работоспособности откройте в браузере: http://$VPS_IP:3000" 
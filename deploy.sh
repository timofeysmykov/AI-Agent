#!/bin/bash

# Скрипт для деплоя AI Assistant на VPS
# Автоматизирует процесс обновления кода и перезапуска сервисов

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

# Проверка наличия необходимых команд
check_command() {
  if ! command -v $1 &> /dev/null; then
    error "Команда $1 не найдена. Пожалуйста, установите ее."
  fi
}

check_command git
check_command python3
check_command npm
check_command pm2

# Директория проекта на VPS
PROJECT_DIR="/path/to/AI-Agent"
VENV_DIR="$PROJECT_DIR/venv"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Переход в директорию проекта
log "Переход в директорию проекта: $PROJECT_DIR"
cd $PROJECT_DIR || error "Не удалось перейти в директорию проекта"

# Получение последних изменений из репозитория
log "Получение последних изменений из репозитория..."
git pull || error "Не удалось получить изменения из репозитория"

# Активация виртуального окружения и установка зависимостей Python
log "Установка зависимостей Python..."
if [ ! -d "$VENV_DIR" ]; then
  log "Создание виртуального окружения..."
  python3 -m venv $VENV_DIR || error "Не удалось создать виртуальное окружение"
fi

source $VENV_DIR/bin/activate || error "Не удалось активировать виртуальное окружение"
pip install -r requirements.txt || error "Не удалось установить зависимости Python"

# Установка зависимостей фронтенда
log "Установка зависимостей фронтенда..."
cd $FRONTEND_DIR || error "Не удалось перейти в директорию фронтенда"
npm install || error "Не удалось установить зависимости фронтенда"

# Сборка фронтенда
log "Сборка фронтенда..."
npm run build || error "Не удалось собрать фронтенд"

# Перезапуск сервисов с помощью PM2
log "Перезапуск сервисов..."
cd $PROJECT_DIR || error "Не удалось перейти в директорию проекта"

# Проверка наличия конфигурации PM2
if [ ! -f "ecosystem.config.js" ]; then
  warning "Файл конфигурации PM2 не найден. Создаем новый..."
  cat > ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'ai-assistant-frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'start',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      }
    }
  ]
};
EOF
fi

# Перезапуск или запуск приложения с помощью PM2
if pm2 list | grep -q "ai-assistant-frontend"; then
  log "Перезапуск существующего процесса..."
  pm2 reload ecosystem.config.js || error "Не удалось перезапустить процесс"
else
  log "Запуск нового процесса..."
  pm2 start ecosystem.config.js || error "Не удалось запустить процесс"
fi

# Сохранение конфигурации PM2
pm2 save || warning "Не удалось сохранить конфигурацию PM2"

log "Деплой успешно завершен! Приложение доступно по адресу http://ваш_домен:3000" 
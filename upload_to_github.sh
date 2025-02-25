#!/bin/bash

# Скрипт для загрузки проекта на GitHub

# Проверка наличия git
if ! command -v git &> /dev/null; then
    echo "Git не установлен. Пожалуйста, установите git."
    exit 1
fi

# Инициализация git, если репозиторий не существует
if [ ! -d ".git" ]; then
    echo "Инициализация git репозитория..."
    git init
fi

# Добавление всех файлов
echo "Добавление файлов в индекс..."
git add .

# Создание коммита
echo "Создание коммита..."
git commit -m "Исправлен бэкенд для корректной работы с фронтендом"

# Проверка наличия удаленного репозитория
if ! git remote | grep -q "origin"; then
    echo "Удаленный репозиторий не настроен."
    echo "Пожалуйста, создайте репозиторий на GitHub и выполните следующую команду:"
    echo "git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
    echo "Затем выполните: git push -u origin main"
    exit 0
fi

# Отправка изменений в удаленный репозиторий
echo "Отправка изменений в удаленный репозиторий..."
git push -u origin main

echo "Готово! Проект успешно загружен на GitHub." 
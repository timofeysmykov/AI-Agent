#!/bin/bash

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем зависимости Python
pip install -r requirements.txt

# Запускаем фронтенд
cd frontend && ./run_frontend.sh 
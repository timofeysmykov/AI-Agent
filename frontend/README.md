# AI Assistant Frontend

Современный фронтенд для AI Assistant с Material You дизайном и поддержкой светлой/темной темы.

## Особенности

- 🎨 Material You дизайн
- 🌓 Поддержка светлой и темной темы
- 📱 Адаптивный интерфейс
- 💬 Форматирование сообщений с поддержкой Markdown
- 🖥️ Подсветка синтаксиса кода
- 💾 Сохранение и очистка истории чата

## Технологии

- Next.js 14
- React 18
- TypeScript
- Material UI
- Tailwind CSS
- Axios

## Запуск

```bash
# Установка зависимостей
npm install

# Запуск в режиме разработки
npm run dev

# Сборка для продакшена
npm run build

# Запуск продакшен-версии
npm start
```

## Структура проекта

```
src/
├── app/              # Next.js App Router
│   ├── api/          # API роуты
│   ├── globals.css   # Глобальные стили
│   ├── layout.tsx    # Основной макет
│   └── page.tsx      # Главная страница
├── components/       # React компоненты
│   ├── ChatHistory.tsx
│   ├── ChatInput.tsx
│   ├── ChatMessage.tsx
│   └── ThemeToggle.tsx
└── ...
``` 
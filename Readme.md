Python Meetup Bot

Стек
- Python 3.13
- Django 5.2.8
- aiogram 3.22.0
- environs[django] 14.5.0 — для чтения .env
- SQLite по умолчанию

Структура
- pythonmeetup_service/ — настройки и маршрутизация Django
- app_core/ — приложение проекта
  - management/commands/runbot.py — запуск Telegram‑бота
  - bot/ — код бота (aiogram)
- .env — переменные окружения (см. ниже)

Подготовка окружения
1. Установите зависимости
   - pip install -r requirements.txt
2. Создайте .env в корне (или используйте существующий) и задайте ключи:
   - DJANGO_DEBUG=True
   - DJANGO_SECRET_KEY=СЛУЧАЙНАЯ_СТРОКА
   - DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
   - DJANGO_TIME_ZONE=Europe/Moscow
   - DJANGO_LANGUAGE_CODE=ru
   - TELEGRAM_BOT_TOKEN=Токен из @BotFather (нужен для runbot)

Локальный запуск
1. Миграции (моделей пока нет, но база инициализируется):
   - python manage.py migrate
2. Сервер разработки:
   - python manage.py runserver
3. Бот (в отдельном терминале):
   - python manage.py runbot
   - Проверка: отправьте /start вашему боту в Telegram

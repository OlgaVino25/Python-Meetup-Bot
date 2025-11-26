import os
from django.core.management.base import BaseCommand, CommandError
from app_core.bot.bot_main import run as run_bot


class Command(BaseCommand):
    help = "Запускает Telegram-бота (aiogram). Токен берётся из переменной окружения TELEGRAM_BOT_TOKEN"

    def handle(self, *args, **options):
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise CommandError("TELEGRAM_BOT_TOKEN не задан в .env или окружении")

        run_bot(token)

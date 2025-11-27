import os
import asyncio
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pythonmeetup_service.settings')
django.setup()

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

async def setup_bot(token: str):
    bot = Bot(token=token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    from .middlewares.django import DjangoORMMiddleware
    dp.update.middleware(DjangoORMMiddleware())
    
    from .handlers import start, program, questions, networking, donations, help, admin, subscription, speaker
    dp.include_router(start.router)
    dp.include_router(program.router)
    dp.include_router(questions.router)
    dp.include_router(networking.router)
    dp.include_router(donations.router)
    dp.include_router(help.router)
    dp.include_router(admin.router)
    dp.include_router(subscription.router)
    dp.include_router(speaker.speaker_router)
    
    return bot, dp

async def start_bot(token: str):
    bot, dp = await setup_bot(token)
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

def run(token: str):
    asyncio.run(start_bot(token))
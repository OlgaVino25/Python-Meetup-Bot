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
    
    dp.update.outer_middleware(DjangoORMMiddleware())
    dp.message.middleware(DjangoORMMiddleware())
    dp.callback_query.middleware(DjangoORMMiddleware())
    
    from .handlers import (
        start_router, 
        program_router, 
        questions_router, 
        networking_router, 
        donations_router, 
        help_router, 
        admin_router, 
        subscription_router,
        speaker_router
    )
    
    dp.include_router(start_router)
    dp.include_router(program_router)
    dp.include_router(questions_router)
    dp.include_router(networking_router)
    dp.include_router(donations_router)
    dp.include_router(help_router)
    dp.include_router(admin_router)
    dp.include_router(subscription_router)
    dp.include_router(speaker_router)
    
    return bot, dp

async def start_bot(token: str):
    bot, dp = await setup_bot(token)
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

def run(token: str):
    asyncio.run(start_bot(token))
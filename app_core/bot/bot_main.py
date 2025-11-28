import os
import asyncio
import django
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        subscription_router,
        speaker_router,
        speaker_application_router
    )
    
    dp.include_router(start_router)
    dp.include_router(program_router)
    dp.include_router(speaker_router)
    dp.include_router(questions_router)
    dp.include_router(networking_router)
    dp.include_router(donations_router)
    dp.include_router(subscription_router)
    dp.include_router(speaker_application_router)

    return bot, dp

async def start_bot_with_scheduler(token: str):
    bot, dp = await setup_bot(token)
    
    from .services.scheduler import NotificationScheduler
    
    scheduler = NotificationScheduler(bot)
    scheduler_task = asyncio.create_task(scheduler.start())
    
    try:
        logger.info("Бот запущен с планировщиком уведомлений")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await scheduler.stop()
        if not scheduler_task.done():
            scheduler_task.cancel()
        await bot.session.close()
        logger.info("Бот остановлен")

def run(token: str):
    asyncio.run(start_bot_with_scheduler(token))
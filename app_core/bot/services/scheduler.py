import asyncio
import logging
from aiogram import Bot
from .notification_service import check_and_send_notifications

logger = logging.getLogger(__name__)

class NotificationScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.is_running = False
    
    async def start(self):
        self.is_running = True
        logger.info("Планировщик уведомлений запущен")
        
        while self.is_running:
            try:
                sent_count = await check_and_send_notifications(self.bot)
                if sent_count > 0:
                    logger.info(f"Отправлено уведомлений: {sent_count}")
                
                await asyncio.sleep(6 * 60 * 60)
                
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}")
                await asyncio.sleep(60)
    
    async def stop(self):
        """Остановить планировщик"""
        self.is_running = False
        logger.info("Планировщик уведомлений остановлен")
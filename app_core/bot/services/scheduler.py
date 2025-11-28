import asyncio
import logging
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .notification_service import check_and_send_week_notifications, check_and_send_day_notifications

logger = logging.getLogger(__name__)

class NotificationScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
    
    async def start(self):
        """Запуск планировщика с точным временем"""
        try:
            # Напоминания за неделю - каждый день в 10:00
            self.scheduler.add_job(
                self.send_week_notifications,
                trigger=CronTrigger(hour=10, minute=0),
                id='week_notifications',
                replace_existing=True
            )
            
            # Напоминания за день - каждый день в 18:00
            self.scheduler.add_job(
                self.send_day_notifications,
                trigger=CronTrigger(hour=18, minute=0),
                id='day_notifications', 
                replace_existing=True
            )
            
            # Быстрая проверка при запуске (для отладки)
            self.scheduler.add_job(
                self.quick_check,
                trigger='date',
                id='quick_check'
            )
            
            self.scheduler.start()
            logger.info("✅ Планировщик уведомлений запущен")
            logger.info("📅 Напоминания за неделю: ежедневно в 10:00")
            logger.info("📅 Напоминания за день: ежедневно в 18:00")
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска планировщика: {e}")
    
    async def send_week_notifications(self):
        """Отправка напоминаний за неделю"""
        try:
            logger.info("🔔 Проверка напоминаний за неделю...")
            sent_count = await check_and_send_week_notifications(self.bot)
            if sent_count > 0:
                logger.info(f"✅ Отправлено напоминаний за неделю: {sent_count}")
            else:
                logger.info("ℹ️ Нет мероприятий для напоминания за неделю")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминаний за неделю: {e}")
    
    async def send_day_notifications(self):
        """Отправка напоминаний за день"""
        try:
            logger.info("🔔 Проверка напоминаний за день...")
            sent_count = await check_and_send_day_notifications(self.bot)
            if sent_count > 0:
                logger.info(f"✅ Отправлено напоминаний за день: {sent_count}")
            else:
                logger.info("ℹ️ Нет мероприятий для напоминания за день")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминаний за день: {e}")
    
    async def quick_check(self):
        """Быстрая проверка при запуске (для отладки)"""
        try:
            logger.info("🔍 Быстрая проверка уведомлений при запуске...")
            week_count = await check_and_send_week_notifications(self.bot)
            day_count = await check_and_send_day_notifications(self.bot)
            
            if week_count > 0 or day_count > 0:
                logger.info(f"🎯 При запуске отправлено: {week_count} за неделю, {day_count} за день")
        except Exception as e:
            logger.error(f"❌ Ошибка быстрой проверки: {e}")
    
    async def stop(self):
        """Остановить планировщик"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        logger.info("🛑 Планировщик уведомлений остановлен")
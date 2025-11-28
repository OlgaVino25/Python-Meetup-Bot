from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import timedelta, datetime
from app_core.models import User, Event
from aiogram import Bot
import logging
import pytz

logger = logging.getLogger(__name__)

@sync_to_async
def get_events_for_week_notification():
    """Получить мероприятия, которые начнутся через 7 дней"""
    now = timezone.now()
    target_date = now + timedelta(days=7)
    
    events = Event.objects.filter(
        start_date__date=target_date.date(),
        notification_sent_week=False
    )
    return list(events)

@sync_to_async
def get_events_for_day_notification():
    """Получить мероприятия, которые начнутся через 1 день"""
    now = timezone.now()
    target_date = now + timedelta(days=1)
    
    events = Event.objects.filter(
        start_date__date=target_date.date(),
        notification_sent_day=False
    )
    return list(events)

@sync_to_async
def mark_week_notification_sent(event):
    event.notification_sent_week = True
    event.save()

@sync_to_async
def mark_day_notification_sent(event):
    event.notification_sent_day = True
    event.save()

@sync_to_async
def get_subscribed_users():
    return list(User.objects.filter(is_subscribed=True))

async def send_week_notification(bot: Bot, event: Event):
    """Отправка напоминания за неделю"""
    try:
        subscribed_users = await get_subscribed_users()
        
        if not subscribed_users:
            logger.info(f"Нет подписанных пользователей для мероприятия '{event.title}'")
            return 0
        
        message_text = (
            "🔔 Напоминание о мероприятии!\n\n"
            f"🎯 <b>{event.title}</b>\n"
            f"📅 Через неделю: {event.start_date.strftime('%d.%m.%Y')}\n"
            f"🕐 В {event.start_date.strftime('%H:%M')}\n"
            f"📝 {event.description[:150]}{'...' if len(event.description) > 150 else ''}\n\n"
            "Не пропустите интересные доклады и общение с коллегами! 🚀"
        )
        
        success_count = 0
        for user in subscribed_users:
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=message_text,
                    parse_mode="HTML"
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление пользователю {user.telegram_id}: {e}")
        
        await mark_week_notification_sent(event)
        
        logger.info(f"Напоминание за неделю о '{event.title}' отправлено {success_count} пользователям")
        return success_count
        
    except Exception as e:
        logger.error(f"Ошибка при отправке напоминания за неделю: {e}")
        return 0

async def send_day_notification(bot: Bot, event: Event):
    """Отправка напоминания за день"""
    try:
        subscribed_users = await get_subscribed_users()
        
        if not subscribed_users:
            logger.info(f"Нет подписанных пользователей для мероприятия '{event.title}'")
            return 0
        
        message_text = (
            "🔔 Завтра митап!\n\n"
            f"🎯 <b>{event.title}</b>\n"
            f"📅 {event.start_date.strftime('%d.%m.%Y')}\n"
            f"🕐 Начало в {event.start_date.strftime('%H:%M')}\n"
            f"📝 {event.description[:150]}{'...' if len(event.description) > 150 else ''}\n\n"
            "Успейте подготовить вопросы спикерам! 💬"
        )
        
        success_count = 0
        for user in subscribed_users:
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=message_text,
                    parse_mode="HTML"
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление пользователю {user.telegram_id}: {e}")
        
        await mark_day_notification_sent(event)
        
        logger.info(f"Напоминание за день о '{event.title}' отправлено {success_count} пользователям")
        return success_count
        
    except Exception as e:
        logger.error(f"Ошибка при отправке напоминания за день: {e}")
        return 0

async def check_and_send_week_notifications(bot: Bot):
    """Проверить и отправить напоминания за неделю"""
    events = await get_events_for_week_notification()
    
    total_sent = 0
    for event in events:
        sent_count = await send_week_notification(bot, event)
        total_sent += sent_count
    
    return total_sent

async def check_and_send_day_notifications(bot: Bot):
    """Проверить и отправить напоминания за день"""
    events = await get_events_for_day_notification()
    
    total_sent = 0
    for event in events:
        sent_count = await send_day_notification(bot, event)
        total_sent += sent_count
    
    return total_sent

async def send_test_notification(bot: Bot, user_id: int):
    """Тестовая отправка уведомления"""
    try:
        message_text = (
            "🧪 <b>Тестовое уведомление</b>\n\n"
            "Система напоминаний работает корректно! ✅\n"
            "Вы будете получать уведомления за неделю и за день до митапов."
        )
        
        await bot.send_message(
            chat_id=user_id,
            text=message_text,
            parse_mode="HTML"
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка тестовой отправки: {e}")
        return False
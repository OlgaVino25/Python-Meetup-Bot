from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import timedelta
from app_core.models import User, Event
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)

@sync_to_async
def get_events_for_notification():
    now = timezone.now()
    week_from_now = now + timedelta(days=7)
    
    events = Event.objects.filter(
        start_date__date=week_from_now.date(),
        notification_sent=False
    )
    return list(events)

@sync_to_async
def mark_notification_sent(event):
    event.notification_sent = True
    event.save()

@sync_to_async
def get_subscribed_users():
    return list(User.objects.filter(is_subscribed=True))

async def send_event_notification(bot: Bot, event: Event):
    try:
        subscribed_users = await get_subscribed_users()
        
        if not subscribed_users:
            logger.info(f"Нет подписанных пользователей для мероприятия '{event.title}'")
            return 0
        
        message_text = (
            "🔔 Напоминание о мероприятии!\n\n"
            f"🎯 {event.title}\n"
            f"📅 Через неделю: {event.start_date.strftime('%d.%m.%Y в %H:%M')}\n"
            f"📝 {event.description[:200]}{'...' if len(event.description) > 200 else ''}\n\n"
            "Не пропустите интересные доклады и общение с коллегами! 🚀"
        )
        
        success_count = 0
        for user in subscribed_users:
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=message_text
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление пользователю {user.telegram_id}: {e}")
        
        await mark_notification_sent(event)
        
        logger.info(f"Уведомление о мероприятии '{event.title}' отправлено {success_count} пользователям")
        return success_count
        
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений: {e}")
        return 0

async def check_and_send_notifications(bot: Bot):
    events = await get_events_for_notification()
    
    total_sent = 0
    for event in events:
        sent_count = await send_event_notification(bot, event)
        total_sent += sent_count
    
    return total_sent
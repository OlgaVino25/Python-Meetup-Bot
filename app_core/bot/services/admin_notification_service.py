from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from django.conf import settings
from app_core.models import User, MassNotification
from django.utils import timezone
import logging
import asyncio

logger = logging.getLogger(__name__)

async def send_message_to_user(bot: Bot, user_telegram_id: str, text: str):
    try:
        await bot.send_message(chat_id=user_telegram_id, text=text)
        logger.info(f"✅ Сообщение успешно отправлено пользователю {user_telegram_id}")
        return True
    except TelegramForbiddenError as e:
        logger.warning(f"❌ Пользователь {user_telegram_id} заблокировал бота: {e}")
        return False
    except TelegramBadRequest as e:
        if "chat not found" in str(e).lower():
            logger.warning(f"❌ Чат с пользователем {user_telegram_id} не найден (возможно, бот заблокирован)")
        else:
            logger.error(f"❌ Ошибка запроса для пользователя {user_telegram_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Неизвестная ошибка для пользователя {user_telegram_id}: {e}")
        return False

def send_mass_notification_sync(notification):
    try:
        if notification.target_users == 'all':
            users = User.objects.filter(is_subscribed=True)
            target_description = "всем подписанным пользователям"
            logger.info(f"📊 Рассылка для всех подписанных. Найдено пользователей: {users.count()}")
        else:
            users = notification.custom_users.all()
            target_description = f"выбранным пользователям ({users.count()} чел.)"
            logger.info(f"📊 Рассылка для выбранных пользователей. Найдено: {users.count()}")
        
        if not users.exists():
            notification.status = 'failed'
            notification.save()
            logger.warning("❌ Нет пользователей для рассылки")
            return 0, 0, "Нет пользователей для рассылки"
        
        user_list = [f"{user.telegram_id} ({user.first_name})" for user in users]
        logger.info(f"👥 Пользователи для рассылки: {user_list}")
        
        notification.status = 'sending'
        notification.save()
        
        message_text = f"📢 {notification.title}\n\n{notification.message}"
        logger.info(f"📝 Текст рассылки: {message_text[:100]}...")
        
        async def send_messages():
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            success_count = 0
            failed_count = 0
            failed_users = []
            
            for user in users:
                logger.info(f"🔄 Отправка пользователю {user.telegram_id} ({user.first_name})")
                if await send_message_to_user(bot, user.telegram_id, message_text):
                    success_count += 1
                    logger.info(f"✅ Успешно отправлено пользователю {user.telegram_id}")
                else:
                    failed_count += 1
                    failed_users.append(f"{user.telegram_id} ({user.first_name})")
                    logger.warning(f"❌ Не удалось отправить пользователю {user.telegram_id}")
            
            await bot.session.close()
            
            logger.info(f"📊 Итоги рассылки: Успешно - {success_count}, Ошибок - {failed_count}")
            if failed_users:
                logger.warning(f"❌ Пользователи с ошибками: {failed_users}")
            
            return success_count, failed_count
        
        success_count, failed_count = asyncio.run(send_messages())
        
        if success_count > 0:
            notification.status = 'sent'
            notification.sent_to_count = success_count
            notification.failed_count = failed_count
            notification.sent_at = timezone.now()
            result_message = f"Рассылка отправлена {target_description}. Успешно: {success_count}, Ошибок: {failed_count}"
            logger.info(f"🎉 Рассылка завершена успешно: {result_message}")
        else:
            notification.status = 'failed'
            result_message = f"Рассылка не отправлена. Все попытки завершились ошибкой"
            logger.error(f"💥 Рассылка полностью провалилась: {result_message}")
        
        notification.save()
        return success_count, failed_count, result_message
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка при массовой рассылке: {e}", exc_info=True)
        notification.status = 'failed'
        notification.save()
        return 0, 0, f"Ошибка при рассылке: {str(e)}"

def send_custom_notification_sync(user_ids, title, message_text):
    try:
        users = User.objects.filter(id__in=user_ids)
        
        if not users.exists():
            return 0, 0, "Нет пользователей для рассылки"
        
        full_message = f"📢 {title}\n\n{message_text}"
        
        async def send_custom_messages():
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            success_count = 0
            failed_count = 0
            
            for user in users:
                logger.info(f"🔄 Кастомная рассылка пользователю {user.telegram_id} ({user.first_name})")
                if await send_message_to_user(bot, user.telegram_id, full_message):
                    success_count += 1
                else:
                    failed_count += 1
            
            await bot.session.close()
            return success_count, failed_count
        
        success_count, failed_count = asyncio.run(send_custom_messages())
        
        result_message = f"Сообщение отправлено выбранным пользователям. Успешно: {success_count}, Ошибок: {failed_count}"
        logger.info(f"Кастомная рассылка: {result_message}")
        return success_count, failed_count, result_message
        
    except Exception as e:
        logger.error(f"Ошибка при кастомной рассылке: {e}")
        return 0, 0, f"Ошибка при рассылке: {str(e)}"
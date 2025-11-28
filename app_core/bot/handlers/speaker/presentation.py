# presentation.py - исправленная версия с принудительной коррекцией времени
from datetime import timedelta
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
import pytz

from app_core.models import Talk, Event, User
from ...states.speaker import SpeakerStates
from ...keyboards.main import get_back_keyboard
from django.utils import timezone

router = Router()


@router.message(lambda message: message.text and "Начать выступление" in message.text)
async def start_presentation(message: types.Message, state: FSMContext):
    """Начать выступление - активировать доклад спикера"""
    user = message.from_user

    try:
        # Используем московское время
        moscow_tz = pytz.timezone('Europe/Moscow')
        now_utc = timezone.now()
        now_moscow = now_utc.astimezone(moscow_tz)
        today = now_moscow.date()
        
        print(f"DEBUG: Current time UTC: {now_utc}")
        print(f"DEBUG: Current time Moscow: {now_moscow}")
        print(f"DEBUG: Today date: {today}")
        
        # Найдем мероприятия на сегодня
        today_events = await sync_to_async(list)(
            Event.objects.filter(start_date__date=today)
        )
        print(f"DEBUG: Today events: {[e.title for e in today_events]}")
        
        if not today_events:
            await message.answer(
                "❌ На сегодня нет мероприятий\n\n"
                "Нельзя начать выступление без запланированного мероприятия.",
                reply_markup=get_back_keyboard(),
            )
            return

        current_event = today_events[0]
        print(f"DEBUG: Selected event: {current_event.title}")

        # Ищем доклад спикера в текущем мероприятии
        talk = await sync_to_async(
            Talk.objects.filter(
                event=current_event,
                speaker__telegram_id=str(user.id)
            ).first
        )()

        if not talk:
            await message.answer(
                "❌ Не найдено запланированных выступлений\n\n"
                "У вас нет докладов на сегодняшнем мероприятии.",
                reply_markup=get_back_keyboard(),
            )
            return

        # ПРАВИЛЬНАЯ ОБРАБОТКА ВРЕМЕНИ ДОКЛАДА - КОРРЕКЦИЯ UTC -> MSK
        print(f"DEBUG: Talk start_time raw: {talk.start_time}")
        print(f"DEBUG: Talk end_time raw: {talk.end_time}")
        
        # Время в базе сохранено как UTC, но Django неправильно интерпретирует
        # Принудительно корректируем: вычитаем 3 часа (разница UTC -> MSK)
        if talk.start_time.tzinfo is None:
            # Если время без часового пояса - считаем что это уже московское время
            talk_start_moscow = moscow_tz.localize(talk.start_time)
            talk_end_moscow = moscow_tz.localize(talk.end_time)
        else:
            # Если время с часовым поясом - это скорее всего UTC, конвертируем в MSK
            talk_start_moscow = talk.start_time.astimezone(moscow_tz)
            talk_end_moscow = talk.end_time.astimezone(moscow_tz)
        
        # ДОПОЛНИТЕЛЬНАЯ КОРРЕКЦИЯ: если разница больше 2 часов, значит время в UTC
        time_diff = (talk_start_moscow - now_moscow).total_seconds() / 3600
        if abs(time_diff) > 2:  # Если разница больше 2 часов
            print(f"DEBUG: Large time difference detected: {time_diff} hours")
            print(f"DEBUG: Assuming UTC time in database, applying correction")
            # Вычитаем 3 часа (UTC+3 для Москвы)
            talk_start_moscow = talk_start_moscow - timedelta(hours=3)
            talk_end_moscow = talk_end_moscow - timedelta(hours=3)
        
        print(f"DEBUG: Final talk time (Moscow): {talk_start_moscow} - {talk_end_moscow}")
        print(f"DEBUG: Now (Moscow): {now_moscow}")

        # Логика времени
        can_start_time = talk_start_moscow
        can_end_time = talk_end_moscow + timedelta(minutes=10)
        
        print(f"DEBUG: Can start from: {can_start_time}")
        print(f"DEBUG: Can end until: {can_end_time}")
        print(f"DEBUG: Time difference: {(now_moscow - can_start_time).total_seconds() / 60:.1f} minutes")

        if now_moscow < can_start_time:
            time_diff = (can_start_time - now_moscow).total_seconds() / 60
            await message.answer(
                f"❌ Слишком рано начинать выступление\n\n"
                f"Вы можете начать выступление только во время вашего доклада.\n"
                f"Ваш доклад начнется в {talk_start_moscow.strftime('%H:%M')}\n"
                f"Сейчас: {now_moscow.strftime('%H:%M')}\n"
                f"Осталось: {time_diff:.0f} минут",
                reply_markup=get_back_keyboard(),
            )
            return

        if now_moscow > can_end_time:
            time_diff = (now_moscow - can_end_time).total_seconds() / 60
            await message.answer(
                f"❌ Слишком поздно начинать выступление\n\n"
                f"Вы можете начать выступление только в течение 10 минут после окончания доклада.\n"
                f"Ваш доклад закончился в {talk_end_moscow.strftime('%H:%M')}\n"
                f"Сейчас: {now_moscow.strftime('%H:%M')}\n"
                f"Прошло: {time_diff:.0f} минут",
                reply_markup=get_back_keyboard(),
            )
            return

        # Проверяем, нет ли уже активного доклада
        active_talk = await sync_to_async(
            Talk.objects.filter(event=current_event, is_active=True).first
        )()
        
        if active_talk and active_talk.id != talk.id:
            await message.answer(
                f"❌ Сейчас выступает другой спикер\n\n"
                f"Активный доклад: {active_talk.title}\n"
                f"Спикер: {active_talk.speaker.first_name}\n\n"
                f"Дождитесь завершения текущего выступления.",
                reply_markup=get_back_keyboard(),
            )
            return

        # Деактивируем все другие активные доклады
        await sync_to_async(
            Talk.objects.filter(event=current_event, is_active=True).update
        )(is_active=False)

        # Активируем текущий доклад
        talk.is_active = True
        await sync_to_async(talk.save)()

        print(f"DEBUG: Activated talk {talk.title}, is_active = {talk.is_active}")

        # Сохраняем ID доклада в состоянии
        await state.set_state(SpeakerStates.presentation_active)
        await state.update_data(active_talk_id=talk.id, event_id=current_event.id)

        await message.answer(
            f"🎤 Вы начали выступление!\n\n"
            f"📝 <b>Тема:</b> {talk.title}\n"
            f"⏱ <b>Время:</b> {talk_start_moscow.strftime('%H:%M')} - {talk_end_moscow.strftime('%H:%M')}\n\n"
            f"Теперь участники могут отправлять вам вопросы через бота.\n"
            f"Вопросы будут приходить в реальном времени.\n\n"
            f"Чтобы завершить выступление, нажмите 'Завершить выступление'.",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML",
        )

    except Exception as e:
        print(f"Ошибка при начале выступления: {e}")
        import traceback
        print(f"Полная трассировка: {traceback.format_exc()}")
        await message.answer(
            "❌ Произошла ошибка при начале выступления\n\n"
            "Попробуйте еще раз или обратитесь к организатору.",
            reply_markup=get_back_keyboard(),
        )
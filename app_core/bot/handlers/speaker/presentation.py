# presentation.py - чистая версия без отладки
from datetime import timedelta
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
import pytz

from app_core.models import Talk, Event, User, Question
from ...states.speaker import SpeakerStates
from ...keyboards.main import get_back_keyboard, get_main_keyboard
from ...keyboards.speaker import get_speaker_keyboard
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
        
        # Найдем мероприятия на сегодня
        today_events = await sync_to_async(list)(
            Event.objects.filter(start_date__date=today)
        )
        
        if not today_events:
            await message.answer(
                "❌ На сегодня нет мероприятий\n\n"
                "Нельзя начать выступление без запланированного мероприятия.",
                reply_markup=get_back_keyboard(),
            )
            return

        current_event = today_events[0]

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

        # Обработка времени доклада
        if talk.start_time.tzinfo is None:
            talk_start_moscow = moscow_tz.localize(talk.start_time)
            talk_end_moscow = moscow_tz.localize(talk.end_time)
        else:
            talk_start_moscow = talk.start_time.astimezone(moscow_tz)
            talk_end_moscow = talk.end_time.astimezone(moscow_tz)
        
        # Коррекция UTC -> MSK если нужно
        time_diff = (talk_start_moscow - now_moscow).total_seconds() / 3600
        if abs(time_diff) > 2:
            talk_start_moscow = talk_start_moscow - timedelta(hours=3)
            talk_end_moscow = talk_end_moscow - timedelta(hours=3)

        # Логика времени
        can_start_time = talk_start_moscow
        can_end_time = talk_end_moscow + timedelta(minutes=10)

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

        # Сохраняем ID доклада в состоянии
        await state.set_state(SpeakerStates.presentation_active)
        await state.update_data(
            active_talk_id=talk.id, 
            event_id=current_event.id,
            talk_title=talk.title
        )

        await message.answer(
            f"🎤 Вы начали выступление!\n\n"
            f"📝 <b>Тема:</b> {talk.title}\n"
            f"⏱ <b>Время:</b> {talk_start_moscow.strftime('%H:%M')} - {talk_end_moscow.strftime('%H:%M')}\n\n"
            f"Теперь участники могут отправлять вам вопросы через бота.\n"
            f"Вопросы будут приходить в реальном времени.\n\n"
            f"Чтобы завершить выступление, нажмите 'Завершить выступление'.",
            reply_markup=get_speaker_keyboard(),
            parse_mode="HTML",
        )

    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при начале выступления\n\n"
            "Попробуйте еще раз или обратитесь к организатору.",
            reply_markup=get_back_keyboard(),
        )


@router.message(lambda message: message.text and "Завершить выступление" in message.text)
async def end_presentation(message: types.Message, state: FSMContext):
    """Завершить выступление - деактивировать доклад спикера"""
    user = message.from_user
    
    try:
        # Ищем активный доклад пользователя в базе (основной способ)
        active_talk = await sync_to_async(
            Talk.objects.filter(
                speaker__telegram_id=str(user.id),
                is_active=True
            ).first
        )()
        
        if not active_talk:
            # Если не нашли в базе, проверяем состояние FSM
            user_data = await state.get_data()
            active_talk_id = user_data.get('active_talk_id')
            
            if active_talk_id:
                try:
                    active_talk = await sync_to_async(Talk.objects.get)(
                        id=active_talk_id,
                        speaker__telegram_id=str(user.id)
                    )
                except Talk.DoesNotExist:
                    active_talk = None
        
        if not active_talk:
            await message.answer(
                "❌ У вас нет активного выступления",
                reply_markup=get_main_keyboard("speaker", False),
            )
            return
        
        # Деактивируем доклад
        active_talk.is_active = False
        await sync_to_async(active_talk.save)()
        
        # Очищаем состояние FSM
        await state.clear()
        
        # Получаем статистику вопросов
        questions_count = await sync_to_async(
            Question.objects.filter(talk=active_talk).count
        )()
        unanswered_count = await sync_to_async(
            Question.objects.filter(talk=active_talk, is_answered=False).count
        )()
        
        success_message = (
            f"✅ Выступление завершено!\n\n"
            f"🎤 <b>Доклад:</b> {active_talk.title}\n"
            f"📊 <b>Статистика по вопросам:</b>\n"
            f"• Всего вопросов: {questions_count}\n"
            f"• Осталось ответить: {unanswered_count}\n\n"
        )
        
        if unanswered_count > 0:
            success_message += "💡 Вы можете ответить на вопросы в разделе 'Мои вопросы'."
        
        await message.answer(
            success_message,
            reply_markup=get_main_keyboard("speaker", False),
            parse_mode="HTML",
        )
        
    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при завершении выступления\n\n"
            "Попробуйте еще раз или обратитесь к организатору.",
            reply_markup=get_main_keyboard("speaker", False),
        )
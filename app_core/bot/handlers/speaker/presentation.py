from datetime import timedelta
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
import pytz
import logging

from app_core.models import Talk, Event, User, Question
from ...states.speaker import SpeakerStates
from ...keyboards.main import get_back_keyboard, get_main_keyboard
from ...keyboards.speaker import get_speaker_keyboard
from django.utils import timezone

router = Router()
logger = logging.getLogger(__name__)

@router.message(lambda message: message.text and "Начать выступление" in message.text)
async def start_presentation(message: types.Message, state: FSMContext):
    user = message.from_user

    try:
        moscow_tz = pytz.timezone('Europe/Moscow')
        now_utc = timezone.now()
        now_moscow = now_utc.astimezone(moscow_tz)
        today = now_moscow.date()
        
        today_events = await sync_to_async(list)(
            Event.objects.filter(start_date__date=today)
        )
        
        if not today_events:
            await message.answer(
                "❌ На сегодня нет мероприятий",
                reply_markup=get_back_keyboard(),
            )
            return

        current_event = today_events[0]

        user_talks = await sync_to_async(
            lambda: list(
                Talk.objects.filter(
                    event=current_event,
                    speaker__telegram_id=str(user.id)
                ).order_by('start_time')
            )
        )()

        if not user_talks:
            await message.answer(
                "❌ У вас нет докладов на сегодняшнем мероприятии",
                reply_markup=get_back_keyboard(),
            )
            return

        current_user_talk = None
        for talk in user_talks:
            if talk.start_time.tzinfo is None:
                talk_start_moscow = moscow_tz.localize(talk.start_time)
                talk_end_moscow = moscow_tz.localize(talk.end_time)
            else:
                talk_start_moscow = talk.start_time.astimezone(moscow_tz)
                talk_end_moscow = talk.end_time.astimezone(moscow_tz)

            can_start_time = talk_start_moscow - timedelta(minutes=5)
            can_end_time = talk_end_moscow + timedelta(minutes=10)

            if can_start_time <= now_moscow <= can_end_time:
                current_user_talk = talk
                break

        if not current_user_talk:
            talks_info = ""
            for i, talk in enumerate(user_talks, 1):
                if talk.start_time.tzinfo is None:
                    talk_start = moscow_tz.localize(talk.start_time)
                    talk_end = moscow_tz.localize(talk.end_time)
                else:
                    talk_start = talk.start_time.astimezone(moscow_tz)
                    talk_end = talk.end_time.astimezone(moscow_tz)
                
                talks_info += f"{i}. {talk_start.strftime('%H:%M')}-{talk_end.strftime('%H:%M')} - {talk.title}\n"
            
            await message.answer(
                f"❌ Сейчас не время для ваших выступлений\n\n"
                f"📋 Ваши доклады на сегодня:\n{talks_info}\n"
                f"🕐 Текущее время: {now_moscow.strftime('%H:%M')}\n\n"
                f"Вы можете начать выступление за 5 минут до начала и в течение 10 минут после окончания доклада.",
                reply_markup=get_back_keyboard(),
            )
            return

        if current_user_talk.start_time.tzinfo is None:
            talk_start_moscow = moscow_tz.localize(current_user_talk.start_time)
            talk_end_moscow = moscow_tz.localize(current_user_talk.end_time)
        else:
            talk_start_moscow = current_user_talk.start_time.astimezone(moscow_tz)
            talk_end_moscow = current_user_talk.end_time.astimezone(moscow_tz)

        active_talk = await sync_to_async(
            lambda: Talk.objects.filter(event=current_event, is_active=True).first()
        )()
        
        if active_talk and active_talk.id != current_user_talk.id:
            await message.answer(
                f"❌ Сейчас выступает другой спикер\n\n"
                f"Активный доклад: {active_talk.title}\n"
                f"Спикер: {active_talk.speaker.first_name}\n\n"
                f"Дождитесь завершения текущего выступления.",
                reply_markup=get_back_keyboard(),
            )
            return

        await sync_to_async(
            lambda: Talk.objects.filter(event=current_event, is_active=True).update(is_active=False)
        )()

        current_user_talk.is_active = True
        await sync_to_async(current_user_talk.save)()

        await state.set_state(SpeakerStates.presentation_active)
        await state.update_data(
            active_talk_id=current_user_talk.id, 
            event_id=current_event.id,
            talk_title=current_user_talk.title
        )

        await message.answer(
            f"🎤 Вы начали выступление!\n\n"
            f"📝 <b>Тема:</b> {current_user_talk.title}\n"
            f"⏱ <b>Время:</b> {talk_start_moscow.strftime('%H:%M')} - {talk_end_moscow.strftime('%H:%M')}\n\n"
            f"Теперь участники могут отправлять вам вопросы через бота.\n"
            f"Вопросы будут приходить в реальном времени.\n\n"
            f"Чтобы завершить выступление, нажмите 'Завершить выступление'.",
            reply_markup=get_speaker_keyboard(),
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error(f"Error starting presentation: {e}")
        await message.answer(
            "❌ Произошла ошибка при начале выступления\n\n"
            "Попробуйте еще раз или обратитесь к организатору.",
            reply_markup=get_back_keyboard(),
        )


@router.message(lambda message: message.text and "Завершить выступление" in message.text)
async def end_presentation(message: types.Message, state: FSMContext):
    user = message.from_user
    
    try:
        active_talk = await sync_to_async(
            lambda: Talk.objects.filter(
                speaker__telegram_id=str(user.id),
                is_active=True
            ).first()
        )()
        
        if not active_talk:
            user_data = await state.get_data()
            active_talk_id = user_data.get('active_talk_id')
            
            if active_talk_id:
                try:
                    active_talk = await sync_to_async(
                        lambda: Talk.objects.get(
                            id=active_talk_id,
                            speaker__telegram_id=str(user.id)
                        )
                    )()
                except Talk.DoesNotExist:
                    active_talk = None
        
        if not active_talk:
            await message.answer(
                "❌ У вас нет активного выступления",
                reply_markup=get_main_keyboard("speaker", False),
            )
            return
        
        active_talk.is_active = False
        await sync_to_async(active_talk.save)()
        
        await state.clear()
        
        questions_count = await sync_to_async(
            lambda: Question.objects.filter(talk=active_talk).count()
        )()
        unanswered_count = await sync_to_async(
            lambda: Question.objects.filter(talk=active_talk, is_answered=False).count()
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
        logger.error(f"Error ending presentation: {e}")
        await message.answer(
            "❌ Произошла ошибка при завершении выступления\n\n"
            "Попробуйте еще раз или обратитесь к организатору.",
            reply_markup=get_main_keyboard("speaker", False),
        )
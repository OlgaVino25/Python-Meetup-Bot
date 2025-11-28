from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async

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
        # Ищем текущее активное мероприятие
        current_event = await sync_to_async(
            Event.objects.filter(
                start_date__lte=timezone.now(), end_date__gte=timezone.now()
            ).first
        )()

        if not current_event:
            await message.answer(
                "❌ Сейчас нет активных мероприятий\n\n"
                "Нельзя начать выступление вне рамок мероприятия.",
                reply_markup=get_back_keyboard(),
            )
            return

        # Ищем доклад спикера в текущем мероприятии
        talk = await sync_to_async(
            Talk.objects.filter(
                event=current_event,
                speaker__telegram_id=str(user.id),
                start_time__lte=timezone.now(),
                end_time__gte=timezone.now(),
            ).first
        )()

        if not talk:
            await message.answer(
                "❌ Не найдено запланированных выступлений\n\n"
                "У вас нет докладов в текущее время на этом мероприятии.",
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

        print(f"DEBUG: Активирован доклад {talk.title}, is_active = {talk.is_active}")

        # Сохраняем ID доклада в состоянии
        await state.set_state(SpeakerStates.presentation_active)
        await state.update_data(active_talk_id=talk.id, event_id=current_event.id)

        await message.answer(
            f"🎤 Вы начали выступление!\n\n"
            f"📝 <b>Тема:</b> {talk.title}\n"
            f"⏱ <b>Время:</b> {talk.start_time.strftime('%H:%M')} - {talk.end_time.strftime('%H:%M')}\n\n"
            f"Теперь участники могут отправлять вам вопросы через бота.\n"
            f"Вопросы будут приходить в реальном времени.\n\n"
            f"Чтобы завершить выступление, нажмите 'Завершить выступление'.",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML",
        )

    except Exception as e:
        print(f"Ошибка при начале выступления: {e}")
        await message.answer(
            "❌ Произошла ошибка при начале выступления\n\n"
            "Попробуйте еще раз или обратитесь к организатору.",
            reply_markup=get_back_keyboard(),
        )


@router.message(
    lambda message: message.text and "Завершить выступление" in message.text
)
async def end_presentation(message: types.Message, state: FSMContext):
    """Завершить выступление - деактивировать доклад"""

    user_data = await state.get_data()
    active_talk_id = user_data.get("active_talk_id")

    if not active_talk_id:
        await message.answer(
            "❌ У вас нет активного выступления\n\n"
            "Сначала начните выступление, чтобы его завершить.",
            reply_markup=get_back_keyboard(),
        )
        return

    try:
        # Находим и деактивируем доклад
        talk = await sync_to_async(Talk.objects.get)(id=active_talk_id)
        talk.is_active = False
        await sync_to_async(talk.save)()

        # Получаем статистику вопросов для этого доклада
        from app_core.models import Question

        questions_count = await sync_to_async(
            Question.objects.filter(talk=talk).count
        )()
        answered_count = await sync_to_async(
            Question.objects.filter(talk=talk, is_answered=True).count
        )()

        await state.clear()

        stats_text = ""
        if questions_count > 0:
            stats_text = (
                f"\n📊 <b>Статистика по выступлению:</b>\n"
                f"• Всего вопросов: {questions_count}\n"
                f"• Отвечено: {answered_count}\n"
                f"• Осталось ответить: {questions_count - answered_count}"
            )

        await message.answer(
            f"✅ Выступление завершено!\n\n"
            f"📝 <b>Тема:</b> {talk.title}\n"
            f"⏱ <b>Время:</b> {talk.start_time.strftime('%H:%M')} - {talk.end_time.strftime('%H:%M')}"
            f"{stats_text}\n\n"
            f"Теперь вы можете:\n"
            f"• Просмотреть вопросы к вашему докладу\n"
            f"• Перейти в режим слушателя\n"
            f"• Подать заявку на следующее выступление",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML",
        )

    except Talk.DoesNotExist:
        await message.answer(
            "❌ Доклад не найден\n\n" "Возможно, он уже был завершен или удален.",
            reply_markup=get_back_keyboard(),
        )
        await state.clear()
    except Exception as e:
        print(f"Ошибка при завершении выступления: {e}")
        await message.answer(
            "❌ Произошла ошибка при завершении выступления\n\n"
            "Обратитесь к организатору.",
            reply_markup=get_back_keyboard(),
        )
        await state.clear()

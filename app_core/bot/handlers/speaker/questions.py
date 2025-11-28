from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
import pytz
from datetime import timedelta
from django.utils import timezone
from app_core.models import Question, Talk, User
from ...keyboards.main import get_back_keyboard
from ...keyboards.speaker import get_question_management_keyboard

router = Router()


class AnswerStates(StatesGroup):
    waiting_for_answer = State()


@router.message(lambda message: message.text and "Мои вопросы" in message.text)
async def show_speaker_questions(message: types.Message, state: FSMContext):
    """Показать вопросы к выступлениям спикера с детализацией"""

    user = message.from_user

    try:
        moscow_tz = pytz.timezone('Europe/Moscow')
        
        talks = await sync_to_async(list)(
            Talk.objects.filter(speaker__telegram_id=str(user.id))
            .order_by("-start_time")
            .prefetch_related("questions")
        )

        if not talks:
            await message.answer(
                "❓ У вас пока нет докладов\n\n"
                "Когда вы будете выступать, здесь появятся вопросы от участников.",
                reply_markup=get_back_keyboard(),
            )
            return

        questions_text = "❓ <b>Вопросы к вашим выступлениям:</b>\n\n"
        total_questions = 0
        has_questions = False

        for talk in talks:
            questions = await sync_to_async(list)(
                Question.objects.filter(talk=talk).order_by("-created_at")
            )

            if questions:
                has_questions = True
                total_questions += len(questions)
                status_icon = "🟢" if talk.is_active else "🔴"

                questions_text += f"{status_icon} <b>{talk.title}</b>\n"
                
                if talk.start_time.tzinfo is None:
                    talk_start_moscow = moscow_tz.localize(talk.start_time)
                    talk_end_moscow = moscow_tz.localize(talk.end_time)
                else:
                    talk_start_moscow = talk.start_time.astimezone(moscow_tz)
                    talk_end_moscow = talk.end_time.astimezone(moscow_tz)
                
                now_moscow = timezone.now().astimezone(moscow_tz)
                time_diff = (talk_start_moscow - now_moscow).total_seconds() / 3600
                if abs(time_diff) > 2:
                    talk_start_moscow = talk_start_moscow - timedelta(hours=3)
                    talk_end_moscow = talk_end_moscow - timedelta(hours=3)
                    
                questions_text += f"   📅 {talk_start_moscow.strftime('%d.%m.%Y %H:%M')}\n"
                questions_text += f"   ❓ Всего вопросов: {len(questions)}\n"
                questions_text += f"   ✅ Отвечено: {len([q for q in questions if q.is_answered])}\n\n"

                for i, question in enumerate(questions[:3], 1):
                    if question.created_at.tzinfo is None:
                        question_time_moscow = moscow_tz.localize(question.created_at)
                    else:
                        question_time_moscow = question.created_at.astimezone(moscow_tz)
                    
                    answer_status = (
                        "✅ Отвечен" if question.is_answered else "⏳ Ожидает ответа"
                    )
                    questions_text += f"   {i}. {answer_status}\n"
                    questions_text += f"      💬 {question.text}\n"
                    questions_text += f"      📅 {question_time_moscow.strftime('%d.%m %H:%M')}\n\n"

                if len(questions) > 3:
                    questions_text += f"   ... и еще {len(questions) - 3} вопросов\n\n"

        if not has_questions:
            questions_text += "📭 Пока вопросов нет.\n\n"
            questions_text += "Когда вы начнете выступление, участники смогут отправлять вопросы через бота."

        if has_questions:
            questions_text += f"\n📊 <b>Общая статистика:</b>\n"
            questions_text += f"• Всего вопросов: {total_questions}\n"
            answered_count = await sync_to_async(
                Question.objects.filter(
                    talk__speaker__telegram_id=str(user.id), is_answered=True
                ).count
            )()
            questions_text += f"• Отвечено: {answered_count}\n"
            questions_text += f"• Осталось ответить: {total_questions - answered_count}"

        await message.answer(
            questions_text,
            reply_markup=get_question_management_keyboard(),
            parse_mode="HTML",
        )

    except Exception as e:
        print(f"Ошибка при получении вопросов: {e}")
        import traceback
        print(f"Полная трассировка ошибки: {traceback.format_exc()}")
        await message.answer(
            "❌ Произошла ошибка при загрузке вопросов\n\n"
            "Попробуйте позже или обратитесь к организатору.",
            reply_markup=get_back_keyboard(),
        )


@router.message(lambda message: message.text and "📋 Обновить список" in message.text)
async def refresh_questions_list(message: types.Message, state: FSMContext):
    await show_speaker_questions(message, state)


@router.message(F.text.startswith("✅ Ответить на вопрос"))
async def handle_question_response(message: types.Message, state: FSMContext):
    user = message.from_user

    try:
        moscow_tz = pytz.timezone('Europe/Moscow')
        
        unanswered_questions = await sync_to_async(list)(
            Question.objects.select_related("talk", "from_user")
            .filter(talk__speaker__telegram_id=str(user.id), is_answered=False)
            .order_by("created_at")[:10]
        )

        if not unanswered_questions:
            await message.answer(
                "✅ У вас нет неотвеченных вопросов!",
                reply_markup=get_question_management_keyboard(),
            )
            return

        keyboard = InlineKeyboardBuilder()
        
        for i, question in enumerate(unanswered_questions, 1):
            if question.created_at.tzinfo is None:
                question_time_moscow = moscow_tz.localize(question.created_at)
            else:
                question_time_moscow = question.created_at.astimezone(moscow_tz)
                
            question_preview = (
                question.text[:50] + "..."
                if len(question.text) > 50
                else question.text
            )
            
            keyboard.button(
                text=f"{i}. {question_preview} ({question_time_moscow.strftime('%H:%M')})",
                callback_data=f"answer_question_{question.id}"
            )
        
        keyboard.adjust(1)
        
        questions_text = "📝 <b>Выберите вопрос для ответа:</b>\n\n"
        questions_text += "Нажмите на вопрос, чтобы ответить на него."

        await message.answer(
            questions_text,
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML",
        )

    except Exception as e:
        print(f"Ошибка при получении вопросов для ответа: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке вопросов\n\nПопробуйте позже.",
            reply_markup=get_question_management_keyboard(),
        )


@router.callback_query(F.data.startswith("answer_question_"))
async def select_question_for_answer(callback: types.CallbackQuery, state: FSMContext):
    question_id = int(callback.data.split("_")[2])
    
    try:
        question = await sync_to_async(Question.objects.select_related('from_user', 'talk').get)(id=question_id)
        
        moscow_tz = pytz.timezone('Europe/Moscow')
        if question.created_at.tzinfo is None:
            question_time_moscow = moscow_tz.localize(question.created_at)
        else:
            question_time_moscow = question.created_at.astimezone(moscow_tz)
        
        await state.set_state(AnswerStates.waiting_for_answer)
        await state.update_data(
            question_id=question.id,
            user_id=question.from_user.telegram_id
        )
        
        question_text = (
            f"❓ <b>Вопрос от участника:</b>\n\n"
            f"💬 {question.text}\n"
            f"📅 {question_time_moscow.strftime('%d.%m %H:%M')}\n\n"
            f"✍️ <b>Введите ваш ответ:</b>\n"
            f"(Ответ будет отправлен участнику)"
        )
        
        await callback.message.answer(
            question_text,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="❌ Отменить ответ")]],
                resize_keyboard=True
            ),
            parse_mode="HTML"
        )
        
        await callback.answer()
        
    except Question.DoesNotExist:
        await callback.answer("❌ Вопрос не найден", show_alert=True)
    except Exception as e:
        print(f"Ошибка при выборе вопроса: {e}")
        await callback.answer("❌ Ошибка при загрузке вопроса", show_alert=True)


@router.message(AnswerStates.waiting_for_answer, F.text == "❌ Отменить ответ")
async def cancel_answer(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Ответ отменен",
        reply_markup=get_question_management_keyboard(),
    )


@router.message(AnswerStates.waiting_for_answer)
async def process_answer(message: types.Message, state: FSMContext, bot: Bot):
    answer_text = message.text
    
    if not answer_text.strip():
        await message.answer("❌ Ответ не может быть пустым. Введите текст ответа:")
        return
    
    try:
        user_data = await state.get_data()
        question_id = user_data.get('question_id')
        user_id = user_data.get('user_id')
        
        question = await sync_to_async(Question.objects.get)(id=question_id)
        
        question.is_answered = True
        await sync_to_async(question.save)()
        
        try:
            answer_message = (
                f"📨 <b>Ответ на ваш вопрос</b>\n\n"
                f"💬 <b>Ваш вопрос:</b> {question.text}\n"
                f"👨‍💼 <b>Ответ спикера:</b> {answer_text}\n\n"
                f"Спасибо за участие в митапе! 🎉"
            )
            
            await bot.send_message(
                chat_id=user_id,
                text=answer_message,
                parse_mode="HTML"
            )
            
            success_text = (
                f"✅ <b>Ответ отправлен!</b>\n\n"
                f"💬 <b>Вопрос:</b> {question.text}\n"
                f"📝 <b>Ваш ответ:</b> {answer_text}\n\n"
                f"Участник получил ваше сообщение."
            )
            
            await message.answer(
                success_text,
                reply_markup=get_question_management_keyboard(),
                parse_mode="HTML"
            )
            
        except Exception as e:
            error_text = (
                f"✅ <b>Ответ сохранен, но не отправлен участнику</b>\n\n"
                f"💬 <b>Вопрос:</b> {question.text}\n"
                f"📝 <b>Ваш ответ:</b> {answer_text}\n\n"
                f"⚠️ Участник, возможно, заблокировал бота."
            )
            
            await message.answer(
                error_text,
                reply_markup=get_question_management_keyboard(),
                parse_mode="HTML"
            )
        
        await state.clear()
        
    except Exception as e:
        print(f"Ошибка при обработке ответа: {e}")
        await message.answer(
            "❌ Произошла ошибка при отправке ответа\n\nПопробуйте еще раз.",
            reply_markup=get_question_management_keyboard(),
        )
        await state.clear()
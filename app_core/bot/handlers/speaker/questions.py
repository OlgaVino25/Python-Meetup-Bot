from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from asgiref.sync import sync_to_async
from app_core.models import Question, Talk
from ...keyboards.main import get_back_keyboard
from ...keyboards.speaker import get_question_management_keyboard

router = Router()


@router.message(lambda message: message.text and "Мои вопросы" in message.text)
async def show_speaker_questions(message: types.Message, state: FSMContext):
    """Показать вопросы к выступлениям спикера с детализацией"""

    user = message.from_user

    try:
        # Находим все доклады спикера
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
            # Получаем вопросы для каждого доклада
            questions = await sync_to_async(list)(
                Question.objects.filter(talk=talk).order_by("-created_at")
            )

            if questions:
                has_questions = True
                total_questions += len(questions)
                status_icon = "🟢" if talk.is_active else "🔴"

                questions_text += f"{status_icon} <b>{talk.title}</b>\n"
                questions_text += (
                    f"   📅 {talk.start_time.strftime('%d.%m.%Y %H:%M')}\n"
                )
                questions_text += f"   ❓ Всего вопросов: {len(questions)}\n"
                questions_text += f"   ✅ Отвечено: {len([q for q in questions if q.is_answered])}\n\n"

                # Последние 3 вопроса с деталями
                for i, question in enumerate(questions[:3], 1):
                    answer_status = (
                        "✅ Отвечен" if question.is_answered else "⏳ Ожидает ответа"
                    )
                    questions_text += f"   {i}. {answer_status}\n"
                    questions_text += f"      💬 {question.text}\n"
                    questions_text += (
                        f"      📅 {question.created_at.strftime('%d.%m %H:%M')}\n\n"
                    )

                if len(questions) > 3:
                    questions_text += f"   ... и еще {len(questions) - 3} вопросов\n\n"

        if not has_questions:
            questions_text += "📭 Пока вопросов нет.\n\n"
            questions_text += "Когда вы начнете выступление, участники смогут отправлять вопросы через бота."

        # Статистика
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
        # Оптимизируем запрос к базе данных
        unanswered_questions = await sync_to_async(list)(
            Question.objects.select_related("talk")
            .filter(talk__speaker__telegram_id=str(user.id), is_answered=False)
            .order_by("created_at")[:10]
        )

        if not unanswered_questions:
            await message.answer(
                "✅ У вас нет неотвеченных вопросов!",
                reply_markup=get_question_management_keyboard(),
            )
            return

        # Формируем список вопросов
        questions_text = "📝 <b>Выберите вопрос для отметки как отвеченный:</b>\n\n"

        for i, question in enumerate(unanswered_questions, 1):
            question_preview = (
                question.text[:100] + "..."
                if len(question.text) > 100
                else question.text
            )
            questions_text += f"{i}. {question_preview}\n"
            questions_text += f"   📅 {question.created_at.strftime('%d.%m %H:%M')}\n"
            questions_text += f"   🎤 {question.talk.title}\n\n"

        questions_text += (
            "Отправьте номер вопроса, который хотите отметить как отвеченный."
        )

        # Сохраняем вопросы в состоянии
        await state.update_data(
            unanswered_questions={
                i: q.id for i, q in enumerate(unanswered_questions, 1)
            }
        )

        await message.answer(
            questions_text,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True
            ),
            parse_mode="HTML",
        )

    except Exception as e:
        print(f"Ошибка при получении вопросов для ответа: {e}")
        import traceback

        print(f"Полная трассировка: {traceback.format_exc()}")

        await message.answer(
            "❌ Произошла ошибка при загрузке вопросов\n\nПопробуйте позже.",
            reply_markup=get_question_management_keyboard(),
        )


@router.message(lambda message: message.text and message.text.isdigit())
async def mark_question_answered(message: types.Message, state: FSMContext):
    """Отметить вопрос как отвеченный по номеру"""

    try:
        question_number = int(message.text)
        user_data = await state.get_data()
        unanswered_questions = user_data.get("unanswered_questions", {})

        if question_number not in unanswered_questions:
            await message.answer(
                "❌ Неверный номер вопроса.\n\n"
                "Пожалуйста, выберите номер из списка.",
                reply_markup=get_question_management_keyboard(),
            )
            return

        question_id = unanswered_questions[question_number]
        question = await sync_to_async(Question.objects.get)(id=question_id)
        question.is_answered = True
        await sync_to_async(question.save)()

        await message.answer(
            f"✅ Вопрос отмечен как отвеченный!\n\n"
            f"💬 {question.text[:200]}...\n\n"
            f"Теперь он не будет отображаться в списке неотвеченных вопросов.",
            reply_markup=get_question_management_keyboard(),
        )

        await state.clear()

    except Exception as e:
        print(f"Ошибка при отметке вопроса: {e}")
        await message.answer(
            "❌ Произошла ошибка при отметке вопроса\n\n" "Попробуйте еще раз.",
            reply_markup=get_question_management_keyboard(),
        )


@router.message(lambda message: message.text and "❌ Отмена" in message.text)
async def cancel_question_action(message: types.Message, state: FSMContext):
    """Отмена действия с вопросами"""
    await state.clear()
    await message.answer(
        "❌ Действие отменено",
        reply_markup=get_question_management_keyboard(),
    )

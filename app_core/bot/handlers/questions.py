from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
from ..keyboards.main import get_back_keyboard
from ...models import Talk, Question, User

router = Router()


class QuestionState(StatesGroup):
    waiting_for_question = State()


@router.message(lambda message: message.text and "Вопрос" in message.text)
async def ask_question(message: types.Message, state: FSMContext):
    current_talk = await sync_to_async(Talk.objects.filter(is_active=True).first)()

    if not current_talk:
        await message.answer(
            "❌ Сейчас нет активного доклада для вопросов",
            reply_markup=get_back_keyboard(),
        )
        return

    await state.set_state(QuestionState.waiting_for_question)
    await state.update_data(talk_id=current_talk.id)
    await message.answer(
        "✍️ Введите ваш вопрос для текущего спикера:\n\n"
        "Вопрос будет анонимно передан спикеру.\n"
        "Он сможет ответить на него после выступления.",
        reply_markup=get_back_keyboard(),
    )


@router.message(QuestionState.waiting_for_question)
async def process_question(message: types.Message, state: FSMContext):
    question_text = message.text
    user_data = await state.get_data()
    talk_id = user_data.get("talk_id")

    try:
        talk = await sync_to_async(Talk.objects.get)(id=talk_id)
        user = await sync_to_async(User.objects.get)(
            telegram_id=str(message.from_user.id)
        )

        await sync_to_async(Question.objects.create)(
            talk=talk, from_user=user, text=question_text, is_answered=False
        )

        await message.answer(
            "✅ Ваш вопрос отправлен спикеру!\n\n"
            "Спикер получит его после выступления и сможет ответить.\n"
            "Спасибо за активное участие!",
            reply_markup=get_back_keyboard(),
        )
    except Talk.DoesNotExist:
        await message.answer(
            "❌ Ошибка: активный доклад не найден",
            reply_markup=get_back_keyboard(),
        )
    except User.DoesNotExist:
        await message.answer(
            "❌ Ошибка: пользователь не найден",
            reply_markup=get_back_keyboard(),
        )
    finally:
        await state.clear()

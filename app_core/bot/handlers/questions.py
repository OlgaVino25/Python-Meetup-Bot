from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from ..keyboards.main import get_back_keyboard

router = Router()


class QuestionState(StatesGroup):
    waiting_for_question = State()


@router.message(lambda message: message.text and "Вопрос" in message.text)
async def ask_question(message: types.Message, state: FSMContext):
    await state.set_state(QuestionState.waiting_for_question)
    await message.answer(
        "✍️ Введите ваш вопрос для текущего спикера:\n\n"
        "Вопрос будет анонимно передан спикеру.\n"
        "Он сможет ответить на него после выступления.",
        reply_markup=get_back_keyboard(),
    )


@router.message(QuestionState.waiting_for_question)
async def process_question(message: types.Message, state: FSMContext):
    question_text = message.text

    await message.answer(
        "✅ Ваш вопрос отправлен спикеру!\n\n"
        "Спикер получит его после выступления и сможет ответить.\n"
        "Спасибо за активное участие!",
        reply_markup=get_back_keyboard(),
    )
    await state.clear()

from aiogram import Router, types
from ...keyboards.main import get_back_keyboard

router = Router()

@router.message(lambda message: message.text and "Мои вопросы" in message.text)
async def show_my_questions(message: types.Message):
    await message.answer(
        "Функция просмотра вопросов скоро будет доступна",
        reply_markup=get_back_keyboard()
    )
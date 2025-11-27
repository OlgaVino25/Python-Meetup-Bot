from aiogram import Router, types
from ..keyboards.main import get_back_keyboard

router = Router()

@router.message(lambda message: message.text and "Вопрос" in message.text)  # ← БЕЗ эмодзи
async def ask_question(message: types.Message):
    await message.answer(
        "Функция вопросов скоро будет доступна!",
        reply_markup=get_back_keyboard()
    )
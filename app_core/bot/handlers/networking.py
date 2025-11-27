from aiogram import Router, types
from ..keyboards.main import get_back_keyboard

router = Router()

@router.message(lambda message: message.text and "Знакомства" in message.text)
async def start_networking(message: types.Message):
    await message.answer(
        "Функция знакомств скоро будет доступна!",
        reply_markup=get_back_keyboard()
    )
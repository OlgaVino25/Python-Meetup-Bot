from aiogram import Router, types
from ..keyboards.main import get_back_keyboard

router = Router()

@router.message(lambda message: message.text and "Донат" in message.text)
async def show_donations(message: types.Message):
    await message.answer(
        "Функция донатов скоро будет доступна!",
        reply_markup=get_back_keyboard()
    )
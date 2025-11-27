from aiogram import Router, types
from ...keyboards.main import get_back_keyboard

router = Router()

@router.message(lambda message: message.text and "Заявка спикером" in message.text)
async def speaker_application(message: types.Message):
    await message.answer(
        "Функция заявок спикером скоро будет доступна",
        reply_markup=get_back_keyboard()
    )
from aiogram import Router, types
from aiogram.filters import Command
from ..keyboards.main import get_back_keyboard

router = Router()

@router.message(Command("program"))
@router.message(lambda message: message.text and "Программа" in message.text)
async def show_program(message: types.Message):
    await message.answer(
        "Программа мероприятия:\n\n"
        "Здесь будет расписание докладов...",
        reply_markup=get_back_keyboard()
    )
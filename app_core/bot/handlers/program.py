from aiogram import Router, types
from aiogram.filters import Command
from ..keyboards.main import get_back_keyboard
from ..services.event_service import get_current_event_program

router = Router()

@router.message(Command("program"))
@router.message(lambda message: message.text and "Программа" in message.text)
async def show_program(message: types.Message):
    program_text = await get_current_event_program()
    await message.answer(program_text, reply_markup=get_back_keyboard())

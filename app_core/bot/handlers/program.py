from aiogram import Router, types
from aiogram.filters import Command
from ..keyboards.main import get_back_keyboard, get_program_keyboard
from ..services.event_service import get_todays_tomorrows_program, get_week_events_for_subscription

router = Router()

@router.message(Command("program"))
@router.message(lambda message: message.text and "Программа" in message.text)
async def show_program_menu(message: types.Message):
    await message.answer(
        "📅 Выберите тип программы:",
        reply_markup=get_program_keyboard()
    )

@router.message(lambda message: message.text and "Митапы на неделю" in message.text)
async def show_week_program(message: types.Message):
    
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    program_text = await get_week_events_for_subscription()
    await message.answer(
        program_text,
        reply_markup=get_program_keyboard()
    )

@router.message(lambda message: message.text and "Сегодня и завтра" in message.text)
async def show_todays_program(message: types.Message):
    
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    program_text = await get_todays_tomorrows_program()
    await message.answer(
        program_text,
        reply_markup=get_program_keyboard()
    )
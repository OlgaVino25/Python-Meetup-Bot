from aiogram import Router, types
from ..keyboards.main import get_back_keyboard

router = Router()

@router.message(lambda message: message.text and "Помощь" in message.text)
async def show_help(message: types.Message):
    await message.answer(
        "Помощь по боту PythonMeetup:\n\n"
        "Программа - посмотреть расписание докладов\n"
        "Вопрос - задать вопрос текущему спикеру\n"
        "Знакомства - найти собеседников для нетворкинга\n"
        "Донат - поддержать мероприятие\n"
        "Подписаться - получать уведомления о новых мероприятиях\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=get_back_keyboard()
    )
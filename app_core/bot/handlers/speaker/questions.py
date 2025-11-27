from aiogram import Router, types
from ...keyboards.main import get_back_keyboard

router = Router()


@router.message(lambda message: message.text and "Мои вопросы" in message.text)
async def show_speaker_questions(message: types.Message):
    await message.answer(
        "❓ Вопросы к вашим выступлениям:\n\n"
        "Здесь будут отображаться вопросы от участников.\n"
        "Пока вопросов нет.\n\n"
        "Когда вы начнете выступление, участники смогут\n"
        "отправлять вопросы через бота.",
        reply_markup=get_back_keyboard(),
    )

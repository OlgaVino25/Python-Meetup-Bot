from aiogram import Router, types
from ..keyboards.main import get_back_keyboard

router = Router()

@router.message(lambda message: message.text and "Подписаться" in message.text)
async def handle_subscription(message: types.Message):
    await message.answer(
        "Подписка на уведомления:\n\n"
        "Подпишитесь, чтобы получать:\n"
        "• Уведомления о новых мероприятиях\n"
        "• Напоминания о начале докладов\n"
        "• Новости от организаторов\n\n"
        "Функция подписки скоро будет доступна!",
        reply_markup=get_back_keyboard()
    )
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from ...keyboards.main import get_back_keyboard

router = Router()


@router.message(lambda message: message.text and "Заявка спикером" in message.text)
async def speaker_application(message: types.Message, state: FSMContext):
    await message.answer(
        "Подача заявки на выступление:\n\n"
        "Чтобы подать заявку на следующее мероприятие, отправьте:\n"
        "• Тему доклада\n"
        "• Краткое описание\n"
        "• Продолжительность\n\n"
        "Функция заявок спикером скоро будет доступна",
        reply_markup=get_back_keyboard(),
    )

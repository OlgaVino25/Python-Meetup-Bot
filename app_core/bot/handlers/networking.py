from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from ..keyboards.main import get_back_keyboard, get_networking_keyboard

router = Router()


class NetworkingState(StatesGroup):
    waiting_for_profile = State()
    waiting_for_decision = State()


@router.message(lambda message: message.text and "Знакомства" in message.text)
async def start_networking(message: types.Message, state: FSMContext):
    await message.answer(
        "🤝 Функция знакомств\n\n"
        "Как это работает:\n"
        "• Заполните анкету о себе\n"
        "• Бот найдет подходящих собеседников\n"
        "• Вы сможете обменяться контактами\n\n"
        "Всё анонимно и комфортно!",
        reply_markup=get_networking_keyboard(),
    )

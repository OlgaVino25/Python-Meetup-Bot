from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from ...states.speaker import SpeakerStates
from ...keyboards.main import get_back_keyboard

router = Router()


@router.message(lambda message: message.text and "Начать выступление" in message.text)
async def start_presentation(message: types.Message, state: FSMContext):
    await state.set_state(SpeakerStates.presentation_active)

    await message.answer(
        "🎤 Вы начали выступление!\n\n"
        "Теперь участники могут отправлять вам вопросы через бота.\n"
        "Вопросы будут приходить в реальном времени.\n\n"
        "Чтобы завершить выступление, нажмите 'Завершить выступление'.",
        reply_markup=get_back_keyboard(),
    )


@router.message(
    lambda message: message.text and "Завершить выступление" in message.text
)
async def end_presentation(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "✅ Выступление завершено!\n\n"
        "Вы можете:\n"
        "• Просмотреть вопросы к вашему докладу\n"
        "• Перейти в режим слушателя\n"
        "• Подать заявку на следующее выступление",
        reply_markup=get_back_keyboard(),
    )

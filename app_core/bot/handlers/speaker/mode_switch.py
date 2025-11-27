from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from ...keyboards.main import get_main_keyboard

router = Router()

@router.message(lambda message: message.text and "Режим слушателя" in message.text)
async def switch_to_listener_mode(message: types.Message, state: FSMContext):
    await state.update_data(is_listener_mode=True)

    await message.answer(
        "✅ Вы перешли в режим слушателя!\n\n"
        "Теперь вам доступны все функции участника:\n"
        "• Просмотр программы\n"
        "• Вопросы спикерам\n"
        "• Нетворкинг\n"
        "• Поддержка мероприятия\n\n"
        "Чтобы вернуться в режим спикера, нажмите соответствующую кнопку.",
        reply_markup=get_main_keyboard("speaker", True),
    )


@router.message(lambda message: message.text and "Режим спикера" in message.text)
async def switch_to_speaker_mode(message: types.Message, state: FSMContext):
    await state.update_data(is_listener_mode=False)

    await message.answer(
        "🎤 Вы вернулись в режим спикера!\n\n"
        "Теперь вам доступны функции управления выступлениями:\n"
        "• Начать/завершить выступление\n"
        "• Просмотр вопросов\n"
        "• Подача заявок\n\n"
        "Для участия как слушатель используйте режим слушателя.",
        reply_markup=get_main_keyboard("speaker", False),
    )

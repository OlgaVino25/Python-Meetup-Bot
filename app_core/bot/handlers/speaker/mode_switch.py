from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from ...keyboards.main import get_main_keyboard

router = Router()

@router.message(lambda message: message.text and "Режим слушателя" in message.text)
async def switch_to_listener_mode(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_role = data.get('user_role', 'guest')
    
    if user_role != "speaker":
        await message.answer("Эта функция доступна только спикерам")
        return
        
    await state.update_data(is_listener_mode=True)
    
    await message.answer(
        "Вы перешли в режим слушателя",
        reply_markup=get_main_keyboard(user_role, is_listener_mode=True)
    )

@router.message(lambda message: message.text and "Режим спикера" in message.text)
async def switch_to_speaker_mode(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_role = data.get('user_role', 'guest')
    
    if user_role != "speaker":
        await message.answer("Эта функция доступна только спикерам")
        return
        
    await state.update_data(is_listener_mode=False)
    
    await message.answer(
        "Вы вернулись в режим спикера",
        reply_markup=get_main_keyboard(user_role, is_listener_mode=False)
    )
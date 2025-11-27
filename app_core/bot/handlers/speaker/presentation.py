from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from ...keyboards.main import get_back_keyboard

router = Router()

@router.message(lambda message: message.text and "Начать выступление" in message.text)
async def start_presentation(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_role = data.get('user_role', 'guest')
    
    if user_role != "speaker":
        await message.answer("Эта функция доступна только спикерам")
        return
        
    await message.answer(
        "Функция начала выступления скоро будет доступна",
        reply_markup=get_back_keyboard()
    )

@router.message(lambda message: message.text and "Завершить выступление" in message.text)
async def end_presentation(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_role = data.get('user_role', 'guest')
    
    if user_role != "speaker":
        await message.answer("Эта функция доступна только спикерам")
        return
        
    await message.answer(
        "Функция завершения выступления скоро будет доступна",
        reply_markup=get_back_keyboard()
    )
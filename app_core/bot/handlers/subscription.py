from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
from ..keyboards.main import get_back_keyboard, get_main_keyboard
from ..keyboards.subscription import (
    get_subscription_confirmation_keyboard, 
    get_subscription_management_keyboard,
    get_simple_subscription_keyboard
)
from app_core.models import User

router = Router()

class SubscriptionStates(StatesGroup):
    waiting_confirmation = State()

async def get_or_create_user(telegram_id, username, first_name, last_name):
    try:
        return await sync_to_async(User.objects.get)(telegram_id=str(telegram_id))
    except User.DoesNotExist:
        return await sync_to_async(User.objects.create)(
            telegram_id=str(telegram_id),
            username=username or "",
            first_name=first_name or "",
            last_name=last_name or "",
            role="guest"
        )

@router.message(lambda message: message.text and "Подписаться" in message.text)
async def handle_subscription(message: types.Message, state: FSMContext):
    
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name
    )
    
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    if user.is_subscribed:
        await message.answer(
            "✅ Вы уже подписаны на уведомления!\n\n"
            "Мы напомним вам за неделю до каждого митапа.\n\n"
            "Чтобы посмотреть программу митапов, перейдите в раздел «Программа»",
            reply_markup=get_subscription_management_keyboard(is_subscribed=True)
        )
        return
    
    await message.answer(
        "🔔 Хотите подписаться на уведомления?\n\n"
        "Мы будем напоминать вам за неделю до каждого митапа,\n"
        "чтобы вы не пропустили интересные встречи!\n\n"
        "Программу митапов можно посмотреть в разделе «Программа»",
        reply_markup=get_subscription_confirmation_keyboard()
    )
    
    await state.set_state(SubscriptionStates.waiting_confirmation)
    await state.update_data(user_id=user.id)

@router.message(SubscriptionStates.waiting_confirmation, lambda message: message.text and "Да, подписаться" in message.text)
async def confirm_subscription(message: types.Message, state: FSMContext):
    
    data = await state.get_data()
    user_id = data.get('user_id')
    
    if user_id:
        try:
            user = await sync_to_async(User.objects.get)(id=user_id)
            user.is_subscribed = True
            await sync_to_async(user.save)()
            
            await message.answer(
                "🎉 Отлично! Вы подписаны на уведомления!\n\n"
                "📅 Мы напомним вам за неделю до каждого митапа\n"
                "💡 Не пропустите интересные встречи с коллегами\n\n"
                "Программу митапов можно посмотреть в разделе «Программа»",
                reply_markup=get_subscription_management_keyboard(is_subscribed=True)
            )
        except User.DoesNotExist:
            await message.answer("❌ Ошибка: пользователь не найден", reply_markup=get_simple_subscription_keyboard())
    else:
        await message.answer("❌ Ошибка: сессия устарела", reply_markup=get_simple_subscription_keyboard())
    
    await state.clear()

@router.message(SubscriptionStates.waiting_confirmation, lambda message: message.text and "Нет, отменить" in message.text)
async def cancel_subscription(message: types.Message, state: FSMContext):
    
    await message.answer(
        "❌ Подписка отменена\n\n"
        "Вы всегда можете подписаться позже через меню",
        reply_markup=get_subscription_management_keyboard(is_subscribed=False)
    )
    await state.clear()

@router.message(lambda message: message.text and "Отписаться от уведомлений" in message.text)
async def unsubscribe(message: types.Message):
    
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name
    )
    
    if user.is_subscribed:
        user.is_subscribed = False
        await sync_to_async(user.save)()
        
        await message.answer(
            "🔕 Вы отписались от уведомлений\n\n"
            "Мы больше не будем присылать напоминания о митапах.\n"
            "Подписаться можно в любой момент!",
            reply_markup=get_subscription_management_keyboard(is_subscribed=False)
        )
    else:
        await message.answer(
            "ℹ️ Вы и так не подписаны на уведомления",
            reply_markup=get_subscription_management_keyboard(is_subscribed=False)
        )

@router.message(lambda message: message.text and "Назад" in message.text)
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name
    )
    
    await message.answer(
        reply_markup=get_main_keyboard(user.role)
    )
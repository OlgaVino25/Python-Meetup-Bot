from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_subscription_confirmation_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, подписаться")],
            [KeyboardButton(text="❌ Нет, отменить")],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )

def get_subscription_management_keyboard(is_subscribed: bool):
    keyboard = []
    
    if is_subscribed:
        keyboard.append([KeyboardButton(text="🔕 Отписаться от уведомлений")])
    else:
        keyboard.append([KeyboardButton(text="✅ Подписаться на уведомления")])
    
    keyboard.append([KeyboardButton(text="Назад")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_simple_subscription_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )
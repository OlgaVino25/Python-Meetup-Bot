from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_speaker_application_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Подать заявку")],
            [KeyboardButton(text="📋 Мои заявки")],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )

def get_application_confirmation_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Подтвердить заявку")],
            [KeyboardButton(text="✏️ Исправить заявку")],
            [KeyboardButton(text="❌ Отменить")]
        ],
        resize_keyboard=True
    )

def get_application_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отменить заявку")]
        ],
        resize_keyboard=True
    )
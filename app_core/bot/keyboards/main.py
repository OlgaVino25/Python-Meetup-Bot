from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_guest_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Программа"), KeyboardButton(text="Вопрос")],
            [KeyboardButton(text="Знакомства"), KeyboardButton(text="Донат")],
            [KeyboardButton(text="Подписаться"), KeyboardButton(text="Заявка спикером")],
        ],
        resize_keyboard=True,
    )

def get_speaker_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Начать выступление"),
                KeyboardButton(text="Завершить выступление"),
            ],
            [
                KeyboardButton(text="Мои вопросы"),
            ],
            [KeyboardButton(text="Режим слушателя")],
        ],
        resize_keyboard=True,
    )

def get_listener_mode_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Программа"), KeyboardButton(text="Вопрос")],
            [KeyboardButton(text="Знакомства"), KeyboardButton(text="Донат")],
            [KeyboardButton(text="Подписаться"), KeyboardButton(text="Заявка спикером")],
            [KeyboardButton(text="Режим спикера")],
        ],
        resize_keyboard=True,
    )

def get_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True
    )

def get_donation_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="100 руб"),
                KeyboardButton(text="300 руб"),
                KeyboardButton(text="500 руб"),
            ],
            [KeyboardButton(text="Другая")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )

def get_program_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🟢 Сегодня и завтра")],
            [KeyboardButton(text="📅 Митапы на неделю")],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )

def get_main_keyboard(user_role="guest", is_listener_mode=False):
    if user_role == "speaker" and not is_listener_mode:
        return get_speaker_keyboard()
    elif user_role == "speaker" and is_listener_mode:
        return get_listener_mode_keyboard()
    else:
        return get_guest_keyboard()

def get_networking_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Заполнить анкету")],
            [KeyboardButton(text="Найти собеседника")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )
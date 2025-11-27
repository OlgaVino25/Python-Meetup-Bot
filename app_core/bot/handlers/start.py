from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from ..keyboards.main import get_main_keyboard

router = Router()

@router.message(CommandStart())
@router.message(lambda message: message.text and "Назад" in message.text)
async def on_start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    is_listener_mode = data.get('is_listener_mode', False)
    user_role = data.get('user_role', 'guest')
    
    role_display = "спикер" if user_role == "speaker" else "гость"
    if user_role == "speaker" and is_listener_mode:
        role_display = "спикер (режим слушателя)"
    
    help_text = (
        f"Привет, {message.from_user.first_name}!\n"
        f"Роль: {role_display}\n\n"
        "Доступные функции:\n\n"
    )
    
    if user_role == "speaker" and not is_listener_mode:
        help_text += (
            "Режим спикера:\n"
            "• Начать выступление - запустить режим доклада и принимать вопросы\n"
            "• Завершить выступление - закончить выступление\n"
            "• Мои вопросы - просмотреть вопросы к вашим докладам\n"
            "• Заявка спикером - подать заявку на выступление\n"
            "• Режим слушателя - перейти в обычный режим\n\n"
        )
    else:
        help_text += (
            "Основные функции:\n"
            "• Программа - расписание всех докладов мероприятия\n"
            "• Вопрос - задать вопрос текущему спикеру\n"
            "• Знакомства - найти собеседников для нетворкинга\n"
            "• Донат - поддержать организаторов мероприятия\n"
            "• Подписаться - получать уведомления о новых событиях\n"
            "• Помощь - справочная информация\n"
        )
        
        if user_role == "speaker":
            help_text += "\n• Режим спикера - вернуться в режим спикера"
    
    await message.answer(
        help_text,
        reply_markup=get_main_keyboard(user_role, is_listener_mode)
    )

@router.message(Command("speaker"))
async def switch_to_speaker(message: types.Message, state: FSMContext):
    """Временная команда для переключения в режим спикера"""
    await state.update_data(user_role='speaker', is_listener_mode=False)
    
    await message.answer(
        "Вы переключены в режим спикера!\n\n"
        "Теперь вам доступны:\n"
        "• Управление выступлениями\n"
        "• Просмотр вопросов к вашим докладам\n"
        "• Режим слушателя для обычного участия\n\n"
        "Используйте кнопки ниже для навигации.",
        reply_markup=get_main_keyboard('speaker', False)
    )

@router.message(Command("guest"))
async def switch_to_guest(message: types.Message, state: FSMContext):
    """Временная команда для переключения в режим гостя"""
    await state.update_data(user_role='guest', is_listener_mode=False)
    
    await message.answer(
        "Вы переключены в режим гостя!\n\n"
        "Доступны все основные функции мероприятия:\n"
        "• Просмотр программы\n"
        "• Вопросы спикерам\n"
        "• Нетворкинг\n"
        "• Поддержка мероприятия\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=get_main_keyboard('guest', False)
    )

@router.message(Command("help"))
async def on_help(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_role = data.get('user_role', 'guest')
    is_listener_mode = data.get('is_listener_mode', False)
    
    if user_role == "speaker" and not is_listener_mode:
        help_text = (
            "Помощь для спикера:\n\n"
            "Управление выступлениями:\n"
            "• Начать выступление - запустить режим доклада\n"
            "• Завершить выступление - завершить текущее выступление\n\n"
            "Работа с вопросами:\n"
            "• Мои вопросы - просмотреть все вопросы к вашим докладам\n\n"
            "Режимы участия:\n"
            "• Режим слушателя - участвовать как обычный участник\n"
            "• Заявка спикером - управление заявками на выступления\n\n"
            "Тестовые команды:\n"
            "/speaker - стать спикером\n"
            "/guest - стать гостем\n"
            "/start - главное меню"
        )
    else:
        help_text = (
            "Помощь по боту PythonMeetup:\n\n"
            "Программа - полное расписание докладов и время выступлений\n"
            "Вопрос - задать вопрос текущему спикеру во время его выступления\n"
            "Знакомства - найти собеседников по интересам для нетворкинга\n"
            "Донат - финансово поддержать организаторов мероприятия\n"
            "Подписаться - получать уведомления о будущих мероприятиях\n\n"
            "Тестовые команды:\n"
            "/speaker - стать спикером\n"
            "/guest - стать гостем\n"
            "/start - главное меню"
        )
    
    await message.answer(help_text)
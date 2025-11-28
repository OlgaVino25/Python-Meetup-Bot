from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
import logging

from app_core.models import SpeakerApplication, User
from ..states.speaker import SpeakerApplicationStates
from ..keyboards.main import get_back_keyboard, get_main_keyboard
from ..keyboards.speaker import get_speaker_application_main_keyboard, get_application_cancel_keyboard, get_application_confirmation_keyboard

router = Router()
logger = logging.getLogger(__name__)

@router.message(lambda message: message.text and "Заявка спикером" in message.text)
async def speaker_application_start(message: types.Message, state: FSMContext):
    """Начало подачи заявки спикером"""
    await message.answer(
        "🎤 Подача заявки на выступление\n\n"
        "Заполните информацию о вашем предложенном докладе. "
        "Организаторы рассмотрят заявку и свяжутся с вами.",
        reply_markup=get_speaker_application_main_keyboard()
    )

@router.message(lambda message: message.text and "📝 Подать заявку" in message.text)
async def start_application(message: types.Message, state: FSMContext):
    """Начало заполнения заявки"""
    await state.set_state(SpeakerApplicationStates.waiting_for_topic)
    await message.answer(
        "📝 Введите тему вашего доклада:\n\n"
        "Пример: 'Машинное обучение на Python для начинающих'",
        reply_markup=get_application_cancel_keyboard()
    )

@router.message(SpeakerApplicationStates.waiting_for_topic)
async def process_topic(message: types.Message, state: FSMContext):
    """Обработка темы доклада"""
    if len(message.text) < 10:
        await message.answer(
            "❌ Тема доклада слишком короткая. "
            "Пожалуйста, напишите развернутую тему (минимум 10 символов)."
        )
        return
    
    await state.update_data(topic=message.text)
    await state.set_state(SpeakerApplicationStates.waiting_for_description)
    await message.answer(
        "📋 Теперь опишите содержание доклада:\n\n"
        "• О чем будет ваш доклад?\n"
        "• Для кого он предназначен?\n"
        "• Какие ключевые моменты осветите?",
        reply_markup=get_application_cancel_keyboard()
    )

@router.message(SpeakerApplicationStates.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    """Обработка описания доклада"""
    if len(message.text) < 50:
        await message.answer(
            "❌ Описание слишком короткое. "
            "Пожалуйста, напишите более подробное описание (минимум 50 символов)."
        )
        return
    
    await state.update_data(description=message.text)
    await state.set_state(SpeakerApplicationStates.waiting_for_duration)
    await message.answer(
        "⏱ Укажите продолжительность доклада (в минутах):\n\n"
        "Рекомендуемая продолжительность: 15-45 минут",
        reply_markup=get_application_cancel_keyboard()
    )

@router.message(SpeakerApplicationStates.waiting_for_duration)
async def process_duration(message: types.Message, state: FSMContext):
    """Обработка продолжительности доклада"""
    try:
        duration = int(message.text)
        if duration < 10 or duration > 120:
            await message.answer(
                "❌ Некорректная продолжительность. "
                "Введите число от 10 до 120 минут."
            )
            return
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите число (продолжительность в минутах)."
        )
        return
    
    user_data = await state.get_data()
    await state.update_data(duration=duration)
    await state.set_state(SpeakerApplicationStates.confirmation)
    
    # Показываем сводку заявки для подтверждения
    summary = (
        "📋 Ваша заявка на выступление:\n\n"
        f"🎤 <b>Тема:</b> {user_data['topic']}\n"
        f"📝 <b>Описание:</b> {user_data['description']}\n"
        f"⏱ <b>Продолжительность:</b> {duration} минут\n\n"
        "Всё верно?"
    )
    
    await message.answer(
        summary,
        reply_markup=get_application_confirmation_keyboard(),
        parse_mode="HTML"
    )

@router.message(SpeakerApplicationStates.confirmation)
async def process_confirmation(message: types.Message, state: FSMContext, user: User):
    """Обработка подтверждения заявки"""
    if message.text == "✅ Подтвердить заявку":
        user_data = await state.get_data()
        
        # Сохраняем заявку в базу
        application = await sync_to_async(SpeakerApplication.objects.create)(
            user=user,
            topic=user_data['topic'],
            description=user_data['description'],
            duration=user_data['duration'],
            status='pending'
        )
        
        await message.answer(
            "✅ Заявка успешно отправлена!\n\n"
            "Организаторы рассмотрят вашу заявку и свяжутся с вами. "
            "Следите за уведомлениями в боте.",
            reply_markup=get_main_keyboard(user.role, False)
        )
        await state.clear()
        
    elif message.text == "✏️ Исправить заявку":
        await state.set_state(SpeakerApplicationStates.waiting_for_topic)
        await message.answer(
            "Давайте начнем заново. Введите тему вашего доклада:",
            reply_markup=get_application_cancel_keyboard()
        )
    else:
        await message.answer(
            "Пожалуйста, используйте кнопки для подтверждения или редактирования заявки.",
            reply_markup=get_application_confirmation_keyboard()
        )

@router.message(lambda message: message.text and "❌ Отменить заявку" in message.text)
async def cancel_application(message: types.Message, state: FSMContext, user: User):
    """Отмена заявки"""
    await state.clear()
    await message.answer(
        "Заявка отменена.",
        reply_markup=get_main_keyboard(user.role, False)
    )

@router.message(lambda message: message.text and "📋 Мои заявки" in message.text)
async def show_my_applications(message: types.Message, user: User):
    """Показ заявок пользователя"""
    applications = await sync_to_async(list)(
        SpeakerApplication.objects.filter(user=user).order_by('-created_at')
    )
    
    if not applications:
        await message.answer(
            "У вас пока нет отправленных заявок.",
            reply_markup=get_speaker_application_main_keyboard()
        )
        return
    
    applications_text = "📋 Ваши заявки на выступление:\n\n"
    
    for i, app in enumerate(applications, 1):
        status_icons = {
            'pending': '🟡',
            'approved': '🟢', 
            'rejected': '🔴'
        }
        
        applications_text += (
            f"{i}. {status_icons.get(app.status, '⚪')} <b>{app.topic}</b>\n"
            f"   Статус: {app.get_status_display()}\n"
            f"   Подана: {app.created_at.strftime('%d.%m.%Y')}\n"
        )
        
        if app.notes:
            applications_text += f"   Заметки: {app.notes}\n"
        
        applications_text += "\n"
    
    await message.answer(
        applications_text,
        reply_markup=get_speaker_application_main_keyboard(),
        parse_mode="HTML"
    )
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async

from app_core.models import SpeakerApplication, User
from app_core.bot.keyboards.speaker import (
    get_speaker_application_main_keyboard,
    get_application_confirmation_keyboard,
    get_application_cancel_keyboard
)
from app_core.bot.keyboards.main import get_back_keyboard, get_main_keyboard
from app_core.bot.states.speaker import SpeakerApplicationStates

router = Router()

@router.message(F.text == "Заявка спикером")
async def speaker_application_main(message: types.Message, state: FSMContext):
    await message.answer(
        "🎤 Подача заявки на выступление\n\n"
        "Здесь вы можете подать заявку на выступление на следующем митапе "
        "или посмотреть статус своих предыдущих заявок.",
        reply_markup=get_speaker_application_main_keyboard()
    )

@router.message(F.text == "📝 Подать заявку")
async def start_application(message: types.Message, state: FSMContext):
    await state.set_state(SpeakerApplicationStates.waiting_for_topic)
    await message.answer(
        "📝 Шаг 1/3: Введите тему вашего доклада\n\n"
        "Пример: 'Асинхронное программирование в Python на практике'",
        reply_markup=get_application_cancel_keyboard()
    )

@router.message(SpeakerApplicationStates.waiting_for_topic, F.text == "❌ Отменить заявку")
@router.message(SpeakerApplicationStates.waiting_for_description, F.text == "❌ Отменить заявку")
@router.message(SpeakerApplicationStates.waiting_for_duration, F.text == "❌ Отменить заявку")
async def cancel_application(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Заявка отменена",
        reply_markup=get_speaker_application_main_keyboard()
    )

@router.message(SpeakerApplicationStates.waiting_for_topic)
async def process_topic(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 5:
        await message.answer("❌ Тема слишком короткая. Введите развернутую тему доклада:")
        return
    
    await state.update_data(topic=message.text.strip())
    await state.set_state(SpeakerApplicationStates.waiting_for_description)
    await message.answer(
        "📄 Шаг 2/3: Опишите содержание доклада\n\n"
        "Что узнают слушатели? Какие основные тезисы? "
        "Какие технологии/инструменты будут рассмотрены?",
        reply_markup=get_application_cancel_keyboard()
    )

@router.message(SpeakerApplicationStates.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 20:
        await message.answer("❌ Описание слишком короткое. Расскажите подробнее о докладе:")
        return
    
    await state.update_data(description=message.text.strip())
    await state.set_state(SpeakerApplicationStates.waiting_for_duration)
    await message.answer(
        "⏱ Шаг 3/3: Укажите продолжительность доклада в минутах\n\n"
        "Рекомендуется 15-45 минут",
        reply_markup=get_application_cancel_keyboard()
    )

@router.message(SpeakerApplicationStates.waiting_for_duration)
async def process_duration(message: types.Message, state: FSMContext):
    try:
        duration = int(message.text.strip())
        if duration < 5 or duration > 120:
            await message.answer("❌ Продолжительность должна быть от 5 до 120 минут:")
            return
    except ValueError:
        await message.answer("❌ Введите число (продолжительность в минутах):")
        return
    
    await state.update_data(duration=duration)
    
    data = await state.get_data()
    
    summary = (
        "📋 Проверьте вашу заявку:\n\n"
        f"🎯 <b>Тема:</b> {data['topic']}\n"
        f"📄 <b>Описание:</b> {data['description']}\n" 
        f"⏱ <b>Продолжительность:</b> {duration} мин\n\n"
        "<i>Всё верно? Отправляем заявку на рассмотрение?</i>"
    )
    
    await state.set_state(SpeakerApplicationStates.confirmation)
    await message.answer(summary, reply_markup=get_application_confirmation_keyboard(), parse_mode="HTML")

@router.message(SpeakerApplicationStates.confirmation, F.text == "✅ Подтвердить заявку")
async def confirm_application(message: types.Message, state: FSMContext):
    print("DEBUG: Хэндлер подтверждения заявки ВЫЗВАН")
    
    from django.core.exceptions import ObjectDoesNotExist
    
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
        print(f"DEBUG: User from DB: {user}")
    except ObjectDoesNotExist:
        await message.answer("❌ Ошибка: пользователь не найден в базе")
        return
    
    data = await state.get_data()
    print(f"DEBUG: Данные для сохранения: {data}")
    
    try:
        application = await sync_to_async(SpeakerApplication.objects.create)(
            user=user,
            topic=data['topic'],
            description=data['description'],
            duration=data['duration']
        )
        print(f"DEBUG: Заявка создана: {application}")
        
        await state.clear()
        
        await message.answer(
            "✅ <b>Заявка отправлена на рассмотрение!</b>\n\n"
            "Мы свяжемся с вами, когда рассмотрим вашу заявку. "
            "Обычно это занимает 1-3 дня.\n\n"
            "Следите за уведомлениями!",
            reply_markup=get_speaker_application_main_keyboard(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"DEBUG: Ошибка при создании заявки: {e}")
        await message.answer(
            "❌ <b>Ошибка при сохранении заявки!</b>\n\n"
            "Попробуйте еще раз или обратитесь к администратору.",
            reply_markup=get_speaker_application_main_keyboard(),
            parse_mode="HTML"
        )

@router.message(SpeakerApplicationStates.confirmation, F.text == "✏️ Исправить заявку")
async def edit_application(message: types.Message, state: FSMContext):
    await state.set_state(SpeakerApplicationStates.waiting_for_topic)
    await message.answer(
        "Давайте исправим заявку. Введите тему доклада:",
        reply_markup=get_application_cancel_keyboard()
    )

@router.message(SpeakerApplicationStates.confirmation, F.text == "❌ Отменить")
async def cancel_confirmation(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Заявка отменена",
        reply_markup=get_speaker_application_main_keyboard()
    )

@router.message(F.text == "📋 Мои заявки")
async def show_my_applications(message: types.Message):
    print("DEBUG: Хэндлер показа заявок ВЫЗВАН")
    
    from django.core.exceptions import ObjectDoesNotExist
    
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
        print(f"DEBUG: User from DB: {user}")
    except ObjectDoesNotExist:
        await message.answer("❌ Ошибка: пользователь не найден в базе")
        return
    
    applications = await sync_to_async(list)(
        SpeakerApplication.objects.filter(user=user).order_by('-created_at')
    )
    
    if not applications:
        await message.answer(
            "📭 У вас пока нет заявок на выступление",
            reply_markup=get_speaker_application_main_keyboard()
        )
        return
    
    text = "📋 <b>Ваши заявки на выступление:</b>\n\n"
    
    for app in applications:
        status_icons = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
        status_texts = {
            "pending": "На рассмотрении", 
            "approved": "Одобрена", 
            "rejected": "Отклонена"
        }
        
        text += (
            f"{status_icons[app.status]} <b>{app.topic}</b>\n"
            f"   ⏱ {app.duration} мин | {status_texts[app.status]}\n"
            f"   📅 {app.created_at.strftime('%d.%m.%Y')}\n\n"
        )
    
    await message.answer(text, reply_markup=get_speaker_application_main_keyboard(), parse_mode="HTML")

@router.message(F.text == "Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    
    await message.answer(
        "Возврат в главное меню",
        reply_markup=get_main_keyboard("speaker", False)
    )
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from asgiref.sync import sync_to_async
import logging
from django.db import models

from app_core.models import User, NetworkingProfile, NetworkingInteraction
from ..states.networking import NetworkingStates
from ..keyboards.main import (
    get_networking_main_keyboard, 
    get_networking_browsing_keyboard,
    get_contact_consent_keyboard,
    get_back_keyboard
)

router = Router()
logger = logging.getLogger(__name__)

@router.message(lambda message: message.text and "Знакомства" in message.text)
async def networking_main(message: types.Message, state: FSMContext):
    """Главное меню знакомств"""
    await message.answer(
        "🤝 <b>Система знакомств</b>\n\n"
        "Как это работает:\n"
        "• Заполните анкету о себе\n"
        "• Просматривайте анкеты других участников\n"
        "• При взаимном интересе - обменяйтесь контактами\n"
        "• Всё анонимно и комфортно!\n\n"
        "Выберите действие:",
        reply_markup=get_networking_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(lambda message: message.text and "📝 Заполнить анкету" in message.text)
async def start_networking_profile(message: types.Message, state: FSMContext):
    """Начало заполнения анкеты"""
    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    
    # Проверяем, есть ли уже анкета
    existing_profile = await sync_to_async(
        lambda: NetworkingProfile.objects.filter(user=user).first()
    )()
    
    if existing_profile:
        await message.answer(
            "📝 У вас уже есть анкета. Хотите её отредактировать?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="✏️ Редактировать анкету")],
                    [KeyboardButton(text="❌ Удалить анкету")],
                    [KeyboardButton(text="Назад")]
                ],
                resize_keyboard=True
            )
        )
        return
    
    await state.set_state(NetworkingStates.waiting_name)
    await message.answer(
        "📝 <b>Заполнение анкеты для знакомств</b>\n\n"
        "Шаг 1/6: <b>Как вас зовут?</b>\n"
        "Укажите имя, которое будут видеть другие участники:",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )

@router.message(lambda message: message.text and "✏️ Редактировать анкету" in message.text)
async def handle_edit_profile(message: types.Message, state: FSMContext):
    """Редактирование существующей анкеты"""
    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    
    # Получаем текущую анкету
    profile = await sync_to_async(
        lambda: NetworkingProfile.objects.filter(user=user).first()
    )()
    
    if not profile:
        await message.answer("❌ У вас еще нет анкеты для редактирования")
        return
    
    # Начинаем процесс редактирования с имени
    await state.set_state(NetworkingStates.waiting_name)
    await state.update_data(editing_profile_id=profile.id)
    
    await message.answer(
        "✏️ <b>Редактирование анкеты</b>\n\n"
        "Шаг 1/6: <b>Как вас зовут?</b>\n"
        f"Текущее значение: <i>{profile.name}</i>\n\n"
        "Введите новое имя или оставьте текущее:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=profile.name)], [KeyboardButton(text="Назад")]],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )

@router.message(lambda message: message.text and "❌ Удалить анкету" in message.text)
async def handle_delete_profile(message: types.Message, state: FSMContext):
    """Удаление анкеты"""
    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    
    profile = await sync_to_async(
        lambda: NetworkingProfile.objects.filter(user=user).first()
    )()
    
    if profile:
        # Удаляем все взаимодействия с этой анкетой
        await sync_to_async(
            NetworkingInteraction.objects.filter(
                models.Q(profile=profile) | models.Q(viewer=user)
            ).delete
        )()
        await sync_to_async(profile.delete)()
        await message.answer(
            "🗑️ <b>Анкета удалена</b>\n\n"
            "Ваша анкета больше не будет видна другим участникам.",
            reply_markup=get_networking_main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ У вас нет анкеты для удаления")

# Обработчики кнопки "Назад" во время заполнения анкеты
@router.message(NetworkingStates.waiting_name, F.text == "Назад")
@router.message(NetworkingStates.waiting_username, F.text == "Назад")
@router.message(NetworkingStates.waiting_company, F.text == "Назад")
@router.message(NetworkingStates.waiting_job_title, F.text == "Назад")
@router.message(NetworkingStates.waiting_interests, F.text == "Назад")
@router.message(NetworkingStates.waiting_contact_consent, F.text == "Назад")
async def networking_back_during_fill(message: types.Message, state: FSMContext):
    """Возврат во время заполнения анкеты"""
    await state.clear()
    await networking_main(message, state)

@router.message(NetworkingStates.waiting_name)
async def process_name(message: types.Message, state: FSMContext):
    """Обработка имени"""
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ Имя должно содержать минимум 2 символа. Попробуйте еще раз:")
        return
    
    await state.update_data(name=name)
    await state.set_state(NetworkingStates.waiting_username)
    
    await message.answer(
        "👤 Шаг 2/6: <b>Ваш username в Telegram</b>\n\n"
        "Укажите ваш @username для связи:\n"
        "• Начинается с @ (например, @ivan_ivanov)\n"
        "• Без пробелов и специальных символов\n"
        "• Можно пропустить, но тогда контакты не смогут вам написать\n\n"
        "<i>Этот username увидят только при взаимном интересе</i>",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="пропустить")],
                [KeyboardButton(text="Назад")]
            ],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )

@router.message(NetworkingStates.waiting_username)
async def process_username(message: types.Message, state: FSMContext):
    """Обработка username"""
    username = message.text.strip()
    
    if username.lower() in ["пропустить", "skip", "-", ""]:
        username = ""
    else:
        # Валидация username
        if username.startswith('@'):
            username = username[1:]  # Убираем @ если пользователь его ввел
        
        if not username.replace('_', '').replace('.', '').isalnum():
            await message.answer("❌ Username может содержать только буквы, цифры, точку и нижнее подчеркивание. Попробуйте еще раз:")
            return
        
        if len(username) < 5:
            await message.answer("❌ Username должен содержать минимум 5 символов. Попробуйте еще раз:")
            return
    
    await state.update_data(username=username)
    await state.set_state(NetworkingStates.waiting_company)
    
    await message.answer(
        "🏢 Шаг 3/6: <b>В какой компании вы работаете?</b>\n\n"
        "Можно:\n"
        "• Указать компанию\n" 
        "• Написать 'пропустить' чтобы пропустить\n"
        "• Написать 'не указано'\n\n"
        "<i>Эта информация поможет найти коллег из вашей индустрии</i>",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="пропустить")],
                [KeyboardButton(text="Назад")]
            ],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )

@router.message(NetworkingStates.waiting_company)
async def process_company(message: types.Message, state: FSMContext):
    """Обработка компании с возможностью пропуска"""
    company = message.text.strip()
    
    if company.lower() in ["пропустить", "skip", "-", ""]:
        company = ""
    
    await state.update_data(company=company)
    await state.set_state(NetworkingStates.waiting_job_title)
    
    await message.answer(
        "💼 Шаг 4/6: <b>Ваша должность?</b>\n\n"
        "Можно:\n"
        "• Указать должность\n"
        "• Написать 'пропустить' чтобы пропустить\n"
        "• Написать 'не указано'\n\n"
        "<i>Расскажите о вашей роли в компании</i>",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="пропустить")],
                [KeyboardButton(text="Назад")]
            ],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )

@router.message(NetworkingStates.waiting_job_title)
async def process_job_title(message: types.Message, state: FSMContext):
    """Обработка должности с возможностью пропуска"""
    job_title = message.text.strip()
    
    if job_title.lower() in ["пропустить", "skip", "-", ""]:
        job_title = ""
    
    await state.update_data(job_title=job_title)
    await state.set_state(NetworkingStates.waiting_interests)
    
    await message.answer(
        "🎯 Шаг 5/6: <b>Ваши интересы и темы для общения</b>\n\n"
        "Пример:\n"
        "• Python, Django, FastAPI\n"
        "• Machine Learning, Data Science\n"
        "• Карьера в IT, менторство\n"
        "• Стартапы, предпринимательство\n\n"
        "<i>Опишите, о чем вам интересно говорить с коллегами</i>",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )

@router.message(NetworkingStates.waiting_interests)
async def process_interests(message: types.Message, state: FSMContext):
    """Обработка интересов"""
    if len(message.text.strip()) < 10:
        await message.answer("❌ Пожалуйста, опишите интересы подробнее (минимум 10 символов):")
        return
    
    await state.update_data(interests=message.text.strip())
    await state.set_state(NetworkingStates.waiting_contact_consent)
    
    # Проверяем, есть ли username
    data = await state.get_data()
    has_username = bool(data.get('username'))
    
    if has_username:
        contact_text = (
            "📞 Шаг 6/6: <b>Согласие на обмен контактами</b>\n\n"
            "При взаимном интересе с другим участником, "
            f"вы сможете обменяться контактами.\n\n"
            f"<b>Разрешаете показывать ваш username (@{data['username']}) другим участникам при взаимном интересе?</b>\n\n"
            "<i>Вы всегда сможете изменить это позже в настройках анкеты</i>"
        )
    else:
        contact_text = (
            "📞 Шаг 6/6: <b>Согласие на обмен контактами</b>\n\n"
            "Вы не указали username, поэтому другие участники не смогут вам написать.\n\n"
            "<b>Хотите разрешить показывать контакты?</b>\n\n"
            "<i>Рекомендуем указать username, чтобы другие могли с вами связаться</i>"
        )
    
    await message.answer(
        contact_text,
        reply_markup=get_contact_consent_keyboard(),
        parse_mode="HTML"
    )

@router.message(NetworkingStates.waiting_contact_consent)
async def process_contact_consent(message: types.Message, state: FSMContext):
    """Обработка согласия на контакт"""
    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    
    if message.text == "✅ Да, делиться контактом":
        contact_consent = True
        consent_text = "✅ Вы согласились делиться контактом"
    elif message.text == "❌ Нет":
        contact_consent = False
        consent_text = "❌ Вы отказались делиться контактом"
    else:
        await message.answer("❌ Пожалуйста, используйте кнопки для выбора:")
        return
    
    data = await state.get_data()
    editing_profile_id = data.get('editing_profile_id')
    
    if editing_profile_id:
        # Редактирование существующей анкеты
        profile = await sync_to_async(NetworkingProfile.objects.get)(id=editing_profile_id)
        profile.name = data['name']
        profile.username = data.get('username', '')
        profile.company = data.get('company', '')
        profile.job_title = data.get('job_title', '')
        profile.interests = data['interests']
        profile.contact_consent = contact_consent
        await sync_to_async(profile.save)()
        
        success_message = "✅ <b>Анкета обновлена!</b>"
    else:
        # Создание новой анкеты
        profile = await sync_to_async(NetworkingProfile.objects.create)(
            user=user,
            name=data['name'],
            username=data.get('username', ''),
            company=data.get('company', ''),
            job_title=data.get('job_title', ''),
            interests=data['interests'],
            contact_consent=contact_consent
        )
        success_message = "🎉 <b>Анкета создана!</b>"
    
    await state.clear()
    
    # Формируем сводку анкеты
    summary = (
        f"{success_message}\n\n"
        f"<b>Имя:</b> {data['name']}\n"
    )
    
    if data.get('username'):
        summary += f"<b>Username:</b> @{data['username']}\n"
    if data.get('company'):
        summary += f"<b>Компания:</b> {data['company']}\n"
    if data.get('job_title'):
        summary += f"<b>Должность:</b> {data['job_title']}\n"
    
    summary += (
        f"<b>Интересы:</b> {data['interests']}\n"
        f"<b>Контакты:</b> {consent_text}\n\n"
    )
    
    if not data.get('username') and contact_consent:
        summary += "⚠️ <i>Вы не указали username, другие участники не смогут вам написать</i>\n\n"
    
    summary += "Теперь вы можете искать собеседников!"
    
    await message.answer(
        summary,
        reply_markup=get_networking_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(lambda message: message.text and "👀 Найти собеседников" in message.text)
async def start_browsing_profiles(message: types.Message, state: FSMContext):
    """Начало просмотра анкет"""
    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    
    # Проверяем, есть ли анкета у пользователя
    user_profile = await sync_to_async(
        lambda: NetworkingProfile.objects.filter(user=user, is_visible=True).first()
    )()
    
    if not user_profile:
        await message.answer(
            "❌ Сначала заполните свою анкету для участия в знакомствах!",
            reply_markup=get_networking_main_keyboard()
        )
        return
    
    # Ищем анкеты для показа
    shown_profiles = await sync_to_async(list)(
        NetworkingInteraction.objects.filter(viewer=user).values_list('profile_id', flat=True)
    )
    
    available_profiles = await sync_to_async(list)(
        NetworkingProfile.objects.filter(
            is_visible=True
        ).exclude(
            user=user
        ).exclude(
            id__in=shown_profiles
        ).order_by('?')[:10]  # Случайные 10 анкет
    )
    
    if not available_profiles:
        await message.answer(
            "👀 <b>Пока нет новых анкет для просмотра</b>\n\n"
            "Все доступные анкеты уже просмотрены. "
            "Попробуйте позже или обновите поиск.",
            reply_markup=get_networking_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    await state.set_state(NetworkingStates.browsing_profiles)
    await state.update_data(
        available_profiles=[p.id for p in available_profiles],
        current_index=0
    )
    
    await show_next_profile(message, state)

async def show_next_profile(message: types.Message, state: FSMContext):
    """Показать следующую анкету"""
    data = await state.get_data()
    available_profiles = data.get('available_profiles', [])
    current_index = data.get('current_index', 0)
    
    if current_index >= len(available_profiles):
        await message.answer(
            "🎉 <b>Вы просмотрели все доступные анкеты!</b>\n\n"
            "Возвращайтесь позже, чтобы увидеть новые анкеты.",
            reply_markup=get_networking_main_keyboard(),
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    profile_id = available_profiles[current_index]
    profile = await sync_to_async(NetworkingProfile.objects.select_related('user').get)(id=profile_id)
    
    # Сохраняем просмотр
    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    await sync_to_async(NetworkingInteraction.objects.get_or_create)(
        viewer=user,
        profile=profile,
        defaults={'status': 'viewed'}
    )
    
    # Формируем текст анкеты
    profile_text = (
        f"👤 <b>{profile.name}</b>\n\n"
    )
    
    if profile.company:
        profile_text += f"🏢 <b>Компания:</b> {profile.company}\n"
    if profile.job_title:
        profile_text += f"💼 <b>Должность:</b> {profile.job_title}\n"
    
    profile_text += (
        f"🎯 <b>Интересы:</b>\n{profile.interests}\n\n"
        f"📊 Анкета {current_index + 1} из {len(available_profiles)}"
    )
    
    await message.answer(
        profile_text,
        reply_markup=get_networking_browsing_keyboard(),
        parse_mode="HTML"
    )

@router.message(NetworkingStates.browsing_profiles, F.text == "✅ Знакомиться!")
async def like_profile(message: types.Message, state: FSMContext, bot: Bot):
    """Лайк анкеты с уведомлением обоих пользователей"""
    data = await state.get_data()
    available_profiles = data.get('available_profiles', [])
    current_index = data.get('current_index', 0)
    
    if current_index >= len(available_profiles):
        await message.answer("❌ Больше нет анкет для просмотра")
        return
    
    profile_id = available_profiles[current_index]
    profile = await sync_to_async(NetworkingProfile.objects.select_related('user').get)(id=profile_id)
    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    
    # Обновляем статус на "понравилось"
    interaction, created = await sync_to_async(NetworkingInteraction.objects.get_or_create)(
        viewer=user,
        profile=profile,
        defaults={'status': 'liked'}
    )
    
    if not created:
        interaction.status = 'liked'
        await sync_to_async(interaction.save)()
    
    # Проверяем взаимный интерес
    mutual_like = await sync_to_async(
        NetworkingInteraction.objects.filter(
            viewer=profile.user,
            profile__user=user,
            status='liked'
        ).exists
    )()
    
    if mutual_like:
        # Взаимный интерес - уведомляем обоих пользователей
        user_profile = await sync_to_async(
            NetworkingProfile.objects.get
        )(user=user)
        
        # Уведомление текущему пользователю
        if profile.contact_consent and profile.username:
            contact_info = f"@{profile.username}"
            await message.answer(
                f"🎉 <b>Взаимный интерес!</b>\n\n"
                f"Вы понравились {profile.name} и они тоже хотят познакомиться!\n\n"
                f"👤 <b>Контакт:</b> {contact_info}\n"
                f"💬 <b>Напишите первым</b> и начните общение!",
                reply_markup=get_networking_browsing_keyboard(),
                parse_mode="HTML"
            )
        elif profile.contact_consent and not profile.username:
            await message.answer(
                f"🎉 <b>Взаимный интерес!</b>\n\n"
                f"Вы понравились {profile.name}, но они не указали username.\n"
                f"Возможно, они сами напишут вам!",
                reply_markup=get_networking_browsing_keyboard(),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"🎉 <b>Взаимный интерес!</b>\n\n"
                f"Вы понравились {profile.name}, но они не разрешили показывать контакт.\n"
                f"Возможно, они сами напишут вам!",
                reply_markup=get_networking_browsing_keyboard(),
                parse_mode="HTML"
            )
        
        # Уведомление другому пользователю
        if user_profile.contact_consent and user_profile.username:
            user_contact_info = f"@{user_profile.username}"
            try:
                await bot.send_message(
                    chat_id=profile.user.telegram_id,
                    text=f"🎉 <b>Взаимный интерес!</b>\n\n"
                         f"Вы понравились {user_profile.name} и они тоже хотят познакомиться!\n\n"
                         f"👤 <b>Контакт:</b> {user_contact_info}\n"
                         f"💬 <b>Напишите первым</b> и начните общение!",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление пользователю {profile.user.telegram_id}: {e}")
        elif user_profile.contact_consent and not user_profile.username:
            try:
                await bot.send_message(
                    chat_id=profile.user.telegram_id,
                    text=f"🎉 <b>Взаимный интерес!</b>\n\n"
                         f"Вы понравились {user_profile.name}, но они не указали username.\n"
                         f"Возможно, они сами напишут вам!",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление пользователю {profile.user.telegram_id}: {e}")
        else:
            try:
                await bot.send_message(
                    chat_id=profile.user.telegram_id,
                    text=f"🎉 <b>Взаимный интерес!</b>\n\n"
                         f"Вы понравились {user_profile.name}, но они не разрешили показывать контакт.\n"
                         f"Возможно, они сами напишут вам!",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление пользователю {profile.user.telegram_id}: {e}")
        
        # Обновляем статус на "matched" для обоих взаимодействий
        await sync_to_async(NetworkingInteraction.objects.filter(
            viewer=profile.user,
            profile__user=user,
            status='liked'
        ).update)(status='matched')
        
        interaction.status = 'matched'
        await sync_to_async(interaction.save)()
        
    else:
        await message.answer(
            "✅ <b>Вы выразили интерес!</b>\n\n"
            "Если этот участник тоже захочет с вами познакомиться, "
            "вы получите уведомление и сможете обменяться контактами.",
            reply_markup=get_networking_browsing_keyboard(),
            parse_mode="HTML"
        )
    
    # Показываем следующую анкету
    await state.update_data(current_index=current_index + 1)
    await show_next_profile(message, state)

@router.message(NetworkingStates.browsing_profiles, F.text == "➡️ Следующий")
async def skip_profile(message: types.Message, state: FSMContext):
    """Пропустить анкету"""
    data = await state.get_data()
    current_index = data.get('current_index', 0)
    
    await state.update_data(current_index=current_index + 1)
    await show_next_profile(message, state)

@router.message(NetworkingStates.browsing_profiles, F.text == "🏠 В главное меню")
async def back_to_main_from_browsing(message: types.Message, state: FSMContext):
    """Возврат в главное меню знакомств из просмотра"""
    await state.clear()
    await networking_main(message, state)

@router.message(NetworkingStates.browsing_profiles, F.text == "📊 Моя анкета")
async def show_my_profile_from_browsing(message: types.Message, state: FSMContext):
    """Показать свою анкету во время просмотра"""
    await show_my_profile(message)
    # Сохраняем состояние просмотра
    data = await state.get_data()
    await state.set_state(NetworkingStates.browsing_profiles)
    await state.update_data(data)

@router.message(lambda message: message.text and "📊 Моя анкета" in message.text)
async def show_my_profile(message: types.Message):
    """Показать свою анкету"""
    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    
    profile = await sync_to_async(
        lambda: NetworkingProfile.objects.filter(user=user).first()
    )()
    
    if not profile:
        await message.answer(
            "❌ У вас еще нет анкеты для знакомств",
            reply_markup=get_networking_main_keyboard()
        )
        return
    
    # Получаем статистику
    likes_received = await sync_to_async(
        NetworkingInteraction.objects.filter(
            profile=profile, 
            status='liked'
        ).count
    )()
    
    profiles_viewed = await sync_to_async(
        NetworkingInteraction.objects.filter(viewer=user).count
    )()
    
    mutual_matches = await sync_to_async(
        NetworkingInteraction.objects.filter(
            viewer=user,
            status='matched'
        ).count
    )()
    
    profile_text = (
        "📊 <b>Ваша анкета для знакомств</b>\n\n"
        f"<b>Имя:</b> {profile.name}\n"
    )
    
    if profile.username:
        profile_text += f"<b>Username:</b> @{profile.username}\n"
    if profile.company:
        profile_text += f"<b>Компания:</b> {profile.company}\n"
    if profile.job_title:
        profile_text += f"<b>Должность:</b> {profile.job_title}\n"
    
    profile_text += (
        f"<b>Интересы:</b>\n{profile.interests}\n\n"
        f"<b>Настройки:</b>\n"
        f"• Видимость: {'✅ Видна другим' if profile.is_visible else '❌ Скрыта от других'}\n"
        f"• Контакты: {'✅ Разрешаю показывать' if profile.contact_consent else '❌ Не разрешаю показывать'}\n\n"
        f"<b>Статистика:</b>\n"
        f"• Получено лайков: {likes_received}\n"
        f"• Просмотрено анкет: {profiles_viewed}\n"
        f"• Взаимные мэтчи: {mutual_matches}\n\n"
    )
    
    if not profile.username and profile.contact_consent:
        profile_text += "⚠️ <i>Вы не указали username, другие участники не смогут вам написать</i>\n\n"
    
    if likes_received > 0:
        profile_text += "💖 У вас есть новые лайки! Посмотрите в '👀 Кто вас лайкнул'"
    
    await message.answer(
        profile_text,
        reply_markup=get_networking_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(lambda message: message.text and "👀 Кто вас лайкнул" in message.text)
async def show_likes_received(message: types.Message):
    """Показать пользователей, которые лайкнули анкету"""
    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    
    profile = await sync_to_async(
        lambda: NetworkingProfile.objects.filter(user=user).first()
    )()
    
    if not profile:
        await message.answer(
            "❌ У вас еще нет анкеты для просмотра лайков",
            reply_markup=get_networking_main_keyboard()
        )
        return
    
    # Получаем лайки к нашей анкете
    likes = await sync_to_async(list)(
        NetworkingInteraction.objects.filter(
            profile=profile,
            status='liked'
        ).select_related('viewer', 'viewer__networking_profile')
        .order_by('-created_at')
    )
    
    if not likes:
        await message.answer(
            "💔 <b>Пока нет лайков</b>\n\n"
            "Вашу анкету еще никто не лайкнул.\n"
            "Продолжайте участвовать в знакомствах!",
            reply_markup=get_networking_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    likes_text = f"💖 <b>Вас лайкнули ({len(likes)}):</b>\n\n"
    
    for i, like in enumerate(likes, 1):
        viewer_profile = like.viewer.networking_profile
        likes_text += f"{i}. <b>{viewer_profile.name}</b>\n"
        
        if viewer_profile.company:
            likes_text += f"   🏢 {viewer_profile.company}\n"
        if viewer_profile.job_title:
            likes_text += f"   💼 {viewer_profile.job_title}\n"
        
        likes_text += f"   🎯 {viewer_profile.interests[:50]}...\n\n"
    
    likes_text += "💡 <i>Лайкните их анкету в ответ, чтобы обменяться контактами!</i>"
    
    await message.answer(
        likes_text,
        reply_markup=get_networking_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(lambda message: message.text and "🤝 Ваши мэтчи" in message.text)
async def show_mutual_matches(message: types.Message):
    """Показать взаимные мэтчи"""
    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    
    # Находим взаимные мэтчи
    mutual_matches = await sync_to_async(list)(
        NetworkingInteraction.objects.filter(
            viewer=user,
            status='matched'
        ).select_related('profile')
        .order_by('-created_at')
    )
    
    if not mutual_matches:
        await message.answer(
            "🤝 <b>Пока нет взаимных мэтчей</b>\n\n"
            "Когда вы и другой участник лайкнете анкеты друг друга, "
            "здесь появятся контакты для общения!",
            reply_markup=get_networking_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    matches_text = f"🤝 <b>Ваши взаимные мэтчи ({len(mutual_matches)}):</b>\n\n"
    
    for i, match in enumerate(mutual_matches, 1):
        profile = match.profile
        
        if profile.username and profile.contact_consent:
            contact_info = f"@{profile.username}"
            contact_line = f"   👤 <b>Контакт:</b> {contact_info}\n"
        elif profile.contact_consent and not profile.username:
            contact_line = "   👤 <b>Контакт:</b> не указан ❌\n"
        else:
            contact_line = "   👤 <b>Контакт:</b> скрыт 🔒\n"
        
        matches_text += f"{i}. <b>{profile.name}</b>\n"
        matches_text += contact_line
        
        if profile.company:
            matches_text += f"   🏢 {profile.company}\n"
        if profile.job_title:
            matches_text += f"   💼 {profile.job_title}\n"
        
        matches_text += f"   🎯 {profile.interests[:50]}...\n\n"
    
    matches_text += "💬 <i>Не стесняйтесь писать первыми!</i>"
    
    await message.answer(
        matches_text,
        reply_markup=get_networking_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(lambda message: message.text and "👁️ Управление видимостью" in message.text)
async def manage_visibility(message: types.Message):
    """Управление видимостью анкеты"""
    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    
    profile = await sync_to_async(
        lambda: NetworkingProfile.objects.filter(user=user).first()
    )()
    
    if not profile:
        await message.answer(
            "❌ У вас еще нет анкеты для управления видимостью",
            reply_markup=get_networking_main_keyboard()
        )
        return
    
    # Получаем статистику лайков
    likes_count = await sync_to_async(
        NetworkingInteraction.objects.filter(
            profile=profile, 
            status='liked'
        ).count
    )()
    
    visibility_status = "✅ Видна другим" if profile.is_visible else "❌ Скрыта от других"
    contact_status = "✅ Разрешаю показывать" if profile.contact_consent else "❌ Не разрешаю показывать"
    
    await message.answer(
        "👁️ <b>Управление видимостью анкеты</b>\n\n"
        f"<b>Текущий статус:</b>\n"
        f"• Видимость: {visibility_status}\n"
        f"• Контакты: {contact_status}\n"
        f"• Новых лайков: {likes_count}\n\n"
        "Выберите действие:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👁️ Скрыть анкету" if profile.is_visible else "👁️ Показать анкету")],
                [KeyboardButton(text="📞 Разрешить контакты" if not profile.contact_consent else "📞 Запретить контакты")],
                [KeyboardButton(text="👀 Кто вас лайкнул"), KeyboardButton(text="🤝 Ваши мэтчи")],
                [KeyboardButton(text="✏️ Редактировать анкету")],
                [KeyboardButton(text="Назад")]
            ],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )

@router.message(lambda message: message.text in ["👁️ Скрыть анкету", "👁️ Показать анкету"])
async def toggle_visibility(message: types.Message):
    """Переключение видимости анкеты"""
    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    
    profile = await sync_to_async(
        lambda: NetworkingProfile.objects.filter(user=user).first()
    )()
    
    if not profile:
        await message.answer("❌ У вас нет анкеты")
        return
    
    profile.is_visible = not profile.is_visible
    await sync_to_async(profile.save)()
    
    status = "скрыта" if not profile.is_visible else "видна"
    await message.answer(
        f"✅ <b>Анкета теперь {status} для других участников</b>",
        reply_markup=get_networking_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(lambda message: message.text in ["📞 Разрешить контакты", "📞 Запретить контакты"])
async def toggle_contact_consent(message: types.Message):
    """Переключение согласия на контакты"""
    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    
    profile = await sync_to_async(
        lambda: NetworkingProfile.objects.filter(user=user).first()
    )()
    
    if not profile:
        await message.answer("❌ У вас нет анкеты")
        return
    
    profile.contact_consent = not profile.contact_consent
    await sync_to_async(profile.save)()
    
    status = "разрешены" if profile.contact_consent else "запрещены"
    await message.answer(
        f"✅ <b>Контакты теперь {status}</b>\n\n"
        f"{'✅ При взаимном интересе другие участники увидят ваш username' if profile.contact_consent else '❌ Ваш контакт не будет показываться другим участникам'}",
        reply_markup=get_networking_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(lambda message: message.text and "🔄 Обновить поиск" in message.text)
async def refresh_search(message: types.Message, state: FSMContext):
    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    
    await sync_to_async(
        NetworkingInteraction.objects.filter(viewer=user).delete
    )()
    
    await message.answer(
        "🔄 <b>Поиск обновлен!</b>\n\n"
        "Теперь вы снова можете просматривать все доступные анкеты.",
        reply_markup=get_networking_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "Назад")
async def networking_back(message: types.Message, state: FSMContext):
    """Возврат в главное меню знакомств"""
    await state.clear()
    await networking_main(message, state)
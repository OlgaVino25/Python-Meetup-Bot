from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
from ..keyboards.main import get_back_keyboard
from ...models import Talk, Question, User

router = Router()


class QuestionState(StatesGroup):
    waiting_for_username = State()
    waiting_for_question = State()


@router.message(lambda message: message.text and "Вопрос" in message.text)
async def ask_question(message: types.Message, state: FSMContext):
    current_talk = await sync_to_async(Talk.objects.filter(is_active=True).first)()

    if not current_talk:
        await message.answer(
            "❌ Сейчас нет активного доклада для вопросов",
            reply_markup=get_back_keyboard(),
        )
        return

    user = await sync_to_async(User.objects.get)(telegram_id=str(message.from_user.id))
    
    if user.username:
        await state.set_state(QuestionState.waiting_for_question)
        await state.update_data(talk_id=current_talk.id)
        await message.answer(
            "✍️ Введите ваш вопрос для текущего спикера:\n\n"
            "Вопрос будет передан спикеру.\n"
            "Он сможет ответить на него после выступления.",
            reply_markup=get_back_keyboard(),
        )
    else:
        await state.set_state(QuestionState.waiting_for_username)
        await state.update_data(talk_id=current_talk.id)
        await message.answer(
            "👤 <b>Укажите ваш username (логин в Telegram)</b>\n\n"
            "Это нужно, чтобы спикер мог упомянуть вас при ответе.\n"
            "Формат: @username или просто username\n\n"
            "Примеры:\n"
            "• @ivanov\n"
            "• ivanov\n"
            "• mynickname",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )


@router.message(QuestionState.waiting_for_username)
async def process_username(message: types.Message, state: FSMContext):
    username = message.text.strip()
    
    if username.startswith('@'):
        username = username[1:]
    
    if not username or len(username) < 3:
        await message.answer(
            "❌ Username должен содержать не менее 3 символов.\n"
            "Пожалуйста, введите ваш username еще раз:"
        )
        return
    
    await state.update_data(username=username)
    await state.set_state(QuestionState.waiting_for_question)
    
    await message.answer(
        f"✅ Username сохранен: @{username}\n\n"
        "✍️ Теперь введите ваш вопрос для текущего спикера:\n\n"
        "Вопрос будет передан спикеру.\n"
        "Он сможет ответить на него после выступления.",
        reply_markup=get_back_keyboard(),
    )


@router.message(QuestionState.waiting_for_question)
async def process_question(message: types.Message, state: FSMContext):
    question_text = message.text
    user_data = await state.get_data()
    talk_id = user_data.get("talk_id")
    username = user_data.get("username")

    try:
        talk = await sync_to_async(Talk.objects.get)(id=talk_id)
        user = await sync_to_async(User.objects.get)(
            telegram_id=str(message.from_user.id)
        )
        
        if username and user.username != username:
            user.username = username
            await sync_to_async(user.save)()

        await sync_to_async(Question.objects.create)(
            talk=talk, from_user=user, text=question_text, is_answered=False
        )

        await message.answer(
            "✅ Ваш вопрос отправлен спикеру!\n\n"
            "Спикер получит его после выступления и сможет ответить.\n"
            "Спасибо за активное участие!",
            reply_markup=get_back_keyboard(),
        )
    except Talk.DoesNotExist:
        await message.answer(
            "❌ Ошибка: активный доклад не найден",
            reply_markup=get_back_keyboard(),
        )
    except User.DoesNotExist:
        await message.answer(
            "❌ Ошибка: пользователь не найден",
            reply_markup=get_back_keyboard(),
        )
    finally:
        await state.clear()
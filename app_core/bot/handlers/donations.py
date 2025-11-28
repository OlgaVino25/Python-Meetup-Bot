from aiogram import Router, types, F
from aiogram.types import (
    LabeledPrice,
    PreCheckoutQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from django.conf import settings
from asgiref.sync import sync_to_async
from django.utils import timezone
from decimal import Decimal
from app_core.models import Event, User, Donation
from ..keyboards.main import get_back_keyboard, get_guest_keyboard, get_donation_keyboard

router = Router()

class DonationAmount(StatesGroup):
    waiting_for_amount = State()


@sync_to_async
def _get_active_event():
    now = timezone.now()
    return (
        Event.objects.filter(start_date__lte=now, end_date__gte=now)
        .order_by("start_date")
        .first()
    )


@sync_to_async
def _get_relevant_event():
    now = timezone.now()
    # 1) Активное
    active = (
        Event.objects.filter(start_date__lte=now, end_date__gte=now)
        .order_by("start_date")
        .first()
    )
    if active:
        return active

    # 2) Последнее прошедшее
    last_past = (
        Event.objects.filter(end_date__lt=now)
        .order_by("-end_date")
        .first()
    )
    if last_past:
        return last_past

    # 3) Ближайшее будущее
    next_future = (
        Event.objects.filter(start_date__gt=now)
        .order_by("start_date")
        .first()
    )
    return next_future


@sync_to_async
def _ensure_user(tg_id: str, username: str | None, first_name: str | None):
    user, _ = User.objects.get_or_create(
        telegram_id=tg_id,
        defaults={
            "first_name": first_name or "",
            "username": username or "",
        },
    )
    return user


@sync_to_async
def _create_donation(event: Event, user: User, amount: Decimal):
    return Donation.objects.create(event=event, from_user=user, amount=amount)


@router.message(lambda message: message.text and "Донат" in message.text)
async def show_donations(message: types.Message):
    await message.answer(
        "Выберите сумму доната или укажите другую:",
        reply_markup=get_donation_keyboard(),
    )

async def send_invoice(message: types.Message, amount_rub: int):
    invoice_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить", pay=True)],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="donation_back")],
        ]
    )

    await message.answer_invoice(
        title="Поддержку проекта",
        description="Спасибо за интерес к мероприятию! Вы можете поддержать нас 💙",
        payload=f"donation|fixed|{amount_rub}",
        provider_token=settings.TELEGRAM_PAYMENTS_PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label=f"Донат {amount_rub}₽", amount=amount_rub * 100)],
        start_parameter="donate",
        need_name=False,
        need_email=False,
        is_flexible=False,
        reply_markup=invoice_kb,
    )


@router.message(F.text.in_({"100 руб", "300 руб", "500 руб"}))
async def donate_fixed_amount(message: types.Message):
    text = message.text.strip()
    amount = int(text.split()[0])  # "100 руб" -> 100
    await send_invoice(message, amount)


@router.message(F.text == "Другая")
async def donate_other_amount(message: types.Message, state: FSMContext):
    await state.set_state(DonationAmount.waiting_for_amount)
    await message.answer(
        "Введите сумму в рублях (например, 150 или 199.99).",
        reply_markup=get_back_keyboard(),
    )


@router.message(DonationAmount.waiting_for_amount, F.text == "Назад")
async def cancel_other_amount(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=get_guest_keyboard())


@router.message(DonationAmount.waiting_for_amount)
async def process_other_amount(message: types.Message, state: FSMContext):
    raw = (message.text or "").strip().replace(",", ".")
    try:
        from decimal import Decimal, ROUND_DOWN

        amount_dec = Decimal(raw)
        if amount_dec <= 0:
            raise ValueError
        amount_dec = amount_dec.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        amount_int = int(amount_dec * 100)
        if amount_int < 100:
            await message.answer("Минимальная сумма — 1 ₽. Попробуйте снова или нажмите Назад.")
            return
    except Exception:
        await message.answer("Некорректная сумма. Введите число, например 150 или 199.99.")
        return

    await state.clear()
    await message.answer_invoice(
        title="Поддержку проекта",
        description="Спасибо за интерес к мероприятию! Вы можете поддержать нас 💙",
        payload=f"donation|custom|{amount_int}",
        provider_token=settings.TELEGRAM_PAYMENTS_PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Донат", amount=amount_int)],
        start_parameter="donate",
        need_name=False,
        need_email=False,
        is_flexible=False,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Оплатить", pay=True)],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="donation_back")],
            ]
        ),
    )


@router.callback_query(F.data == "donation_back")
async def donation_back_callback(callback: types.CallbackQuery):
    """Возврат из окна оплаты к выбору пресетов суммы.
    Удаляем сообщение с инвойсом и показываем клавиатуру донатов.
    """
    try:
        await callback.message.delete()
    except Exception:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

    await callback.answer("Возвращаемся назад")
    # Показываем заново выбор сумм
    await callback.message.answer(
        "Выберите сумму доната или укажите другую:",
        reply_markup=get_donation_keyboard(),
    )


@router.pre_checkout_query()
async def pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    amount_rub = Decimal(message.successful_payment.total_amount) / Decimal(100)

    event = await _get_relevant_event()
    tg = message.from_user
    user = await _ensure_user(str(tg.id), tg.username, tg.first_name)
    await _create_donation(event, user, amount_rub)
    return
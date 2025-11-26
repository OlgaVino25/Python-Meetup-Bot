import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart


async def start_bot(token: str):
    bot = Bot(token=token)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def on_start(message: types.Message):
        await message.answer(
            "Привет! Я бот Python Meetup."
        )

    @dp.message()
    async def echo(message: types.Message):
        # Простое эхо для проверки
        await message.answer(message.text)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


def run(token: str):
    """Синхронная обёртка для удобного вызова из команд."""
    asyncio.run(start_bot(token))

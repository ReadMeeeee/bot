import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from config import API_TG
from Chat.commands import *
from Chat.handler import handle_message
from database.models import Base, engine


# Инициализация бота и диспетчера
bot = Bot(token=API_TG)
dp = Dispatcher()

dp.message.register(send_welcome, Command("start"))
dp.message.register(send_help, Command("help"))
dp.message.register(send_about, Command("about"))
dp.message.register(create_group, Command("create_group"))
dp.message.register(add_stud, Command("add_student"))
dp.message.register(handle_message)

async def init_db():
    """Инициализация базы данных, если она еще не создана."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("База данных и таблицы созданы или уже существуют")

async def run_bot():
    # Снести после релиза!
    # =====================================
    logging.basicConfig(level=logging.INFO)
    logging.info("Бот запущен!")
    # =====================================
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(init_db())
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print('\nExited')
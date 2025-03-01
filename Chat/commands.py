from Chat.config import types
from Chat.keyboard import keyboard


async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот-ассистент старосты.", reply_markup=keyboard)

async def send_help(message: types.Message):
    await message.reply("Список доступных команд:\n"
                        "/start - Начало работы\n"
                        "/help - Помощь\n"
                        "/about - О боте\n"
                        "/create_group - Создать группу\n"
                        "/add_student - Добавить студента")

async def send_about(message: types.Message):
    await message.reply("Этот бот отвечает на твои вопросы, используя ИИ.")
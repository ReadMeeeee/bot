from Chat.config import types
from Chat.keyboard import keyboard
from database.requests import add_group, add_student, update_leader, delete_student


async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот-ассистент старосты.", reply_markup=keyboard)

async def send_help(message: types.Message): # Когда буду расписывать /help - подтянуть клавиатуру
    await message.reply("Список доступных команд:\n"
                        "/start - Начало работы\n"
                        "/help - Помощь\n"
                        "/about - О боте\n"
                        "/create_group - Создать группу\n"
                        "/add_student - Добавить студента")

async def send_about(message: types.Message):
    await message.reply("Этот бот отвечает на твои вопросы, используя ИИ.")


async def create_group(message: types.Message):
    params = message.text.split()[1:]  # /create_group ПМИ4 1 https://t.me/group_link
    if len(params) != 3:
        await message.reply("Неверный формат.\n"
                            "Пример: /create_group <название с курсом> <номер> <ссылка на группу>")
        return

    name, number, link = params
    number = int(number)

    await add_group(tg_id=message.chat.id, name=name, number=number, link=link)
    await message.reply(f"Группа {name}-{number} добавлена!")

async def add_stud(message: types.Message):
    params = message.text.split()[1:]  # /add @student Иванов_Иван 0 Бакалавриат_4 1
    if len(params) != 5:
        await message.reply("Неверный формат.\n"
                            "Пример: /add_student <@username> <Фамилия_Имя> <староста 0/1> <курс> <ID группы>")
        return

    username, full_name, is_leader, course, group_id = params
    if username[0] != '@':
        await message.reply("Неверный формат: @username")
        return

    is_leader = bool(int(is_leader))
    group_id = int(group_id)

    await add_student(tg_id=message.chat.id, username=username, full_name=full_name,
                      is_leader=is_leader, course=course, group_id=group_id)
    await message.reply(f"Студент {full_name} добавлен в группу {group_id}!")

async def remove_stud(message: types.Message):
    params = message.text.split()[1:]
    if len(params) != 1 or params[0][0] != '@':
        await message.reply("Неверный формат.\n"
                            "Пример: /remove_student <@username>")
        return
    username = params[0]
    await delete_student(username)
    await message.reply(f"Студент {username} удален из группы!")

async def change_leader(message: types.Message):
    params = message.text.split()[1:]
    if len(params) != 1 or params[0][0] != '@':
        await message.reply("Неверный формат.\n"
                            "Пример: /change_leader <@username>")
        return
    username = params[0]
    await update_leader(username)
    await message.reply(f"Студент {username} назначен старостой!")
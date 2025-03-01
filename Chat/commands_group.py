from Chat.config import types
from database.requests import add_group, add_student, update_leader, delete_student, get_group_by_tg_id


def is_group_chat(message: types.Message) -> bool:
    return message.chat.type in ("group", "supergroup")

async def create_group(message: types.Message):
    """
    Ожидаемый формат:
    /create_group <название группы> <курс> <номер> <ссылка на группу>
    Пример: /create_group ПМИ4 1 101 https://t.me/group_link
    """
    if not is_group_chat(message):
        await message.reply("Эта команда доступна только в групповых чатах.")
        return

    params = message.text.split()[1:]
    if len(params) != 4:
        await message.reply("Неверный формат.\n"
                            "Пример: /create_group <название группы> <курс> <номер> <ссылка на группу>")
        return

    name, course, number, link = params
    try:
        course = int(course)
        number = int(number)
    except ValueError:
        await message.reply("Курс и номер группы должны быть числовыми значениями.")
        return

    await add_group(tg_id=message.chat.id, name=name, course=course, number=number, link=link)
    await message.reply(f"Группа {name}-{number} добавлена!")

async def add_stud(message: types.Message):
    """
    Ожидаемый формат:
    /add_student <@username> <Фамилия_Имя> <староста 0/1>
    Пример: /add_student @ivanov Иванов_Иван 0
    """
    if not is_group_chat(message):
        await message.reply("Эта команда доступна только в групповых чатах.")
        return

    params = message.text.split()[1:]
    if len(params) != 3:
        await message.reply("Неверный формат.\n"
                            "Пример: /add_student <@username> <Фамилия_Имя> <староста 0/1>")
        return

    username, full_name, is_leader = params
    if username[0] != '@':
        await message.reply("Неверный формат: @username должен начинаться с '@'")
        return

    try:
        is_leader = bool(int(is_leader))
    except ValueError:
        await message.reply("Значение старосты должно быть 0 или 1.")
        return

    # Определяем группу по Telegram ID чата
    group = await get_group_by_tg_id(message.chat.id)
    if not group:
        await message.reply("Группа не найдена. Зарегистрируйте группу командой /create_group")
        return

    await add_student(
        tg_id=message.from_user.id,
        username=username,
        full_name=full_name,
        is_leader=is_leader,
        group_id=group.id  # используем суррогатный ключ группы из БД
    )
    await message.reply(f"Студент {full_name} добавлен в группу {group.group_name}-{group.group_number}!")

async def remove_stud(message: types.Message):
    """
    Ожидаемый формат:
    /remove_student <@username>
    Пример: /remove_student @ivanov
    """
    if not is_group_chat(message):
        await message.reply("Эта команда доступна только в групповых чатах.")
        return

    params = message.text.split()[1:]
    if len(params) != 1 or params[0][0] != '@':
        await message.reply("Неверный формат.\n"
                            "Пример: /remove_student <@username>")
        return

    username = params[0]
    await delete_student(username)
    await message.reply(f"Студент {username} удален из группы!")

async def change_leader(message: types.Message):
    """
    Ожидаемый формат:
    /change_leader <@username>
    Пример: /change_leader @ivanov
    """
    if not is_group_chat(message):
        await message.reply("Эта команда доступна только в групповых чатах.")
        return

    params = message.text.split()[1:]
    if len(params) != 1 or params[0][0] != '@':
        await message.reply("Неверный формат.\n"
                            "Пример: /change_leader <@username>")
        return

    username = params[0]
    await update_leader(username)
    await message.reply(f"Студент {username} назначен старостой!")
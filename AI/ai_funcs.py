from requests import get
from database.requests import get_schedule_by_group


# обновлять расписание в первые дни семестров
def get_schedule(link, course, group_name, group_number, day='all'):
    url = link + str(course)
    response = get(url)
    response.raise_for_status()
    data = response.json()

    # Находим все группы с заданным именем и номером равным group_number
    groups = [g for g in data['groups'] if g['name'] == group_name and g.get('grorder') == group_number]
    if not groups:
        return f"Группа '{group_name}' с номером {group_number} не найдена."

    # Собираем ID найденных групп
    group_ids = [g['id'] for g in groups]

    # Отбираем занятия для этих групп
    lessons = [lesson for lesson in data['lessons'] if lesson['groupid'] in group_ids]

    # Создаём словарь для расписания по дням (0 - понедельник, 5 - суббота)
    schedule = {i: [] for i in range(6)}

    for lesson in lessons:
        # Парсим время занятия
        timeslot = lesson['timeslot'].strip('()')
        parts = [part.strip() for part in timeslot.split(',')]
        if len(parts) < 4:
            continue  # Пропускаем некорректный формат

        day_of_week = int(parts[0])
        start_time = parts[1]
        end_time = parts[2]

        # Обрабатываем все учебные планы (подномера)
        for subnum in range(1, lesson['subcount'] + 1):
            curriculum = next((c for c in data['curricula'] if c['lessonid'] == lesson['id'] and c['subnum'] == subnum),
                              None)
            if curriculum:
                # Добавляем запись с информацией занятия
                entry = {
                    'start': start_time,
                    'end': end_time,
                    'subject': curriculum['subjectabbr'],
                    'teacher': curriculum['teachername'],
                    'room': curriculum['roomname'],
                    'info': lesson['info']
                }
                schedule[day_of_week].append(entry)

    # Сортируем занятия в каждом дне по времени начала
    for day_num in schedule:
        schedule[day_num].sort(key=lambda x: x['start'])

    # Функция для форматирования записи занятия в строку без служебных слов
    def format_entry(entry):
        info_text = f" ({entry['info']})" if entry['info'] else ""
        return f"{entry['start']} - {entry['end']}: {entry['subject']}, {entry['teacher']}, Аудитория: {entry['room']}{info_text}"

    # Формируем итоговый вывод
    day_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
    if day == 'all':
        formatted_schedule = {}
        for day_num in range(6):
            formatted_schedule[day_names[day_num]] = [format_entry(e) for e in schedule[day_num]]
        return formatted_schedule
    elif isinstance(day, int) and 0 <= day <= 5:
        return [format_entry(e) for e in schedule[day]]
    else:
        return "Ошибка: параметр day должен быть 'all' или числом от 0 (Понедельник) до 5 (Суббота)"


# url = "https://schedule.sfedu.ru/APIv1/schedule/grade/"
# schedule_result = get_schedule(url, 4, 'ПМИ', 1, day='all')
# for i in ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']:
#     print(i, schedule_result[i])


async def send_schedule(group_id, day=7):
    schedule = await get_schedule_by_group(group_id)
    days_dict = {
        '1': schedule['Понедельник'],
        '2': schedule['Вторник'],
        '3': schedule['Среда'],
        '4': schedule['Четверг'],
        '5': schedule['Пятница'],
        '6': schedule['Суббота'],
    }
    if day == 7:
        return schedule
    elif day in days_dict:
        return {day: days_dict[day]}


async def get_news_site():
    return

async def send_news_site():
    return "news from site"

async def send_news_vk():
    return "news from vk"

async def send_news():
    news_site = await send_news()
    news_vk = await send_news_vk()
    return (f"Новости на веб-сайте мехмата: {news_site}\n "
            f"Новости на странице ВК мехмата {news_vk}")

# нужна функция обработки ответа ИИ по запросу студента
async def get_task(task):
    tasks = {
        'расписание': send_schedule,
        'новости': send_news()
    }
    return {tasks: tasks[task]}

url = "https://schedule.sfedu.ru/APIv1/schedule/grade/"
schedule_result = get_schedule(url, 4, 'ПМИ', 1, day='all')
for i in ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']:
    print(i, schedule_result[i])
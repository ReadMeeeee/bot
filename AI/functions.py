from AI.ai_model import *
from Web.url_data import *
from config import link_news_sfedu, link_news_mmcs
from Database.requests import get_schedule_by_group, get_events_by_group, get_homework_by_group
import datetime


def filter_relevant_news(model: AIModel, news_list: list[dict]) -> list[dict]:
    """
    Фильтрует и возвращает новости, актуальные для студентов

    :param model: Модель ИИ, которая обрабатывает новости по релевантности студентам
    :param news_list: Список новостей (каждая новость — словарь с ключами: title, date, text, link, image)
    :return: Список новостей, релевантных для студентов
    """

    relevant_news = []

    role = (
        "You are an AI assistant for university group, text classification expert specialized in academic content. "
        "Your task is to analyze a headline in Russian and determine whether it belongs to an academic category or not. "
        "The academic categories are defined as follows: "
        "1. 'обучение' – headlines related to courses, lectures, seminars, or general academic instruction at the university; "
        "2. 'учебный план' – headlines related to curriculum design, course schedules, syllabi, or changes in the academic program; "
        "3. 'стажировки' – headlines related to internships, internship recruitment, or company demonstrations for internships; "
        "4. 'олимпиады' – headlines related to academic competitions, olympiads, or contests organized for university students. "
        "If the headline clearly belongs to at least one of these categories, you should return True; "
        "if it does not, return False. "
        "Note: Headlines that mention generic university events (such as celebrations, anniversaries, tutor announcements) "
        "should be classified as False, unless the main focus is on educational activities."
    )

    instructions = (
        "Instruction: Analyze the following headline in Russian and determine whether it primarily refers to academic topics "
        "(i.e. 'обучение', 'учебный план', 'стажировки', or 'олимпиады') and is directly connected to educational activities. "
        "Return True if the headline is primarily about educational topics; otherwise, return False. "
        "Do not include any additional text in your answer, only the Boolean value 'True' or 'False'. "
        "Important: Even if the headline contains words like 'отпраздновала', 'юбилей', 'праздник', or 'подготовил тьюторов', "
        "return True if the main focus is on educational topics; otherwise, return False. "
        "Examples: "
        "1. Headline: 'Новый курс по программированию запущен в ЮФУ' → True "
        "2. Headline: 'Обновление учебного плана факультета математики' → True "
        "3. Headline: 'Программа стажировок от ведущих компаний для студентов' → True "
        "4. Headline: 'Олимпиада по физике для студентов университета стартует в этом году' → True "
        "5. Headline: 'Кафедра «Теории и технологий в менеджменте» отпраздновала своё 25-летие' → False "
        "6. Headline: 'ЮФУ подготовил тьюторов для Образовательного Фонда' → False "
        "7. Headline: 'Конкурс «Мисс Мехмат»: яркое событие студенческой жизни!' → False "
        "\nHeadline to process: "
    )

    for news in news_list:
        message = (
            news.get('title', '')
        )

        response = model.get_response(
            message=message,
            instruction=instructions,
            role=role,
            max_tokens=10,
            temperature=0.1,
            sampling=True
        )

        if "true" in response.lower():
            relevant_news.append(news)

    return relevant_news

async def handle_define(model: AIModel, message: str, group_id) -> str:
    """
    Обрабатывает сообщение, определяет категорию и выбирает, какой ответ отправить студенту.

    :param model: Модель ИИ, для обработки новостей
    :param message: Сообщение от пользователя
    :param group_id: ID группы (для определения релевантности информации для группы)
    :return: Строка с сообщением для студента
    """

    role = (
        "You are an AI assistant for a university Telegram group chat. "
        "You are an expert in text classification of academic content in Russian and in extracting schedule details. "
        "Your goal is to accurately classify the incoming message into one of the defined categories and, if applicable, determine the specific day(s) of the week."
    )

    instructions = (
        "Analyze the given message in Russian and determine its topic. "
        "Classify the message into one of the following categories: "
        "'расписание' if the message is about schedules or timetables; "
        "'новости' if it contains university or academic news; "
        "'события' if it refers to events such as lectures, seminars, or social gatherings; "
        "'домашнее задание' if it includes homework or academic assignments; "
        "and 'другое' if it does not clearly belong to any of the above categories. "
        "If the message is classified as 'расписание', further analyze it for day-of-week references. "
        "Detect words like 'сегодня', 'завтра', 'послезавтра', explicit day names like 'понедельник', 'вторник', etc., or a date in the format 'dd.mm' or 'dd.mm.yyyy'. "
        "Return the final answer as a single string. For schedule queries, the returned string must be in the following format: "
        "'расписание <day> <day> ...', where <day> represents the day of the week in Russian (in lowercase). "
        "If no specific day is mentioned beyond 'расписание', return the schedule for the entire week."
    )

    category = model.get_response(
        message=message,
        instruction=instructions,
        role=role,
        max_tokens=10,
        temperature=0.1,
        sampling=True
    )

    category = category.strip().lower()
    category = category.split()

    # TODO положить определения дня недели из сообщения на модель ИИ
    if "расписание" in category:
        schedule = await get_schedule_by_group(group_id)
        schedule = {key.lower(): value for key, value in schedule.items()}
        answer = ""
        answer_if_sunday = ("В воскресенье пар не бывает.\n"
                            "Если вам поставили пары на воскресенье - скорее всего они в ближайших событиях")

        if len(category) < 2:
            answer = schedule

        elif category[1] == "воскресенье":
            answer += answer_if_sunday

        else:
            for i in category[1:]:

                if i in [
                    'понедельник', 'вторник', 'среда',
                    'четверг', 'пятница', 'суббота'
                ]:
                    answer += f"Расписание на {i}:\n{schedule[i]}\n"

                else:
                    days_dict = {
                        0: "понедельник",
                        1: "вторник",
                        2: "среда",
                        3: "четверг",
                        4: "пятница",
                        5: "суббота",
                        6: "воскресенье",
                        7: "понедельник",
                        8: "вторник"
                    }
                    today = datetime.datetime.now().weekday()

                    if i in ["завтра", "послезавтра"]:
                        day = today + 1
                        if i == "послезавтра":
                            day += 1

                        day_of_week = days_dict[day]
                        if day_of_week == "воскресенье":
                            answer += answer_if_sunday
                        else:
                            answer += f"Расписание на {i}:\n{schedule[day_of_week]}\n"

                    else:
                        parsed_date = None
                        try:
                            parsed_date = datetime.datetime.strptime(i, "%d.%m.%Y")
                        except ValueError:
                            try:
                                parsed_date = datetime.datetime.strptime(i, "%d.%m")
                                parsed_date = parsed_date.replace(year=datetime.datetime.now().year)
                            except ValueError:
                                parsed_date = None
                        if parsed_date is not None:
                            day_index = parsed_date.weekday()
                            day_of_week = days_dict.get(day_index, "неизвестный день")
                            if day_of_week == "воскресенье":
                                answer += answer_if_sunday
                            else:
                                answer += f"расписание на {i} ({day_of_week}):\n{schedule[day_of_week]}\n"
                        else:
                            answer += f"неверный формат даты: {i}\n"


        return f"Пожалуйста, ознакомьтесь с актуальным расписанием занятий:\n{answer}"

    if 'новости' in category:
        sfedu = URLData(link_news_sfedu)
        mmcs = URLData(link_news_mmcs)
        data = sfedu._get_news_sfedu() + mmcs._get_news_mmcs()
        relevant_news = filter_relevant_news(model, data)
        news = ""
        for i in relevant_news:
            news += i['title'] + '\n'
        return news

    if 'события' in category:
        return f"Не пропустите предстоящие события и мероприятия:\n{await get_events_by_group(group_id)}"

    if 'домашнее задание' in category:
        return f"Проверьте, пожалуйста, информацию по домашним заданиям:\n{await get_homework_by_group(group_id)}"

    else:
        return model.get_response(message)

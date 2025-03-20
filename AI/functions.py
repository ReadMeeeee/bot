from AI.ai_model import *
from Web.url_data import *
from config import link_news_sfedu, link_news_mmcs
from Database.requests import get_schedule_by_group, get_events_by_group, get_homework_by_group


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
        "You are an expert in text classification of academic content in Russian. "
        "Your goal is to accurately classify the incoming message into one of the defined categories."
    )

    instructions = (
        "Analyze the given message in Russian and determine its topic. "
        "Classify the message into one of the following categories: "
        "'Расписание' if the message is about schedules or timetables; "
        "'Новости' if it contains university or academic news; "
        "'События' if it refers to events such as lectures, seminars, or social gatherings; "
        "'Домашнее задание' if it includes homework or academic assignments; "
        "and 'Другое' if it does not clearly belong to any of the above categories. "
        "Return only one of these category names as the final answer."
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

    # TODO положить определения дня недели из сообщения на модель ИИ
    if 'расписание' in category:
        return f"Пожалуйста, ознакомьтесь с актуальным расписанием занятий:\n{await get_schedule_by_group(group_id)}"

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

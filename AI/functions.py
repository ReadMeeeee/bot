from AI.models.class_ai_local import *
from AI.models.class_ai_api import *

from AI.embedding_manager import embeddings, load_embedded_data, find_similarity

from Parsing.url_data import *
from config import link_news_sfedu, link_news_mmcs

import datetime

from AI.models.instructions import role_news, instructions_news,\
                                   role_classification, instructions_classification,\
                                   instructions_fallback, role_fallback
from Database.requests import get_events_by_group, get_homework_by_group, get_schedule_by_group


async def just_response(model, instructions, role, message, tokens):
    response = model.get_response(
        message=message,
        instruction=instructions,
        role=role,
        max_tokens=tokens,
        temperature=0.1,
        # sampling=True # Для локальных моделей
    )
    return response

async def filter_relevant_news(model: AIModelLocal | AIModelAPI, news_list: list[dict]) -> list[dict]:
    """
    Фильтрует и возвращает новости, актуальные для студентов

    :param model: Модель ИИ, которая обрабатывает новости по релевантности студентам
    :param news_list: Список новостей (каждая новость — словарь с ключами: title, date, text, link, image)
    :return: Список новостей, релевантных для студентов
    """

    relevant_news = []

    for news in news_list:
        message = (
            news.get('title', '')
        )

        response = await just_response(model, instructions_news, role_news, message,10)

        if "true" in response.lower():
            relevant_news.append(news)

    return relevant_news

async def get_schedule(category, group_id):
    schedule = await get_schedule_by_group(group_id)
    schedule = {key.lower(): value for key, value in schedule.items()}

    formatted_schedule = "\n\n".join(
        schedule.get(day, f"{day.capitalize()}:\n  Нет занятий")
        for day in ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота']
    )

    answer = ""
    answer_if_sunday = ("В воскресенье пар не бывает.\n"
                        "Если вам поставили пары на воскресенье - скорее всего они в ближайших событиях")

    if len(category) < 2:
        answer = formatted_schedule

    elif category[1] == "воскресенье":
        answer += answer_if_sunday

    else:
        for i in category[1:]:

            if i in [
                'понедельник', 'вторник', 'среда',
                'четверг', 'пятница', 'суббота'
            ]:
                answer += f"{schedule[i]}\n"

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
                        answer += f"{schedule[day_of_week]}\n"

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
                            answer += f"{i}:\n{schedule[day_of_week]}\n"
                    else:
                        answer += f"неверный формат даты: {i}\n"

    return f"Пожалуйста, ознакомьтесь с актуальным расписанием занятий:\n{answer}"

async def get_homework(group_id):
    return (f"Проверьте, пожалуйста, информацию по домашним заданиям:"
            f"\n{await get_homework_by_group(group_id)}")

async def get_events(group_id):
    return (f"Не пропустите предстоящие события и мероприятия:"
            f"\n{await get_events_by_group(group_id)}")

async def get_news(model, group_id):
    sfedu = URLData(link_news_sfedu)
    mmcs = URLData(link_news_mmcs)
    data = sfedu._get_news_sfedu() + mmcs._get_news_mmcs()
    relevant_news = await filter_relevant_news(model, data)
    news = ""
    for i in relevant_news:
        news += i['title'] + '\n'
    return news


async def handle_define(model: AIModelLocal | AIModelAPI, message: str, group_id, path_f: str) -> str:
    category_response = await just_response(model, instructions_classification, role_classification, message, 25)
    category = category_response.strip().lower().split()

    category_map = {
        "расписание": lambda: get_schedule(category, group_id),
        "новости": lambda: get_news(model, group_id),
        "события": lambda: get_events(group_id),
        "домашнее задание": lambda: get_homework(group_id),
    }

    for key, func in category_map.items():
        if key in category:
            return await func()

    # Если ни одна категория не подошла, используем fallback
    db = await load_embedded_data(path_f, embeddings)
    relevant_data = await find_similarity(db, message)
    instructions_fb = await instructions_fallback(relevant_data)

    return await just_response(model, instructions_fb, role_fallback, message, 200)


import yaml
import json
import requests
from bs4 import BeautifulSoup
import re
import os


def clear_text(text: str, to_lower: bool = False) -> str:
    remove_chars = {
        0x00A0: None,  # NBSP – no-break space
        0x00AD: None,  # SHY  – soft hyphen
        0x200B: None  # ZWSP – zero width space
    }
    text = re.sub(r'\n+', '\n', text)
    text = text.translate(remove_chars)

    if to_lower:
        text = text.lower()

    return text


def load_config(path="config.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_page(url, headers):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def parse_selectors(soup, selectors):
    """Обрабатываем селекторы для одиночной страницы (data)"""
    result = {}
    for key, selector in selectors.items():
        element = soup.select_one(selector)
        result[key] = element.text.strip() if element else None
        if result[key] is not None: result[key] = clear_text(result[key], to_lower=True)

    return result


def parse_item(item, selectors):
    """Обрабатываем каждый элемент в новостях (news)"""
    result = {}
    for key, selector_conf in selectors.items():
        # Если selector_conf – словарь, значит нужно извлечь атрибут
        if isinstance(selector_conf, dict):
            element = item.select_one(selector_conf.get("selector"))
            if element:
                # Если запрошено значение атрибута, берём его, иначе текст
                result[key] = element.get(selector_conf.get("attribute"), element.text.strip())
            else:
                result[key] = None
        else:
            element = item.select_one(selector_conf)
            result[key] = element.text.strip() if element else None
            if result[key] not in (None, 'link'): result[key] = clear_text(result[key])

    return result


def parse_info_data(path_to_yaml_cfg):
    total_data = []
    config = load_config(path_to_yaml_cfg)
    headers = config["parsers"]["headers"]
    websites = config["websites"]
    for site, site_config in websites.items():

        base_url = site_config['base_url']
        print(f"\n\nОбработка сайта: {site} ({base_url})")

        pages = site_config.get('pages', {})

        # Обработка информационных страниц (data)
        for page in pages.get('data', []):
            url = base_url + page['path']
            print(f"Парсинг data-страницы '{page['name']}' по URL: {url}")

            html = fetch_page(url, headers)
            soup = BeautifulSoup(html, 'html.parser')
            data = parse_selectors(soup, page['selectors'])

            total_data.append(data)
            print("Полученные данные:", data)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(script_dir, ".."))
    file_path = os.path.join(parent_dir, "AI", "embeddings_data", "json_data", "sfedu_mmcs_data.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(total_data, f, ensure_ascii=False, indent=4)


def parse_news_data(path_to_yaml_cfg):
    total_data_news = []

    config = load_config(path_to_yaml_cfg)
    headers = config["parsers"]["headers"]
    websites = config["websites"]
    for site, site_config in websites.items():

        base_url = site_config['base_url']
        print(f"\n\nОбработка сайта: {site} ({base_url})")

        pages = site_config.get('pages', {})

        # Обработка новостных страниц (news)
        for page in pages.get('news', []):
            url = base_url + page['path']
            print(f"Парсинг news-страницы '{page['name']}' по URL: {url}")

            html = fetch_page(url, headers)
            soup = BeautifulSoup(html, 'html.parser')
            container = soup.select_one(page.get('container'))
            if not container:
                print("Не удалось найти контейнер новостей.")
                continue
            items = container.select(page.get('item_selector'))
            news_data = [parse_item(item, page['selectors']) for item in items]

            total_data_news.append(news_data)
            print("Новости:", news_data)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(script_dir, ".."))
    file_path = os.path.join(parent_dir, "AI", "embeddings_data", "json_data", "sfedu_mmcs_news.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(total_data_news, f, ensure_ascii=False, indent=4)


def parse_schedule(path_to_yaml_cfg, group='ПМИ', number=1, course=1):
    config = load_config(path_to_yaml_cfg)
    websites = config["websites"]

    base_url = websites['MMCS_schedule']['base_url']
    base_url = base_url + str(course)

    response = requests.get(base_url)
    response.raise_for_status()

    data = response.json()

    groups = [g for g in data['groups'] if g['name'] == group and g.get('grorder') == number]
    if not groups:
        return f"Группа '{group}' с номером {number} не найдена."

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

        # Обрабатываем все учебные планы
        for subnum in range(1, lesson['subcount'] + 1):
            curriculum = next(
                (c for c in data['curricula'] if c['lessonid'] == lesson['id'] and c['subnum'] == subnum),
                None
            )
            if curriculum:
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

    result = ''

    days_dict = {
        0: 'Понедельник',
        1: 'Вторник',
        2: 'Среда',
        3: 'Четверг',
        4: 'Пятница',
        5: 'Суббота',
    }

    def format_day(day_list):
        day_string = day_list['start'] + '-' + day_list['end'] + '\n' +\
                     day_list['subject'] + '\n' +\
                     day_list['teacher'] + '\n' +\
                     day_list['room']
        return day_string

    for i in schedule:
        day = days_dict[i]
        if schedule[i]: print(day, format_day(schedule[i][0]), '\n')
        else: print(day, schedule[i], '\n')
        # print(key, data)
        # result += days_dict[key] + data + '\n'

    return result




if __name__ == "__main__":
    path_to_yaml = "config.yaml"

    # parse_info_data(path_to_yaml)
    # parse_news_data(path_to_yaml)

    schedule = parse_schedule(path_to_yaml, course=4)
    print(schedule)
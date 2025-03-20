from requests import get
from bs4 import BeautifulSoup


class URLData:
    def __init__(self, url: str = None):
        self.url = url

        try:
            if not url:
                raise ValueError("URL не предоставлен")
            if not (url.startswith("http://") or url.startswith("https://")):
                raise ValueError("URL должен начинаться с 'http://' или с 'https://'.")
        except Exception as e:
            print(f"Ошибка URLData: {e}")
            raise e

    # Выглядит пока странно, так как данные зависят от курса (указывается в конце ссылки)
    def _get_from_api(self, course: int = None):
        """
        Получает данные по API. Можно добавить курс, если расписание

        :param course: Номер курса (по умолчанию None)

        :return: данные по API
        """
        url = self.url + str(course)
        response = get(url)
        response.raise_for_status()
        data = response.json()
        return data

    def _parse(self):
        """
        Парсит HTML-страницу

        :return: Объект BeautifulSoup
        """
        try:
            response = get(self.url)
            response.raise_for_status()
            html = response.text
            data = BeautifulSoup(html, "html.parser")
            return data
        except Exception as e:
            print(f"Ошибка при парсинге URL {self.url}: {e}")
            raise e

    def _get_schedule(self, course: int = 1, group_name: str = 'ПМИ', group_number: int = 1, day='all'):
        """
        Получает расписание по API и фильтрует его

        :param course: Номер курса (по умолчанию 1)
        :param group_name: Название курса (по умолчанию ПМИ)
        :param group_number: Номер группы (по умолчанию 1)
        :param day: Число от 0 до 5 (0 - понедельник, 5 - суббота) или 'all' (по умолчанию 'all')

        :return: Словарь-расписание
        """
        data = self._get_from_api(course)

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
                curriculum = next(
                    (c for c in data['curricula'] if c['lessonid'] == lesson['id'] and c['subnum'] == subnum),
                    None
                )
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

        # Функция для форматирования записи занятия в строку
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

    def _get_news_mmcs(self):
        """
        Парсит HTML и достает оттуда новостные посты (сайт МехМата)

        Каждая новость - словарь с ключами:
            - title: заголовок новости;
            - date: дата создания;
            - author: автор новости;
            - text: краткое описание или текст новости;
            - link: ссылка "Подробнее…".

        :return: Список словарей с информацией о новостях
        """
        soup = self._parse()

        # Находим контейнер с новостными постами
        news_container = soup.find("div", class_="yjsg-newsitems")
        if not news_container:
            return []

        # Ищем все отдельные новости внутри контейнера
        news_posts = news_container.find_all("div", class_="news_item_f")
        news_list = []

        for post in news_posts:
            # Извлекаем заголовок
            title_el = post.find("h2", class_="article_title")
            title = title_el.get_text(strip=True) if title_el else "Нет заголовка"

            # Извлекаем дату создания и автора
            info_el = post.find("div", class_="newsitem_info")
            created_date = None
            author = None
            if info_el:
                date_el = info_el.find("span", class_="createdate")
                if date_el:
                    created_date = date_el.get_text(strip=True)
                author_el = info_el.find("span", class_="createby")
                if author_el:
                    author = author_el.get_text(strip=True)

            # Извлекаем текст новости
            text_el = post.find("div", class_="newsitem_text")
            text = text_el.get_text(strip=True) if text_el else ""

            # Извлекаем ссылку "Подробнее…"
            link_el = post.find("a", class_="btn")
            link = link_el["href"] if link_el and link_el.has_attr("href") else None

            news_list.append({
                "title": title,
                "date": created_date,
                "author": author,
                "text": text,
                "link": link
            })

        return news_list

    # TODO настрой получение изображение новостей
    def _get_news_sfedu(self):
        """
        Парсит HTML и достает оттуда новостные посты (сайт ЮФУ)


        Каждая новость - словарь с ключами:
          - title: заголовок (из <div class="acttitle">, текст ссылки);
          - date: дата новости (из <div class="actdate">);
          - text: описание или краткий текст (из <div class="acttext">);
          - link: URL для "Подробнее…" (из ссылки внутри <div class="acttitle">);
          - image: URL картинки (из <div class="actfoto">, атрибут src у <img>).

        :return: Список словарей с информацией о новостях
        """
        soup = self._parse()

        # Находим контейнер с новостями по id
        news_container = soup.find("div", id="Dcont")
        if not news_container:
            return []

        # Находим все новости, представленные как <div class="act">
        news_posts = news_container.find_all("div", class_="act")
        news_list = []

        for post in news_posts:
            # Извлекаем заголовок и ссылку
            title_div = post.find("div", class_="acttitle")
            title = None
            link = None
            if title_div:
                a_tag = title_div.find("a")
                if a_tag:
                    title = a_tag.get_text(strip=True)
                    link = a_tag.get("href")

            # Извлекаем дату новости
            date_div = post.find("div", class_="actdate")
            date = date_div.get_text(strip=True) if date_div else None

            # Извлекаем текст новости
            text_div = post.find("div", class_="acttext")
            text = text_div.get_text(strip=True) if text_div else ""

            # Извлекаем URL картинки, если она есть
            image_div = post.find("div", class_="actfoto")
            image = None
            if image_div:
                img_tag = image_div.find("img")
                if img_tag:
                    image = img_tag.get("src")

            news_list.append({
                "title": title,
                "date": date,
                "text": text,
                "link": link,
                "image": image
            })

        return news_list

    def _get_train_mmcs(self):
        """
        Парсит HTML и достает оттуда новостные посты (сайт МехМата)

        Каждая новость - словарь с ключами:
            - __label__ - оценка новости;
            - title: заголовок новости;

        :return: Список словарей с данными для обучения
        """
        soup = self._parse()

        # Находим контейнер с новостными постами
        news_container = soup.find("div", class_="yjsg-newsitems")
        if not news_container:
            return []

        # Ищем все отдельные новости внутри контейнера
        news_posts = news_container.find_all("div", class_="news_item_f")
        data_list = []

        for post in news_posts:
            # Извлекаем заголовок
            title_el = post.find("h2", class_="article_title")
            title = title_el.get_text(strip=True) if title_el else "Нет заголовка"

            data_list.append(title)

        return data_list

    # Пока заморозим
    def _get_news_vk(self, data):
        pass

    def f_schedule(self):
        pass

    # Пока заморозим
    def f_news_vk(self):
        pass


# url = "https://schedule.sfedu.ru/APIv1/schedule/grade/"
# data = URLData(url)
# schedule = data._get_schedule(4, 'ПМИ', 1)
# for i in ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']: print(i, schedule[i])
# print(schedule)

# url = "https://sfedu.ru/press-center/newspage/1"
# data = URLData(url)
# news = data._get_news_sfedu()
# for i in news: print(i)
# print(news)

# url = "https://vk.com/mmcs.official"
# url = "https://vk.com/sfedu_official"

# from AI.ai_model import AIModel
# AI = AIModel("Qwen/Qwen2-1.5B-Instruct")
# filtered_news = AI.filter_relevant_news(news)
# for i in filtered_news: print(i)

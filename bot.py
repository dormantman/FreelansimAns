# -*- coding: utf-8 -*-

import datetime
import json
import logging
import os
import threading
import traceback

import bs4
import html2text
import requests
import telegram
import telegram.ext

logging.basicConfig(
    format='[%(asctime)s] %(message)s', level='INFO',
    handlers=[logging.StreamHandler()], datefmt='%Y.%m.%d %H:%M:%S'
)


class Network:
    urls = {
        'root': 'https://freelansim.ru',
        'auth': 'https://freelansim.ru/users/sign_in',
        'tasks': 'https://freelansim.ru/tasks',
        'freelancers': 'https://freelansim.ru/freelancers',
        'personal': 'https://freelansim.ru/my/personal'
    }


class Task:
    def __init__(self, data=None):
        self.id = None
        self.title = None
        self.description = None
        self.price = None
        self.date = None
        self.reply_count = None
        self.has_responded = None
        self.is_marked = None
        self.tags = None
        self.safe_deal_only = None
        self.user = None
        self.is_publish = None
        self.category_name = None
        self.sub_category_name = None
        self.published_at = None
        self.url = None
        self.task_comments_count = None
        self.page_views_count = None

        if data is not None:
            self.parse(data)

    def parse(self, data: dict):
        self.id = data['id']
        self.title = data['title']
        self.description = data['description']
        self.price = data['price']
        self.date = data['date']
        self.reply_count = data['reply_count']
        self.has_responded = data['has_responded']
        self.is_marked = data['is_marked']
        self.tags = data['tags']
        self.safe_deal_only = data['safe_deal_only']
        self.user = data['user']
        self.is_publish = data.get('is_publish')
        self.category_name = data.get('category_name')
        self.sub_category_name = data.get('sub_category_name')
        self.published_at = data.get('published_at')
        self.url = data.get('url')
        self.task_comments_count = data.get('task_comments_count')
        self.page_views_count = data.get('page_views_count')

    def update(self, task):
        keys = [
            'title', 'description', 'price', 'has_responded', 'date', 'user',
            'reply_count', 'page_views_count', 'task_comments_count',
            'is_publish', 'category_name', 'sub_category_name', 'url',
            'published_at', 'tags'
        ]

        for key in keys:
            if getattr(self, key) != getattr(task, key):
                task_label = str(self)
                print(
                    'UPDATE', '#', task_label, ' ' * (80 - len(task_label)), '|', key + ':\t',
                    getattr(self, key), getattr(task, key)
                )
                setattr(self, key, getattr(task, key))

    def format_message(self, full=False):
        odds = '✅ ' if self.reply_count < 4 else (
            '❔ ' if self.reply_count < 8 else '❌ '
        )
        star = '✨ ' if self.safe_deal_only else ''
        price = f'*{self.price["value"]}* за проект' if self.price['type'] == 'per_project' else (
            f'_{self.price["value"]} цена_' if self.price['type'] == 'none' else f'*{self.price["value"]}* в час')
        date = 'Только что' if self.date == '0 мин.' else self.date

        if full:
            desc = self.format_description(1024)
            user = self.format_user()

            return f'{odds}{star}*{self.title}*\n{price} | {date}\n\n_{", ".join(self.tags)}_\n' \
                f'{self.category_name} | {self.sub_category_name}\n' \
                f'{self.url}\n\nПросмотров: *{self.page_views_count}* | Ответов: *{self.reply_count}* ' \
                f'| Комментариев: *{self.task_comments_count}*\n\n{desc}\n\n{user}'

        desc = self.format_description(128)

        return f'{odds}{star}*{self.title}*\n{price} | {date}\n\n_{", ".join(self.tags)}_\n{self.url}\n\n{desc}'

    def format_user(self):
        rating = self.user["rating"] if self.user["rating"] else ''

        if self.user["firstname"]:
            if self.user["lastname"]:
                name = f'{self.user["firstname"]} {self.user["lastname"]}'
            else:
                name = self.user["firstname"]
        else:
            name = 'Без имени'

        return f'{name} | [{self.user["username"]}]({Network.urls["freelancers"]}/{self.user["username"]}) {rating}'

    def format_description(self, max_count: int):
        result = []
        length = 0
        for word in self.description.split('\n'):
            if length + len(word) > max_count:
                break
            result.append(word)
            length += len(word) + 1

        return '\n'.join(result).replace(
            '<br>', '\n').replace(
            '*', '•').replace(
            '_', '-').replace(
            '`', '"').replace(
            '\n\n', '\n'
        )

    def json(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'date': self.date,
            'reply_count': self.reply_count,
            'has_responded': self.has_responded,
            'is_marked': self.is_marked,
            'tags': self.tags,
            'safe_deal_only': self.safe_deal_only,
            'user': self.user,
            'is_publish': self.is_publish,
            'category_name': self.category_name,
            'sub_category_name': self.sub_category_name,
            'published_at': self.published_at,
            'url': self.url,
            'task_comments_count': self.task_comments_count,
            'page_views_count': self.page_views_count,
        }

    def __repr__(self):
        return '<Task %s | %s >' % (self.date, self.title)


class User:
    def __init__(self):
        self.cookies_path = os.path.join(os.path.split(__file__)[0], 'cookies.json')

        self.session = requests.Session()

        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        }

        self.authorized = False

    def load_cookies(self, path=None, data=None):
        """ Загрузить cookies """

        self.log('Start cookies loading...')

        try:
            if data is None:
                with open(self.cookies_path if path is None else path) as file:
                    data = json.load(file)

            data = {obj['name']: obj['value'] for obj in data}

            session_id = data.get('_session_id')
            if session_id:
                self.session.cookies.set('_session_id', session_id)
                if self.auth_check():
                    self.authorized = True

            if self.authorized:
                self.log('Cookies successfully load!')

            else:
                self.log('Failed to load cookies!')

        except (BaseException, Exception):
            print(traceback.format_exc(), end='\n\n')
            self.log('Failed to load cookies!')

        return self.authorized

    def get_cookies(self):
        return self.session.cookies

    def auth_check(self):
        """ Проверка авторизации """

        response = self.session.get(Network.urls['personal'])
        soup = bs4.BeautifulSoup(response.content, 'lxml')

        avatar = soup.find('form', {'class': 'form_avatar'})

        if avatar:
            username = avatar.get('action').split('/')[2]
            avatar = avatar.find('img', {'class': 'avatario'}).get('src')
            if avatar.startswith('/assets/default'):
                avatar = None

            first_name = soup.find('input', {'name': 'freelancer[first_name]'}).get('value')
            last_name = soup.find('input', {'name': 'freelancer[last_name]'}).get('value')

            birth_date = ' '.join([
                soup.find('select', {
                    'name': 'freelancer[birth_date(3i)]'
                }).find('option', {'selected': 'selected'}).text,
                soup.find('select', {
                    'name': 'freelancer[birth_date(2i)]'
                }).find('option', {'selected': 'selected'}).text,
                soup.find('select', {
                    'name': 'freelancer[birth_date(1i)]'
                }).find('option', {'selected': 'selected'}).text,
            ])

            location = soup.find('input', {'name': 'freelancer[location]'}).get('value')
            about = soup.find('textarea', {'name': 'freelancer[self_about]'}).text.strip()

            balance = soup.find('ul', {'class': 'menu_user-settings'}).find('span', {'class': 'count'}).text
            available_responses = soup.find(
                'a', {'class': 'subscription'}
            ).find('small', {'class': 'active'}).text

            print(username, avatar)
            print(first_name, last_name)
            print(birth_date)
            print(location)
            print(about)
            print(balance)
            print(available_responses)
            return True
        return False

    def answer(self, task, text):
        print(task)

        comment_url = f'{Network.urls["tasks"]}/{task.id}/task_comments'

        response = self.session.get(task.url)
        soup = bs4.BeautifulSoup(response.content, 'lxml')

        token = soup.find('meta', {'name': 'csrf-token'}).get('content')

        response = self.session.post(
            comment_url,
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': task.url,
                'Accept': '*/*;q=0.5, text/javascript, application/javascript, '
                          'application/ecmascript, application/x-ecmascript',
                'X-CSRF-Token': token,
            },
            data={
                'utf8': '✓',
                'task_comment[body]': text,
                'button': ''
            }
        )

        print(response.reason, '|', response.content.decode())

    @staticmethod
    def log(msg, name='USER'):
        logging.info(f'[{name}]: {msg}')


class FreelansimBot:
    def __init__(self, user=None):
        """ FreelansimBot | Бот для автоответов на freelansim.ru"""

        logging.info('FreelansimBot init')

        self.cookies_path = os.path.join(os.path.split(__file__)[0], 'cookies.json')

        self.session = requests.Session()

        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        }

        self.tg_token = '964982277:AAH0nZXMlWGvYGpSIwWr69jpM3pvrTYftfM'
        self.updater = telegram.ext.Updater(self.tg_token)
        self.tg_bot = telegram.Bot(self.tg_token)
        self.tg_author = 448254726

        self.updater.dispatcher.add_handler(
            telegram.ext.CallbackQueryHandler(self.query_handler)
        )

        self.tasks = {}
        self.users = {self.tg_author, }
        self.__threads__ = []

        self.user = user

        if self.user is not None:
            self.session.cookies = self.user.session.cookies

    def query_handler(self, bot, update):
        query = update.callback_query

        command, *args = query.data.split(':')

        query.answer('')

        if command == 'full':
            task_id = int(args[0])
            task = self.tasks.get(task_id)

            if task:
                try:
                    query.edit_message_text(
                        text=task.format_message(full=True),
                        parse_mode='Markdown',
                        disable_web_page_preview=True,
                        reply_markup=telegram.InlineKeyboardMarkup(
                            [[
                                telegram.InlineKeyboardButton('Скрыть', callback_data=f'short:{task.id}'),
                                telegram.InlineKeyboardButton('Обновить', callback_data=f'full:{task.id}')
                            ]]
                        )
                    )

                except telegram.error.BadRequest as error:
                    self.log(error)

            else:
                try:
                    query.edit_message_text(
                        text=f'Информация по заказу устарела\n\n{Network.urls["tasks"]}/{task_id}',
                        parse_mode='Markdown',
                        reply_markup=None,
                    )

                except telegram.error.BadRequest as error:
                    self.log(error)

        elif command == 'short':
            task_id = int(args[0])
            task = self.tasks.get(task_id)

            if task:
                try:
                    query.edit_message_text(
                        text=task.format_message(full=False),
                        parse_mode='Markdown',
                        disable_web_page_preview=True,
                        reply_markup=telegram.InlineKeyboardMarkup(
                            [[telegram.InlineKeyboardButton('Показать полностью', callback_data=f'full:{task.id}')]]
                        )
                    )

                except telegram.error.BadRequest as error:
                    self.log(error)

            else:
                try:
                    query.edit_message_text(
                        text=f'Информация по заказу устарела\n\n{Network.urls["tasks"]}/{task_id}',
                        parse_mode='Markdown',
                        reply_markup=None
                    )

                except telegram.error.BadRequest as error:
                    self.log(error)

    def event_new_task(self, task):
        print('NEW TASK', '#', task)

        for user_id in self.users:
            thr = threading.Thread(target=self.__event_new_task__, args=[user_id, task.id], daemon=True)
            thr.start()
            self.__threads__.append(thr)

    def get_tasks(self, page=1):
        """ Получить список задачь
        :return: :list:`Tasks`
        """

        data = self.session.get(
            Network.urls['tasks'],
            headers={
                'Accept': 'application/json',
            },
            params={
                'per_page': 50,
                'page': page
            }
        ).json()

        data_addition = {obj['id']: {
            'is_publish': obj['is_publish'],
            'category_name': obj['category_name'],
            'sub_category_name': obj['sub_category_name'],
            'published_at': datetime.datetime.strptime(
                obj['published_at'].split('.')[0], "%Y-%m-%dT%H:%M:%S"
            ),
            'url': obj['url'],
            'task_comments_count': obj['task_comments_count'],
            'page_views_count': obj['page_views_count']
        } for obj in data}

        data = self.session.get(
            Network.urls['tasks'],
            headers={
                'Accept': 'application/json',
                'X-Version': '1'
            },
            params={
                'per_page': 50,
                'page': page
            }
        ).json()['tasks']

        for task in data:
            if task['id'] in data_addition:
                task.update(data_addition[task['id']])

            task['tags'] = list(map(lambda x: x.get('name'), task['tags']))

            avatar = task['user']['avatar']
            root = Network.urls["root"]

            task['user']['avatar'] = {
                'src': f'{root}{avatar["src"]}' if avatar['src'].startswith('/assets/') else avatar['src'],
                'src2x': f'{root}{avatar["src2x"]}' if avatar['src2x'].startswith('/assets/') else avatar['src2x'],
            }

        return data

    def listen(self):
        """ Слушать сервер
        :yields: :class:`Event`
        """

        while True:
            try:
                for event in self.get_tasks():
                    yield event

            except requests.exceptions.ConnectionError:
                self.log('Error updating server...')

                yield []

    def get_task_detailed(self, task_id):
        response = self.session.get(f"{Network.urls['tasks']}/{task_id}")
        soup = bs4.BeautifulSoup(response.content, 'lxml')

        description_html = str(soup.find('div', {'class': 'task__description'}))
        description_text = html2text.HTML2Text().handle(description_html)

        months = [
            'января', 'февраля', 'марта',
            'апреля', 'мая', 'июня',
            'июля', 'августа', 'сентября',
            'октября', 'ноября', 'декабря',
        ]

        date = soup.find('div', {'class': 'task__meta'}).text.split('\n')[1]
        month_index = months.index(date.split()[1])
        date = date.replace(months[month_index], '{:0>2d}').format(month_index + 1)
        date = datetime.datetime.strptime(date, '%d %m %Y, %H:%M')

        about_user = soup.find('div', {'class': 'user_about'})
        avatar = about_user.find('div', {'class': 'avatar'}).find('a')
        username = avatar.get('href').split('/')[-1]

        avatar = avatar.find('img').get('src')
        if avatar.startswith('/assets/default'):
            avatar = None

        verified = about_user.find('span', {'class': 'verified'})
        if verified:
            verified = verified.get('title')

        return {
            'description': {
                'text': description_text,
                'html': description_html,
            },
            'date': date,
            'avatar': avatar,
            'username': username,
            'verified': verified
        }

    def init_tasks(self, pages=10):
        """ Init load tasks"""

        self.log('Start loading tasks...', 'TASKS')

        for page in range(1, pages + 1):
            suffix = 'st' if page == 1 else (
                'nd' if page == 2 else (
                    'rd' if page == 3 else 'th'
                )
            )
            self.log(f'Loading {page}{suffix} page...', 'TASKS')
            for element in self.get_tasks(page=page):
                task = Task(element)
                self.tasks[task.id] = task

        self.log('Tasks successfully loaded!', 'TASKS')

    def telegram_polling(self):
        """ Telegram bot """
        self.log('Start telegram bot polling...', 'TELEGRAM')
        self.updater.start_polling()

    def long_polling(self):
        """ Main pool """

        self.log('Start main pool...')

        try:
            for element in self.listen():
                task = Task(element)

                if task.id not in self.tasks:
                    self.tasks[task.id] = task
                    self.event_new_task(task)

                else:
                    self.tasks[task.id].update(task)

        except KeyboardInterrupt:
            print('Exit...')
            self.exit()

    def exit(self):
        self.log('The final exit.')
        self.session.close()
        self.updater.stop()
        exit()

    def __event_new_task__(self, user_id, task_id):
        self.tg_bot.send_message(
            user_id,
            self.tasks.get(task_id).format_message(),
            parse_mode='Markdown',
            disable_web_page_preview=True,
            reply_markup=telegram.InlineKeyboardMarkup(
                [[telegram.InlineKeyboardButton('Показать полностью', callback_data=f'full:{task_id}')]]
            )
        )

    @staticmethod
    def log(msg, name='BOT'):
        logging.info(f'[{name}]: {msg}')


if __name__ == '__main__':
    admin = User()
    admin.load_cookies()

    bot = FreelansimBot(user=admin)
    bot.init_tasks(pages=1)
    bot.telegram_polling()
    bot.long_polling()

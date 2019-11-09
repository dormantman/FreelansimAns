# -*- coding: utf-8 -*-

import datetime
import json
import logging
import os
import threading
import traceback
from typing import Dict, List

import requests
import telegram.ext

from objects.database import Database
from objects.static import Static
from objects.task import Task
from objects.user import User

logging.basicConfig(
    format='[%(asctime)s] %(message)s', level='INFO', datefmt='%Y.%m.%d %H:%M:%S'
)


class FreelansimBot:
    def __init__(self):
        """ FreelansimBot | Бот для автоответов на freelansim.ru"""

        logging.info('FreelansimBot initialization')

        self.__root_path__ = os.path.split(__file__)[0]

        self.__config__ = {}

        self.__load_config__(os.path.join(self.__root_path__, 'config.json'))

        self.__session__ = requests.Session()
        self.__session__.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        }

        self.__updater__ = telegram.ext.Updater(self.__config__['token'])
        self.__tg_bot__ = self.__updater__.bot

        self.__updater__.dispatcher.add_handler(
            telegram.ext.CallbackQueryHandler(self.__query_handler__),
        )
        self.__updater__.dispatcher.add_handler(
            telegram.ext.MessageHandler(telegram.ext.Filters.all, self.__message_handler__)
        )

        self.__tasks__: Dict[int, Task] = {}
        self.__users__: Dict[int, User] = {}

        self.__threads__: List[threading.Thread] = []

        self.__dollar_rate__ = self.__get_dollar_rate__()

        self.__db__ = Database(self.__users__, self.__tasks__, self.__root_path__)
        self.__db__.load_data()
        self.__db__.run_auto_save()

        self.__logger__ = logging.getLogger('freelansim_bot')

    def __query_handler__(self, bot, update):
        query = update.callback_query

        command, *args = query.data.split(':')

        query.answer('')

        if command == 'full':
            task_id = int(args[0])
            task = self.__tasks__.get(task_id)

            if task:
                try:
                    query.edit_message_text(
                        text=task.format_message(full=True),
                        parse_mode='Markdown',
                        disable_web_page_preview=True,
                        reply_markup=telegram.InlineKeyboardMarkup(
                            [
                                [
                                    telegram.InlineKeyboardButton('Скрыть', callback_data=f'short:{task.id}'),
                                    telegram.InlineKeyboardButton('Обновить', callback_data=f'full:{task.id}')
                                ],
                                [
                                    telegram.InlineKeyboardButton('Убрать', callback_data=f'delete:{task_id}')
                                ]
                            ]
                        )
                    )

                except telegram.error.BadRequest as error:
                    self.__log__(error)

            else:
                try:
                    query.edit_message_text(
                        text=f'Информация по заказу устарела\n\n{Static.urls["tasks"]}/{task_id}',
                        parse_mode='Markdown',
                        reply_markup=None,
                    )

                except telegram.error.BadRequest as error:
                    self.__log__(error)

        elif command == 'short':
            task_id = int(args[0])
            task = self.__tasks__.get(task_id)

            if task:
                try:
                    query.edit_message_text(
                        text=task.format_message(full=False),
                        parse_mode='Markdown',
                        disable_web_page_preview=True,
                        reply_markup=telegram.InlineKeyboardMarkup(
                            [
                                [
                                    telegram.InlineKeyboardButton('Подробнее', callback_data=f'full:{task.id}'),
                                    telegram.InlineKeyboardButton('Обновить', callback_data=f'short:{task.id}')
                                ],
                                [
                                    telegram.InlineKeyboardButton('Убрать', callback_data=f'delete:{task_id}')
                                ]
                            ]
                        )
                    )

                except telegram.error.BadRequest as error:
                    self.__log__(error)

            else:
                try:
                    query.edit_message_text(
                        text=f'Информация по заказу устарела\n\n{Static.urls["tasks"]}/{task_id}',
                        parse_mode='Markdown',
                        reply_markup=None
                    )

                except telegram.error.BadRequest as error:
                    self.__log__(error)

        elif command == 'delete':
            self.__tg_bot__.delete_message(query.message['chat']['id'], query.message['message_id'])

    def __message_handler__(self, bot, update):
        user = self.__get_user__(
            update.message.from_user.to_dict()
        )
        text = update.message.text

        print(user)

        if text.startswith('/'):
            if text == '/start':
                user.set_page('start')

            elif text == '/tasks':
                return self.__tg_bot__.send_message(
                    user.id,
                    text=Static.format_tasks_list(self.__tasks__),
                    parse_mode='Markdown',
                    disable_web_page_preview=True,
                )

            elif text == '/stats':
                return self.__tg_bot__.send_message(
                    user.id,
                    text=Static.format_stats(self.__tasks__, self.__users__),
                    parse_mode='Markdown',
                    disable_web_page_preview=True,
                )

            elif text.startswith('/start'):
                _, command = text.split()

                if command.startswith('taskId'):
                    task_id = command.split('_')[-1]

                    if not task_id.isdigit():
                        return self.__tg_bot__.send_message(
                            user.id,
                            text=f'Неккоректный заказ',
                            parse_mode='Markdown',
                            reply_markup=None,
                        )

                    task = self.__tasks__.get(int(task_id))

                    if task:
                        return self.__tg_bot__.send_message(
                            user.id,
                            task.format_message(event=True),
                            parse_mode='Markdown',
                            disable_web_page_preview=True,
                            reply_markup=telegram.InlineKeyboardMarkup(
                                [
                                    [
                                        telegram.InlineKeyboardButton('Подробнее', callback_data=f'full:{task_id}'),
                                        telegram.InlineKeyboardButton('Обновить', callback_data=f'short:{task_id}')
                                    ],
                                    [
                                        telegram.InlineKeyboardButton('Убрать', callback_data=f'delete:{task_id}')
                                    ]
                                ]
                            )
                        )

                    else:
                        return self.__tg_bot__.send_message(
                            user.id,
                            text=f'Информация по заказу устарела\n\n{Static.urls["tasks"]}/{task_id}',
                            parse_mode='Markdown',
                            reply_markup=None,
                        )

        if user.page == 'start':
            self.__tg_bot__.send_message(
                user.id,
                text=Static.strings[user.page],
                reply_markup=Static.main_menu_keyboard(user),
                parse_mode='Markdown'
            )
            user.set_page('main')

        elif user.page == 'main':
            if text == 'Список задач':
                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.format_tasks_list(self.__tasks__),
                    reply_markup=None,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )

            elif text == 'Включить уведомления':
                user.set_notifications(True)

                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings['turn_on_notifications'],
                    reply_markup=Static.main_menu_keyboard(user),
                    parse_mode='Markdown'
                )

            elif text == 'Отключить уведомления':
                user.set_notifications(False)

                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings['turn_off_notifications'],
                    reply_markup=Static.main_menu_keyboard(user),
                    parse_mode='Markdown'
                )

            elif text == 'Настройки автоответов':
                user.set_page('auto_answer')

                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings[user.page][user.auto_answer],
                    reply_markup=Static.auto_answer_keyboard(user),
                    parse_mode='Markdown'
                )

            elif text == 'Выбор категорий':
                user.set_page('choose_category')

                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings[user.page],
                    reply_markup=Static.choose_category_keyboard(user),
                    parse_mode='Markdown'
                )

            else:
                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings[user.page],
                    reply_markup=Static.main_menu_keyboard(user),
                    parse_mode='Markdown'
                )

        elif user.page == 'auto_answer':
            if text == 'Назад':
                user.set_page('main')
                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings[user.page],
                    reply_markup=Static.main_menu_keyboard(user),
                    parse_mode='Markdown'
                )

            else:
                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings[user.page][user.auto_answer],
                    reply_markup=Static.auto_answer_keyboard(user),
                    parse_mode='Markdown'
                )

        elif user.page == 'choose_category':
            if text == 'Назад':
                user.set_page('main')
                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings[user.page],
                    reply_markup=Static.main_menu_keyboard(user),
                    parse_mode='Markdown'
                )

            elif text == 'Далее':
                user.set_page('choose_subcategory')
                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings[user.page],
                    reply_markup=Static.choose_subcategory_keyboard(user),
                    parse_mode='Markdown'
                )

            elif text.startswith('●'):
                _, name = text.split()
                user.set_category(name, False)
                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings['category_off'].format(category=name),
                    reply_markup=Static.choose_category_keyboard(user),
                    parse_mode='Markdown'
                )

            elif text.startswith('○'):
                _, name = text.split()
                user.set_category(name, True)

                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings['category_on'].format(category=name),
                    reply_markup=Static.choose_category_keyboard(user),
                    parse_mode='Markdown'
                )

            else:
                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings[user.page],
                    reply_markup=Static.choose_category_keyboard(user),
                    parse_mode='Markdown'
                )

        elif user.page == 'choose_subcategory':
            if text == 'Назад':
                user.set_page('choose_category')
                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings[user.page],
                    reply_markup=Static.choose_category_keyboard(user),
                    parse_mode='Markdown'
                )

            elif text == 'Готово':
                user.set_page('main')
                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings[user.page],
                    reply_markup=Static.main_menu_keyboard(user),
                    parse_mode='Markdown'
                )

            elif text.startswith('Выбрать подкатегории'):
                name = text.split('«')[1].rstrip('»')

                if user.categories.get(name):
                    user.set_page(f'choose_sub_subcategory:{name}')

                    self.__tg_bot__.send_message(
                        user.id,
                        text=Static.strings[user.page.split(':')[0]],
                        reply_markup=Static.choose_sub_subcategory_keyboard(user),
                        parse_mode='Markdown'
                    )

            else:
                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings[user.page],
                    reply_markup=Static.choose_subcategory_keyboard(user),
                    parse_mode='Markdown'
                )

        elif user.page.startswith('choose_sub_subcategory'):
            if text == 'Готово':
                user.set_page('choose_subcategory')
                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings[user.page],
                    reply_markup=Static.choose_subcategory_keyboard(user),
                    parse_mode='Markdown'
                )

            elif text.startswith('●'):
                name = user.page.split(':')[1]
                subcategory = text.lstrip('●').strip()

                user.set_subcategory(name, subcategory, False)

                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings['subcategory_off'].format(subcategory=subcategory),
                    reply_markup=Static.choose_sub_subcategory_keyboard(user),
                    parse_mode='Markdown'
                )

            elif text.startswith('○'):
                name = user.page.split(':')[1]
                subcategory = text.lstrip('○').strip()

                user.set_subcategory(name, subcategory, True)

                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings['subcategory_on'].format(subcategory=subcategory),
                    reply_markup=Static.choose_sub_subcategory_keyboard(user),
                    parse_mode='Markdown'
                )

            else:
                self.__tg_bot__.send_message(
                    user.id,
                    text=Static.strings[user.page.split(':')[0]],
                    reply_markup=Static.choose_sub_subcategory_keyboard(user),
                    parse_mode='Markdown'
                )

    def __get_user__(self, user_data: dict):
        user_id = user_data['id']

        if user_id in self.__users__:
            user = self.__users__[user_id]
            user.update(user_data)
            return user

        user = User(user_data)
        self.__users__[user_id] = user
        return user

    def __send_event_new_task__(self, task):
        print('NEW TASK', '#', task)

        thr = threading.Thread(target=self.__event_new_task__, args=[task.id], daemon=True)
        thr.start()
        self.__threads__.append(thr)

    def __event_new_task__(self, task_id):
        task = self.__tasks__.get(task_id)
        message_text = task.format_message(event=True)
        category_name, sub_category_name = task.category_name, task.sub_category_name

        for user in self.__users_notifications_list__:
            if user.categories[category_name][sub_category_name]:
                try:
                    self.__tg_bot__.send_message(
                        user.id,
                        message_text,
                        parse_mode='Markdown',
                        disable_web_page_preview=True,
                        reply_markup=telegram.InlineKeyboardMarkup(
                            [
                                [
                                    telegram.InlineKeyboardButton('Подробнее', callback_data=f'full:{task_id}'),
                                    telegram.InlineKeyboardButton('Обновить', callback_data=f'short:{task_id}')
                                ],
                                [
                                    telegram.InlineKeyboardButton('Убрать', callback_data=f'delete:{task_id}')
                                ]
                            ]
                        )
                    )

                except telegram.error.BadRequest as error:
                    self.__log__(error)

                except telegram.error.Unauthorized as error:
                    self.__log__(error)

                    msg = str(error)
                    if 'bot was blocked by the user' in msg:
                        user.set_notifications(False)

    def get_tasks(self, page=1):
        """ Получить список задачь
        :return: :list:`Tasks`
        """

        data = self.__session__.get(
            Static.urls['tasks'],
            headers={
                'Accept': 'application/json',
            },
            params={
                'per_page': 50,
                'page': page
            },
            timeout=2,
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
        } for obj in data if obj is not None}

        data = self.__session__.get(
            Static.urls['tasks'],
            headers={
                'Accept': 'application/json',
                'X-Version': '1'
            },
            params={
                'per_page': 50,
                'page': page
            },
            timeout=2,
        ).json()['tasks']

        for task in data:
            if task is not None:
                if task['id'] in data_addition:
                    local_data = data_addition[task['id']]
                    task.update(local_data)

            task['tags'] = list(map(lambda x: x.get('name'), task['tags']))

            avatar = task['user']['avatar']
            root = Static.urls["root"]

            task['user']['avatar'] = {
                'src': f'{root}{avatar["src"]}' if avatar['src'].startswith('/assets/') else avatar['src'],
                'src2x': f'{root}{avatar["src2x"]}' if avatar['src2x'].startswith('/assets/') else avatar['src2x'],
            }

            if task['price']['type'].startswith('per'):
                task['price']['RUB'] = int(''.join(task['price']['value'].split()[:-1]))
                task['price']['USD'] = self.__convert_to_dollars__(task['price']['RUB'])
                task['price']['value_usd'] = self.__convert_to_dollars__(
                    task['price']['RUB'], beauty=True
                )
                task['price']['value'] = task['price']['value']

        return data

    def __listen__(self):
        """ Слушать сервер
        :yields: :class:`Event`
        """

        while True:
            try:
                for event in self.get_tasks():
                    yield event

            except requests.exceptions.ConnectionError:
                self.__log__('Error updating server...')

            except requests.exceptions.ReadTimeout:
                self.__log__('Read timeout with updating server...')

    def init_tasks(self, pages=10):
        """ Init load tasks"""

        self.__log__('Start loading tasks...', 'TASKS')

        for page in range(1, pages + 1):
            suffix = 'st' if page == 1 else (
                'nd' if page == 2 else (
                    'rd' if page == 3 else 'th'
                )
            )
            self.__log__(f'Loading {page}{suffix} page...', 'TASKS')
            for element in self.get_tasks(page=page):
                task = Task(element)
                self.__tasks__[task.id] = task

        self.__log__('Tasks successfully loaded!', 'TASKS')

    def telegram_polling(self):
        """ Telegram bot """
        self.__log__('Start telegram bot polling...', 'TELEGRAM')
        self.__updater__.start_polling()

    def long_polling(self):
        """ Main pool """

        self.__log__('Start main pool...')

        while True:
            try:
                for element in self.__listen__():
                    task = Task(element)

                    if task.id not in self.__tasks__:
                        if element.get('url'):
                            self.__tasks__[task.id] = task
                            self.__send_event_new_task__(task)

                    else:
                        self.__tasks__[task.id].update(task)

            except KeyboardInterrupt:
                self.__exit__()
                break

            except (Exception, BaseException):
                print(traceback.format_exc())

            self.__log__('Restart system...')

    @property
    def __users_notifications_list__(self):
        return list(map(
            lambda user_id: self.__users__[user_id],
            filter(lambda user_id: self.__users__[user_id].has_notifications, self.__users__)
        ))

    @staticmethod
    def __get_dollar_rate__():
        url = 'https://api.exchangeratesapi.io/latest'
        return requests.get(url, params={'base': 'USD'}).json()['rates']['RUB']

    def __convert_to_dollars__(self, rubles: int, beauty=False):
        if beauty:
            return '{:,}$'.format(round(rubles / self.__dollar_rate__)).replace(',', ' ')
        return rubles / self.__dollar_rate__

    def __load_config__(self, path: str):
        with open(path) as file:
            self.__config__ = json.load(file)

    def __log__(self, msg, name='BOT'):
        self.__logger__.info(f'[{name}]: {msg}')

    def __exit__(self):
        self.__log__('The final exit.')
        self.__session__.close()
        self.__updater__.stop()
        self.__db__.exit()
        exit()


if __name__ == '__main__':
    bot = FreelansimBot()
    bot.init_tasks(pages=1)
    bot.telegram_polling()
    bot.long_polling()

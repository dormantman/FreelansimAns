# -*- coding: utf-8

import telegram.ext


class Static:
    urls = {
        'root': 'https://freelansim.ru',
        'auth': 'https://freelansim.ru/users/sign_in',
        'tasks': 'https://freelansim.ru/tasks',
        'freelancers': 'https://freelansim.ru/freelancers',
        'personal': 'https://freelansim.ru/my/personal'
    }

    strings = {
        'start': '*Добро пожаловать!*\n\n'
                 'Вы можете выбрать интересующие вас категории, '
                 'также вы можете включить автоответы для заказов',

        'main': 'Вы можете выбрать интересующие вас категории, '
                'также вы можете включить автоответы для заказов',

        'turn_on_notifications': 'Уведомления о новых заказах *включены*',
        'turn_off_notifications': 'Уведомления о новых заказах *отключены*',

        'choose_category': 'Выберите категории заказов, по которым хотите получать обновления',
        'choose_subcategory': 'Вы можете выбрать подкатегории для выбранных категорий заказов',
        'choose_sub_subcategory': 'Выберите подкатегории заказов, по которым хотите получать обновления',

        'category_on': 'Вы подписались на категорию «{category}»',
        'category_off': 'Вы отписались от категории «{category}»',

        'subcategory_on': 'Вы подписались на подкатегорию «{subcategory}»',
        'subcategory_off': 'Вы отписались от подкатегории «{subcategory}»',

        'unavailable': 'Временно недоступно',

        'auto_answer': {
            True: 'Вы можете выключить автоответы в любое время',
            False: 'Вы можете включить автоответы в любое время',
        },
    }

    keyboards = {
        'start': None,
        'main': None,
    }

    @staticmethod
    def main_menu_keyboard(user):
        return telegram.ReplyKeyboardMarkup(
            [
                [telegram.KeyboardButton('Список задач'), ],
                [telegram.KeyboardButton('Выбор категорий'), ],
                # [
                #     telegram.KeyboardButton('Настройки автоответов'),
                # ],
                [
                    telegram.KeyboardButton(
                        'Включить уведомления' if not user.has_notifications else 'Отключить уведомления'
                    )
                ]
            ], resize_keyboard=True
        )

    @staticmethod
    def auto_answer_keyboard(user):
        return telegram.ReplyKeyboardMarkup(
            [
                [
                    telegram.KeyboardButton(
                        'Включить автоответы' if not user.auto_answer else 'Выключить автоответы'
                    )
                ],
                [telegram.KeyboardButton('Пример cookies данных'), ],
                [telegram.KeyboardButton('Назад'), ],
            ], resize_keyboard=True
        )

    @staticmethod
    def choose_category_keyboard(user):
        keyboards = []

        line = []
        for category in user.categories:
            icon = '●' if any(user.categories[category].values()) else '○'
            line.append(telegram.KeyboardButton(f'{icon} {category}'))

            if len(line) == 2:
                keyboards.append(line)
                line = []

        if line:
            keyboards.append(line)

        keyboards.append([
            telegram.KeyboardButton('Назад'),
            telegram.KeyboardButton('Далее')
        ])

        return telegram.ReplyKeyboardMarkup(keyboards, resize_keyboard=True)

    @staticmethod
    def choose_subcategory_keyboard(user):
        keyboards = []

        line = []
        for category in user.categories:
            if any(user.categories[category].values()):
                line.append(telegram.KeyboardButton(f'Выбрать подкатегории в «{category}»'))

            if len(line):
                keyboards.append(line)
                line = []

        if line:
            keyboards.append(line)

        keyboards.append([
            telegram.KeyboardButton('Назад'),
            telegram.KeyboardButton('Готово')
        ])

        return telegram.ReplyKeyboardMarkup(keyboards, resize_keyboard=True)

    @staticmethod
    def choose_sub_subcategory_keyboard(user):
        keyboards = []

        name = user.page.split(':')[1]

        line = []
        for subcategory in user.categories[name]:
            icon = '●' if user.categories[name][subcategory] else '○'
            line.append(telegram.KeyboardButton(f'{icon} {subcategory}'))

            if len(line) == 2:
                keyboards.append(line)
                line = []

        if line:
            keyboards.append(line)

        keyboards.append([
            telegram.KeyboardButton('Готово')
        ])

        return telegram.ReplyKeyboardMarkup(keyboards, resize_keyboard=True)

    @staticmethod
    def format_tasks_list(tasks):
        last_tasks = list(map(lambda x: tasks[x], sorted(
            tasks,
            key=lambda x: tasks[x].published_at
        )[-15:]))

        result = ''

        for task in last_tasks:
            title = task.title.replace('[', '').replace(']', '')
            price = task.format_price()
            date = 'Только что' if task.date == '0 мин.' else task.date
            result += f'*{title}*\n{price} | {date}\n' \
                      f'[Открыть](https://t.me/freelansim_robot?start=taskId_{task.id}) • ' \
                      f'[На сайте]({task.url})\n\n'

        return result

    @staticmethod
    def format_stats(tasks, users):
        users_with_notification = len(list(filter(lambda user_id: users[user_id].has_notifications, users)))

        return f'*Статистика бота*\n\n' \
               f'Загруженных задач: *{len(tasks)}*\n' \
               f'Пользователей: *{len(users)}*\n' \
               f'Подписок на уведомления: *{users_with_notification}*'

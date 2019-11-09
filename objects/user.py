# -*- coding: utf-8 -*-


class User:
    def __init__(self, user_data: dict):
        self.id = user_data['id']

        self.first_name = user_data.get('first_name')
        self.last_name = user_data.get('last_name')
        self.username = user_data.get('username')

        self.is_bot = user_data.get('is_bot')
        self.language_code = user_data.get('language_code')

        self.page = user_data.get('page') if user_data.get('page') is not None else 'start'

        self.auto_answer = bool(user_data.get('auto_answer'))
        self.has_notifications = bool(user_data.get('has_notifications'))

        self.categories = user_data.get('categories')

        if user_data.get('categories') is None:
            self.categories = {
                'Разработка': {
                    'Сайты «под ключ»': False,
                    'Бэкенд': False,
                    'Фронтенд': False,
                    'Прототипирование': False,
                    'iOS': False,
                    'Android': False,
                    'Десктопное ПО': False,
                    'Боты и парсинг данных': False,
                    'Разработка игр': False,
                    '1С-программирование': False,
                    'Скрипты и плагины': False,
                    'Разное': False,
                },
                'Тестирование': {
                    'Сайты': False,
                    'Мобайл': False,
                    'Софт': False,
                },
                'Администрирование': {
                    'Серверы': False,
                    'Компьютерные сети': False,
                    'Базы данных': False,
                    'Защита ПО и безопасность': False,
                    'Разное': False,
                },
                'Дизайн': {
                    'Сайты': False,
                    'Лендинги': False,
                    'Логотипы': False,
                    'Рисунки и иллюстрации': False,
                    'Мобильные приложения': False,
                    'Иконки': False,
                    'Полиграфия': False,
                    'Баннеры': False,
                    'Векторная графика': False,
                    'Фирменный стиль': False,
                    'Презентации': False,
                    '3D': False,
                    'Анимация': False,
                    'Обработка фото': False,
                    'Разное': False,
                },
                'Контент': {
                    'Копирайтинг': False,
                    'Рерайтинг': False,
                    'Расшифровка аудио и видео': False,
                    'Статьи и новости': False,
                    'Сценарии': False,
                    'Нейминг и слоганы': False,
                    'Редактура и корректура': False,
                    'Переводы': False,
                    'Рефераты, дипломы, курсовые': False,
                    'Техническая документация': False,
                    'Контент-менеджмент': False,
                    'Разное': False,
                },
                'Маркетинг': {
                    'SMM': False,
                    'SEO': False,
                    'Контекстная реклама': False,
                    'E-mail маркетинг': False,
                    'Исследования рынка и опросы': False,
                    'Продажи и генерация лидов': False,
                    'PR-менеджмент': False,
                    'Разное': False,
                },
                'Разное': {
                    'Аудит и аналитика': False,
                    'Консалтинг': False,
                    'Юриспруденция': False,
                    'Бухгалтерские услуги': False,
                    'Аудио': False,
                    'Видео': False,
                    'Инженерия': False,
                    'Разное': False,
                },
            }

    def set_notifications(self, sign: bool):
        self.has_notifications = sign

    def set_page(self, page: str):
        self.page = page

    def set_category(self, name: str, status: bool):
        if self.categories.get(name):
            for subcategory in self.categories[name]:
                self.categories[name][subcategory] = status

    def set_subcategory(self, name: str, subcategory: str, status: bool):
        self.categories[name][subcategory] = status

    def __repr__(self):
        return '<User %s | %s %s | %s | %s >' % (
            self.id, self.first_name, self.last_name, self.username, self.page
        )

    def update(self, user_data):
        keys = [
            'first_name', 'last_name', 'username',
            'is_bot', 'language_code',
        ]

        for key in keys:
            if getattr(self, key) != user_data.get(key):
                setattr(self, key, user_data.get(key))

    def json(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'username': self.username,
            'is_bot': self.is_bot,
            'language_code': self.language_code,
            'page': self.page,
            'has_notifications': self.has_notifications,
            'auto_answer': self.auto_answer,
            'categories': self.categories
        }

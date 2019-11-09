# -*- coding: utf-8

import datetime

from objects.static import Static


class Task:
    def __init__(self, data=None):
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
        self.url = f'{Static.urls["tasks"]}/{self.id}'
        self.task_comments_count = data.get('task_comments_count')
        self.page_views_count = data.get('page_views_count')

        if isinstance(self.published_at, str):
            self.published_at = datetime.datetime.strptime(self.published_at, '%Y-%m-%dT%H:%M:%S')

    def update(self, task):
        keys = [
            'title', 'description', 'price', 'has_responded', 'date', 'user',
            'reply_count', 'page_views_count', 'task_comments_count',
            'is_publish', 'category_name', 'sub_category_name',
            'published_at', 'tags'
        ]

        for key in keys:
            if getattr(self, key) != getattr(task, key):
                task_label = str(self)
                print(
                    'UPDATE', '#', task_label, ' ' * (120 - len(task_label)), '|', key + ':\t',
                    getattr(self, key), getattr(task, key)
                )
                setattr(self, key, getattr(task, key))

    def format_message(self, full=False, event=False):
        odds = '✅ ' if self.reply_count < 4 else (
            '❔ ' if self.reply_count < 8 else '❌ '
        )
        star = '✨ ' if self.safe_deal_only else ''
        price = self.format_price()
        date = 'Только что' if self.date == '0 мин.' else self.date

        if event:
            odds = ''

        if full:
            desc = self.format_description(2048)
            user = self.format_user()

            return f'{odds}{star}*{self.title}*\n{price} | {date}\n\n_{", ".join(self.tags)}_\n' \
                   f'{self.category_name} | {self.sub_category_name}\n' \
                   f'{self.url}\n\nПросмотров: *{self.page_views_count}* | Откликов: *{self.reply_count}* ' \
                   f'| Комментариев: *{self.task_comments_count}*\n\n{desc}\n\n{user}'

        desc = self.format_description(128)

        return f'{odds}{star}*{self.title}*\n{price} | {date}\n\n_{", ".join(self.tags)}_\n{self.url}\n\n{desc}'

    def format_price(self, markdown=True, with_dollars=True):
        value = None
        if self.price['type'] != 'none':
            if with_dollars:
                value = f'{self.price["value"]} ({self.price["value_usd"]})'
            else:
                value = f'{self.price["value"]}'

        if markdown:
            if self.price['type'] == 'per_project':
                return f'{value} за проект'
            elif self.price['type'] == 'none':
                return f'{self.price["value"]} цена'
            return f'{value} в час'

        if self.price['type'] == 'per_project':
            return f'{value} за проект'
        elif self.price['type'] == 'none':
            return f'{self.price["value"]} цена'
        return f'{value} в час'

    def format_user(self):
        rating = self.user["rating"] if self.user["rating"] else ''

        if self.user["firstname"]:
            if self.user["lastname"]:
                name = f'{self.user["firstname"]} {self.user["lastname"]}'
            else:
                name = self.user["firstname"]
        else:
            name = 'Без имени'

        return f'{name} | [{self.user["username"]}]({Static.urls["freelancers"]}/{self.user["username"]}) {rating}'

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
        ).strip()

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
            'published_at': self.published_at.strftime('%Y-%m-%dT%H:%M:%S') if self.published_at is not None else None,
            'url': self.url,
            'task_comments_count': self.task_comments_count,
            'page_views_count': self.page_views_count,
        }

    def __repr__(self):
        return '<Task %s | %s | %s >' % (self.date, self.title, self.format_price(markdown=False))

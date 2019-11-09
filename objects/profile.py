# -*- coding: utf-8 -*-

import json
import logging
import os
import traceback

import bs4
import requests

from objects.static import Static


class Profile:
    def __init__(self):
        self.cookies_path = os.path.join(os.path.split(__file__)[0], 'cookies.json')

        self.session = requests.Session()

        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        }

        self.authorized = False

        self.logger = logging.getLogger('freelansim_bot')

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

        response = self.session.get(Static.urls['personal'])
        soup = bs4.BeautifulSoup(response.content, 'lxml')

        avatar = soup.find('form', {'class': 'form_avatar'})

        if avatar:
            username = avatar.get('action').split('/')[2]
            avatar = avatar.find('img', {'class': 'avatario'}).get('src')
            if avatar.startswith('/assets/default'):
                avatar = None

            first_name = soup.find('input', {'name': 'freelancer[first_name]'}).get('value')
            last_name = soup.find('input', {'name': 'freelancer[last_name]'}).get('value')

            birth_date = [
                soup.find('select', {
                    'name': 'freelancer[birth_date(3i)]'
                }).find('option', {'selected': 'selected'}).text,
                soup.find('select', {
                    'name': 'freelancer[birth_date(2i)]'
                }).find('option', {'selected': 'selected'}).text,
                soup.find('select', {
                    'name': 'freelancer[birth_date(1i)]'
                }).find('option', {'selected': 'selected'}).text,
            ]

            location = soup.find('input', {'name': 'freelancer[location]'}).get('value')
            about = soup.find('textarea', {'name': 'freelancer[self_about]'}).text.strip()

            balance = soup.find('ul', {'class': 'menu_user-settings'}).find('span', {'class': 'count'}).text
            balance = int(balance.split()[0])

            available_responses = soup.find(
                'a', {'class': 'subscription'}
            ).find('small', {'class': 'active'}).text

            available_responses = int(available_responses.split()[1]) if available_responses != 'Не активна' else 0

            print(username, avatar)
            print(first_name, last_name)
            print(birth_date)
            print(location)
            print(about)
            print('Кредитов:', balance)
            print('Откликов:', available_responses)

            return True

        return False

    def answer(self, task, text):
        print(task)

        comment_url = f'{Static.urls["tasks"]}/{task.id}/task_comments'

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

    def log(self, msg, name='PROFILE'):
        self.logger.info(f'[{name}]: {msg}')

# -*- coding: utf-8 -*-

import json
import logging
import os
import threading
import time
from typing import Dict

from objects.task import Task
from objects.user import User


class Database:
    def __init__(self, users: Dict[int, User], tasks: Dict[int, Task], root_path: str):
        self.__routing_path__ = {
            'root': os.path.join(root_path, 'data'),
            'users': os.path.join(root_path, 'data', 'users.json'),
            'tasks': os.path.join(root_path, 'data', 'tasks.json')
        }

        self.__last_save__ = time.time()
        self.__auto_save_thread__ = None
        self.__users__ = users
        self.__tasks__ = tasks

        self.kill_flag = False

        self.logger = logging.getLogger('freelansim_bot')

        self.__folders_init__()

    def __folders_init__(self):
        if not os.access(self.__routing_path__['root'], os.F_OK):
            os.mkdir(self.__routing_path__['root'])

        if not os.access(self.__routing_path__['users'], os.F_OK):
            with open(self.__routing_path__['users'], 'w') as file:
                json.dump({}, file)

        if not os.access(self.__routing_path__['tasks'], os.F_OK):
            with open(self.__routing_path__['tasks'], 'w') as file:
                json.dump({}, file)

    def save_data(self):
        self.log('Saving data...')

        with open(self.__routing_path__['users'], encoding='utf-8', mode='w') as file:
            json.dump(self.to_json(self.__users__), file, ensure_ascii=False, indent=2)

        # with open(self.__routing_path__['tasks'], mode='w') as file:
        #     json.dump(self.to_json(self.__tasks__), file, ensure_ascii=False, indent=2)

        self.__last_save__ = time.time()

    def load_data(self):
        with open(self.__routing_path__['users'], encoding='utf-8') as file:
            try:
                data = json.load(file)
                for key in data:
                    self.__users__[int(key)] = User(data[key])
                self.log(f'Load {len(data)} users')

            except json.decoder.JSONDecodeError:
                self.log('Error loading users !')

        with open(self.__routing_path__['tasks'], encoding='utf-8') as file:
            try:
                data = json.load(file)
                for key in data:
                    self.__tasks__[int(key)] = Task(data[key])
                self.log(f'Load {len(data)} tasks')

            except json.decoder.JSONDecodeError:
                self.log('Error loading tasks !')

    def run_auto_save(self, interval: int or float = 60):
        thr = threading.Thread(target=self.__auto_save__, args=[interval], daemon=True)
        thr.start()
        self.__auto_save_thread__ = thr

    def __auto_save__(self, interval: int):
        while True:
            if self.kill_flag:
                self.log('Saving before exiting')
                break
            now = time.time()
            if (now - self.__last_save__) >= interval:
                self.save_data()
            time.sleep(0.1)

    @staticmethod
    def to_json(data: dict):
        response = {}

        for key in data.keys():
            response[str(key)] = data[key].json()

        return response

    def exit(self):
        self.kill_flag = True

    def log(self, msg, name='DATABASE'):
        self.logger.info(f'[{name}]: {msg}')

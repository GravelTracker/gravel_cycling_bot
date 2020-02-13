#!/usr/bin/env python

import os
import sys
sys.path.append('../')
from pymongo import MongoClient
from env import EnvVarSetter


class DbCleaner():
    def __init__(self):
        EnvVarSetter().set_vars()
        self.db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])
        self.event_collection = self.db_client.gravel_cycling.events
        self.bicycle_collection = self.db_client.bicycles.bicycles

    def prompt_clean_event_db(self):
        print('WARNING! This is a destructive operation that cannot be undone.')
        selection = input(
            'This will delete all scraped event data (records added by users are preserved)! Continue? y/n: ')
        if(selection.lower() != 'y'):
            return

        self.wipe_event_db()

    def wipe_event_db(self):
        print('Wiping Mongo database...')
        self.event_collection.remove({'insertion_type': 'scraped'})
        print('Finished!')

    def prompt_clean_bicycle_db(self):
        print('WARNING! This is a destructive operation that cannot be undone.')
        selection = input(
            'This will delete all scraped bicycle data! Continue? y/n: ')
        if(selection.lower() != 'y'):
            return

        self.wipe_event_db()

    def wipe_bicycle_db(self):
        print('Wiping Mongo database...')
        self.bicycle_collection.remove({})
        print('Finished!')

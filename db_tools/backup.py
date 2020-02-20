#!/usr/bin/env python

import os
import sys
import traceback
sys.path.append('../')
from pymongo import MongoClient
from env import EnvVarSetter


class BackupDB():
    def __init__(self):
        EnvVarSetter().set_vars()
        self.db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])
        master_collection = self.db_client.bicycles.bicycles
        backup_collection = self.db_client.bicycles.backup
        print('Wiping backup DB...')

        backup_collection.remove({})

        print('Finished!')

        self.backup_db(master_collection, backup_collection)

    def backup_db(self, master_collection, backup_collection):
        print('Backing up master DB...')

        try:
            records = master_collection.find({})
            for record in records:
                backup_collection.insert_one(record)
        except Exception:
            traceback.print_exc()
            return

        print('Finished!')

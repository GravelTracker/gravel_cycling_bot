#!/usr/bin/env python

import os, sys
sys.path.append('../')
from pymongo import MongoClient
from env import EnvVarSetter

class DbCleaner():
  def __init__(self):
    EnvVarSetter().set_vars()
    self.db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])
    self.event_collection = self.db_client.gravel_cycling.events

  def clean_db(self):
    selection = input('WARNING! This is a destructive operation that cannot be undone. Continue? y/n: ')
    if(selection.lower() != 'y'):
      return 

    print('Wiping Mongo database...')
    self.event_collection.remove({})
    print('Finished!')

DbCleaner().clean_db()
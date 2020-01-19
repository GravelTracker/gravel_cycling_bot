#!/usr/bin/env python

import os, pdb, praw, sys
sys.path.append('../')
from pymongo import MongoClient
from env import EnvVarSetter

class GravelCyclingBot():
  def __init__(self):
    EnvVarSetter().set_vars()
    self.reddit_instance = self.setup()

  def setup(self):
    reddit = praw.Reddit(client_id=os.environ['REDDIT_CLIENT_ID'],
                         client_secret=os.environ['REDDIT_CLIENT_SECRET'],
                         user_agent=os.environ['REDDIT_USER_AGENT'],
                         username=os.environ['REDDIT_USERNAME'],
                         password=os.environ['REDDIT_PASSWORD'])

    return reddit

  def fetch_events(self):
    db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])

  def create_post(self):
    pass

print( GravelCyclingBot().reddit_instance )
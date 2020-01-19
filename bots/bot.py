#!/usr/bin/env python

import os, pdb, praw, re, sys
sys.path.append('../')
from pymongo import MongoClient
from env import EnvVarSetter
from datetime import datetime as dt

class GravelCyclingBot():
  def __init__(self):
    EnvVarSetter().set_vars()
    self.reddit_instance = self.setup()
    self.subreddit = self.reddit_instance.subreddit(os.environ['REDDIT_SUBREDDIT'])

  def setup(self):
    reddit = praw.Reddit(client_id=os.environ['REDDIT_CLIENT_ID'],
                         client_secret=os.environ['REDDIT_CLIENT_SECRET'],
                         user_agent=os.environ['REDDIT_USER_AGENT'],
                         username=os.environ['REDDIT_USERNAME'],
                         password=os.environ['REDDIT_PASSWORD'])

    return reddit

  def fetch_events(self):
    db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])
    events = db_client.gravel_cycling.events

    return events

  def build_text(self, events):
    event_text = ''
    for event in events.find().limit(10):
      try:
        event_text += event['description']
        event_text += '\n'
      except Exception:
        pass

    newline = re.compile('\\n')
    return re.sub(newline, '\n\n', event_text)

  def create_monthly_post(self):
    title = 'Gravel Events for Month of {}'.format(dt.now().strftime('%B, %Y'))
    events = self.fetch_events()
    text = self.build_text(events)

    self.subreddit.submit(title=title,
                          selftext=text,
                          send_replies=False)

gcb = GravelCyclingBot()
gcb.create_monthly_post()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
    events    = db_client.gravel_cycling.events

    return events

  def build_text(self, events):
    na_events     = []
    eu_events     = []
    aus_events    = []
    events_header = 'Date | Title | Location | Link\n----|-----|-----|----'
    na_matcher    = re.compile('(US)|(USA)|(United States)')
    aus_matcher   = re.compile('(Australia)|(New Zealand)')
    today         = dt.today()
    start_date    = dt(year=today.year, month=today.month, day=1)
    end_month     = 1 if today.month + 1 == 13 else today.month + 1
    end_year      = today.year + 1 if end_month == 1 else today.year
    end_date      = dt(year=end_year, month=end_month, day=1)
    query         = { 
                      'start_time': {
                        '$gte': start_date,
                        '$lt': end_date 
                      } 
                    }

    for event in events.find(query):
      event_dict = [
        event['start_time'].strftime('%m/%d/%Y'),
        event['summary'].split(' – ')[0],
        event['summary'].split(' – ')[1],
        '[Link](%s)' % event['url']
      ]
      
      event_line = ' | '.join(event_dict)

      if (re.search(na_matcher, event['location'])):
        na_events.append(event_line)
      elif (re.search(aus_matcher, event['location'])):
        aus_events.append(event_line)
      else:
        eu_events.append(event_line)

    na_line  = '#North American\n\n%s\n%s\n' % (events_header, '\n'.join(na_events))
    eu_line  = '#European\n\n%s\n%s\n' % (events_header, '\n'.join(eu_events))
    aus_line = '#Australia / New Zealand\n\n%s\n%s\n' % (events_header, '\n'.join(aus_events))

    event_text = na_line + eu_line + aus_line
    return event_text

  def create_monthly_post(self):
    title  =  'Gravel Events for Month of {}'.format(dt.now().strftime('%B, %Y'))
    events =  self.fetch_events()
    text   =  self.build_text(events)
    text   += self.bot_message()

    return self.subreddit.submit(title=title,
                                 selftext=text,
                                 send_replies=False)

  def bot_message(self):
    spaces  = '\n\n&nbsp;\n\n&nbsp;\n\n'
    message = ("*Hi. I'm a bot to help with things around [/r/gravelcycling](https://www.reddit.com/r/gravelcycling). "
               "If I seem broken or do anything stupid, send [/u/pawptart](https://www.reddit.com/message/compose?to="
               "pawptart&subject=gravelcyclingbot&message=1) a PM and let him know to fix me!*")

    return spaces + message

  def get_bottom_sticky(self):
    try:
      return self.subreddit.sticky(2)
    except:
      return None

  def unsticky(self, post):
    self.reddit_instance.submission(id=post.id).mod.sticky(state=False)

  def sticky(self, post):
    self.reddit_instance.submission(id=post.id).mod.sticky(state=True, bottom=True)

  def update_monthly_post(self):
    sticky2_id = self.get_bottom_sticky()
    post = self.create_monthly_post()
    
    if (sticky2_id != None):
      self.unsticky(sticky2_id)

    self.sticky(post)
    
gcb = GravelCyclingBot()
gcb.update_monthly_post()
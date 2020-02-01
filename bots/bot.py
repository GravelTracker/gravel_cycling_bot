#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, pdb, praw, re, requests, sys
sys.path.append('../')
from pymongo import MongoClient
from db_tools.cleaner import DbCleaner
from scrapers.gravelcyclist import Scraper as GCScraper
from env import EnvVarSetter
from datetime import datetime as dt, timezone
from time import sleep

class GravelCyclingBot():
  def __init__(self):
    EnvVarSetter().set_vars()
    self.reddit_instance = self.setup()
    self.subreddit = self.reddit_instance.subreddit(os.environ['REDDIT_SUBREDDIT'])
    self.last_updated = self.get_last_post_date()

  def setup(self):
    reddit = praw.Reddit(client_id=os.environ['REDDIT_CLIENT_ID'],
                         client_secret=os.environ['REDDIT_CLIENT_SECRET'],
                         user_agent=os.environ['REDDIT_USER_AGENT'],
                         username=os.environ['REDDIT_USERNAME'],
                         password=os.environ['REDDIT_PASSWORD'])

    return reddit
  
  def get_last_post_date(self):
    last_post = self.get_bottom_sticky()
    last_post_date = self.reddit_instance.submission(id=last_post.id).created_utc if last_post else 0
    return dt.utcfromtimestamp(last_post_date)

  def fetch_events(self):
    db_client   = MongoClient(os.environ['MONGO_CONNECT_URL'])
    events      = db_client.gravel_cycling.events
    today       = dt.now(timezone.utc)
    start_date  = dt(year=today.year, month=today.month, day=1)
    end_month   = 1 if today.month + 1 == 13 else today.month + 1
    end_year    = today.year + 1 if end_month == 1 else today.year
    end_date    = dt(year=end_year, month=end_month, day=1)
    query       = { 
                    'start_time': {
                      '$gte': start_date,
                      '$lt': end_date 
                    },
                    'active': True
                  }

    return events.find(query)

  def build_text(self, events):
    na_events     = []
    eu_events     = []
    aus_events    = []
    events_header = 'Date | Title | Location | Link\n----|-----|-----|----'
    na_matcher    = re.compile('(US)|(USA)|(United States)')
    aus_matcher   = re.compile('(Australia)|(New Zealand)')
    events        = self.fetch_events()

    for event in events:
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
    title  =  'Gravel Events for Month of {}'.format(dt.now(timezone.utc).strftime('%B, %Y'))
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

  def post_monthly_post(self):
    print('Posting to /r/gravelcycling!')
    sticky2_id = self.get_bottom_sticky()
    post = self.create_monthly_post()
    
    if (sticky2_id != None):
      self.unsticky(sticky2_id)

    self.sticky(post)
    print('Finished!')

  def send_status(self, status_code):
    payload = {
      'token': os.environ['GRAVEL_TRACKER_API_KEY'],
      'post_time': str(dt.now(timezone.utc)),
      'status_code': status_code
    }

    print('Pinging status update -- {}...'.format(status_code))
    requests.post(os.environ['GRAVEL_TRACKER_APP_URL'], json = payload)
    print('Finished!')

  def run(self):
    # if dt.now(timezone.utc).month != self.last_updated.month:
    #   self.last_updated = dt.now(timezone.utc)
    #   DbCleaner().wipe_db()
    #   GCScraper().scrape()
    self.post_monthly_post()

    self.send_status('success')
    sleep(900)

gcb = GravelCyclingBot()

if __name__ == '__main__':
  while True:
    try:
      gcb.run()
    except KeyboardInterrupt:
      gcb.send_status('offline')
      break
    except Exception:
      gcb.send_status('error')
      break
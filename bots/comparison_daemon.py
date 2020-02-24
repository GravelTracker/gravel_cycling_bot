#!/usr/bin/env python

import os
import pdb
import praw
import re
import sys
import traceback
from pymongo import MongoClient
from datetime import datetime as dt
sys.path.append('../')
from env import EnvVarSetter as e


class ComparisonDaemon():
    def __init__(self):
        self.reddit = self.setup()
        self.subreddit = self.reddit.subreddit(
            os.environ['REDDIT_SUBREDDIT'])
        self.db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])
        print('Running!')

    def setup(self):
        reddit = praw.Reddit(client_id=os.environ['REDDIT_CLIENT_ID'],
                             client_secret=os.environ['REDDIT_CLIENT_SECRET'],
                             user_agent=os.environ['REDDIT_USER_AGENT'],
                             username=os.environ['REDDIT_USERNAME'],
                             password=os.environ['REDDIT_PASSWORD'])

        return reddit

    def make_ngrams(self, word, min_size=3):
        length = len(word)
        size_range = range(min_size, max(length, min_size) + 1)
        return list(set(
            word[i:i + size]
            for size in size_range
            for i in range(0, max(0, length - size) + 1)
        ))

    def parse_comparison(self, text):
        return [bike.strip() for bike in re.sub('!compare', '', text).split(':')]

    def fetch_bike_id(self, bike):
        search_results = self.db_client.bicycles.bicycles.search.find(
            {
                '$text': {
                    '$search': bike
                }
            },
            {
                'bike_name': True,
                'bike_id': True,
                'score': {
                    '$meta': 'textScore'
                }
            }
        )
        sorted_results = search_results.sort([('score', {'$meta': 'textScore'})])
        bike_details = sorted_results[0]

        return None if bike_details == None else bike_details['bike_id']

    def run(self):
        new_comments = self.subreddit.stream.comments(skip_existing=True)
        for comment in new_comments:
            if '!compare' in comment.body:

                print('New mention! Posting a notification...')

                try:
                    bike1, bike2 = self.parse_comparison(comment.body)
                    self.db_client.gravel_cycling.notifications.insert_one({
                        'updated_at': dt.now(),
                        'type': 'comparison',
                        'post_id': comment.id,
                        'author': comment.author.name,
                        'bike_1': bike1,
                        'bike_1_id': self.fetch_bike_id(bike1),
                        'bike_2': bike2,
                        'bike_2_id': self.fetch_bike_id(bike2)
                    })
                    print('Finished!')
                except Exception:
                    print('Failed!')
                    traceback.print_exc()
                    continue

if __name__ == '__main__':
    e().set_vars()
    print('Starting comparison daemon...')
    while True:
        try:
            ComparisonDaemon().run()
        except KeyboardInterrupt:
            print('Shutting down daemon...')
            break
        except Exception:
            traceback.print_exc()
            break
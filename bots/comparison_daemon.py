#!/usr/bin/env python

import os
import pdb
import praw
import re
import sys
import traceback
from pymongo import MongoClient
from datetime import datetime as dt


class ComparisonDaemon():
    def __init__(self):
        self.reddit = self.setup()
        self.subreddit = self.reddit.subreddit(
            os.environ['REDDIT_SUBREDDIT'])
        self.db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])

    def setup(self):
        reddit = praw.Reddit(client_id=os.environ['REDDIT_CLIENT_ID'],
                             client_secret=os.environ['REDDIT_CLIENT_SECRET'],
                             user_agent=os.environ['REDDIT_USER_AGENT'],
                             username=os.environ['REDDIT_USERNAME'],
                             password=os.environ['REDDIT_PASSWORD'])

        return reddit

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
                        'bike_2': bike2
                    })
                    print('Finished!')
                except Exception:
                    print('Failed!')
                    traceback.print_exc()
                    continue

    def parse_comparison(self, text):
        return [bike.strip() for bike in re.sub('!compare', '', text).split(':')]

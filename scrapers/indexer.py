#!/usr/bin/env python

import os
import pdb
from pymongo import MongoClient


class BikeIndexer():
    def __init__(self):
        self.db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])

    def index_bikes_for_search(self):
        print('Deleting old search index...')

        self.db_client.bicycles.bicycles.search.remove({})

        print('Finished!')
        print('Building new search index...')

        bikes_list = self.db_client.bicycles.bicycles.find({})

        for bike in bikes_list:
            self.index_bike_name_for_search(bike)

        print('Finished!')

    def index_bike_name_for_search(self, bike):
        self.db_client.bicycles.bicycles.search.update(
            {
                'bike_id': bike['_id'],
                'bike_name': bike['name']
            },
            {
                '$set': {
                    'bike_id': bike['_id'],
                    'ngrams': ' '.join(
                        self.make_ngrams(bike['name'].lower())
                    ),
                },
            },
            upsert=True
        )

        self.db_client.bicycles.bicycles.search.create_index(
            [
                ("ngrams", "text"),
            ],
            name="search_bike_ngrams",
            weights={
                "ngrams": 100,
            }
        )

    def make_ngrams(self, word, min_size=3):
        length = len(word)
        size_range = range(min_size, max(length, min_size) + 1)
        return list(set(
            word[i:i + size]
            for size in size_range
            for i in range(0, max(0, length - size) + 1)
        ))

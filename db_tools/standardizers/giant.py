#!/usr/bin/env python

import copy
import os
import pdb
import re
import sys
import traceback
sys.path.append('../..')
from pymongo import MongoClient
from datetime import datetime


class GiantStandardizer():
    def __init__(self):
        self.db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])
        self.collection = self.db_client.bicycles.bicycles
        query = {
            'manufacturer': {
                '$in': ['Giant', 'Liv']
            }
        }
        self.bikes = self.collection.find(query)

    def standardize_records(self):
        print('Attempting to standardize Giant/Liv records...')
        errors_count = 0
        for bike in self.bikes:
            new_record = self.standardize(bike)
            if new_record == None:
                errors_count += 1

            object_id = bike['_id']
            self.collection.find_one_and_replace(
                {'_id': object_id}, new_record)
        print('Completed with {} errors.'.format(errors_count))

    def standardize(self, bike):
        try:
            new_record = copy.deepcopy(bike)

            for field in bike:
                value = new_record.pop(field)

                if value == 'N/A':
                    continue

                if self.no_standardization(field):
                    new_record[field] = value
                    continue

                if field in ['rims', 'spokes', 'hubs']:
                    if 'wheels' in new_record.keys():
                        new_record['wheels'] += ', ' + value
                    else:
                        new_record['wheels'] = value
                    continue

                if field in ['brakes', 'tires']:
                    new_record[self.singularize(field)] = value
                    continue

                if field == 'crankset':
                    field = 'crank'

                if not self.can_be_deleted(field):
                    new_record[field] = value
        except Exception:
            traceback.print_exc()
            return

        return new_record

    def no_standardization(self, field):
        return field not in [
            'rims',
            'hubs',
            'spokes',
            'brake_levers',
            'crankset',
            'pedals',
            'brakes',
            'tires'
        ]

    def can_be_deleted(self, field):
        return field in ['brake_levers']

    def singularize(self, field):
        return field[:-1]

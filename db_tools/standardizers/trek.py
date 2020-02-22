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


class TrekStandardizer():
    def __init__(self):
        self.db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])
        self.collection = self.db_client.bicycles.bicycles
        query = {
            'manufacturer': {
                '$in': ['Trek']
            }
        }
        self.bikes = self.collection.find(query)

    def standardize_records(self):
        print('Attempting to standardize Trek records...')
        errors_count = 0
        error_ids = []
        for bike in self.bikes:
            new_record = self.standardize(bike)
            if new_record == None:
                errors_count += 1
                error_ids.append(bike['_id'])
                continue

            object_id = bike['_id']
            self.collection.find_one_and_replace(
                {'_id': object_id}, new_record)
        print('Completed with {} errors.'.format(errors_count))
        for error in error_ids:
            print(error)

    def standardize(self, bike):
        try:
            new_record = copy.deepcopy(bike)

            for field in bike:
                value = new_record.pop(field)

                if field in ['front_wheel', 'rear_wheel', 'rim', 'spokes', 'front_hub', 'rear_hub']:
                    if 'wheels' in new_record.keys():
                        if isinstance(value, list):
                            value = value[0]['details']
                        new_record['wheels'] += ', ' + value
                    else:
                        new_record['wheels'] = value
                    continue

                if not self.can_be_deleted(field):
                    new_record[field] = value
        except Exception:
            traceback.print_exc()
            pdb.set_trace()
            return None

        return new_record

    def can_be_deleted(self, field):
        return field in ['bag', 'handlebar_tape']

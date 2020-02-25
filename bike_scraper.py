#!/usr/bin/env python

import traceback
from env import EnvVarSetter
from scrapers.trek import TrekScraper
from scrapers.giant import GiantScraper
from scrapers.liv import LivScraper
from scrapers.indexer import BikeIndexer
from db_tools.cleaner import DbCleaner
from db_tools.backup import BackupDB
from standardizer import Standardizer

class BikeScraper():
    def scrape(self):
        # DbCleaner().wipe_bicycle_db()
        # GiantScraper().scrape()
        # LivScraper().scrape()
        # TrekScraper().scrape()
        # BikeIndexer().index_bikes_for_search()
        # BackupDB()
        Standardizer().standardize_records()

if __name__ == '__main__':
    try:
        EnvVarSetter().set_vars()
        BikeScraper().scrape()
    except Exception:
        traceback.print_exc()

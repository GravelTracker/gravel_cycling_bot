#!/usr/bin/env python

import traceback
from env import EnvVarSetter
from scrapers.trek import TrekScraper
from scrapers.giant import GiantScraper
from scrapers.liv import LivScraper
from db_tools.cleaner import DbCleaner

if __name__ == '__main__':
    try:
        EnvVarSetter().set_vars()
        DbCleaner().wipe_bicycle_db()
        GiantScraper().scrape()
        LivScraper().scrape()
        TrekScraper().scrape()
    except Exception:
        traceback.print_exc()

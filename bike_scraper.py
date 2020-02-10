#!/usr/bin/env python

import traceback
from env import EnvVarSetter
from scrapers.trek import Scraper as TrekScraper

if __name__ == '__main__':
    try:
        EnvVarSetter().set_vars()
        TrekScraper().scrape()
    except Exception:
        traceback.print_exc()

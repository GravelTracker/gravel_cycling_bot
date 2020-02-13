#!/usr/bin/env python

import traceback
from env import EnvVarSetter
from scrapers.gravelcyclist import GCScraper

if __name__ == '__main__':
    try:
        EnvVarSetter().set_vars()
        GCScraper().scrape()
    except Exception:
        traceback.print_exc()

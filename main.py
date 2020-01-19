#!/usr/bin/env python

from env import EnvVarSetter
from scrapers.gravelcyclist import Scraper

EnvVarSetter().set_vars()
Scraper().scrape()
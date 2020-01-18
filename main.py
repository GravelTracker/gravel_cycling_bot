#!/usr/bin/env python

from sites import VarSetter
from scrapers.gravelcyclist import Scraper

VarSetter.set_vars()
Scraper.scrape()
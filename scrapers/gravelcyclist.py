#!/usr/bin/env python

import requests, os
from bs4 import BeautifulSoup

class Scraper():
  def scrape():
    response = requests.get(os.environ['GRAVEL_CYCLIST_URL'])
    parser = BeautifulSoup(response.content, "lxml-xml")

    results = parser.find_all('description')
    print(results)
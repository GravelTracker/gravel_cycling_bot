#!/usr/bin/env python

import requests, os, pdb, re, sys
from bs4 import BeautifulSoup as bs
sys.path.append('../')
from pymongo import MongoClient
from datetime import datetime

class Scraper():
  def scrape(self):
    print('Downloading Trek bike details... ')

    category_link = self.fetch_bike_category_link()
    bike_links = self.fetch_bike_links(category_link)
    bike_details = [ self.fetch_bike_details(link) for link in bike_links ]

    print('Finished!')
    print('Parsing data and uploading to MongoDB... ')

    db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])
    for bike in bike_details:
      self.upload_bike(bike, db_client)

    print('Finished!')

  def fetch_bike_category_link(self):
    response = requests.get(self.url(), headers=self.headers())
    parser = bs(response.content, 'lxml-html')
    gravel_bike_link = parser.find('a', id='gravelBikesLink')['href']
    return self.url() + gravel_bike_link

  def url(self):
    return os.environ['TREK_URL']

  def headers(self):
    headers = { 
      'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }

    return headers

  def fetch_bike_links(self, category_link):
    response = requests.get(category_link, headers=self.headers())
    parser = bs(response.content, 'lxml-html')
    product_tiles = parser.find_all('article', class_='product-tile')
    links = self.parse_product_tiles(product_tiles)

    return links

  def parse_product_tiles(self, tiles):
    links = []
    for tile in tiles:
      link_object = tile.find('a', class_='product-tile__link')
      if link_object == None:
        continue
      link = link_object['href']

      links.append(self.url() + link)

    return links

  def fetch_bike_details(self, bike_link):
    response = requests.get(bike_link, headers=self.headers())
    parser = bs(response.content, 'lxml-html')
    
    return self.build_bike_details(parser)

  def build_bike_details(self, parser):
    spec_tables = parser.find_all('table', class_='sprocket__table spec')

    try:
      bike_details_object = {
        'name': parser.find('h1', class_='buying-zone__title').text
      }

      header = ''

      for table in spec_tables:
        if table.text == None:
          continue

        for row in table.find_all('tr'):
          header = header if row.th == None else re.sub(r'\*', '', row.th.text).lower()
          raw_spec = row.td.text
          sanitized_spec = self.strip_whitespace(raw_spec)
          spec = self.build_spec_object(sanitized_spec)

          if header in bike_details_object:
            existing_value = bike_details_object[header]
            bike_details_object[header] = self.build_spec_array(existing_value, spec)
          else:
            bike_details_object[header] = spec

    except Exception:
      bike_details_object = None
    
    return bike_details_object

  def strip_whitespace(self, text):
    string = [ line.strip() for line in text.split('\n') ]

    return ' '.join(string).strip()

  def build_spec_object(self, spec):
    size_matcher = re.compile(r'Size:\s([0-98]{2}(,\s)?)+')
    match_object = re.search(size_matcher, spec)

    if match_object == None:
      return spec

    match = re.sub('Size: ', '', match_object[0])
    sizes = [ int(size) for size in match.split(', ') ]

    spec_object = {
      'sizes': sizes,
      'details': re.sub(size_matcher, '', spec)
    }

    return spec_object

  def build_spec_array(self, value, spec):
    if isinstance(value, list):
      value.append(spec)
      return value

    return [value, spec]

  def upload_bike(self, bike, db_client):
    if bike == None:
      return

    db_client.bicycles.bicycles.insert_one(bike)
    
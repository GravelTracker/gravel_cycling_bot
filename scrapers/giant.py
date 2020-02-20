#!/usr/bin/env python

import requests
import os
import pdb
import re
import sys
import traceback
from bs4 import BeautifulSoup as bs
sys.path.append('../')
from pymongo import MongoClient
from datetime import datetime


class GiantScraper():
    def scrape(self):
        print('Downloading Giant bike details... ')

        bike_links = self.fetch_bike_links()
        bike_details = [self.fetch_bike_details(link) for link in bike_links]

        print('Finished!')
        print('Parsing data and uploading to MongoDB... ')

        db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])
        for bike in bike_details:
            self.upload_bike(bike, db_client)

        print('Finished!')

    def url(self):
        return os.environ['GIANT_URL']

    def country(self):
        return 'us/'

    def headers(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
        }

        return headers

    def fetch_bike_links(self):
        response = requests.get(
            self.url() + self.country(), headers=self.headers())
        parser = bs(response.content, 'lxml-html')
        bike_menu = parser.find('div', id='megamenubikes')
        links = [item.a['href']
                 for item in bike_menu.find_all('li', class_='showall')]

        bike_links = []
        for link in links:
            model_list_response = requests.get(self.url() + link)
            parser = bs(model_list_response.content, 'lxml-html')
            product_tiles = parser.find_all('div', class_='tile-inner')

            bike_links.extend(self.parse_product_tiles(product_tiles))

        return bike_links

    def parse_product_tiles(self, tiles):
        links = []
        for tile in tiles:
            link = tile.find('a')['href']

            links.append(self.url() + link)

        bike_links = []
        for link in links:
            response = requests.get(link, headers=self.headers())
            parser = bs(response.content, 'lxml-html')
            bike_tiles = parser.find_all('article', class_='aos-item')

            for bike in bike_tiles:
                link = bike.find('a')['href']
                bike_links.append(self.url() + link)

        return bike_links

    def fetch_bike_details(self, bike_link):
        response = requests.get(bike_link, headers=self.headers())
        parser = bs(response.content, 'lxml-html')

        return self.build_bike_details(parser, bike_link)

    def build_bike_details(self, parser, link):
        try:
            if self.frameset_or_not_current_year(parser):
                return None

            spec_tables = parser.find_all('table', class_='specifications')
            geometry_table = parser.find('table', class_='geometry')

            bike_details_object = {
                'name': parser.find('div', id='text').h1.text,
                'manufacturer': 'Giant',
                'link': link,
                'model_year': int(parser.find('h4', class_='modelyear').text),
                'msrp': self.parse_money(parser.find('div', class_='price').p.text),
                'updated_at': datetime.utcnow()
            }

            for table in spec_tables:
                for spec in table.find_all('tr'):
                    spec_name, spec_value = self.build_spec_object(spec)

                    if spec_name == None or spec_value == None:
                        continue

                    bike_details_object[self.snake_case(
                        spec_name)] = spec_value

            try:
                geo_headers = geometry_table.find(
                    'tr', class_='heading').find_all('th')
                geo_rows = geometry_table.tbody.find_all('tr')

                size_object = self.build_size_object(geo_headers, geo_rows)
                bike_details_object['sizes'] = []
                for size in size_object:
                    bike_details_object['sizes'].append(size)
            except Exception:
                return bike_details_object

        except:
            traceback.print_exc()
            bike_details_object = None

        return bike_details_object

    def build_spec_object(self, spec):
        spec_name = spec.th.text.lower()
        spec_value = spec.td.text

        if spec_name in ['weight', 'sizes', 'colors']:
            return [None, None]

        return [spec_name, spec_value]

    def build_size_object(self, headers, rows):
        size_object = []
        for i in range(2, len(headers)):
            size_details = {}
            size_details['frame_size'] = headers[i].text

            for row in rows:
                raw_name = row.find('td', class_='name').text
                name = self.snake_case(raw_name)
                value = self.find_value(row, i)
                size_details[name] = self.convert_mm_to_cm(value, name)

            size_object.append(size_details)

        return size_object

    def parse_money(self, text):
        first_value = text.split(' - ')[0]
        money = float(re.sub(r'[\$\,]', '', first_value))

        return money

    def snake_case(self, text):
        text = self.remove_parens(text)
        return '_'.join(text.lower().strip().split(' '))

    def remove_parens(self, text):
        stripped_text = re.sub(r'\(.*?\)', '', text)

        return stripped_text

    def find_value(self, item, iterator):
        try:
            return item.find_all('td')[iterator].find('span', class_='value-mm').text
        except Exception:
            return item.find_all('td')[iterator].text

    def convert_mm_to_cm(self, value, name):
        ignore = ['crank_length', 'stem_length']

        if re.search(r'^[0-9]+\.?[0-9]+?$', value) and name not in ignore:
            return float(value) / 10

        return value

    def frameset_or_not_current_year(self, parser):
        try:
            model_year = int(parser.find('h4', class_='modelyear').text)
            model_name = parser.find('div', id='text').h1.text

            return model_year != 2020 or ('frameset' in model_name.lower())
        except Exception:
            traceback.print_exc()
            return True

    def upload_bike(self, bike, db_client):
        if bike == None:
            return

        db_client.bicycles.bicycles.insert_one(bike)

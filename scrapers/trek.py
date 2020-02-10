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


class Scraper():
    def scrape(self):
        print('Downloading Trek bike details... ')

        bike_links = self.fetch_bike_links()
        bike_details = [self.fetch_bike_details(link) for link in bike_links]

        print('Finished!')
        print('Parsing data and uploading to MongoDB... ')

        db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])
        for bike in bike_details:
            self.upload_bike(bike, db_client)

        print('Finished!')

    def url(self):
        return os.environ['TREK_URL']

    def headers(self):
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
        }

        return headers

    def fetch_bike_links(self):
        last_body = bs('', 'lxml-html')
        i = 0
        links = []
        while last_body.find('body', 'page-notFound') == None:
            query = 'bikes/c/B100/?q=%3Arelevance&page={}&pageSize=72'.format(
                str(i))
            response = requests.get(self.url() + query, headers=self.headers())
            parser = bs(response.content, 'lxml-html')
            product_tiles = parser.find_all('article', class_='product-tile')
            links.extend(self.parse_product_tiles(product_tiles))
            last_body = parser
            i += 1

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

        return self.build_bike_details(parser, bike_link)

    def build_bike_details(self, parser, link):
        sprocket_table = parser.find_all(
            'table', class_='sprocket__table spec')
        ul_table = parser.find(
            'section', id='trekProductSpecificationsComponent')

        if sprocket_table:
            spec_tables = sprocket_table
            build_spec_tables = self.build_new_spec_tables
        elif ul_table:
            spec_tables = ul_table
            build_spec_tables = self.build_old_spec_tables
        else:
            return None

        size_table = parser.find('table', id='sizing-table')

        try:
            if self.frameset_or_not_current_year(parser):
                return None

            bike_details_object = {
                'name': parser.find('h1', class_='buying-zone__title').text,
                'link': link,
                'model_year': parser.find('span', class_='buying-zone__model-year').text,
                'msrp': self.parse_money(parser.find('span', class_='actual-price').text),
                'updated_at': datetime.utcnow()
            }

            bike_details_object = build_spec_tables(
                bike_details_object, spec_tables)

            size_headers = [self.build_header(
                header.text) for header in size_table.find_all('th')]
            size_body = size_table.find('tbody', class_='sizing-table__body')
            size_rows = size_body.find_all(
                'tr', class_='sizing-table__body-row')

            rows = []
            for row in size_rows:
                row_object = {}
                for i, data in enumerate(row.find_all('td')):
                    data = data.text
                    header = size_headers[i]
                    row_object[header] = data

                rows.append(row_object)

            bike_details_object['sizes'] = rows

        except Exception:
            traceback.print_exc()
            bike_details_object = None

        return bike_details_object

    def strip_whitespace(self, text):
        string = [line.strip() for line in text.split('\n')]

        return ' '.join(string).strip()

    def build_spec_object(self, spec):
        size_matcher = re.compile(r'Size:\s([0-98]{2}(,\s)?)+')
        match_object = re.search(size_matcher, spec)

        if match_object == None:
            return spec

        match = re.sub('Size: ', '', match_object[0])
        sizes = [int(size) for size in match.split(', ')]

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

    def frameset_or_not_current_year(self, parser):
        try:
            model_year = parser.find(
                'span', class_='buying-zone__model-year').text
            model_name = parser.find('h1', class_='buying-zone__title').text

            return model_year != '2020' or ('frameset' in model_name.lower())
        except Exception:
            traceback.print_exc()
            return True

    def build_header(self, text):
        raw_header = self.strip_whitespace(text)
        dash_matcher = re.compile(r'[A-Z] — ')
        header = re.sub(dash_matcher, '', raw_header)
        header = self.snake_case(header)

        if header in self.header_override():
            header = self.header_override()[header]

        return header

    def header_override(self):
        overrider = {
            'frame_size_number': 'frame_size',
            'saddle_rail_height_minimum_(w/short_mast)': 'minimum_saddle_height',
            'saddle_rail_height_maximum_(w/tall_mast)': 'maximum_saddle_height'
        }

        return overrider

    def snake_case(self, text):
        return '_'.join(text.lower().split(' '))

    def parse_money(self, text):
        first_value = text.split(' - ')[0]
        money = float(re.sub(r'[\$\,]', '', first_value))

        return money

    def upload_bike(self, bike, db_client):
        if bike == None:
            return

        db_client.bicycles.bicycles.insert_one(bike)

    def build_new_spec_tables(self, bike_details_object, spec_tables):
        for table in spec_tables:
            if table.text == None:
                continue

            header = ''
            for row in table.find_all('tr'):
                header = header if row.th == None else self.snake_case(
                    re.sub(r'\*', '', row.th.text))
                raw_spec = row.td.text
                sanitized_spec = self.strip_whitespace(raw_spec)
                spec = self.build_spec_object(sanitized_spec)

                if header in bike_details_object:
                    existing_value = bike_details_object[header]
                    bike_details_object[header] = self.build_spec_array(
                        existing_value, spec)
                else:
                    bike_details_object[header] = spec

        return bike_details_object

    def build_old_spec_tables(self, bike_details_object, spec_tables):
        rows = spec_tables.find_all('dl', class_='details-list__item')
        header = ''

        for row in rows:
            if row.text == None:
                continue

            row_header = row.find('dt', class_='details-list__title')
            if row_header == None:
                header = header
            else:
                raw_header = self.strip_whitespace(row_header.text)
                header = self.snake_case(re.sub(r'\*', '', raw_header))

            if header == 'weight' or header == 'weight_limit':
                continue

            raw_spec = row.find('dd', class_='details-list__definition').text
            sanitized_spec = self.strip_whitespace(raw_spec)
            spec = self.build_spec_object(sanitized_spec)

            if header in bike_details_object:
                existing_value = bike_details_object[header]
                bike_details_object[header] = self.build_spec_array(
                    existing_value, spec)
            else:
                bike_details_object[header] = spec

        return bike_details_object

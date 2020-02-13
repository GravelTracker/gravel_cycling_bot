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
        # print('Downloading Giant bike details... ')

        bike_links = self.fetch_bike_links()
        bike_details = [self.fetch_bike_details(link) for link in bike_links]

        # print('Finished!')
        # print('Parsing data and uploading to MongoDB... ')

        # db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])
        # for bike in bike_details:
        #     self.upload_bike(bike, db_client)

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

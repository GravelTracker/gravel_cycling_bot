#!/usr/bin/env python

import requests, os, pdb, re, sys, traceback
from bs4 import BeautifulSoup as bs
sys.path.append('../')
from pymongo import MongoClient
from datetime import datetime

class Scraper():
  def scrape(self):
    print('Downloading event details... ')
    response = requests.get(os.environ['GRAVEL_CYCLIST_URL'])
    parser = bs(response.content, "lxml-xml")

    events = parser.find_all('vevent')
    clean = re.compile('<.*?>')
    url_matcher = re.compile('https?:(.*?);')

    db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])

    print('Parsing data and uploading to MongoDB... ')
    success_count = 0
    error_count = 0
    for event in events:
      properties = event.properties
      
      try:
        updated = properties.dtstamp.find('date-time').text.strip()
        summary = properties.summary.text.strip()
        description = re.sub(clean, '', properties.description.text.strip())
        start_time_unparsed = properties.dtstart.find('date-time').text.strip()
        end_time_unparsed = properties.dtend.find('date-time').text.strip()
        tz = properties.dtstart.parameters.tzid.text.strip()
        contact = properties.contact.text.strip()
        location = properties.location.text.strip()
        url = properties.url.uri.text.strip()
        thumbnail = re.sub(';', '', re.search(url_matcher, properties.find('x-wp-images-url').unknown.text.strip()).group())

        start_time = datetime.strptime(start_time_unparsed,"%Y-%m-%dT%H:%M:%S")
        end_time = datetime.strptime(end_time_unparsed,"%Y-%m-%dT%H:%M:%S")

        event_object = {
        "updated": updated,
        "summary": summary,
        "description": description,
        "start_time": start_time,
        "end_time": end_time,
        "time_zone": tz,
        "location": location,
        "url": url,
        "contact": contact,
        "thumbnail_url": thumbnail,
        "insertion_type": "scraped",
        "active": True
        }

        db_client.gravel_cycling.events.insert_one(event_object)
        success_count += 1
      except Exception:
        error_count += 1
        print('Error in record #{}, see traceback below:'.format(error_count + success_count))
        traceback.print_exc()
        pass
      
    print('Successfully uploaded {} event records with {} errors.'.format(success_count, error_count))

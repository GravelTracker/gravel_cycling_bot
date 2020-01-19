#!/usr/bin/env python

import requests, os, pdb, re
from bs4 import BeautifulSoup as bs
from pymongo import MongoClient

class Scraper():
  def scrape(self):
    response = requests.get(os.environ['GRAVEL_CYCLIST_URL'])
    parser = bs(response.content, "lxml-xml")

    events = parser.find_all('vevent')
    clean = re.compile('<.*?>')
    url_matcher = re.compile('https?:(.*?);')

    db_client = MongoClient(os.environ['MONGO_CONNECT_URL'])

    for event in events:
      properties = event.properties
      
      try:
        updated = properties.dtstamp.find('date-time').text
        summary = properties.summary.text
        description = re.sub(clean, '', properties.description.text)
        start_time = properties.dtstart.find('date-time').text
        end_time = properties.dtend.find('date-time').text
        tz = properties.dtstart.parameters.tzid.text
        contact = properties.contact.text
        location = properties.location.text
        url = properties.url.uri.text
        thumbnail = re.sub(';', '', re.search(url_matcher, properties.find('x-wp-images-url').unknown.text)[0])
      except Exception:
        pass

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
      }

      db_client.gravel_cycling.events.insert_one(event_object)
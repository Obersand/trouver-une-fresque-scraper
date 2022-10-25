import numpy as np
import time
import pandas as pd
import requests
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from geopy.geocoders import Nominatim
from geopy import geocoders
from dateutil.parser import *

from utils.readJson import get_address_data

def get_billetweb_data(dr, headless=False):
    print('Scraping data from www.billetweb.fr\n\n')

    options = Options()
    options.headless = headless

    driver = webdriver.Chrome(options=options, executable_path=dr)

    webSites = [
        {
            # Fresque des Nouveaux Récits
            "url": "https://www.billetweb.fr/pro/fdnr",
            "iframe": 'event21569',
            "id": 0
        },
        {
            # Fresque Océane
            "url": "https://www.billetweb.fr/pro/billetteriefo",
            "iframe": 'event15247',
            "id": 1
        },
        {
            # Fresque de la Biodiversité
            "url": "https://www.billetweb.fr/multi_event.php?user=82762",
            "iframe": 'event17309',
            "id": 2
        },
        {
            # Fresque du Numérique
            "url": "https://www.billetweb.fr/multi_event.php?user=84999",
            "iframe": 'eventu84999',
            "id": 3
        },
        {
            # Fresque Agri'Alim
            "url": "https://www.billetweb.fr/pro/fresqueagrialim",
            "iframe": 'event11421',
            "id": 4
        },
        {
            # Fresque de l'Alimentation
            "url": "https://www.billetweb.fr/pro/fresquealimentation",
            "iframe": 'event11155',
            "id": 5
        },
        {
            # Fresque de la Construction
            "url": "https://www.billetweb.fr/pro/fresquedelaconstruction",
            "iframe": 'event11574',
            "id": 6
        },
        {
            # Fresque de la Mobilité
            "url": "https://www.billetweb.fr/pro/fresquedelamobilite",
            "iframe": 'event11698',
            "id": 7
        },
        {
            # Fresque du Sexisme
            "url": "https://www.billetweb.fr/pro/fresquedusexisme",
            "iframe": 'event21743',
            "id": 8
        },
        {
            # Atelier OGRE
            "url": "https://www.billetweb.fr/pro/atelierogre",
            "iframe": 'event13026',
            "id": 9
        },
        {
            # Atelier Nos vies bas carbone
            "url": "https://www.billetweb.fr/multi_event.php?user=132897",
            "iframe": 'event22230',
            "id": 10
        }
    ]

    records = []

    for page in webSites:
        print(f"\n==================\nProcessing page {page}")
        driver.get(page["url"])
        driver.implicitly_wait(2)

        driver.switch_to.frame(page["iframe"])

        ele = driver.find_elements(By.CSS_SELECTOR, 'a.naviguate')
        links = [e.get_attribute("href") for e in ele]

        for link in links:
            if 'https://www.billetweb.fr/multi_event.php?&multi' not in link:
                print(f"-> Processing {link}...")

                driver.get(link)
                driver.implicitly_wait(3)

                try:
                    driver.find_element(By.ID, 'more_info').click()
                except:
                    pass

                try:
                    page_link = driver.find_element(
                        by=By.CSS_SELECTOR, value='#page_block_location > div > div.location_info > div.address > a')
                except Exception as e:
                    print(f"Rejecting record: {e}")
                    continue

                title_el = driver.find_element(
                    by=By.CSS_SELECTOR, value='#description_block > div.event_title.center > div.event_name.custom_font')
                title = title_el.text
                if 'cadeau' in title.lower():
                    print("Rejecting record: gift card")
                    continue

                time_el = driver.find_element(
                    by=By.CSS_SELECTOR, value='#description_block > div.event_title.center > span > a > div')
                event_time = time_el.text
                event_arr = event_time.lower().split(' from ')
                if len(event_arr) > 1:
                    date_event = event_arr[0]
                    try:
                        time_split = event_arr[1].split(' to ')
                        start_time = time_split[0]
                        end_time = time_split[1]
                    except:
                        print(f"Rejecting record: invalid dates")
                        continue

                    event_start_time = f'{date_event}, {start_time}'
                    event_end_time = f'{date_event}, {end_time}'
                else:
                    event_arr = event_time.lower().split(' at ')
                    try:
                        date_event = event_arr[0]
                        start_time = event_arr[1]
                        end_time = start_time
                    except:
                        print(f"Rejecting record: invalid dates")
                        continue

                    event_start_time = f'{start_time}'
                    event_end_time = f'{end_time}'

                if page_link.get_attribute("href") == "http://maps.google.fr/maps?q=":
                    try:
                        page_link = driver.find_element(
                            by=By.CSS_SELECTOR, value='#description_block > div.event_title.center > div.event_name.custom_font > a.action_button.secondary.virtual.active')
                        location = page_link.text
                        location_text = page_link.text
                    except:
                        location_text = 'Online'
                    if 'en ligne' in title.lower():
                        location_text = 'Online'
                    depart = ''
                    postal_code = ''
                    longitude = ''
                    lattitude = ''
                else:
                    location = page_link.get_attribute("href")
                    location_text = page_link.text
                    address_dict = get_address_data(location_text)

                    try:
                        depart = address_dict['cod_dep']
                    except:
                        depart = ''
                    try:
                        longitude = address_dict['longitude']
                    except:
                        longitude = ''
                    try:
                        lattitude = address_dict['lattitude']
                    except:
                        lattitude = ''
                    try:
                        postal_code = address_dict['postcode']
                    except:
                        postal_code = ''

                # Get the description
                try:
                    even_el = driver.find_element(
                            by=By.CSS_SELECTOR, value='#description')
                except:
                    print(f"Rejecting record: no description")
                    continue
                description = even_el.text

                # Is it a training event?
                training_list = ["formation", "briefing", "animateur"]
                check_tr = 0
                for w in training_list:
                    if w in title.lower():
                        check_tr = +1
                training = (check_tr > 0)

                # Is it an online event?
                online = ('online' in title.lower() or 'en ligne' in title.lower())
                
                # Is the event full?
                #TODO scrape middle div
                full = ('complet' in title.lower())

                # Is it an event for kids?
                kids = ('kids' in title.lower() or 'junior' in title.lower())

                # Parse location fields
                if ',' in location_text:
                    loc_arr = location_text.split(',')
                    if len(loc_arr) >= 3:
                        if loc_arr[2].strip().lower() == 'france':
                            location_name = ''
                            location_address = loc_arr[0]
                            location_city = loc_arr[1]
                        else:
                            location_name = loc_arr[0]
                            location_address = loc_arr[1]
                            location_city = loc_arr[2]
                    elif len(loc_arr) == 2:
                        if loc_arr[1].strip().lower() == 'france':
                            location_name = ''
                            location_address = ''
                            location_city = loc_arr[0]
                        else:
                            location_name = ''
                            location_address = loc_arr[0]
                            location_city = loc_arr[1]
                else:
                    location_name = ''
                    location_address = ''
                    location_city = ''
                location_name = location_name.strip()
                location_address = location_address.strip()
                location_city = location_city.strip().title()

                #TODO strip postal code from address

                if not online and location_address == '':
                    print("Rejecting record: empty address")
                    continue

                # Parse start and end dates
                try:
                    start_datetime = parse(event_start_time)
                except ParserError:
                    try :
                        start_datetime = parse(event_time)
                    except ParserError as e:
                        print(f"Rejecting record: {e}")
                        continue

                start_date = start_datetime.strftime('%Y-%m-%d')
                start_time = start_datetime.strftime('%H:%M:%S')

                try:
                    end_datetime = parse(event_end_time)
                    end_date = end_datetime.strftime('%Y-%m-%d')
                    end_time = end_datetime.strftime('%H:%M:%S')

                    duration = end_datetime - start_datetime
                    hours = divmod(duration.total_seconds(), 3600)[0]
                    if hours > 48:
                        print(f"Rejecting record: event is too long {end_datetime}")
                        continue
                except:
                    end_date = ''
                    end_time = ''

                record = {
                    'page_id': page["id"],
                    'title': title,
                    'start_date': start_date,
                    'start_time': start_time,
                    'end_date': end_date,
                    'end_time': end_time,
                    'location': location,
                    'location_text': location_text,
                    'location_name': location_name,
                    'location_address': location_address,
                    'location_city': location_city,
                    'depart': depart,
                    'postal_code': postal_code,
                    'latitude': lattitude,
                    'longitude': longitude,
                    'online': online,
                    'training': training,
                    'full': full,
                    'kids': kids,
                    'original_source_link': link,
                    'ticketing_platform_link': link,
                    'description': description
                }
                records.append(record)
                print(f"Successfully scraped {link}\n{json.dumps(record, indent=4)}")
    
    driver.quit()

    return records

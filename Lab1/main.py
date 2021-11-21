#!/usr/bin/python3
import csv
import logging
import logging.handlers
import os
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
FORMATTER = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
FILE_HANDLER = logging.FileHandler('scrapper.log')
FILE_HANDLER.setFormatter(FORMATTER)
LOGGER.addHandler(FILE_HANDLER)

try:
    if os.path.exists("scrapper.log"):
        open('scrapper.log', 'w').close()
except Exception as e:
    pass

try:
    if os.path.exists("Lab1/export/content.csv"):
        open('Lab1/export/content.csv', 'w').close()
except Exception as e:
    pass


try:
    os.mkdir('Lab1/export')
except OSError as error:
    LOGGER.debug(error)

starting_web_address = 'https://www.techsterowniki.pl/serwis/kontakt-serwis'


def scrape_web(web_adress, starting_web_address):
    try:
        r = requests.get(web_adress)
    except requests.exceptions.SSLError as e:
        LOGGER.info("SSL Certificate failed")
        r = requests.get(web_adress, verify=False)
    except requests.exceptions.MissingSchema as e:
        r = requests.get(starting_web_address + web_adress)
    except Exception as e:
        raise e

    if r.status_code == requests.codes.ok and BeautifulSoup(r.content, 'lxml') != None:
        return BeautifulSoup(r.content, 'lxml')

    else:
        LOGGER.warning(f"Page returned code {r.status_code}. Skipping.")
        return BeautifulSoup("BLANK", "lxml")


def find_links(soup):

    # TODO: find in text
    links = []
    for link in soup.findAll('a'):
        links.append(link.get('href'))

    regex = r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})'

    r = re.compile(regex)
    # regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    links_filtered = [i for i in links if i]
    try:
        links_filtered.remove("javascript:void(0)")
    except Exception as e:
        raise e

    # links_filtered = list(filter(r.match, links_filtered))
    LOGGER.info(f"LINKS: {links_filtered}")

    return links_filtered


def extract_text(soup, webpage):
    try:
        text = soup.get_text(separator=';')
        for x in range(5):
            text = text.replace("\r", " ")
            text = text.replace("\n", " ")
            text = text.replace("; ;", ";")
            text = text.replace(" ;", ";")
            text = text.replace("; ", ";")
            text = text.replace(";;", ";")
            text = text.replace("\t", " ")
            text = text.replace("  ", " ")

        text = text.strip()
        with open(f'Lab1/export/content.csv', 'a') as f:
            f.write(webpage + ';')
            f.write(text)
            f.write("\n")
            LOGGER.debug(f"[WRITE]{text}")
        return text
    except Exception as e:
        raise e


def find_email(page_content):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(regex, page_content)
    # emails = emails.split()
    if emails:
        for idx, val in enumerate(emails):
            f = open('Lab1/export/emails.csv', 'a')
            write = csv.writer(f)
            write.writerow([val])
            f.close()
    return emails


def remove_duplicates(emails_file='Lab1/export/emails.csv'):
    df = pd.read_csv(emails_file, delimiter=',')
    df.drop_duplicates(subset=None, inplace=True)
    df.to_csv(emails_file, index=False)
    # mylist = list(dict.fromkeys(mylist))


def main(web_adress):
    starting_web_address = web_adress
    visited_adresses = {starting_web_address}
    LOGGER.info("[Starting]")
    soup = scrape_web(web_adress, starting_web_address)
    links = find_links(soup)

    text = extract_text(soup.body, web_adress)
    find_email(text)

    LOGGER.info("Initial scraping done. Scraping links")
    for idx, val in enumerate(links):
        if val in visited_adresses:
            LOGGER.debug("Adress already visited. Skipping.")
            continue
        else:
            visited_adresses.add(val)
            LOGGER.debug(f"Scraping: {val}")
            soup = scrape_web(val, starting_web_address)
            text = extract_text(soup.body, val)
            find_email(text)

    remove_duplicates()
    LOGGER.info("[DONE]")


if __name__ == "__main__":
    main(starting_web_address)

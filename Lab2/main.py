#!/usr/bin/python3
import csv
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
    if os.path.exists("export/content.csv"):
        open('export/content.csv', 'w').close()
except Exception as e:
    pass

try:
    os.mkdir('export')
except OSError as error:
    LOGGER.debug(error)

starting_web_address = 'https://www.techsterowniki.pl/serwis/kontakt-serwis'


def scrape_web(web_address, starting_web_address):
    try:
        r = requests.get(web_address)
    except requests.exceptions.SSLError as e:
        LOGGER.info("SSL Certificate failed")
        r = requests.get(web_address, verify=False)
    except requests.exceptions.MissingSchema as e:
        r = requests.get(starting_web_address + web_address)
    except Exception as e:
        raise e

    if r.status_code == requests.codes.ok and BeautifulSoup(r.content, 'lxml') != None:
        return BeautifulSoup(r.content, 'lxml')

    else:
        LOGGER.warning(f"Page returned code {r.status_code}. Skipping.")
        return BeautifulSoup("BLANK", "lxml")


def ngram(text_dump, n=1):
    text_dump = re.sub('[^A-Za-z0-9; ążźćńółęśŻŹĆĄŚĘŁÓŃ]+', '', text_dump)
    sentence_list = text_dump.split(';')
    ngrams = set()
    for idx, val in enumerate(sentence_list):

        words = [word for word in val.split(" ")]
        temp = zip(*[words[i:] for i in range(0, n)])
        ans = [' '.join(n) for n in temp]
        for idx, val2 in enumerate(ans):
            ngrams.add(val2)

    return ngrams


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
        text = re.sub("\s?;+\s?|\r|\n|\t", ";", text)
        text = re.sub("\s+", " ", text)

        text = text.strip()
        with open(f'export/content.csv', 'a') as f:
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
            f = open('export/emails.csv', 'a')
            write = csv.writer(f)
            write.writerow([val])
            f.close()
    return emails


def remove_duplicates(emails_file='export/emails.csv'):
    df = pd.read_csv(emails_file, delimiter=',')
    df.drop_duplicates(subset=None, inplace=True)
    df.to_csv(emails_file, index=False)
    # mylist = list(dict.fromkeys(mylist))


def main(web_address):
    starting_web_address = web_address
    visited_adresses = {starting_web_address}
    LOGGER.info("[Starting]")
    soup = scrape_web(web_address, starting_web_address)
    links = find_links(soup)

    text = extract_text(soup.body, web_address)
    ngram_set = ngram(text, 2)
    find_email(text)

    LOGGER.info("Initial scraping done. Scraping links")
    for idx, val in enumerate(links):
        if val in visited_adresses:
            LOGGER.debug("Address already visited. Skipping.")
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
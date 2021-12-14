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
    if os.path.exists("export/ngrams.csv"):
        open('export/ngrams.csv', 'w').close()
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


def scrape_web(web_address, starting_web_address):
    try:
        r = requests.get(web_address, timeout=3)
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


def ngram(text_dump, webpage, n=1):
    text_dump = re.sub('[^A-Za-z0-9; ążźćńółęśŻŹĆĄŚĘŁÓŃ]+', '', text_dump)
    sentence_list = text_dump.split(';')
    ngrams = set()
    for idx, val in enumerate(sentence_list):
        words = [word for word in val.split(" ")]
        temp = zip(*[words[i:] for i in range(0, n)])
        ans = [' '.join(n) for n in temp]
        for _, val2 in enumerate(ans):
            ngrams.add(val2)

    with open(f'export/ngrams.csv', 'a') as f:
        f.write(webpage + ';')
        for _, val in enumerate(list(ngrams)):
            f.write(f"{val};")

        f.write("\n")
        LOGGER.debug(f"[WRITE]{ngrams}")
    return ngrams


def find_links(soup):
    # TODO: find in text
    links = []
    for link in soup.findAll('a'):
        links.append(link.get('href'))

    regex = r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})'

    r = re.compile(regex)
    links_filtered = [i for i in links if i]
    try:
        links_filtered.remove("javascript:void(0)")
    except Exception as e:
        raise e

    LOGGER.info(f"LINKS: {links_filtered}")

    return links_filtered


def extract_text(soup, webpage):
    try:
        text = soup.get_text(separator=';')
        text = re.sub("\s?;+\s?|\r|\n|\t", ";", text)
        text = re.sub("\s?;+\s?", ";", text)
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


def prepare_data(web_address):
    starting_web_address = web_address
    visited_addresses = {starting_web_address}
    LOGGER.info("[Starting]")
    soup = scrape_web(web_address, starting_web_address)
    links = find_links(soup)

    text = extract_text(soup.body, web_address)
    ngram_set = ngram(text, web_address, 2)
    find_email(text)

    LOGGER.info("Initial scraping done. Scraping links")
    print("Initial scraping done. Scraping links")
    for idx, new_address in enumerate(links):
        print(f"step:{idx + 1}/{len(links)} {round(((idx + 1) / len(links) * 100))}%")
        if new_address in visited_addresses:
            LOGGER.debug("Address already visited. Skipping.")
            continue
        else:
            visited_addresses.add(new_address)
            LOGGER.debug(f"Scraping: {new_address}")
            soup = scrape_web(new_address, starting_web_address)
            text = extract_text(soup.body, new_address)
            ngram_set = ngram(text, new_address, 2)
            find_email(text)

    remove_duplicates()
    LOGGER.info("[DONE] prepare data")


def read_ngrams_csv(path_to_file='export/ngrams.csv'):
    ngrams = []
    with open(path_to_file, newline='') as csvfile:
        file = csv.reader(csvfile, delimiter=';')
        for row in file:
            ngrams.append(row)

    return ngrams


def jaccard_index(ngrams, url):
    def return_index(e):
        return e['jaccard_index']

    for idx, ngram in enumerate(ngrams):
        if ngram[0] == url:
            my_ngrams = set(ngrams.pop(idx)[1:])
            break
    try:
        all_results = []
        for idx, ngram in enumerate(ngrams):
            x = set(ngram[1:])
            all = len(x.union(my_ngrams))
            common = len(x & my_ngrams)
            index = common / all
            all_results.append({'website': ngram[0], 'jaccard_index': index})
    except:
        LOGGER.error(f"url not in database")
        exit(1)

    all_results.sort(reverse=True, key=return_index)

    return all_results[1:4]


def bag_of_words():
    pass


def cosinus_distance():
    pass


def find_similar_webpages(url):
    ngrams = read_ngrams_csv()
    top_matches = jaccard_index(ngrams, url)
    return top_matches


if __name__ == "__main__":
    prepare_data('https://www.techsterowniki.pl/serwis/kontakt-serwis')
    top_matches = find_similar_webpages('https://www.techsterowniki.pl/k/sterowniki-do-instalacji')
    LOGGER.info(f"Top matches:{top_matches}")
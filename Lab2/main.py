#!/usr/bin/python3
import csv
import logging.handlers
import os
import re
import math

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


def create_bag_of_words(text_dump, webpage):
    bag = {}
    text_dump = re.sub('[^A-Za-z0-9; ążźćńółęśŻŹĆĄŚĘŁÓŃ]+', '', text_dump)
    sentence_list = text_dump.split(';')
    for sentence in sentence_list:
        word_list = sentence.split(' ')
        for word in word_list:
            if word in bag:
                bag[word] += 1
            else:
                bag[word] = 1

    try:
        bag.pop('')
    except:
        pass
    result = [webpage, bag]
    LOGGER.debug(f"[Bag of words]:{result}")
    return result


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
    bag = []
    starting_web_address = web_address
    visited_addresses = {starting_web_address}
    LOGGER.info("[Starting]")
    soup = scrape_web(web_address, starting_web_address)
    links = find_links(soup)

    text = extract_text(soup.body, web_address)
    ngram_set = ngram(text, web_address, 2)
    bag.append(create_bag_of_words(text, web_address))
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
            bag.append(create_bag_of_words(text, new_address))
            find_email(text)

    remove_duplicates()
    LOGGER.info("[DONE] prepare data")
    return bag


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

    all_results = []
    my_ngrams = set()
    for idx, ngram in enumerate(ngrams):
        if ngram[0] == url:
            my_ngrams = set(ngrams.pop(idx)[1:])
            break
        else:
            continue
    try:
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
    LOGGER.info(f"jaccard results: {all_results}")

    return all_results[0:3]


def bag_of_words(bag, url):
    def return_index(e):
        return e['cosinus_distance']

    results = []
    for idx, website in enumerate(bag):
        if website[0] == url:
            print(f"found website {website[0]}")
            my_bag = bag.pop(idx)[1]

    for website in bag:
        my_bag_copy = my_bag
        other_bag = website[1]
        for key in other_bag.keys():
            if key not in my_bag_copy:
                my_bag_copy[key] = 0
        for key in my_bag_copy.keys():
            if key not in other_bag:
                other_bag[key] = 0
        vector_my_bag = list(my_bag_copy.values())
        vector_other_bag = list(other_bag.values())

        x, my_bag_a, other_bag_a = 0, 0, 0
        for idx, val in enumerate(vector_my_bag):
            x += val * vector_other_bag[idx]
            my_bag_a += val ^ 2
            other_bag_a += vector_other_bag[idx]
        my_bag_a = math.sqrt(my_bag_a)
        other_bag_a = math.sqrt(other_bag_a)
        try:
            result = x / (my_bag_a * other_bag_a)
        except:
            result = 0
        results.append({'website': website[0], 'cosinus_distance': result})

    results.sort(reverse=True, key=return_index)
    LOGGER.info(f"Cosinus distance results: {results}")

    return results[0:3]


def find_similar_webpages(url, bag):
    ngrams = read_ngrams_csv()
    top_matches_jaccard = jaccard_index(ngrams, url)
    top_matches_cosinous_distance = bag_of_words(bag, url)
    return top_matches_jaccard, top_matches_cosinous_distance


if __name__ == "__main__":
    bag = prepare_data('https://www.techsterowniki.pl/serwis/kontakt-serwis')
    top_matches_jaccard, top_matches_cosinous_distance = find_similar_webpages(
        'https://www.techsterowniki.pl/k/sterowniki-do-instalacji', bag)
    LOGGER.info(f"Top matches jaccard:{top_matches_jaccard}")
    LOGGER.info(f"Top matches cosinous distance:{top_matches_cosinous_distance}")
    print(f"Top matches jaccard:{top_matches_jaccard}")
    print(f"Top matches cosinous distance:{top_matches_cosinous_distance}")

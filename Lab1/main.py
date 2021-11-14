#!/usr/bin/python3
import csv
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup

web_adress = 'https://www.techsterowniki.pl/serwis/kontakt-serwis'


def scrape_web(web_adress):
    r = requests.get(web_adress, verify=False)
    return BeautifulSoup(r.content, 'lxml')


def find_links(soup):
    links = []
    for link in soup.findAll('a'):
        links.append(link.get('href'))

    regex = r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})'

    r = re.compile(regex)
    # regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    links_filtered = [i for i in links if i]
    links_filtered.remove("javascript:void(0)")
    # TODO: Remove bad links
    links_filtered.remove(
        "/przewodowy-sterownik-zaworow-termostatycznych-L-5s")
    links_filtered.remove("/sterylizator-powietrza-SPT-31-inox")
    # links_filtered.remove("/przewodowy-sterownik-zaworow-termostatycznych-L-5s")
    # links_filtered.remove("/przewodowy-sterownik-zaworow-termostatycznych-L-5s")

    # links_filtered = list(filter(r.match, links_filtered))
    print(f"LINKS: {links_filtered}")

    return links_filtered


def extract_text(soup, webpage):
    if soup:
        text = soup.get_text(separator=';')
        text = text.replace("\n", " ")
        for x in range(5):
            text = re.sub(r"; ;", ";", text)
        with open(f'export/content.csv', 'a') as f:
            f.write(webpage)
            f.write(text)
            f.write("\n")
        return text
    else:
        return "Blank"


def find_email(text):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(regex, text)
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


def main(web_adress):
    print("[Starting]")
    soup = scrape_web(web_adress)
    links = find_links(soup)

    text = extract_text(soup.body, web_adress)
    find_email(text)

    print("Initial scraping done. Scraping links")
    for idx, val in enumerate(links):
        print(f"Scraping: {val}")
        soup = scrape_web(val)
        text = extract_text(soup.body, web_adress)
        find_email(text)

    remove_duplicates()


if __name__ == "__main__":
    main(web_adress)

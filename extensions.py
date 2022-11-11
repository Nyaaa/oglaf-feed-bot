import requests
import os
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup
from lxml import html


class API:
    """Gets telegram token from .env"""
    load_dotenv(find_dotenv())
    TOKEN = os.getenv('BOT_TOKEN')


class FetchException(Exception):
    pass


def get_last_strip():
    base = 'https://www.oglaf.com/'
    page = 'mrowrowr/'
    url = base + page
    counter = 1
    src = []
    title = []
    while True:
        try:
            r = requests.get(url)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            return src, title
        else:
            htm = r.content
            soup = BeautifulSoup(htm, 'lxml')
            strip = soup.find('img', {'id': 'strip'})
            src.append(strip.attrs['src'])
            title.append(strip.attrs['title'])
            counter += 1
            url = base + page + str(counter)


def update():
    base = 'https://www.oglaf.com/archive/'
    page = requests.get(base)
    tree = html.fromstring(page.content)
    name = tree.xpath('/html/body/div/div[1]/div[1]/a[1]/@href')
    return name[0]

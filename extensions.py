import dotenv
import requests
import os
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup


class API:
    """Gets telegram token from .env"""
    load_dotenv(find_dotenv())
    TOKEN = os.getenv('BOT_TOKEN')


class FetchException(Exception):
    pass


def get_last_strip():
    base = 'https://www.oglaf.com'
    page = update()
    last_page = dotenv.get_key(find_dotenv(), key_to_get='last_page')
    if page == last_page:
        raise FetchException('No updates')
    else:
        dotenv.set_key(find_dotenv(), key_to_set='last_page', value_to_set=page)
    url = base + page
    counter = 1
    src = []
    title = []
    alt = []
    name = ''
    while True:
        try:
            r = requests.get(url)
            r.raise_for_status()
        except requests.exceptions.RequestException:
            return src, title, alt, name
        else:
            soup = BeautifulSoup(r.content, 'lxml')
            strip = soup.find('img', {'id': 'strip'})
            name = soup.find('title').string
            src.append(strip.attrs['src'])
            title.append(strip.attrs['title'])
            alt.append(strip.attrs['alt'])
            counter += 1
            url = base + page + str(counter)


def update():
    base = 'https://www.oglaf.com/archive/'
    r = requests.get(base)
    soup = BeautifulSoup(r.content, 'lxml')
    name = soup.find_all('div')[2].find('a')
    return name['href']


def force_update():
    dotenv.set_key(find_dotenv(), key_to_set='last_page', value_to_set='')

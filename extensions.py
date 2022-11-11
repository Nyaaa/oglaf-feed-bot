import requests
from dotenv import load_dotenv, find_dotenv
import os
from bs4 import BeautifulSoup


class API:
    """Gets telegram token from .env"""
    load_dotenv(find_dotenv())
    TOKEN = os.getenv('BOT_TOKEN')


class FetchException(Exception):
    pass


def get_last_strip():
    base = 'https://www.oglaf.com/officialduties/'
    html = requests.get(base).content
    soup = BeautifulSoup(html, 'lxml')
    strip = soup.find('img', {'id': 'strip'})
    alt = strip.attrs['alt']
    src = strip.attrs['src']
    title = strip.attrs['title']

    nav = soup.find('div', {'id': 'nav'})
    a = nav.find('a', {'class': 'button next'})
    next_strip = a['href']

    return alt, src, title, next_strip

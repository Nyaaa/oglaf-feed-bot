import requests
import os
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup
import sqlite3

con = sqlite3.connect("bot.db")
cur = con.cursor()
# cur.execute("DROP TABLE conf;")
cur.execute("CREATE TABLE IF NOT EXISTS conf(setting TEXT NOT NULL PRIMARY KEY, value TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER NOT NULL PRIMARY KEY)")
cur.execute("INSERT OR IGNORE INTO conf(setting, value) VALUES('last_page', NULL)")


class API:
    """Gets telegram token from .env"""
    load_dotenv(find_dotenv())
    TOKEN = os.getenv('BOT_TOKEN')


class BotException(Exception):
    pass


class Users:
    @staticmethod
    def add(user_id):
        try:
            cur.execute("INSERT INTO users(user_id) VALUES(?)", (user_id, ))
        except sqlite3.IntegrityError:
            raise
        else:
            con.commit()

    @staticmethod
    def delete(user_id):
        cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        if cur.rowcount <= 0:
            raise BotException("User not found")
        else:
            con.commit()

    @staticmethod
    def get_users():
        search = cur.execute("SELECT user_id FROM users")
        return search.fetchall()


def get_last_strip():
    base = 'https://www.oglaf.com'
    page = update()
    res = cur.execute("SELECT value FROM conf WHERE setting='last_page'")
    last_page = res.fetchone()[0]
    if page == last_page:
        raise BotException('No updates')
    else:
        cur.execute("UPDATE conf SET value = ? WHERE setting = 'last_page'", (page, ))
        con.commit()
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
    cur.execute("UPDATE conf SET value = NULL WHERE setting = 'last_page'")
    con.commit()

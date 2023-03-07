import requests
from bs4 import BeautifulSoup
import sqlite3


class DBopen(object):
    def __init__(self, path='./db/db.sqlite3'):
        self.path = path

    def __enter__(self):
        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_class, exc, traceback):
        self.conn.commit()
        self.conn.close()


class BotException(Exception):
    pass


class UserException(BotException):
    """Raise when a user repeats an action."""


class UpdateException(BotException):
    """Raise when an expected update is not fetched."""


class Users:
    def __init__(self, user_id):
        self.id = user_id

    def add(self):
        with DBopen() as cur:
            try:
                cur.execute("INSERT INTO users(user_id) VALUES(?)", (self.id, ))
            except sqlite3.IntegrityError:
                raise UserException(f"ID {self.id}: you are already subscribed")

    def delete(self):
        with DBopen() as cur:
            cur.execute("DELETE FROM users WHERE user_id = ?", (self.id, ))
            if cur.rowcount <= 0:
                raise UserException(f"ID {self.id}: you are not subscribed")

    @staticmethod
    def get_users():
        with DBopen() as cur:
            search = cur.execute("SELECT user_id FROM users")
            return search.fetchall()


def get_comic():
    page = update()

    with DBopen() as cur:
        res = cur.execute("SELECT value FROM conf WHERE setting = 'last_page'")
        last_page = res.fetchone()[0]
        if page == last_page:
            raise UpdateException('No updates')
        else:
            cur.execute("UPDATE conf SET value = ? WHERE setting = 'last_page'", (page, ))
            src, title, alt, name = download(page)
            return src, title, alt, name


def download(page):
    base = 'https://www.oglaf.com'
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
            soup = BeautifulSoup(r.content, 'html.parser')
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
    soup = BeautifulSoup(r.content, 'html.parser')
    name = soup.find_all('div')[2].find('a')
    return name['href']


def create_db():
    with DBopen() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER NOT NULL PRIMARY KEY)")
        cur.execute("CREATE TABLE IF NOT EXISTS conf(setting TEXT NOT NULL PRIMARY KEY, value TEXT)")
        cur.execute("INSERT OR IGNORE INTO conf(setting, value) VALUES('last_page', NULL)")

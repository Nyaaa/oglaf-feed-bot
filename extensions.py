import sqlite3
from sqlite3 import Cursor, IntegrityError
from types import TracebackType
from urllib.parse import urljoin

import aiohttp
from aiogram.utils.media_group import MediaGroupBuilder
from bs4 import BeautifulSoup

from settings import ARCHIVE_URL, BASE_URL, DB_PATH


class DBopen:
    def __init__(self, path: str = DB_PATH) -> None:
        self.path = path

    def __enter__(self) -> Cursor:
        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(
            self,
            type_: type[BaseException] | None,
            value: BaseException | None,
            traceback: TracebackType | None,
    ) -> None:
        self.conn.commit()
        self.conn.close()


class BotError(Exception):
    pass


class UserError(BotError):
    """Raise when a user repeats an action."""


class UpdateError(BotError):
    """Raise when an expected update is not fetched."""


class Users:
    def __init__(self, user_id: int) -> None:
        self.id = user_id

    def add(self) -> None:
        with DBopen() as cur:
            try:
                cur.execute("INSERT INTO users(user_id) VALUES(?)", (self.id, ))
            except IntegrityError as e:
                raise UserError(f"ID {self.id}: you are already subscribed") from e

    def delete(self) -> None:
        with DBopen() as cur:
            cur.execute("DELETE FROM users WHERE user_id = ?", (self.id, ))
            if cur.rowcount <= 0:
                raise UserError(f"ID {self.id}: you are not subscribed")

    @staticmethod
    def get_users() -> list[tuple[int]]:
        with DBopen() as cur:
            search = cur.execute("SELECT user_id FROM users")
            return search.fetchall()


async def get_comic() -> tuple[MediaGroupBuilder, str]:
    page_slug = await get_latest_update()

    with DBopen() as cur:
        res = cur.execute("SELECT value FROM conf WHERE setting = 'last_page'")
        last_page = res.fetchone()[0]
        if page_slug == last_page:
            raise UpdateError("No updates")
        cur.execute("UPDATE conf SET value = ? WHERE setting = 'last_page'", (page_slug, ))
        images, name = await download(page_slug)
        return images, name


async def download(page_slug: str) -> tuple[MediaGroupBuilder, str]:
    result_images = MediaGroupBuilder()
    name = ""
    urls = [urljoin(BASE_URL, page_slug)]
    while urls:
        url = urls.pop(0)
        soup = await download_resource(url)

        next_page = soup.find("link", {"rel": "next"})
        if next_page and page_slug in (next_page_slug := next_page["href"]):
            urls.append(urljoin(BASE_URL, next_page_slug))

        strip = soup.find("img", {"id": "strip"})
        name = soup.find("title").string
        src = strip.attrs["src"]
        title = strip.attrs["title"]
        alt = strip.attrs["alt"]
        result_images.add_photo(src, f'"{alt}"\n{title}')

    return result_images, name


async def get_latest_update() -> str:
    soup = await download_resource(ARCHIVE_URL)
    name = soup.find_all("div")[2].find("a")
    return name["href"]


async def download_resource(url: str) -> BeautifulSoup:
    async with aiohttp.ClientSession() as session, session.get(url) as resp:
        r = await resp.text()
    return BeautifulSoup(r, "html.parser")


def create_db() -> None:
    with DBopen() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER NOT NULL PRIMARY KEY)")
        cur.execute("CREATE TABLE IF NOT EXISTS conf(setting TEXT NOT NULL PRIMARY KEY, value TEXT)")
        cur.execute("INSERT OR IGNORE INTO conf(setting, value) VALUES('last_page', NULL)")

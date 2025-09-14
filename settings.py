import logging
import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

BASE_URL = "https://www.oglaf.com"
ARCHIVE_URL = "https://www.oglaf.com/archive/"

DB_PATH = "./db/db.sqlite3"

TOKEN = os.getenv("BOT_TOKEN")
ADMIN = int(os.getenv("ADMIN"))
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%b-%d %H:%M:%S",
)
log = logging.getLogger("broadcast")

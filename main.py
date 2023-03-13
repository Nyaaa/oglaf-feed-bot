from aiogram import Bot, Dispatcher, executor, types, exceptions
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import logging
import os
from extensions import Users, get_comic, UserException, UpdateException, create_db
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta


load_dotenv(find_dotenv())
scheduler = AsyncIOScheduler()
bot = Bot(token=os.getenv('BOT_TOKEN'))
ADMIN = int(os.getenv('ADMIN'))
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')


@dp.message_handler(commands=['start'])
async def begin(message: types.Message):
    user_id = message.from_user.id
    text = f"ID {user_id}: subscribed"
    try:
        Users(user_id).add()
    except UserException as e:
        text = str(e)
    finally:
        log.info(text)
        await bot.send_message(user_id, text + "\n/stop to unsubscribe")


@dp.message_handler(commands=['stop'])
async def stop(message: types.Message):
    user_id = message.from_user.id
    text = f"ID {user_id}: unsubscribed"
    try:
        Users(user_id).delete()
    except UserException as e:
        text = str(e)
    finally:
        log.info(text)
        await bot.send_message(user_id, text)


@dp.message_handler(content_types=['text'], text='update')
async def force_update(message: types.Message):
    user_id = message.from_user.id
    if message.from_user.id == ADMIN:
        log.info('Forcing update...')
        await get_strip(force=True)
    else:
        log.info(f'Unauthorised update by {user_id}')


async def get_strip(force: bool = False):
    """Checks if there is a new comic"""
    try:
        log.info("Parsing...")
        src, text, alt, name = get_comic()
    except UpdateException as err:
        today = datetime.now()
        if (today.weekday() <= 2 or today.weekday() >= 5) and not force:
            retry = today + timedelta(hours=6)
            scheduler.add_job(get_strip, 'date', run_date=retry)
            log.info(f'Retry at {retry}')
        log.info(err)
    else:
        log.info(f'Got new comic "{name}"')
        media = types.MediaGroup()
        for page in range(len(src)):
            description = f'"{alt[page]}"\n{text[page]}'
            media.attach_photo(src[page], description)
        await broadcast(name, media)


async def comic(user_id, name, media):
    """Forms & sends a message"""
    try:
        await bot.send_chat_action(user_id, 'upload_photo')
        await bot.send_message(user_id, name)
        await bot.send_media_group(user_id, media=media)
    except (exceptions.Unauthorized, exceptions.ChatNotFound):
        Users(user_id).delete()
        log.info(f"ID {user_id}: User removed")
    except exceptions.RetryAfter as e:
        log.error(f"ID {user_id}: Timeout {e.timeout} seconds")
        await asyncio.sleep(e.timeout)
        return await comic(user_id, name, media)
    else:
        log.info(f"ID {user_id}: Message sent")
        return True
    return False


async def broadcast(name, media):
    """Sends a comic to subscribers"""
    count = 0
    try:
        for user_id in Users.get_users():
            user_id = user_id[0]
            if await comic(user_id, name, media):
                count += 1
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
    finally:
        log.info(f"{count} messages sent out.")
    return count


async def on_startup(_):
    scheduler.add_job(get_strip, "cron", day_of_week='sun', hour=21, minute=00)
    # scheduler.add_job(get_strip, "interval", seconds=60)

if __name__ == '__main__':
    os.path.isdir('db') or os.makedirs('db')
    create_db()
    scheduler.start()
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

from aiogram import Bot, Dispatcher, executor, types
import aioschedule
import asyncio
import logging
from extensions import *

bot = Bot(token=API.TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')
users = []


@dp.message_handler(commands=['start'])
async def hello(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users:
        users.append(user_id)
        text = f"ID {user_id} subscribed"
    else:
        text = f"ID {user_id} is already subscribed"
    await bot.send_message(user_id, text+"\n/stop to unsubscribe")


@dp.message_handler(commands=['stop'])
async def hello(message: types.Message):
    user_id = message.from_user.id
    if user_id in users:
        users.remove(user_id)
        text = f"ID {user_id} unsubscribed"
    else:
        text = f"ID {user_id} is not subscribed"
    await bot.send_message(user_id, text)


@dp.message_handler(commands=['update'])
async def update(message: types.Message):
    force_update()


async def get_strip():
    """Checks if there is a new comic"""
    try:
        log.info("Parsing...")
        src, text, alt, name = get_last_strip()
    except FetchException as err:
        log.info(err)
    else:
        log.info(f"Got new comic {name}")
        media = types.MediaGroup()
        for page in range(len(src)):
            description = f'"{alt[page]}"\n{text[page]}'
            media.attach_photo(src[page], description)
        await broadcast(name, media)


def get_users():
    yield from users


async def comic(user_id, name, media):
    """Forms & sends a message"""
    # await types.ChatActions.upload_photo()
    await bot.send_chat_action(user_id, 'upload_photo')
    await bot.send_message(user_id, name)
    await bot.send_media_group(user_id, media=media)
    log.info(f"Message sent to {user_id}")
    return True


async def broadcast(name, media):
    """Sends a comic to subscribers"""
    count = 0
    try:
        for user_id in get_users():
            if await comic(user_id, name, media):
                count += 1
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
    finally:
        log.info(f"{count} messages sent out.")
    return count


async def scheduler():
    # aioschedule.every().day.at("12:00").do(broadcast)
    aioschedule.every(1).minutes.do(get_strip)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

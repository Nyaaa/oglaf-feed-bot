from aiogram import Bot, Dispatcher, executor, types, exceptions
import aioschedule
import asyncio
import logging
import os
from extensions import Users, get_last_strip, BotException, create_db

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')


@dp.message_handler(commands=['start'])
async def begin(message: types.Message):
    user_id = message.from_user.id
    text = f"ID {user_id}: subscribed"
    try:
        Users.add(user_id)
    except BotException as e:
        text = str(e)
    finally:
        log.info(text)
        await bot.send_message(user_id, text + "\n/stop to unsubscribe")


@dp.message_handler(commands=['stop'])
async def stop(message: types.Message):
    user_id = message.from_user.id
    text = f"ID {user_id}: unsubscribed"
    try:
        Users.delete(user_id)
    except BotException as e:
        text = str(e)
    finally:
        log.info(text)
        await bot.send_message(user_id, text)


async def get_strip():
    """Checks if there is a new comic"""
    try:
        log.info("Parsing...")
        src, text, alt, name = get_last_strip()
    except BotException as err:
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
        Users.delete(user_id)
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


async def scheduler():
    aioschedule.every().sunday.at("20:00").do(get_strip)
    # aioschedule.every(1).minutes.do(get_strip)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    os.path.isdir('db') or os.makedirs('db')
    create_db()
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

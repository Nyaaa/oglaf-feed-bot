import asyncio
import pathlib
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import (
    TelegramNotFound,
    TelegramRetryAfter,
    TelegramUnauthorizedError,
)
from aiogram.filters import Command
from aiogram.types import BotCommand, InputMediaPhoto, Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from extensions import UpdateError, UserError, Users, create_db, get_comic
from settings import ADMIN, TOKEN, log

scheduler = AsyncIOScheduler(job_defaults={"misfire_grace_time": None})
bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command(commands=["start"]))
async def begin(message: Message) -> None:
    user_id = message.from_user.id
    text = f"ID {user_id}: subscribed"
    try:
        Users(user_id).add()
    except UserError as e:
        text = str(e)
    finally:
        log.info(text)
        await bot.send_message(user_id, text + "\n/stop to unsubscribe")


@dp.message(Command(commands=["stop"]))
async def stop(message: Message) -> None:
    user_id = message.from_user.id
    text = f"ID {user_id}: unsubscribed"
    try:
        Users(user_id).delete()
    except UserError as e:
        text = str(e)
    finally:
        log.info(text)
        await bot.send_message(user_id, text)


@dp.message(F.text == "update")
async def force_update(message: Message) -> None:
    user_id = message.from_user.id
    if user_id == ADMIN:
        log.info("Forcing update...")
        await get_strip(force=True)
    else:
        log.info(f"Unauthorised update by {user_id}")


async def get_strip(force: bool = False) -> None:
    """Checks if there is a new comic"""
    try:
        log.info("Parsing...")
        media_builder, name = await get_comic()
    except UpdateError as err:
        today = datetime.now()
        if (today.weekday() <= 2 or today.weekday() >= 5) and not force:
            retry = today + timedelta(hours=6)
            scheduler.add_job(get_strip, "date", run_date=retry)
            log.info(f"Retry at {retry}")
        log.info(err)
    else:
        log.info(f'Got new comic "{name}"')
        media = media_builder.build()
        await broadcast(name, media)


async def send_comic(user_id: int, name: str, media: list[InputMediaPhoto]) -> bool:
    """Forms & sends a message"""
    try:
        await bot.send_chat_action(user_id, "upload_photo")
        await bot.send_message(user_id, name)
        await bot.send_media_group(user_id, media=media)
    except (TelegramUnauthorizedError, TelegramNotFound):
        Users(user_id).delete()
        log.info(f"ID {user_id}: User removed")
    except TelegramRetryAfter as e:
        log.exception(f"ID {user_id}: Timeout {e.retry_after} seconds")
        await asyncio.sleep(e.retry_after)
        return await send_comic(user_id, name, media)
    else:
        log.info(f"ID {user_id}: Message sent")
        return True
    return False


async def broadcast(name: str, media: list[InputMediaPhoto]) -> None:
    """Sends a comic to subscribers"""
    count = 0
    try:
        for user_id_ in Users.get_users():
            user_id = user_id_[0]
            if await send_comic(user_id, name, media):
                count += 1
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
    finally:
        log.info(f"{count} messages sent out.")


async def main() -> None:
    pathlib.Path("db").mkdir(parents=True, exist_ok=True)
    create_db()

    scheduler.add_job(get_strip, "cron", day_of_week="sun", hour=21, minute=00)
    # scheduler.add_job(get_strip, "interval", seconds=60)
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start", description="Subscribe"),
            BotCommand(command="stop", description="Unsubscribe"),
        ]
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

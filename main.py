from aiogram import Bot, Dispatcher, executor, filters, types
from extensions import *

bot = Bot(token=API.TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    src, title = get_last_strip()
    for page in range(len(src)):
        await types.ChatActions.upload_photo()
        media = types.MediaGroup()
        media.attach_photo(src[page], title[page])
        await message.answer_media_group(media=media)


@dp.message_handler(commands=['update'])
async def check_update(message: types.Message):
    title = update()
    await message.answer(title)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

from aiogram import Bot, Dispatcher, executor, filters, types
from extensions import *

bot = Bot(token=API.TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(filters.CommandStart())
async def send_welcome(message: types.Message):
    alt, src, title, next_strip = get_last_strip()
    await types.ChatActions.upload_photo()
    media = types.MediaGroup()
    media.attach_photo(src, title)
    await message.answer_media_group(media=media)
    await message.answer(next_strip)
    if next_strip:
        pass


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

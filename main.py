from aiogram import Bot, Dispatcher, executor, types

from extensions import *

bot = Bot(token=API.TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def post_strip(message: types.Message):
    await types.ChatActions.upload_photo()
    try:
        src, text, alt, name = get_last_strip()
    except FetchException as e:
        await message.answer(str(e))
    else:
        await message.answer(name)
        media = types.MediaGroup()
        for page in range(len(src)):
            description = f'"{alt[page]}"\n{text[page]}'
            media.attach_photo(src[page], description)
        await message.answer_media_group(media=media)


@dp.message_handler(commands=['update'])
async def update(message: types.Message):
    force_update()
    await post_strip(message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

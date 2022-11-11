from telebot.async_telebot import AsyncTeleBot
import telebot
from extensions import *
import asyncio
from textwrap import dedent

bot = AsyncTeleBot(API.TOKEN)


async def menu():
    await bot.set_my_commands(commands=[
        telebot.types.BotCommand("help", "Bot usage"),
        telebot.types.BotCommand("start", "Bot info"),
        telebot.types.BotCommand("values", "Supported currencies")
    ])


@bot.message_handler(commands=['start'])
async def message_start(message):
    text = """
            Welcome to currency converter bot!
            Usage: /help
            Supported currencies: /values
            """
    await bot.send_message(message.chat.id, dedent(text))


@bot.message_handler(commands=['help'])
async def message_help(message):
    text = """
            Usage:
            [currency to convert from] [currency to convert to] [amount]
            Example:
            usd eur 100
            Supported currencies: /values
            """
    await bot.send_message(message.chat.id, dedent(text))


@bot.message_handler(commands=['values'])
async def message_help(message):
    try:
        await bot.send_message(message.chat.id, Converter.get_currencies())
    except APIException as e:
        await bot.send_message(message.chat.id, str(e))


@bot.message_handler(content_types=['text'])
async def message_convert(message):
    try:
        await bot.send_message(message.chat.id, Converter.convert(message.text))
    except APIException as e:
        await bot.send_message(message.chat.id, str(e))


asyncio.run(bot.polling())

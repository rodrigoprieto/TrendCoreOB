import asyncio

import telegram.ext.filters
from telegram import Update, error
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler
import config
import trendcore
import utils
import pandas as pd
from UserDatabase import UserDatabase

# Initiate the Database where we're going to persist user's settings
db = UserDatabase(config.user_data)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Return the welcome message
    :param update:
    :param context:
    :return:
    """
    try:
        user = update.message.from_user
        db_user = db.get_user(user.id)
        if db_user is None:
            db.insert_user(user)
        await update.message.reply_text('Hi! Use /data to get the Order Book information '
                                        'or /help to get more information.')
    except error.TelegramError as e:
        print(f"Telegram Error occurred: {e.message}")


async def wallsize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Command to update the minimum wall size for each user
    :param update:
    :param context:
    :return:
    """
    # the command should be in the format "/wallsize 100k"
    # we split the text by space and take the second element

    try:
        user = update.message.from_user
        db_user = db.get_user(user.id)
        if db_user is None:
            db.insert_user(user)

        wall_size = update.message.text.split()[1]
        wall_size = wall_size.upper()
        if 'K' in wall_size or 'M' in wall_size:
            # convert 100k to 100000
            wall_size = utils.convert_units(wall_size)
        else:
            wall_size = float(wall_size)

        db.update_wallsize(user, wall_size)
        await update.message.reply_text(f"Minimal wall size updated to {wall_size} USD")
    except error.TelegramError as e:
        print(f"Telegram Error occurred: {e.message}")
    except Exception as e:
        await update.message.reply_text("There was a problem updating the minimum wall size.\n"
                                        "Usage: */wallsize [amount]*\n"
                                        "Example: */wallsize 100k*", parse_mode="Markdown")


async def distance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Command to update the distance from current price to wall price
    :param update:
    :param context:
    :return:
    """
    # the command should be in the format "/distance [number]"
    # we split the text by space and take the second element


    try:
        user = update.message.from_user
        db_user = db.get_user(user.id)
        if db_user is None:
            db.insert_user(user)

        distance = update.message.text.split()[1]
        distance = distance.replace('%','').strip()
        distance = float(distance)

        db.update_distance(user, distance)
        await update.message.reply_text(f"Maximum distance updated to {distance:.2f}%")
    except error.TelegramError as e:
        print(f"Telegram Error occurred: {e.message}")
    except Exception as e:
        print(e)
        await update.message.reply_text("There was a problem updating the distance.\n"
                                        "Usage: */distance [number]*\n"
                                        "Example: */distance 5*", parse_mode="Markdown")


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text('Welcome to the TrendCore OrderBook Bot, a handy tool for accessing cryptocurrency '
                                        'order wall information from the TrendCore website with the /data command.\n\n'
                                        '*Understanding the Symbols*:\n\n'
                                        'The moon icons denote the age of the wall:\n\n'
                                        '🌑 Wall is less than 15 minutes old.\n'
                                        '🌒 Wall is more than 15 minutes old but less than an hour.\n'
                                        '🌓 Wall is more than an hour old but less than 4 hours.\n'
                                        '🌔 Wall is more than 4 hours old but less than a day.\n'
                                        '🌕 Wall is more than a day old.\n\n'
                                        'The circle icons represent the type of wall:\n\n'
                                        '🔴 The wall is an ask wall (located above the current price).\n'
                                        '🟢 The wall is a bid wall (located below the current price).\n\n'
                                        'Along with these symbols, you\'ll also find: \n'
                                        '- The price at which the wall is located. \n'
                                        '- The distance (%) from the current price to the wall.\n'
                                        '- An estimated time (in minutes) it may take for the price '
                                        'to erode (go through) the wall.\n\n'
                                        'Feel free to use /data anytime to get the most recent order wall '
                                        'information.\n', parse_mode="Markdown")
        await update.message.reply_text('*Configuration Commands*:\n\n'
                                        '1. *Minimum Wall Size*:\n'
                                        'Command: /wallsize [amount]\n'
                                        'Description: This command sets the minimum wall size you\'re interested in. '
                                        'Walls smaller than this size will not be displayed.\n'
                                        'Usage Examples:\n' 
                                        '- /wallsize 100k : Sets the minimum wall size to 100,000.\n'
                                        '- /wallsize 1M : Sets the minimum wall size to 1,000,000.\n\n'
                                        '2. *Maximum Allowed Distance from Last Price to the Wall*:\n'
                                        'Command: /distance [number]\n'
                                        'Description: This command sets the maximum allowed distance from the last price to the wall. '
                                        'Walls farther than this distance will not be displayed.\n'
                                        'Usage Example:\n'
                                        '- /distance 5 : Sets the maximum allowed distance to 5%.\n\n'
                                        'Remember, to retrieve the order book data, use the /data command.\n\n'
                                        'Happy trading!'
                                        , parse_mode="Markdown")
    except error.TelegramError as e:
        print(f"Telegram Error occurred: {e.message}")


async def data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:

        user = update.message.from_user
        db_user = db.get_user(user.id)

        wallsize = float(db_user['wallsize'])
        distance = float(db_user['distance'])

        # Optional: Send chat action to the user while we retrieve and process the data
        # await context.bot.send_chat_action(chat_id=update.effective_message.chat_id,
        #                              action=telegram.constants.ChatAction.TYPING)

        tc_webscrapper = trendcore.TrendCore()
        formatted_data = tc_webscrapper.get_formatted_data(wallsize, distance)
        await update.message.reply_text(formatted_data, parse_mode="Markdown")
    except error.TelegramError as e:
        print(f"Telegram Error occurred: {e.message}")

async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    db_user = db.get_user(user.id)
    if db_user is None:
        db.insert_user(user)

app = ApplicationBuilder().token(config.telegram_token).build()
# Start commands & help
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
# Data commands
app.add_handler(CommandHandler("data", data))
# Configuration
app.add_handler(CommandHandler("wallsize", wallsize))
app.add_handler(CommandHandler("distance", distance))
# Start listening
try:
    app.run_polling()
except error.TelegramError as e:
    print(f"Telegram Error occurred: {e.message}")

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import config
import trendcore

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hi! Use /data to get the Order Book information '
                                    'or /help to get more information.')

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
                                    'information. \n\nHappy trading! '
                                    , parse_mode="Markdown")

async def data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tc_webscrapper = trendcore.TrendCore()
    formatted_data = tc_webscrapper.get_formatted_data(250000, 5.0)

    await update.message.reply_text(formatted_data, parse_mode="MarkdownV2")


app = ApplicationBuilder().token(config.telegram_token).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("data", data))

app.run_polling()

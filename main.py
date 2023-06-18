from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import config
import trendcore

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hi! Use /data to get the Order Book information')

async def data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tc_webscrapper = trendcore.TrendCore()
    formatted_data = tc_webscrapper.get_formatted_data(250000, 5.0)

    await update.message.reply_text(formatted_data, parse_mode="HTML")


app = ApplicationBuilder().token(config.telegram_token).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("data", data))

app.run_polling()

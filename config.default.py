import os
from os.path import join

# File Configuration
base_path = os.path.dirname(os.path.abspath(__file__))

# TrendCore
trendcore_url = 'https://trendcore.ru/indexsee.php'
trendcore_csv = join(base_path, 'data', 'trendcore.csv')

# Telegram
telegram_token=""
telegram_bot=""


import os
from os.path import join

# File Configuration
base_path = os.path.dirname(os.path.abspath(__file__))
data_path = join(base_path, 'data')

if not os.path.exists(data_path):
    os.mkdir(data_path)

# TrendCore
trendcore_url = 'https://trendcore.ru/indexsee.php'
trendcore_csv = join(data_path, 'trendcore.csv')

# Telegram
telegram_token = ""  # Update your token
telegram_bot = ""  # Optional

# User data
user_data = join(data_path, 'users_data.db')
import config
import time
import os
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import utils
import re
from datetime import datetime, timedelta


class TrendCore():
    #cached data for 1 minute
    filename = ""
    # dataframe
    dataframe = pd.DataFrame()

    def __init__(self):
        """
        Initialize the class and call the scrapper if the cached file contains outdated information
        """
        # get the proper filename
        self.filename = config.trendcore_csv
        # load the dataframe from server when more than 1 minute has elapsed since the last retrieved file
        if self.elapsed_more_than_minute():
            self.dataframe = self.scrap()
        else:
            self.dataframe = pd.read_csv(self.filename)
            self.dataframe.set_index("Coin", inplace=True)

    def get_data(self, min_wall_size=100_000, max_distance_to_level=5.0):
        """
        Filter the information based on the parameters and retrieve the information
        in a beautiful message to send to Telegram
        :param min_wall_size: minimum amount of wall size
        :param max_distance_to_level: the maximum distance from the current price to the bid/ask wall
        :return: a dataframe with the filtered information
        """
        slice = self.dataframe.copy()
        slice = slice[(slice['Amount'] >= min_wall_size) &
                      (slice['Distance'] <= max_distance_to_level)]
        slice.sort_index(ascending=True, inplace=True)
        return slice

    def get_formatted_data(self, min_wall_size=100_000, max_distance_to_level=5.0):
        """
        Filter the information based on the parameters and retrieve the information
        in a beautiful message to send to Telegram
        :param min_wall_size: minimum amount of wall size
        :param max_distance_to_level: maximum distance from the current price to to bid/ask wall
        :return: a table formatted to send to Telegram bot
        """
        slice = self.get_data(min_wall_size, max_distance_to_level)
        """
        From trendcore documentation:
        Densities from $3M - pink, from $1M - purple, from $500K - yellow, from $250K - orange, from $100K - gray
        (the number of coins in the density multiplied by the price
        at which the density is, we get the amount in dollars).
        We are going to use the emoji moon icon for this.
        """
        #slice['Amount icon'] = slice['Amount'].apply(self.icon_from_amount)  # Disabled
        # get the infographic depending on the wall duration in minutes
        slice['Infographic'] = slice['Elapsed Minutes'].apply(self.icon_from_elapsed_time)
        # get the wall type icon (buy wall = green ~ sell wall = red)
        slice['Wall type icon'] = np.where((slice['Wall type'] == 'buy'), '🟢', '🔴')

        rows = []

        to_print = slice.copy().reset_index()
        to_print = to_print[['Infographic','Coin','Price','USD per level','To level %','Wall type icon']]
        for index, row in slice.iterrows():
            columns = [f"{row['Infographic']}",
                       f"{index}",
                       f"${row['Price']}",
                       f"{row['USD per level']}",
                       f"{row['To level %']:.2f}%",
                       f"{row['Wall type icon']}",
                       f"{row['Estimate time to corrode (mins)']}'"
                       ]
            rows.append(columns)
        return utils.format_telegram_message(rows)

    def icon_from_elapsed_time(self, minutes):
        """
        From trendcore documentation:
        The dashes in the coin column are an infographic showing how long ago the density was discovered.
        When you hover, you can see the exact time the density was detected and how many minutes
        have passed since that moment.
        4 dashes - density detected more than a day ago, (60*24 = +1440 minutes)
        3 dashes - more than 4 hours,  (4*60 = +240 minutes)
        2 dashes - more than 1 hour, (1*60 = +60 minutes)
        1 dash - more than 15 minutes.
        :param minutes: int
        :return: Moon emoji icon depending on the elapsed time the wall was created.
        """
        if minutes >= 1440:
            return '🌕'  # Full Moon
        elif minutes >= 240:
            return '🌔'  # Waxing Gibbous Moon
        elif minutes >= 60:
            return '🌓'  # First Quarter Moon
        elif minutes >= 15:
            return '🌒'  # Waxing Crescent Moon
        else:
            return '🌑'  # New Moon

    def elapsed_more_than_minute(self):
        """
        Check the last time the file was retrieved from the server to avoid multiple
        web scraps in a short period of time. We're going to cache the information
        for one minute and retrieve it again after that time.
        :return: True if more than one minute has passed. Otherwise, False.
        """
        if not os.path.isfile(self.filename):
            # file does not exists, return True
            return True
        modification_time = os.path.getmtime(self.filename)
        current_time = time.time()
        return current_time - modification_time > 60  # more than 60 seconds

    def scrap(self):
        # target URL to scrap
        url = config.trendcore_url
        start_time = time.time()
        print(f"Retrieving new information from server...")

        # send a GET request
        response = requests.get(url)

        # parse the HTML from the web page
        soup = BeautifulSoup(response.text, 'html.parser')

        # find the main table
        table = soup.find('table')

        # create a list to store the header data (in Russian)
        headers = []
        for th in table.find('thead').find_all('td'):
            column_text = th.text
            if column_text == "":
                column_text = th.find("img").get("title")
            headers.append(column_text)

        # create a list to store the table data
        table_data = []
        counter = 0
        for tr in table.find_all('tr'):

            t_row = {}
            for td, th in zip(tr.find_all('td'), headers):
                # Parse the rest of the information as text
                t_row[th] = td.text.strip()

                if t_row[th] == '1INCH':
                    pass
                if len(table_data) > 0 and th == 'Монета':
                    # The following information came from the first parsed column only.
                    # 1. Parse the time when the wall was created (inside the title's attribute in second img tag)
                    s_datetime = td.findAll('img')[1].get('title')  # 2023-06-14 04:06:37 (111.1 ч. назад)
                    # This time is GMT+3 (Moscow Zone). We have to remove 3 hours
                    if s_datetime is not None:
                        s_datetime = re.sub(r'\(.*?\)', '', s_datetime).strip()  # 2023-06-14 04:06:37
                        t_row['Created'] = datetime.strptime(s_datetime, '%Y-%m-%d %H:%M:%S') - timedelta(hours=3)
                    else:
                        t_row['Created'] = datetime.utcnow()  # Instead of none
                    # Parse the link to the coin
                    t_row['Link'] = td.find('a').get('href').replace('/ru','/en')  # I will rename /ru to /en
            table_data.append(t_row)
        table_data.pop(0)
        # create a pandas dataframe from the table data
        df = pd.DataFrame(table_data)

        # renaming columns
        df.columns = ['Updated seconds ago','Coin','Created','Link','USD per level','Estimate time to corrode (mins)','Price',
                      'Coins per level','To level %']

        # set the index to the Coin
        df.set_index("Coin", inplace=True)
        # extract the info in parentheses into a new column 'Amount left'
        df['Amount left %'] = df['USD per level'].str.extract('\((.*?)\)')
        # remove the '% left' and cast it to float.
        df['Amount left %'] = df['Amount left %'].str.replace('[^\.|\d]', '', regex=True)
        # remove the parenthesis from the 'USD per level' column
        df['USD per level'] = df['USD per level'].str.replace('\s\(.*?\)', '', regex=True).str.strip()
        # create new column to convert to numeric value. Replace K to 1000 and M to 1000000
        df['Amount'] = df['USD per level'].apply(utils.convert_units).astype(float)
        # format 'To level %' column as float. This is the distance from the current price to the level
        df['To level %'] = df['To level %'].str.replace('%','').str.rstrip().astype(float)
        # create a column to measure the distance to level in absolute values
        df['Distance'] = df['To level %'].abs()
        # create a new column for Order type depending on the distance to the wall (above or below)
        df['Wall type'] = np.where(df['To level %'] > 0, 'sell','buy')
        # convert the created column to pandas datetime
        df['Created'] = pd.to_datetime(df['Created'])
        # calculate the time (in minutes) the wall was created. We are going to calculate from the Created column
        # we are going to use this column to create the icon for the alert (moon emoji icon)
        df['Elapsed Minutes'] = round((datetime.utcnow() - df['Created']).dt.total_seconds() / 60)
        # order the data frame distance to level
        df.sort_values('Distance', ascending=True, inplace=True)
        # cached the dataframe
        df.to_csv(self.filename)
        # measure the time it took to complete the web scrapping
        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time >= 60:
            elapsed_time_minutes = elapsed_time / 60
            print("Scrapping time:", elapsed_time_minutes, "minutes")
        else:
            print("Scrapping time:", elapsed_time, "seconds")

        return df





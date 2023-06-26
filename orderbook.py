import datetime
import pandas as pd
from millify import millify
import config
import time
import os
import requests
from bybit_orderbook import Bybit
from okex_orderbook import OKEx
from binance_orderbook import Binance
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.signal import find_peaks

class OrderBook():
    """
    Retrieves the aggregated order book from exchanges (Binance, OKex, Bybit)
    and compose a png file to send to the user.
    Special credits to https://github.com/suleymanozkeskin and
    https://github.com/suleymanozkeskin/btc_aggregated_orderbook

    The code from btc_aggregated_orderbook has been improved
    to include price rounding and better plotting features.
    """

    # cached data for 1 minute
    csv = ""
    order_book_image = ""
    # dataframe
    dataframe = pd.DataFrame()
    # updated time
    updated_time = datetime.datetime.utcnow().timestamp()

    def __init__(self, min_wallsize = 100000):
        # get the proper filename
        self.csv = config.order_book_data
        self.order_book_image = config.order_book_image
        self.wallsize = min_wallsize
        self.refresh_order_book()

    def refresh_order_book(self):
        # load the dataframe from server when more than 1 minute has elapsed since the last retrieved file
        if self.elapsed_more_than_minute():
            # Initialize exchange objects
            bybit = Bybit('Bybit', 'https://api.bybit.com/', 1.0)
            okex = OKEx('OKEx', 'https://www.okex.com/', 1.0)
            binance = Binance('Binance', 'https://api.binance.com/', 1.0)

            # Fetch orderbook data
            bybit_orderbook = bybit.fetch_orderbook()
            okex_orderbook = okex.fetch_orderbook()
            binance_orderbook = binance.fetch_orderbook()

            # Select only the relevant columns for each DataFrame
            bybit_orderbook = bybit_orderbook[['Price', 'Size', 'Side']]
            okex_orderbook = okex_orderbook[['Price', 'Size', 'Side']]
            binance_orderbook = binance_orderbook[['Price', 'Size', 'Side']]

            # Concatenate the modified DataFrames
            orderbook = pd.concat([bybit_orderbook, okex_orderbook, binance_orderbook], ignore_index=True)

            # You may want to sort the orderbook based on price
            orderbook = orderbook.sort_values(by=['Price'], ascending=False).reset_index(drop=True)

            # Save the orderbook to a csv file
            orderbook.to_csv(self.csv, index=False)
        else:
            orderbook = pd.read_csv(self.csv)

        # Get the current BTC price from binance
        response = requests.get('https://api.binance.com/api/v3/ticker/price', params={'symbol': 'BTCUSDT'})
        current_price = float(response.json()['price'])

        # Optional: remove the bids greater than current_price
        # Optional: remove the asks lower than current price

        # Calculate cumulative sums for buy and sell sides
        """
        In this modified code, after sorting the dataframe by price in ascending order, we calculate the cumulative bids as before. However, for the cumulative asks, we reverse the order of the 'Size' column for asks using [::-1], calculate the cumulative sum with cumsum(), and then reverse the order again to get the correct accumulation from the minimum to the maximum price.
        By reversing the asks' 'Size' column, the cumulative sum is calculated starting from the maximum price. Then, reversing it back ensures that the cumulative asks are plotted correctly against the price.
        """
        orderbook['SizeUSD'] = orderbook['Size'] * orderbook['Price']
        orderbook['Buy'] = orderbook[orderbook['Side'] == 'buy']['SizeUSD'].cumsum()
        orderbook['Sell'] = orderbook[orderbook['Side'] == 'sell']['SizeUSD'][::-1].cumsum()[::-1]

        # Separate buy and sell data
        bids = orderbook[(orderbook['Side'] == 'buy')]
        asks = orderbook[(orderbook['Side'] == 'sell')]
        # Find peaks (buy walls) based on size value in USD
        bids_peaks, _ = find_peaks(bids['SizeUSD'].values, prominence=self.wallsize)
        # Sort the buy peaks by size in descending order
        sorted_bids_peaks = bids.iloc[bids_peaks].sort_values('SizeUSD', ascending=False)
        # Find peaks (sell walls) based on size value in USD
        asks_peaks, _ = find_peaks(asks['SizeUSD'].values, prominence=self.wallsize)
        # Sort the sell peaks by size in descending order
        sorted_asks_peaks = asks.iloc[asks_peaks].sort_values('SizeUSD', ascending=False)

        # Sum the total Buy and Sell size
        buy_size = bids['SizeUSD'].sum()
        sell_size = asks['SizeUSD'].sum()
        # Calculate the Bid-Ask ratio
        bid_ask_ratio = buy_size / sell_size

        # Start plotting
        plt.figure(figsize=(8, 6))  # Width: 8 inches, Height: 6 inches
        plt.style.use('dark_background')
        plt.title("Aggregated Orderbook BTC/USD")
        # Plot the updated cumulative sums for buy and sell sides
        plt.plot(orderbook['Price'], orderbook['Buy'], label='Buy', color='g')
        plt.plot(orderbook['Price'], orderbook['Sell'], label='Sell', color='r')

        # Add annotations for the most prominent buy walls
        for index, row in sorted_bids_peaks.head(3).iterrows():
            annotation_text = f"{millify(row['SizeUSD'],1)} USD @ {row['Price']:.0f}"
            plt.annotate(annotation_text, xy=(row['Price'], row['Buy']), xytext=(-20, -15),
                         textcoords='offset points', arrowprops=dict(arrowstyle="->", color='yellow'))

        # Add annotations for the most prominent sell walls
        for index, row in sorted_asks_peaks.head(3).iterrows():
            annotation_text = f"{millify(row['SizeUSD'],1)} USD @ {row['Price']:.0f}"
            plt.annotate(annotation_text, xy=(row['Price'], row['Sell']), xytext=(-20, 15),
                         textcoords='offset points', arrowprops=dict(arrowstyle="->", color='orange'))

        plt.xlabel('Price')
        plt.ylabel('Cumulative Size')
        # Define custom formatter function to display y-axis values in millions
        formatter = ticker.FuncFormatter(lambda x, pos: f'{x / 1e6:.0f}M')
        plt.gca().yaxis.set_major_formatter(formatter)

        plt.legend(loc='lower right')

        # Add text to display current price and buy/sell analysis within the price range
        plt.text(0.03, 0.03, f'Current Price: {current_price:.0f}', transform=plt.gca().transAxes, ha='left')
        plt.text(0.03, 0.08, f'Buy Size: {millify(buy_size,1)}', transform=plt.gca().transAxes, ha='left')
        plt.text(0.03, 0.13, f'Sell Size: {millify(sell_size,1)}', transform=plt.gca().transAxes, ha='left')
        plt.text(0.03, 0.18, f'Bid/Ask Ratio: {bid_ask_ratio:.2f}', transform=plt.gca().transAxes, ha='left')

        plt.savefig(self.order_book_image)


    def elapsed_more_than_minute(self):
        """
        Check the last time the file was retrieved from the server to avoid multiple
        web scraps in a short period of time. We're going to cache the information
        for one minute and retrieve it again after that time.
        :return: True if more than one minute has passed. Otherwise, False.
        """
        if not os.path.isfile(self.csv):
            # file does not exists, return True
            return True
        modification_time = os.path.getmtime(self.csv)
        current_time = time.time()
        return current_time - modification_time > 60  # more than 60 seconds

    def get_caption(self):
        """
        We retrieve extra information to send as caption with the image
        to the Telegram chat.
        We're going to calculate the last time the orderbook was updated
        in a user-friendly format and the exchanges we're pulling the data.
        :return: Last updated YYYY-mm-dd HH:mm ~ 5 seconds ago
        """
        modification_time = os.path.getmtime(self.csv)
        dt = datetime.datetime.utcfromtimestamp(modification_time)
        formatted = dt.strftime("%Y-%m-%d %H:%M")
        time_difference = datetime.datetime.utcnow() - dt
        seconds_difference = time_difference.total_seconds()
        time_ago = f"{int(seconds_difference)} second{'s' if int(seconds_difference) > 1 else ''} ago"
        message = f"BTC-USDT from Binance, OKX, ByBit.\n"\
                  f"Updated on {formatted} ({time_ago})"
        return message


if __name__ == '__main__':
    print('__main__')
    ob = OrderBook(200000)


import os
import numpy as np
import time
import datetime
import requests
import asyncio
import ccxt.async_support as ccxt
import pandas as pd
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import config
from millify import millify

class AggregatedOrderBook():
    """
    This class implement Order Book reading for any specific symbol
    based on a list of exchanges supported by CCXT library.
    More info here: https://github.com/ccxt/ccxt/wiki/Exchange-Markets
    The library will cache the file in the disk for 1-minute.
    Calling the function get_order_book() multiple times within 1-minute
    window will deliver the same Bid/Ask information.
    The function also generates a chart and saves it to the disk.
    You can read the OB chart in the order_book_image property.
    How to use this class:

    api_keys = {
        'binance': {},
        'okex': {}
    }
    exchanges = ['binance', 'okex', 'bybit']
    order_book = AggregatedOrderBook(exchanges, api_keys, symbol)
    status = await order_book.get_order_book()
    if not status:
        # handle error
    await order_book.generate_chart()
    await order_book.close()

    - api_keys are optional (not required).
    - Symbol should be in the accepted format by exchanges. For example: BTCUSDT, ETHUSDT, DOGEUSDT, ADAUSDT
    - You can then access to order_book.order_book_image to get the chart (PNG).
    - You can also access order_book.get_caption() to get the caption to be associated with the generated image.
    """

    symbol = ""
    order_book_image = ""
    order_book_csv = ""

    aggregated_bids = pd.DataFrame()
    aggregated_asks = pd.DataFrame()
    bids_peaks = pd.DataFrame()
    asks_peaks = pd.DataFrame()

    buy_size = 0
    sell_size = 0
    bid_ask_ratio = 0

    exchange_abbr = {
        'binance': 'binance',
        'okx': 'okx',
        'bybit': 'bybit'
    }

    def __init__(self, exchanges, api_keys, symbol):
        self.exchanges = {}
        self.markets = {}
        self.symbol = symbol
        self.order_book_image = os.path.join(config.data_path, symbol.replace("/","")+".png")
        self.order_book_csv = os.path.join(config.data_path, symbol.replace("/","")+".csv")

        for exchange in exchanges:
            # Ensure the exchange is supported by ccxt
            if exchange not in ccxt.exchanges:
                print(f'Exchange {exchange} is not supported.')
                continue

            if exchange in api_keys:
                api_key = api_keys[exchange]["api_key"]
                secret = api_keys[exchange]["secret"]
                self.exchanges[exchange] = getattr(ccxt, exchange)({
                    'apiKey': api_key,
                    'secret': secret,
                    'enableRateLimit': True,
                    "options": {'defaultType': 'spot'}
                })
            else:
                self.exchanges[exchange] = getattr(ccxt, exchange)({
                    'enableRateLimit': True,
                    "options": {'defaultType': 'spot'}
                })

    async def load_markets(self):
        for name, exchange in self.exchanges.items():
            try:
                self.markets[name] = await exchange.load_markets()
            except Exception as e:
                print(f'Error loading markets from {exchange}: {e}')

    async def get_order_book(self, wallsize=100000):
        """
        Retrieve order book from exchanges.
        :param wallsize: Use this value to identify walls equal or bigger of this size in USD.
        :return: The full order book with bids and asks
        """
        order_books = {}
        order_books_df = pd.DataFrame()
        cached = False
        if not self.elapsed_more_than_minute():
            # The saved file is less than 1 minute old (cached version to avoid overload to exchanges)
            order_books_df = pd.read_csv(self.order_book_csv)
            cached = True
        else:
            if len(self.markets) == 0:
                #print("Please call load_markets() first to retrieve available symbols.")
                await self.load_markets()

            for name, exchange in self.exchanges.items():
                if self.symbol in self.markets[name]:
                    try:
                        order_books[name] = await exchange.fetch_order_book(self.symbol)
                        for side in ['bids', 'asks']:
                            if order_books[name][side]:
                                df = pd.DataFrame(order_books[name][side], columns=['Price', 'Size'])
                                df['Side'] = 'buy' if side == 'bids' else 'sell'
                                df['Exchange'] = name
                                df['SizeUSD'] = df['Price'] * df['Size']
                                order_books_df = pd.concat([order_books_df, df], ignore_index=True)
                    except Exception as e:
                        print(f'Error fetching order book from {name}: {e}')
                else:
                     print(f'Exchange {name} does not support symbol {self.symbol}.')

            if len(order_books_df.index) == 0:
                return False

        # Get the current price from binance (even if we have cached OB data)
        response = requests.get('https://api.binance.com/api/v3/ticker/price', params={'symbol': self.symbol.replace("/","")})
        self.current_price = float(response.json()['price'])

        # Sometimes the exchanges have slightly different prices for this reason we're going to
        # remove all asks lower than current price and all bids higher"
        self.aggregated_bids = order_books_df[(order_books_df['Side'] == 'buy') &
                                              (order_books_df['Price'] < self.current_price)].copy()
        self.aggregated_asks = order_books_df[(order_books_df['Side'] == 'sell') &
                                              (order_books_df['Price'] > self.current_price)].copy()

        # Sort by price
        self.aggregated_bids.sort_values("Price", ascending=False, inplace=True)
        self.aggregated_asks.sort_values("Price", ascending=False, inplace=True)

        # Calculate the cumulative quantities
        self.aggregated_bids['Buy'] = self.aggregated_bids['SizeUSD'].cumsum()
        self.aggregated_asks['Sell'] = self.aggregated_asks['SizeUSD'][::-1].cumsum()[::-1]

        # Initialize 'Peak' column with False values
        self.aggregated_bids['Peak'] = False
        self.aggregated_asks['Peak'] = False

        # Find peaks (buy walls) based on size value in USD
        bids_peaks, _ = find_peaks(self.aggregated_bids['SizeUSD'].values, prominence=wallsize)
        # Sort the buy peaks by size in descending order
        self.bids_peaks = self.aggregated_bids.iloc[bids_peaks].sort_values('SizeUSD', ascending=False)
        # Get the actual DataFrame index values for peak indices
        bids_peaks_index = self.aggregated_bids.iloc[bids_peaks].index
        # Set 'Peak' value to True for peak indices
        self.aggregated_bids.loc[bids_peaks_index, 'Peak'] = True

        # Find peaks (sell walls) based on size value in USD
        asks_peaks, _ = find_peaks(self.aggregated_asks['SizeUSD'].values, prominence=wallsize)
        # Sort the sell peaks by size in descending order
        self.asks_peaks = self.aggregated_asks.iloc[asks_peaks].sort_values('SizeUSD', ascending=False)
        # Get the actual DataFrame index values for peak indices
        asks_peaks_index = self.aggregated_asks.iloc[asks_peaks].index
        # Set 'Peak' value to True for peak indices
        self.aggregated_asks.loc[asks_peaks_index, 'Peak'] = True

        # Sum the total Buy and Sell size
        self.buy_size = self.aggregated_bids['SizeUSD'].sum()
        self.sell_size = self.aggregated_asks['SizeUSD'].sum()
        # Calculate the Bid-Ask ratio
        self.bid_ask_ratio = self.buy_size / self.sell_size

        # Compose a dataframe to return
        order_books_df = pd.concat([self.aggregated_asks, self.aggregated_bids], ignore_index=True)

        # Save to file
        if not cached:
            order_books_df.to_csv(self.order_book_csv)

        return True

    def custom_formatter(self, x, pos):
        if x >= 1e6:
            return f'{x / 1e6:.1f}M'
        else:
            return f'{x / 1e3:.1f}K'

    async def generate_chart(self):
        if self.sell_size == 0 or self.buy_size == 0 or self.current_price == 0:
            print("Please call get_order_book() first")
            return False

        # Start plotting
        plt.figure(figsize=(8, 6))  # Width: 8 inches, Height: 6 inches
        plt.style.use('dark_background')
        plt.title(f"Aggregated Orderbook {self.symbol}")
        # Plot the updated cumulative sums for buy and sell sides
        plt.plot(self.aggregated_bids['Price'], self.aggregated_bids['Buy'], label='Buy', color='g')
        plt.plot(self.aggregated_asks['Price'], self.aggregated_asks['Sell'], label='Sell', color='r')

        # Add annotations for the most prominent buy walls
        for index, row in self.bids_peaks.head(3).iterrows():
            annotation_text = f"${millify(row['SizeUSD'], 1)}  @ {row['Price']} ({row['Exchange']})"
            plt.annotate(annotation_text, xy=(row['Price'], row['Buy']), xytext=(-20, -15),
                         textcoords='offset points', arrowprops=dict(arrowstyle="->", color='yellow'))

        # Add annotations for the most prominent sell walls
        for index, row in self.asks_peaks.head(3).iterrows():
            annotation_text = f"${millify(row['SizeUSD'], 1)} @ {row['Price']} ({row['Exchange']})"
            plt.annotate(annotation_text, xy=(row['Price'], row['Sell']), xytext=(10, -15),
                         textcoords='offset points', arrowprops=dict(arrowstyle="->", color='orange'))

        plt.xlabel('Price')
        plt.ylabel('Cumulative Size')
        # Define custom formatter function to display y-axis values in millions
        formatter = ticker.FuncFormatter(self.custom_formatter)
        plt.gca().yaxis.set_major_formatter(formatter)

        plt.legend(loc='lower right')

        # Add text to display current price and buy/sell analysis within the price range
        plt.text(0.03, 0.03, f'Current Price: {self.current_price}', transform=plt.gca().transAxes, ha='left')
        plt.text(0.03, 0.08, f'Buy Size: {millify(self.buy_size,1)}', transform=plt.gca().transAxes, ha='left')
        plt.text(0.03, 0.13, f'Sell Size: {millify(self.sell_size,1)}', transform=plt.gca().transAxes, ha='left')
        plt.text(0.03, 0.18, f'Bid/Ask Ratio: {self.bid_ask_ratio:.2f}', transform=plt.gca().transAxes, ha='left')

        plt.savefig(self.order_book_image)

    async def close(self):
        await asyncio.gather(*[exchange.close() for exchange in self.exchanges.values()])

    def elapsed_more_than_minute(self):
        """
        Check the last time the file was retrieved from the server to avoid multiple
        web scraps in a short period of time. We're going to cache the information
        for one minute and retrieve it again after that time.
        :return: True if more than one minute has passed. Otherwise, False.
        """
        if not os.path.isfile(self.order_book_csv):
            # file does not exists, return True
            return True
        modification_time = os.path.getmtime(self.order_book_csv)
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
        if not os.path.isfile(self.order_book_csv):
            return ""
        modification_time = os.path.getmtime(self.order_book_csv)
        dt = datetime.datetime.utcfromtimestamp(modification_time)
        formatted = dt.strftime("%Y-%m-%d %H:%M")
        time_difference = datetime.datetime.utcnow() - dt
        seconds_difference = time_difference.total_seconds()
        time_ago = f"{int(seconds_difference)} second{'s' if int(seconds_difference) != 1 else ''} ago"
        message = f"{self.symbol} from {', '.join(self.exchanges)}.\n"\
                  f"Updated on {formatted} ({time_ago})"
        return message


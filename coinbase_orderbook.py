# orderbook/coinbase_orderbook.py
import requests
import pandas as pd
import numpy as np

class Exchange:
    def __init__(self, name, api_url, rounding = 1.0):
        self.name = name
        self.api_url = api_url
        self.rounding = rounding

    def fetch_orderbook(self):
        raise NotImplementedError()

class Coinbase(Exchange):
    def fetch_orderbook(self):
        response = requests.get(self.api_url + 'products/BTC-USD/book?level=2')
        data = response.json()
        bids = pd.DataFrame(data['bids'], columns=['Price', 'Size', '_'], dtype=float)
        if self.rounding > 0:
            # Round the prices to the nearest multiple of self.rounding
            bids['Rounded'] = np.round(bids['Price'] / self.rounding) * self.rounding
            # Group by the rounded prices and sum the sizes
            bids = bids.groupby('Rounded', as_index=False).agg({'Size': 'sum'}).reset_index()
        bids['Side'] = 'buy'
        asks = pd.DataFrame(data['asks'], columns=['Price', 'Size', '_'], dtype=float)
        if self.rounding > 0:
            # Round the prices to the nearest multiple of self.rounding
            asks['Price'] = np.round(asks['Price'] / self.rounding) * self.rounding
            # Group by the rounded prices and sum the sizes
            asks = asks.groupby('Price', as_index=False).agg({'Size': 'sum'})
        asks['Side'] = 'sell'
        return pd.concat([bids, asks], ignore_index=True)

if __name__ == '__main__':
    coinbase = Coinbase('Coinbase', 'https://api.pro.coinbase.com/')
    print(coinbase.fetch_orderbook())

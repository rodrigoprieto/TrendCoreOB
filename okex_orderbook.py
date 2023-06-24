# orderbook/okex_orderbook.py
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

class OKEx(Exchange):
    def fetch_orderbook(self):
        response = requests.get(self.api_url + 'api/v5/market/books?instId=BTC-USDT&sz=400')  # Add sz parameter here
        data = response.json()
        if data.get('code') == '0':
            orderbook = data['data'][0]  # Access the first element of the data array
            bids = pd.DataFrame(orderbook['bids'], columns=['Price', 'Size', '_', '_'], dtype=float)
            if self.rounding > 0:
                # Round the prices to the nearest multiple of self.rounding
                bids['Price'] = np.round(bids['Price'] / self.rounding) * self.rounding
                # Group by the rounded prices and sum the sizes
                bids = bids.groupby('Price', as_index=False).agg({'Size': 'sum'})
            bids['Side'] = 'buy'
            asks = pd.DataFrame(orderbook['asks'], columns=['Price', 'Size', '_', '_'], dtype=float)
            if self.rounding > 0:
                # Round the prices to the nearest multiple of self.rounding
                asks['Price'] = np.round(asks['Price'] / self.rounding) * self.rounding
                # Group by the rounded prices and sum the sizes
                asks = asks.groupby('Price', as_index=False).agg({'Size': 'sum'})
            asks['Side'] = 'sell'
            return pd.concat([bids, asks], ignore_index=True)
        else:
            print('Error fetching orderbook:', data.get('msg'))
            return None



if __name__ == '__main__':
    okex = OKEx('OKEx', 'https://www.okex.com/')
    print(okex.fetch_orderbook())

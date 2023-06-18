# TrendCore Order Book Information Parser

This repository contains a Python application that retrieves and parses Order Book information from [TrendCore](https://trendcore.ru/) and sends the data to a Telegram bot.

## Features

- Retrieves Order Book information from [TrendCore](https://trendcore.ru/)
- Parses the data into a Pandas DataFrame, calculating the time for each bid and ask wall.
- 
- Sets up a Telegram bot for retrieving the Order Book information.
- Outputs the parsed data to the Telegram bot on command.

## Installation

Here are the steps to install and run this application:

1. Clone this repository to your local machine.

2. Create a virtual environment:
    ```
    python3 -m venv venv
    ```

3. Activate the virtual environment:
    - On Windows:
      ```
      .\venv\Scripts\activate
      ```
    - On Unix or MacOS:
      ```
      source venv/bin/activate
      ```

4. Install the required packages:
    ```
    pip install -r requirements.txt
    ```

5. Create a Telegram bot and generate a Telegram authentication token (you can follow [this guide](https://core.telegram.org/bots#3-how-do-i-create-a-bot)).

6. Copy `config.default.py` into a new file named `config.py`.

7. Update your Telegram token in the `config.py` file.

8. Run the main script:
    ```
    python3 main.py
    ```

9. Open your Telegram app, navigate to your bot's chat, type `/start` and then `/data` to retrieve coin information.

## Future Work

We plan to continually improve this bot and expand its capabilities. Stay tuned for updates!

Feel free to contribute to this project by creating a pull request or opening an issue.

## Donations
Do you find Trendcore useful? Consider supporting the developer (not me). I just built this app
to use this amazing tool from Telegram.
Below are the wallet addresses with the lowest fees (BSC).
All addresses are the same and correct.

BUSD (BEP20 - Binance Smart Chain)
Address: 0x9b1399898436cf865cedcb67fad7599a127165a3

BNB (BEP20 - Binance Smart Chain)
Address: 0x9b1399898436cf865cedcb67fad7599a127165a3

BTC (BEP20 - Binance Smart Chain)
Address: 0x9b1399898436cf865cedcb67fad7599a127165a3

ETH (BEP20 - Binance Smart Chain)
Address: 0x9b1399898436cf865cedcb67fad7599a127165a3

USDT (BEP20 - Binance Smart Chain)
Address: 0x9b1399898436cf865cedcb67fad7599a127165a3

USDT (TRC20 - Tron network)
Address: TVvJLRA9xCNDoqJX3R15tvaFHq97oSLiBj

Your support is greatly appreciated!
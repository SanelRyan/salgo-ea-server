# Project: MetaTrader5 WebSocket Trading Bot

## Overview

Python MT5 EA that integrates MT5 with WebSocket-based signals to execute and manage trades based on real-time data. The bot connects to MT5, listens for WebSocket signals, and automatically places or closes trades based on the received instructions.

## Features

-   **Real-Time Trade Execution**: The bot listens for WebSocket signals that indicate entry or exit points for trades, executing them instantly on MetaTrader 5.
-   **Dynamic Handling of Buy/Sell Actions**: Based on the WebSocket message, the bot can handle both long (buy) and short (sell) positions.
-   **Auto Retry WebSocket Connection**: In case of connection issues, the bot automatically retries connecting to the WebSocket based on a pre-configured retry logic.
-   **Auto Trade Management**: Upon receiving a new entry signal, the bot closes all existing positions for the symbol before placing a new trade to ensure smooth management of trades.
-   **Color-Coded Terminal Output**: It uses `colorama` to provide color-coded logs for easier tracking of events like trade success, failure, connection attempts, and errors.

## Requirements

-   **MetaTrader 5** (MT5) account with login credentials.
-   **WebSocket** URL to receive trade signals.
-   A `config.json` file containing the following fields:
    -   `symbols`: A dictionary of symbols (assets) and their respective lot sizes.
    -   `retry_attempts`: Number of times to retry WebSocket connection upon failure.
    -   `retry_delay`: Delay (in seconds) between retry attempts.

## Setup

1. **Install the required dependencies**:

    ```bash
    pip install MetaTrader5 websocket-client colorama python-dotenv
    ```

2. **Prepare the Environment**:

    - Create a `.env` file in the project directory with your MT5 account information:

        ```
        MT5_LOGIN=your_login
        MT5_PASSWORD=your_password
        MT5_SERVER=your_server
        ```

    - Create a `config.json` file in the project directory. Example:

        ```json
        {
        	"symbols": {
        		"EURUSD": 0.1,
        		"GBPUSD": 0.1
        	},
        	"retry_attempts": 5,
        	"retry_delay": 10
        }
        ```

3. **Run the Bot**:

    Simply execute the Python script:

    ```bash
    python bot.py
    ```

    During execution, you'll be prompted to enter the WebSocket URL.

## How it Works

1. **WebSocket Connection**:
   The bot establishes a WebSocket connection to listen for real-time trade signals (e.g., buy/sell, entry/exit).

2. **Handling WebSocket Messages**:
   When the bot receives a WebSocket message, it processes the data to determine whether to place a new trade or close existing positions based on the message's `action` field (`entry` or `exit`).

3. **MT5 Trade Execution**:
   The bot uses MetaTrader 5's API to send trade requests. It calculates the buy or sell price based on current market data and executes the trade accordingly.

4. **Connection Retry**:
   If the WebSocket connection fails, the bot retries based on the `retry_attempts` and `retry_delay` configured in `config.json`.

## Key Functions

-   **on_message(ws, message)**: Processes incoming WebSocket messages to determine trading actions (entry/exit).
-   **execute_trade(symbol, position, price)**: Sends the buy/sell order to MetaTrader 5 based on the signal received.
-   **close_trade(symbol)**: Closes all existing open positions for the given symbol.
-   **start_websocket()**: Manages the WebSocket connection and retries in case of connection failures.
-   **main()**: Initializes the MetaTrader 5 API and starts the WebSocket listener.

## Error Handling

-   The bot logs detailed error messages using `colorama` for enhanced readability, including issues with trade execution, WebSocket messages, and connection failures.
-   If MT5 initialization fails, the bot terminates gracefully with an appropriate message.

## License

This project is licensed under the **BSD 2-Clause License**. See the `LICENSE` file for details.

---

**Author**: SanelRyan

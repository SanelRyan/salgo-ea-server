# Salgo Trading EA Server

### Overview

The **Salgo Trading EA Server** is a Python-based application that listens for trade commands from a webhook server, which is triggered by TradingView alerts. This server processes signals to either open or close trades on MetaTrader 5 (MT5) for supported trading pairs like BTCUSD and XAUUSD.

---

### Features

-   **Real-time WebSocket Connectivity**: The server listens for WebSocket messages, decoding them into trade actions.
-   **Automated Trade Execution**: Upon receiving a signal (entry or exit), the EA closes existing trades for the given symbol and executes the appropriate buy/sell action.
-   **Trade Management**: Trades are managed with pre-defined lot sizes, and open positions are automatically closed when a new entry signal is received.
-   **Error Handling**: The system handles WebSocket errors and trade failures gracefully, logging them with descriptive messages.

---

### Supported Trading Pairs

-   **BTCUSD**: 0.1 lot size
-   **XAUUSD**: 0.06 lot size

---

### How It Works

1. **WebSocket Connection**: The EA server connects to a WebSocket URL, which should be provided by the user during startup.
2. **Trade Actions**:
    - **Entry Signal**: When an "entry" signal is received for a symbol (e.g., BTCUSD), the server:
        1. Closes all open positions for that symbol.
        2. Opens a new position (buy or sell) based on the provided direction (`long` or `short`).
    - **Exit Signal**: When an "exit" signal is received, the server closes all open positions for that symbol.
3. **Error Handling**: If an unknown action or error occurs, the server prints a detailed error message.

---

### Installation

1. **Install Requirements**:

    ```bash
    pip install MetaTrader5 websocket-client colorama
    ```

2. **Setup MetaTrader 5**:
   Ensure that you have MetaTrader 5 installed on your machine, and that it is properly connected to your broker's server.

3. **Run the Server**:
   Execute the following command:

    ```bash
    python salgo_ea_server.py
    ```

    You will be prompted to enter the WebSocket URL.

---

### WebSocket Message Structure

The WebSocket server expects incoming messages in JSON format, as shown below:

```json
{
	"symbol": "BTCUSD",
	"action": "entry", // 'entry' for new trades, 'exit' for closing positions
	"price": 20000.5, // Current price (for logging purposes)
	"position": "long" // 'long' for buy, 'short' for sell
}
```

### Example Execution Flow

1. **Entry Signal**:
    - WebSocket message is received:
        ```json
        {
        	"symbol": "XAUUSD",
        	"action": "entry",
        	"price": 1800.5,
        	"position": "long"
        }
        ```
    - The system closes all XAUUSD positions and opens a new buy position.
2. **Exit Signal**:
    - WebSocket message is received:
        ```json
        {
        	"symbol": "BTCUSD",
        	"action": "exit",
        	"price": 22000.0
        }
        ```
    - The system closes all open BTCUSD positions.

---

### Logging & Emojis

The server uses **Colorama** for color-coded console output and emojis to highlight different trade statuses:

-   🟢 Entry signals
-   ⚠️ Exit signals
-   ✅ Successful trades
-   ❌ Failed trades

---

### Contributing

Feel free to fork this repository and submit pull requests. All contributions that enhance the automation of trade execution and signal processing are welcome!

---

### License

This project is unlicensed.

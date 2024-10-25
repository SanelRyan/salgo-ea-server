import MetaTrader5 as mt5
from websocket import WebSocketApp
import json
from colorama import Fore, Style, init
from dotenv import load_dotenv
import os
import time
import threading
from datetime import datetime

import atexit
import signal
import sys

init(autoreset=True)
load_dotenv()

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

lotList = config['symbols']
retry_attempts = config["retry_attempts"]
retry_delay = config["retry_delay"]

log_file = "ea.log"

def logit(message, shouldPrintToo=False, color_code=""):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted_message = f"[{timestamp}] {message}"
    
    with open(log_file, 'a', encoding="utf-8") as f:
        f.write(f"{formatted_message}\n")
    
    if shouldPrintToo:
        colored_message = f"{color_code}{message}{Style.RESET_ALL}"
        print(colored_message)

def input_websocket_url():
    return input("Enter the WebSocket URL: ")

def on_message(ws, message):
    try:
        data = json.loads(message)
        symbol = data['symbol']
        action = data['action']
        price = data['price']
        position = data['position']

        if action == 'entry':
            logit(f"🟢 New entry signal received for {symbol} at {price}. Closing all trades first...", True, Fore.CYAN)
            close_trade(symbol)
            execute_trade(symbol, position, price)
        elif action == 'exit':
            logit(f"⚠️ Exit signal received for {symbol}. Closing open positions...", True, Fore.YELLOW)
            close_trade(symbol)
        else:
            logit(f"❌ Unknown action: {action}", True, Fore.RED)
    except Exception as e:
        logit(f"❗ Error processing message: {e}", True, Fore.RED)

def calculate_tp_sl(lot, price, lshort):
    leverage = config["leverage"]
    tp_value = config["tp_value"]
    sl_value = config["sl_value"]
    
    if lshort == "long":
        tp = price + (tp_value / (lot * leverage))
        sl = price - (sl_value / (lot * leverage))
    else:
        tp = price - (tp_value / (lot * leverage))
        sl = price + (sl_value / (lot * leverage))
    
    return tp, sl

def execute_trade(symbol, position, price):
    if position == 'long':
        order_type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask
        logit(f"📈 Executing long trade for {symbol} at {price}.", True, Fore.GREEN)
    elif position == 'short':
        order_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
        logit(f"📉 Executing short trade for {symbol} at {price}.", True, Fore.RED)
    else:
        logit(f"❌ Unknown position: {position}", True, Fore.RED)
        return

    lot = lotList[symbol]
    tp, sl = calculate_tp_sl(lot, price, position)

    order_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "type": order_type,
        "volume": lot,
        "price": price,
        "deviation": 20,
        "tp": tp,
        "sl": sl,
        "magic": 244,
        "comment": "Webhook trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(order_request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logit(f"❌ Order failed for {symbol}: {result.retcode}, {result.comment}", True, Fore.RED)
    else:
        logit(f"✅ Order successful for {symbol}: {order_request}", True, Fore.GREEN)

def close_trade(symbol):
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        logit(f"⚠️ Closing open positions for {symbol}...", True, Fore.YELLOW)
        for position in positions:
            order_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "type": mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "volume": position.volume,
                "price": mt5.symbol_info_tick(symbol).bid if position.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(symbol).ask,
                "deviation": 20,
                "magic": 244,
                "position": position.ticket,
                "comment": "Webhook close trade",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }

            result = mt5.order_send(order_request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logit(f"❌ Close order failed for {symbol}: {result.retcode}, {result.comment}", True, Fore.RED)
            else:
                logit(f"✅ Closed position for {symbol}: {position.ticket}", True, Fore.GREEN)
    else:
        logit(f"⚠️ No open positions found for symbol {symbol}", True, Fore.YELLOW)

def on_error(ws, error):
    logit(f"❗ WebSocket error: {error}", True, Fore.RED)

def on_close(ws, close_status_code, close_msg):
    logit(f"🔒 WebSocket connection closed with code: {close_status_code}, reason: {close_msg}", True, Fore.CYAN)

def on_open(ws):
    logit(f"🔓 WebSocket connection opened", True, Fore.GREEN)

def keepAlive(ws):
    while True:
        ws.ping()
        time.sleep(30)

def start_websocket():
    for attempt in range(retry_attempts):
        try:
            logit(f"🔗 Attempting WebSocket connection (attempt {attempt + 1})...", True, Fore.GREEN)
            ws = WebSocketApp(input_websocket_url(),
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
            ws.on_open = on_open
            ws.run_forever()
            keepAliveThread = threading.Thread(target=keepAlive, args=(ws,))
            keepAliveThread.daemon = True
            keepAliveThread.start()
            break
        except Exception as e:
            logit(f"❗ WebSocket connection failed: {e}", True, Fore.RED)
            time.sleep(retry_delay)

def handle_exit(signum=None, frame=None):
    logit("🔒 Script is exiting due to signal or exception", True, Fore.CYAN)
    sys.exit(0)

def handle_exception(exc_type, exc_value, exc_traceback):
    if not issubclass(exc_type, KeyboardInterrupt):
        logit(f"❗ Unhandled exception: {exc_value}", True, Fore.RED)
    handle_exit()

def register_exit_handlers():
    signal.signal(signal.SIGINT, handle_exit) 
    signal.signal(signal.SIGTERM, handle_exit)

    atexit.register(handle_exit)

    sys.excepthook = handle_exception

def main():
    register_exit_handlers()
    if not mt5.initialize(login=int(os.getenv('MT5_LOGIN')), password=os.getenv('MT5_PASSWORD'), server=os.getenv('MT5_SERVER')):
        logit(f"❌ MT5 initialization failed: {mt5.last_error()}", True, Fore.RED)
        return
    else:
        logit(f"✅ MT5 connected", True, Fore.GREEN)

    start_websocket()

if __name__ == "__main__":
    main()

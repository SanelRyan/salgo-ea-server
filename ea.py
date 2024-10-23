import MetaTrader5 as mt5
from websocket import WebSocketApp
import json
from colorama import Fore, Style, init
from dotenv import load_dotenv
import os
import time
import threading

init(autoreset=True)
load_dotenv()

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

lotList = config['symbols']
retry_attempts = config["retry_attempts"]
retry_delay = config["retry_delay"]

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
            print(f"{Fore.CYAN}🟢 {Style.BRIGHT}New entry signal received for {symbol} at {price}. Closing all trades first...")
            close_trade(symbol)
            execute_trade(symbol, position, price)
        elif action == 'exit':
            print(f"{Fore.YELLOW}⚠️ {Style.BRIGHT}Exit signal received for {symbol}. Closing open positions...")
            close_trade(symbol)
        else:
            print(f"{Fore.RED}❌ {Style.BRIGHT}Unknown action: {action}")
    except Exception as e:
        print(f"{Fore.RED}❗ {Style.BRIGHT}Error processing message: {e}")

def calculate_dynamic_stop_loss(profit, lot):
    base_initial_sl = -10
    base_profit_threshold = 5
    base_sl_increment_factor = 0.5

    lot_scale = max(1, lot / 0.15) 
    initial_sl = base_initial_sl * lot_scale
    profit_threshold = base_profit_threshold * lot_scale

    if profit >= profit_threshold:
        sl = profit * base_sl_increment_factor
        sl = min(sl, 50 * lot_scale) 
    else:
        sl = initial_sl

    return sl

def update_stop_loss(symbol, lot):
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        for position in positions:
            profit = position.profit
            new_sl = calculate_dynamic_stop_loss(profit, lot)

            order_request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "sl": position.price_open + new_sl,
                "position": position.ticket,
            }
            result = mt5.order_send(order_request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"{Fore.RED}❌ Failed to update SL for {symbol}: {result.retcode}, {result.comment}")
            else:
                print(f"{Fore.GREEN}✅ Updated SL for {symbol} to {new_sl} profit")

def monitor_and_update_sl(symbol):
    lot = lotList[symbol]
    while True:
        update_stop_loss(symbol, lot)
        time.sleep(10)  # Adjust the frequency of SL updates as needed

def execute_trade(symbol, position, price):
    # Decide order type based on position (long or short)
    if position == 'long':
        order_type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask
        print(f"{Fore.GREEN}📈 {Style.BRIGHT}Executing long trade for {symbol} at {price}.")
    elif position == 'short':
        order_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
        print(f"{Fore.RED}📉 {Style.BRIGHT}Executing short trade for {symbol} at {price}.")
    else:
        print(f"{Fore.RED}❌ {Style.BRIGHT}Unknown position: {position}")
        return

    order_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "type": order_type,
        "volume": lotList[symbol],
        "price": price,
        "deviation": 20,
        "magic": 244,
        "comment": "Webhook trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(order_request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"{Fore.RED}❌ {Style.BRIGHT}Order failed for {symbol}: {result.retcode}, {result.comment}")
    else:
        print(f"{Fore.GREEN}✅ {Style.BRIGHT}Order successful for {symbol}: {order_request}")
        threading.Thread(target=monitor_and_update_sl, args=(symbol,)).start()

def close_trade(symbol):
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        print(f"{Fore.YELLOW}⚠️ {Style.BRIGHT}Closing open positions for {symbol}...")
        for position in positions:
            order_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "type": mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "volume": position.volume,
                "price": mt5.symbol_info_tick(symbol).bid if position.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(symbol).ask,
                "deviation": 20,
                "magic": 244,
                "position": position.ticket,  # Target the specific position to close
                "comment": "Webhook close trade",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }

            result = mt5.order_send(order_request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"{Fore.RED}❌ {Style.BRIGHT}Close order failed for {symbol}: {result.retcode}, {result.comment}")
            else:
                print(f"{Fore.GREEN}✅ {Style.BRIGHT}Closed position for {symbol}: {position.ticket}")
    else:
        print(f"{Fore.YELLOW}⚠️ {Style.BRIGHT}No open positions found for symbol {symbol}")

def on_error(ws, error):
    print(f"{Fore.RED}❗ {Style.BRIGHT}WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"{Fore.CYAN}🔒 {Style.BRIGHT}WebSocket connection closed with code: {close_status_code}, reason: {close_msg}")

def on_open(ws):
    print(f"{Fore.GREEN}🔓 {Style.BRIGHT}WebSocket connection opened")

def start_websocket():
    for attempt in range(retry_attempts):
        try:
            print(f"{Fore.GREEN}🔗 Attempting WebSocket connection (attempt {attempt + 1})...")
            ws = WebSocketApp(input_websocket_url(),
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
            ws.on_open = on_open
            ws.run_forever()
            break  # Connection successful, break the loop
        except Exception as e:
            print(f"{Fore.RED}❗ {Style.BRIGHT}WebSocket connection failed: {e}")
            time.sleep(retry_delay)

def main():
    if not mt5.initialize(login=int(os.getenv('MT5_LOGIN')), password=os.getenv('MT5_PASSWORD'), server=os.getenv('MT5_SERVER')):
        print(f"{Fore.RED}❌ {Style.BRIGHT}MT5 initialization failed: {mt5.last_error()}")
        return
    else:
        print(f"{Fore.GREEN}✅ {Style.BRIGHT}MT5 connected")

    # Start WebSocket connection
    start_websocket()

if __name__ == "__main__":
    main()

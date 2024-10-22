import MetaTrader5 as mt5
from websocket import WebSocketApp
import json
from colorama import Fore, Style, init

# Initialize colorama for color support in terminal
init(autoreset=True)

lotList = {
    "BTCUSD": 0.1,
    "XAUUSD": 0.06
}

def input_websocket_url():
    return input("Enter the WebSocket URL: ")

def on_message(ws, message):
    try:
        data = json.loads(message)
        print(f"Received WebSocket data: {data}")
        symbol = data['symbol']
        action = data['action']
        price = data['price']
        position = data['position']  # This is assumed to be either 'buy' or 'sell'

        if action == 'entry':
            print(f"{Fore.CYAN}🟢 {Style.BRIGHT}New entry signal received for {symbol} at {price}. Closing all trades first...")
            close_trade(symbol)  # Close all open trades before taking a new one
            execute_trade(symbol, position, price)
        elif action == 'exit':
            print(f"{Fore.YELLOW}⚠️ {Style.BRIGHT}Exit signal received for {symbol}. Closing open positions...")
            close_trade(symbol)
        else:
            print(f"{Fore.RED}❌ {Style.BRIGHT}Unknown action: {action}")
    except Exception as e:
        print(f"{Fore.RED}❗ {Style.BRIGHT}Error processing message: {e}")

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

def main():
    websocket_url = input_websocket_url()
    
    if not mt5.initialize():
        print(f"{Fore.RED}❌ {Style.BRIGHT}initialize() failed, error code =", mt5.last_error())
        return
    else:
        print(f"{Fore.GREEN}✅ {Style.BRIGHT}MT5 connected")

    ws = WebSocketApp(websocket_url,
                      on_message=on_message,
                      on_error=on_error,
                      on_close=on_close)

    ws.on_open = on_open
    ws.run_forever()

if __name__ == "__main__":
    main()

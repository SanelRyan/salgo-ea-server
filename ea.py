import MetaTrader5 as mt5
from websocket import WebSocketApp
import json

def input_websocket_url():
    return input("Enter the WebSocket URL: ")

def on_message(ws, message):
    try:
        data = json.loads(message)
        symbol = data['symbol']
        action = data['action']
        price = data['price']
        position = data['position']  # This is assumed to be either 'buy' or 'sell'

        if action == 'entry':
            execute_trade(symbol, position, price)
        elif action == 'exit':
            close_trade(symbol)
        else:
            print(f"Unknown action: {action}")
    except Exception as e:
        print(f"Error processing message: {e}")

def execute_trade(symbol, position, price):
    price = price
    if position == 'buy':
        order_type = mt5.ORDER_BUY
        price = mt5.symbol_info_tick(symbol).ask
    elif position == 'sell':
        order_type = mt5.ORDER_SELL
        price = mt5.symbol_info_tick(symbol).bid
    else:
        print(f"Unknown position: {position}")
        return

    order_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "type": order_type,
        "volume": 0.1,
        "price": price,
        "deviation": 50,
        "magic": 0,
        "comment": "Webhook trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(order_request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed: {result.retcode}, {result.comment}")
    else:
        print(f"Order successful: {order_request}")

def close_trade(symbol):
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        for position in positions:
            order_request = {
                "action": "close",
                "symbol": symbol,
                "ticket": position.ticket,
                "volume": position.volume,
                "deviation": 10,
                "magic": 0,
                "comment": "Webhook close trade"
            }

            result = mt5.order_close(order_request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"Close order failed: {result.retcode}, {result.comment}")
            else:
                print(f"Closed position: {position.ticket}")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket connection closed with code: {close_status_code}, reason: {close_msg}")

def on_open(ws):
    print("WebSocket connection opened")

def main():
    websocket_url = input_websocket_url()
    
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return

    ws = WebSocketApp(websocket_url,
                      on_message=on_message,
                      on_error=on_error,
                      on_close=on_close)

    ws.on_open = on_open
    ws.run_forever()

if __name__ == "__main__":
    main()

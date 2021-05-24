import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *

SOCKET = "wss://stream.binance.com:9443/ws/bnbusdt@kline_1m"

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_SYMBOL = "BNBUSDT"
TRADE_QUANTITY = 0.1

closes = []
in_position = False

client = Client(config.API_KEY, config.API_SECRET, tld="us")

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print("Sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        return False
    return True

def on_open(ws):
    print("Openend connection")

def on_close(ws, close_status_code, close_msg):
    print("Closed connection")
    if close_status_code or close_msg:
        print("on_close args:")
        print("close status code: " + str(close_status_code))
        print("close message: " + str(close_msg))

def on_message(ws, message):
    global closes
    print("Received message")
    json_message = json.loads(message)
    pprint.pprint(json_message)

    candle = json_message["k"]
    is_candle_closed = candle["x"]
    close = candle["c"]
    if is_candle_closed:
        print("Candle closed at {}".format(close))
        closes.append(float(close))

        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            print("All RSIs calculated so far")
            print(rsi)
            last_rsi = rsi[-1]
            print("Current RSI value is {}".format(last_rsi))

            if last_rsi > RSI_OVERBOUGHT:
                if in_position:
                    print("Sell!")
                    # Binance logic here: SELL
                    order_succeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeded:
                        in_position = False
                else:
                    print("It is overbough, but we don't own any, nothing to do")

            if last_rsi < RSI_OVERSOLD:
                if in_position:
                    print("It is oversold, but you already own it, nothing to do")
                else:
                    print("Buy!")
                    # Binance logic here: BUY
                    order_succeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeded:
                        in_position = True

def on_error(ws, error):
    print(error)

#websocket.enableTrace(True)
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message, on_error=on_error)
ws.run_forever()

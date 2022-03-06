import json, config
from flask import Flask, render_template, request, jsonify, render_template
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

client = Client(config.API_KEY, config.API_SECRET, tld='com')



def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        if symbol == 'BTCUSDT':
            limited_qty =  "{:.3f}".format(quantity)
        else:
            limited_qty = "{:.3f}".format(quantity)
        order = client.futures_create_order(symbol=symbol, side=side, type=order_type, quantity=limited_qty)
        client.futures_change_leverage(symbol=symbol, leverage=10)
        
        print(f"sending order {order_type} - {side} {limited_qty} {symbol}")
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return order

@app.route("/")
def welcome():
    return render_template('index.html')

@app.route("/webhook", methods=['POST'])
def webhook(): 
    #print(request.data)
    data = json.loads(request.data)

    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return{
            'code': 'error',
            'message': 'Nice try, invalid passphrase'
        }
    print(data['ticker'])
    print(data['bar'])

    side = (data['strategy']['order_action']).upper()
    quantity = data['strategy']['order_contracts']
    ticker = data['ticker']

    order_response = order(side, quantity , ticker)

    if order_response:
        return {
        "code": "success",
        "message": "order executes"
    }
    else:
        print("order failed")

        return{
            "code": "error",
            "message": "order failed"
        }
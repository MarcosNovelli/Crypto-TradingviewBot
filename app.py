import json, config
from flask import Flask, render_template, request, jsonify, render_template
from binance.client import Client
from binance.enums import *
from typing import List
from openpyxl import Workbook, load_workbook

app = Flask(__name__)

client = Client(config.API_KEY, config.API_SECRET, tld='com')

def clean_perp(symbol):
    """
    Will remove perp from the symbol name
    """
    perp = "PERP"
    if perp in symbol:
        symbol = symbol[:-4]
    return symbol

def clean_quantity(quantity):
    """
    Will make the quantity a correct amount for binance to be able to trade it
    """
    if quantity >= 1:
        quantity =  int(quantity)
    elif quantity <= 0.01:
        quantity = float("{:.3f}".format(quantity))
    elif quantity <= 0.1:
        quantity = float("{:.2f}".format(quantity))
    return quantity

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        symbol = clean_perp(symbol)
        quantity = clean_quantity(quantity)

        #order = client.create_test_order(symbol=symbol, side=side, type=order_type, quantity=limited_qty)
        order = client.futures_create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        client.futures_change_leverage(symbol=symbol, leverage=20)
        
        print(f"sending order {order_type} - {side} {quantity} {symbol}")
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return order  

@app.route("/")
def welcome():
    return render_template('index.html')

@app.route("/webhook", methods=['POST'])
def webhook(): 
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
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

def return_trade_data(symbol:str, quantity) -> List[dict]:
    '''
    Requiere: A symbol to look up and quantity that should be traded
    Devuelve: Last trade taken on symbol
    '''
    try:
        trade = client.futures_account_trades(symbol=symbol, limit=1)
        symbol:str = trade[0]['symbol']
        side:str = trade[0]['side']
        traded_quantity:float = float(trade[0]['qty'])
        price:float = float(trade[0]['price'])
        pnl:float = float(trade[0]['realizedPnl'])
        commission:float = float(trade[0]['commission'])

        
        if pnl == 0:
            type = "Opening Order"
        else:
            type = "Closing Order"

        
        try:
            n = 2

            while float(traded_quantity) < quantity:
                trade = client.futures_account_trades(symbol=symbol, limit=n)

                traded_quantity += float(trade[0]['qty'])
                pnl += float(trade[0]['realizedPnl'])
                commission += float(trade[0]['commission'])
                n += 1

        except Exception as e:
            print("An exception ocurred editing the trade amounts - {}".format(e))
                
    except Exception as e:
        print("an exception occured in adding the trade to excel - {}".format(e))
    

    data = [symbol, side, type, price, traded_quantity, pnl, commission]
    return data

def add_to_excel(data:List):
    """
    Requiere: Data compuesta por symbol, side, type, price,
        quantity, pnl and commission
    """
    wb = load_workbook('Trades.xlsx')
    ws = wb[data[0]]
    ws.append(data)
    wb.save('Trades.xlsx')

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
    
    trade_data:List = return_trade_data(clean_perp(ticker), clean_quantity(quantity))
    add_to_excel(trade_data)

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
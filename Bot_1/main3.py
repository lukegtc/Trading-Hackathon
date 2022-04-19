from optibook.synchronous_client import Exchange
from utils3 import BidAskSpread,Hedging,Calculator,OrderHandler 
from settings import *
import time

exchange = Exchange()
exchange.connect()
ask_time = time.time()
bid_time = time.time()
team_orderbook = OrderHandler(exchange,INSTRUMENTS)
team_orderbook.update_outstanding_orders()
exchange.delete_orders("PHILIPS_A")
exchange.delete_orders("PHILIPS_B")
init_pnl = exchange.get_pnl()


def insert_or_delete(timestamp, order_id, new_volume, new_price, exchange, side):
    expired = time.time() - timestamp > TIME_LIMIT
    print(f'expired: {expired}')
    print(f'new_volume: {new_volume}')
    fulfilled = order_id is None
    if fulfilled and abs(new_volume) > 0:
        exchange.insert_order(TICKER_2, price = new_price, volume = abs(new_volume), side = side, order_type = 'limit')
        timestamp = time.time()
    elif expired and abs(new_volume) > 0:
        print(f'-------------------------------------------------order_id: {order_id}')
        remove = exchange.delete_order(TICKER_2,order_id = order_id)
        exchange.insert_order(TICKER_2, price = new_price, volume = abs(new_volume), side = side, order_type = 'limit')
        timestamp = time.time()
    else:
        pass

x = 0
print(f"Init PnL: {init_pnl}")
while True:
    print("~~~~~~~~~~~ TEAM ORDER BOOK OUTSTANDING ORDERS ~~~~~~~~~~~")
    team_orderbook.update_outstanding_orders()
    calculate = Calculator(exchange) # probs not gd to put cls instancein Calculator - Nidish
    new_B_ask       = calculate.next_B_ask
    new_B_ask_volume = calculate.new_B_ask_volume
    new_B_bid       = calculate.next_B_bid
    new_B_bid_volume = calculate.new_B_bid_volume
    if len(team_orderbook.bids[TICKER_2]) != 0:
        team_best_bid = team_orderbook.get_best_bid(TICKER_2).order_id
    if len(team_orderbook.asks[TICKER_2]) != 0:
        team_best_ask = team_orderbook.get_best_ask(TICKER_2).order_id
    elif len(team_orderbook.bids[TICKER_2]) == 0:
        print("no bids team orderbook")
        team_best_bid = None
        team_best_ask = None
    insert_or_delete(ask_time, team_best_ask, new_B_ask_volume, new_B_ask, exchange,'ask')
    insert_or_delete(bid_time, team_best_bid, new_B_bid_volume, new_B_bid, exchange,'bid')
    hedging = Hedging(exchange)
    current_pnl = exchange.get_pnl()
    pnl_diff = current_pnl - init_pnl
    init_pnl = pnl_diff
    print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ delta_pnl= {pnl_diff} ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    
    # time.sleep(0.05)
    time.sleep(0.1)
    


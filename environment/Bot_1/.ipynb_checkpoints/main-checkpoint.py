from optibook.synchronous_client import Exchange
from .utils import BidAskSpread,Hedging,Calculator,OrderHandler 
from .constants import *
#TODO: Finish the while loop
exchange = Exchange()
connection = exchange.connect()
ask_time = time.time()
bid_time = time.time()
team_orderbook = OrderHandler(exchange,INSTRUMENTS)

def insert_or_delete(timestamp,order_id,new_volume,new_price,exchange,side):
    expired = time.time() - timestamp > TIME_LIMIT
    fulfilled = order_id is None
    if fulfilled and new_volume >0:
        exchange.insert_order(TICKER_2, price = new_price, volume = new_volume, side = side, order_type = 'limit')
        timestamp = time.time()
    elif expired and new_volume>0:
        remove = exchange.delete_order(TICKER_2,order_id = order_id)
        exchange.insert_order(TICKER_2,price = new_price)
        timestamp = time.time()
    else:
        pass

while True:
        team_orderbook.update_outstanding_orders()
        team_best_bid = team_orderbook.get_best_bid(TICKER_2)
        team_best_ask = team_orderbook.get_best_ask(TICKER_2)
        
        calculate = CALCULATOR(exchange)
        # Find the new bid/ask prices and volumes for the illiquid market
        new_B_ask       = calculate.next_B_ask
        new_B_ask_volume = calculate.new_B_ask_volume
        new_B_bid       = calculate.next_B_bid
        new_B_bid_volume = calculate.new_B_bid_volume
    
        #Check if the ask has expired
        
        insert_or_delete(ask_time,team_best_ask,new_B_ask_volume,new_B_ask,exchange,'ask')
        
        insert_or_delete(bid_time,team_best_bid,new_B_bid_volume,new_B_bid,exchange,'bid')


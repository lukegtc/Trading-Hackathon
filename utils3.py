from dataclasses import dataclass
import numpy as np
import time

from settings import *
#TODO: DOCUMENTATION

class BidAskSpread:
    """
    Class that finds several technical details about the bid/ask spread
    @author: Luke
    """
    def __init__(self,book, undercut_constant = UC):
        """
        Args:
            book: The order book
            undercut_constant: Undercutting constant, 
        """
        self.book = book
        self.lowest_ask = self.book.asks[0].price #Returns lowest order book ask
        self.highest_bid = self.book.bids[0].price #Returns highest order book bid
        self.spread = self.lowest_ask-self.highest_bid # Returns the spread
        self.average = 0.5*(self.lowest_ask + self.highest_bid) #Returns the Average
        self.undercut_bid = self.average-0.5*undercut_constant*self.spread #An undercut function that creates an undercut bid to optionally use
        self.undercut_ask = self.average+0.5*undercut_constant*self.spread #An undercut function that creates an undercut ask to optionally use 
        self.all = self.lowest_ask,   \
                    self.highest_bid, \
                    self.spread,      \
                    self.average,     \
                    self.undercut_bid,\
                    self.undercut_ask

class Hedging:
    """
    Class that finds and executes potential hedged orders
    @author: Luke
    """
    def __init__(self,exchange, order_type = 'ioc'):
        """
        Args:
            exchange: Exchange that is being connected to
            order_type: limit or ioc
        """
        self.exchange = exchange  #Name of the exchange
        self.PHILIPS_A_price_book = exchange.get_last_price_book(TICKER_1)  # Liquid price book
        self.PHILIPS_B_price_book = exchange.get_last_price_book(TICKER_2) # Illiquid price book
        self.positions = exchange.get_positions()   # Obtain all positions
        self.total_positions = self.positions[TICKER_1] + self.positions[TICKER_2]  # Sum of all positions
        self.volume = abs(self.total_positions) # total volume
        while len(self.PHILIPS_A_price_book.bids) == 0 or len(self.PHILIPS_A_price_book.asks) == 0 or len(self.PHILIPS_B_price_book.bids) == 0 or len(self.PHILIPS_B_price_book.asks) == 0:
            time.sleep(0.05) 
            self.PHILIPS_A_price_book = exchange.get_last_price_book(TICKER_1)
            self.PHILIPS_B_price_book = exchange.get_last_price_book(TICKER_2)
        self.spread_dict = {'PHILIPS_A': BidAskSpread(self.PHILIPS_A_price_book),  
                            'PHILIPS_B' : BidAskSpread(self.PHILIPS_B_price_book)
                            }
        self.order_type = order_type
        self.side_selector()
        # self.create_order()
        print(f'self.volume: {self.volume}')
    def side_selector(self):
        """
        Function that selects the proper side to execute the order on
        Args:
        """
        if self.total_positions > 0:
            self.selected_side = 'ask'
            self.selected_price = self.spread_dict['PHILIPS_A'].highest_bid
        elif self.total_positions < 0:
            self.selected_side = 'bid'
            self.selected_price = self.spread_dict['PHILIPS_A'].lowest_ask
        else:
            return True
        self.exchange.insert_order(instrument_id = TICKER_1,
                        price = self.selected_price,
                        volume = self.volume,
                        side = self.selected_side,
                        order_type = self.order_type)    
        return False
        
class Calculator:
    """
    Calculates new bid/ask prices and volumes
    """
    def __init__(self,exchange,INSTRUMENTS = INSTRUMENTS):
        self.INSTRUMENTS = INSTRUMENTS
        self.A_positions = exchange.get_positions()[self.INSTRUMENTS[0]]
        self.B_positions = exchange.get_positions()[self.INSTRUMENTS[1]]

        self.liquid_price_book = exchange.get_last_price_book(self.INSTRUMENTS[0])

        self.illiquid_price_book = exchange.get_last_price_book(self.INSTRUMENTS[1])
        
        while len(self.liquid_price_book.bids) == 0 or len(self.liquid_price_book.asks) == 0 or len(self.illiquid_price_book.bids) == 0 or len(self.illiquid_price_book.asks) == 0:
            time.sleep(0.05) 
            self.liquid_price_book = exchange.get_last_price_book(self.INSTRUMENTS[0])
            self.illiquid_price_book = exchange.get_last_price_book(self.INSTRUMENTS[1])
            
        self.lowest_ask_A, self.highest_bid_A, self.spread_A, self.average_A,self.undercut_bid_A, self.undercut_ask_A = BidAskSpread(self.liquid_price_book).all
        self.lowest_ask_B, self.highest_bid_B, self.spread_B, self.average_B,self.undercut_bid_B, self.undercut_ask_B = BidAskSpread(self.illiquid_price_book).all
        self.B_pretrade_volume =  exchange.get_positions()['PHILIPS_B']

        self.ask_price()
        self.bid_price()
        self.B_ask_volume()
        self.B_bid_volume()
            
    def ask_price(self):
        if self.lowest_ask_A >= self.lowest_ask_B:
            self.next_B_ask = self.lowest_ask_A
        else:
            average_AB = (self.lowest_ask_A + self.lowest_ask_B)*0.5
            self.next_B_ask = max(self.undercut_ask_B,average_AB)
        self.B_ask_delta = self.next_B_ask - self.lowest_ask_A
    
    def bid_price(self):
        if self.highest_bid_A> self.highest_bid_B:
            average_AB = (self.highest_bid_A + self.highest_bid_B)*0.5
            self.next_B_bid = min(self.undercut_bid_B,average_AB)
        else:
            self.next_B_bid = self.highest_bid_A
        self.B_bid_delta = self.highest_bid_A - self.next_B_bid    
            
        
    def B_ask_volume(self): 
        new_B_ask_volume = int(np.round(MAX_VOLUME*(-np.sin(((self.A_positions-self.B_positions)/1000)*np.pi/2)*0.5+0.5)**(VOLUME_SCALE/(self.B_ask_delta+0.01))))
        vol_limit = 200
        
        if abs(self.B_pretrade_volume - new_B_ask_volume) > vol_limit:
            self.new_B_ask_volume = (vol_limit - abs(self.B_pretrade_volume))*mysign(new_B_ask_volume)
        else:
            self.new_B_ask_volume = new_B_ask_volume
            
        
    def B_bid_volume(self):
        
        vol_limit = 200
        new_B_bid_volume = int(np.round(MAX_VOLUME*(-np.sin(((self.B_positions-self.A_positions)/1000)*np.pi/2)*0.5+0.5)**(VOLUME_SCALE/(self.B_bid_delta+0.01)))) 
        

        
        if abs(self.B_pretrade_volume +  new_B_bid_volume) > vol_limit:

            self.new_B_bid_volume = (vol_limit - abs(self.B_pretrade_volume))*mysign(new_B_bid_volume) 
        else:
            self.new_B_bid_volume = new_B_bid_volume
                    
        
class OrderHandler:
    """
    Wrapper class to insert, delete, and update orders
    @author: Nidhish
    """

    def __init__(self, exchange, INSTRUMENTS):
        self.exchange = exchange
        self.INSTRUMENTS = INSTRUMENTS
        self.bids = {}
        self.asks = {}
        

    def place_order(self, instrument_id, price, volume, side, order_type):
        """
        Places an order on the exchange.
        Args:
            instrument_id (str): The instrument to place the order on.
            price (float): The price to place the order at.
            volume (int): The volume to place the order for.
            side (str): The side to place the order on ['bid' / 'ask'].
            order_type (str): The order type to place the order as ['limit', 'ioc'].
        Returns:
            order_id (int): The id of the order that was placed.
        """
        order_id = self.exchange.insert_order(instrument_id, price, volume, side, order_type)

        return order_id

    def delete_order(self, instrument_id, order_id):
        """
        Deletes an order from the exchange.
        Args:
            instrument_id (str): The instrument to delete the order for.
            order_id (int): The id of the order to delete.
        Returns:
            success (bool): Whether the order was successfully deleted.
        """
        success = self.exchange.delete_order(instrument_id, order_id)
        return success
        
    def update_outstanding_orders(self):
        """
        Update the outstanding limit orders for all instruments.
        """
        for instrument in self.INSTRUMENTS:
            orders = self.exchange.get_outstanding_orders(instrument).values()
            self.asks[instrument] = sorted([o for o in orders if o.side == "ask"], key = lambda x: x.price)
            self.bids[instrument] = sorted([o for o in orders if o.side == "bid"], key = lambda x: x.price)
    
    def get_best_bid(self, instrument):
        """
        Returns the highest bid for the given instrument.
        Args:
            instrument (str): The instrument to get the bid for.
        Returns:
            bid (Order): Order object for the higest bid.
        """
        # The bids are sorted in ascending order, so highest bid is last.
        bids = self.bids[instrument]
        return bids[-1] if bids else None
            
                
    def get_best_ask(self, instrument):
        """
        Returns the lowest ask for the given instrument.
        Args:
            instrument (str): The instrument to get the ask for.
        Returns:
            ask (Order): Order object for the lowest ask. If ther are
            no asks then None is returned.
            asks <list>
            asks[0] type <OrderStatus>
        """
        # The bids are sorted in ascending order, so highest bid is last.
        asks = self.asks[instrument]
        return asks[0] if asks else None
    
    
    def get_ask_volume(self, instrument):
        """
        Returns the total volume of all outstanding asks.
        Args:
            instrument (str): The instrument to get the ask volume for.
        Returns:
            volume (int): The total volume of all outstanding asks.
        """
        asks = self.asks[instrument]
        return sum([o.volume for o in asks])
        
        
    def get_bid_volume(self, instrument):
        """
        Returns the total volume of all outstanding asks.
        Args:
            instrument (str): The instrument to get the ask volume for.
        Returns:
            volume (int): The total volume of all outstanding asks.
        """
        bids = self.bids[instrument]
        return sum([o.volume for o in bids])


def mysign(x):
    if x >= 0: 
        return 1
    else:
        return -1
        
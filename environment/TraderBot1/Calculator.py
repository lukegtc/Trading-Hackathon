import time
import numpy as np


class Calculator:
    def __init__(self, exchange, instruments, undercut_constant=0.8):
        self.exchange = exchange
        self.LIQUID_INSTRUMENT, self.ILLIQUID_INSTRUMENT = instruments
        self.UC = undercut_constant

    def get_positions(self):
        """
        Queries the exchange for the current positions.
        Returns:
            (tuple): The liquid and illiquid positions.
        """
        positions = self.exchange.get_positions()
        liquid_position = positions[self.LIQUID_INSTRUMENT]
        illiquid_position = positions[self.ILLIQUID_INSTRUMENT]
        return liquid_position, illiquid_position
    
    def get_books(self, requery=True, requery_time=0.15):
        """
        Queries the exchange for the current order books.
        Args:
            requery (bool): Whether or not to requery the exchange for the order books if they are empty.
            requery_time (float): The time to wait between requerying the exchange for the order books.
        Returns:
            (tuple): The liquid and illiquid order books.
        """
        liquid_book = self.exchange.get_last_price_book(self.LIQUID_INSTRUMENT)
        illiquid_book = self.exchange.get_last_price_book(self.ILLIQUID_INSTRUMENT)
        if requery:
            while not (liquid_book.bids and liquid_book.asks and illiquid_book.bids and illiquid_book.asks):
                liquid_book = self.exchange.get_last_price_book(self.LIQUID_INSTRUMENT)
                illiquid_book = self.exchange.get_last_price_book(self.ILLIQUID_INSTRUMENT)
                time.sleep(requery_time)
        
        return liquid_book, illiquid_book

    def get_best_ask_price(self, order_book):
        """
        Returns the lowest ask price from the exchange order book.
        Args:
            order_book (PriceBook): The order book to get the lowest ask price from.
        Returns:
            (float): The lowest ask price.
        """
        if not order_book:
            raise ValueError("Order book is empty.")

        # Asks are sorted from lowest to highest.
        return order_book.asks[0].price

    def get_best_bid_price(self, order_book):
        """
        Returns the highest bid price from the exchange order book.
        Args:
            order_book (PriceBook): The order book to get the highest bid price from.
        Returns:
            (float): The highest bid price.
        """
        if not order_book:
            raise ValueError("Order book is empty.")
    
        # Bids are sorted from higest to lowest.
        return order_book.bids[0].price

    def get_bid_ask_spread(self, order_book):
        """
        Returns the spread between the highest bid and lowest ask.
        Args:
            order_book (PriceBook): The order book to get the spread from.
        Returns:
            (float): The spread between the highest bid and lowest ask.
        """
        return self.get_best_ask_price(order_book) - self.get_best_bid_price(order_book)

    def get_mid_price(self, order_book):
        """
        Returns the mid price of the given order book.
        Args:
            order_book (PriceBook): The order book to get the mid price from.
        Returns:
            (float): The mid price of the given order book.
        """
        if not order_book:
            raise ValueError("Order book is empty.")

        # The mid price is the average of the highest bid and lowest ask.
        return (self.get_best_bid_price(order_book) + self.get_best_ask_price(order_book)) / 2

    def get_undercut_bid_price(self, order_book):
        """
        Returns the undercut bid price of the given order book.
        Args:
            order_book (PriceBook): The order book to get the undercut bid price from.
        Returns:
            (float): The undercut bid price of the given order book.
        """
        if not order_book:
            raise ValueError("Order book is empty.")

        mid_price = self.get_mid_price(order_book)
        spread = self.get_bid_ask_spread(order_book)
        return mid_price - (0.5 * spread * self.UC)

    def get_undercut_illiquid_ask_price(self, order_book):
        """
        Returns the undercut ask price of the given order book.
        Args:
            order_book (PriceBook): The order book to get the undercut ask price from.
        Returns:
            (float): The undercut ask price of the given order book.
        """
        if not order_book:
            raise ValueError("Order book is empty.")

        mid_price = self.get_mid_price(order_book)
        spread = self.get_bid_ask_spread(order_book)
        return mid_price + (0.5 * spread * self.UC)


    def get_next_ask_price(self, liquid_book, illiquid_book):
        """
        Calculates the next ask price for the illiquid instrument.
        Args:
            liquid_book (PriceBook): The liquid order book.
            illiquid_book (PriceBook): The illiquid order book.
        Returns:
            (float): The next ask price for the illiquid instrument.
            (float): The difference between the next ask price and best ask price on the exchange.
        """
        best_liquid_ask = self.get_best_ask_price(liquid_book)
        best_illiquid_ask = self.get_best_ask_price(illiquid_book)
        undercut_illiquid_ask = self.get_undercut_illiquid_ask_price(illiquid_book)

        if best_liquid_ask >= best_illiquid_ask:
            next_ask_price = best_liquid_ask
        else:
            next_ask_price = max(undercut_illiquid_ask, (best_liquid_ask + best_illiquid_ask) / 2)

        illiquid_ask_delta = next_ask_price - best_liquid_ask

        return next_ask_price, illiquid_ask_delta

    def get_next_bid_price(self, liquid_book, illiquid_book):
        """
        Calculates the next bid price for the illiquid instrument.
        Args:
            liquid_book (PriceBook): The liquid order book.
            illiquid_book (PriceBook): The illiquid order book.
        Returns:
            (float): The next bid price for the illiquid instrument.
            (float): The difference between the next bid price and best bid price on the exchange.
        """
        best_liquid_bid = self.get_best_bid_price(liquid_book)
        best_illiquid_bid = self.get_best_bid_price(illiquid_book)
        undercut_illiquid_bid = self.get_undercut_bid_price(illiquid_book)

        if best_liquid_bid > best_illiquid_bid:
            next_bid_price = min(undercut_illiquid_bid, (best_liquid_bid + best_illiquid_bid) / 2)
        else:
            next_bid_price = best_liquid_bid
            
        illiquid_bid_delta = best_illiquid_bid - next_bid_price 
        return next_bid_price, illiquid_bid_delta


    def get_next_ask_volume(self, liquid_position, illiquid_position, illiquid_ask_delta, MAX_VOLUME=30, VOL_FACTOR=0.5, VOL_LIMIT=150):
        position_diff = liquid_position - illiquid_position
        print(f"~~~~~~~~~~~ DEBUG get_next_ask_volume(...) | position_diff = liquid_position - illiquid_position-> {position_diff} = {liquid_position} - {illiquid_position}")
        volume_exp = VOL_FACTOR / (illiquid_ask_delta + 0.01)
        volume_base =  MAX_VOLUME * ( -np.sin((position_diff/1000) * np.pi/2) * 0.5 + 0.5 )
        new_ask_volume = np.round(volume_base ** volume_exp)
        if abs(illiquid_position - new_ask_volume) > VOL_LIMIT:
            new_ask_volume = (VOL_LIMIT - abs(illiquid_position)) * np.sign(new_ask_volume)
        print(f"DEBUG INSIDE calculator.get_next_ask_volume(...) -> new_ask_volume: {new_ask_volume}")
        return int(new_ask_volume)
        

    def get_next_bid_volume(self, liquid_position, illiquid_position, illiquid_bid_delta, MAX_VOLUME=30, VOL_FACTOR=0.5, VOL_LIMIT=150):
        position_diff = illiquid_position - liquid_position
        print(f"~~~~~~~~~~~ DEBUG get_next_bid_volume(...) | position_diff = illiquid_position - liquid_position -> {position_diff} = {illiquid_position} - {liquid_position}")
        volume_exp = VOL_FACTOR / (illiquid_bid_delta + 0.01)
        volume_base =  MAX_VOLUME * ( - np.sin((position_diff/1000) * np.pi/2) * 0.5 + 0.5 )
        new_bid_volume = np.round(volume_base ** volume_exp)
        # new_bid_volume = int(np.round(MAX_VOLUME*(-np.sin(((position_diff)/1000)*np.pi/2)*0.5+0.5)**(VOL_FACTOR/(illiquid_bid_delta+0.01))))
        if abs(illiquid_position + new_bid_volume) > VOL_LIMIT:
            new_bid_volume = (VOL_LIMIT - abs(illiquid_position)) * np.sign(new_bid_volume)
        print(f"calculator.get_next_bid_volume(...) -> new_bid_volume: {new_bid_volume}")
        
        return int(new_bid_volume)

    def get_next_bid(self):
        """
        Returns the next bid (price and volume) for the illiquid instrument.
        Returns:
            (float): The next bid price for the illiquid instrument.
            (int): The next bid volume for the illiquid instrument.
        """
        liquid_book, illiquid_book = self.get_books()
        liquid_position, illiquid_position = self.get_positions()

        next_bid_price, price_delta = self.get_next_bid_price(liquid_book, illiquid_book)
        next_bid_volume = self.get_next_bid_volume(liquid_position, illiquid_position, price_delta)

        return next_bid_price, next_bid_volume

    def get_next_ask(self):
        """
        Returns the next ask (price and volume) for the illiquid instrument.
        Returns:
            (float): The next ask price for the illiquid instrument.
            (int): The next ask volume for the illiquid instrument.
        """
        liquid_book, illiquid_book = self.get_books()
        liquid_position, illiquid_position = self.get_positions()

        next_ask_price, volume_delta = self.get_next_ask_price(liquid_book, illiquid_book)
        next_ask_volume = self.get_next_ask_volume(liquid_position, illiquid_position, volume_delta)

        return next_ask_price, next_ask_volume
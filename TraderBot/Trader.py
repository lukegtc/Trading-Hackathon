import logging
import time

from Calculator import Calculator
from OrderHandler import OrderHandler

class Trader:
    def __init__(self, exchange, instruments, quote_time_limit = 0.1):
        self.e = exchange
        self.instruments = instruments
        self.LIQUID_INSTRUMENT = self.instruments[0]
        self.ILLIQUID_INSTRUMENT = self.instruments[1]
        self.order_handler = OrderHandler(self.e, self.instruments)
        self.calculator = Calculator(self.e, self.instruments)
        self.logger = logging.getLogger(__name__)
        self.last_ask_time = time.time()
        self.last_bid_time = time.time()
        self.QUOTE_TIME_LIMIT = quote_time_limit

    def run(self):
        """
        Runs the trader: Update orders and place new ones.
        """
        self.logger.debug("Updating outstanding orders...")
        self.order_handler.update_outstanding_orders()

        self.logger.debug("Updating bids...")
        self._update_bids(self.ILLIQUID_INSTRUMENT)
        self.logger.debug("Updating asks...")
        self._update_asks(self.ILLIQUID_INSTRUMENT)
        self.logger.debug("Hedging...")
        self._hedge()

    def _update_bids(self, instrument):
        """
        For the given instrument:
            - if bid is fulfilled, place a new bid.
            - if bid is expired, delete the bid and place a new one.
        Args:
            instrument (str): The instrument to update bids for.
        """
        next_bid_price, next_bid_volume = self.calculator.get_next_bid()
        if next_bid_volume <= 0:
            self.logger.debug("Negative volume. No action taken.")
            return

        best_bid = self.order_handler.get_best_bid(instrument)
            
        if self._is_fulfilled(best_bid):
            # Insert a new bid if volume is greater than 0.
            self.logger.debug(f"Placing a bid for {next_bid_volume} units @ {next_bid_price}.")
            self.order_handler.place_order(instrument, next_bid_price, next_bid_volume, "bid", "limit")
            self.last_bid_time = time.time()

        elif self._is_expired(self.last_bid_time):
            # Delete the previous bid order and insert a new one.
            self.logger.debug("Last bid expired. Deleting bid.")
            deleted = self.order_handler.delete_order(instrument, best_bid.order_id)
            if not deleted: self.logger.error("Failed to delete bid order.")
            self.logger.debug(f"Placing a bid for {next_bid_volume} units @ {next_bid_price}.")
            self.order_handler.place_order(instrument, next_bid_price, next_bid_volume, "bid", "limit")
            self.last_bid_time = time.time()

        else:
            self.logger.debug("Last bid not expired or fulfilled. No action taken.")

    def _update_asks(self, instrument):
        """
        For the given instrument:
            - if ask is fulfilled, place a new ask.
            - if ask is expired, delete the ask and place a new one.
        Args:
            instrument (str): The instrument to update asks for.
        """
        next_ask_price, next_ask_volume = self.calculator.get_next_ask()
        if next_ask_volume <= 0:
            self.logger.debug("Negative volume. No action taken.")
            return

        best_ask = self.order_handler.get_best_ask(instrument)
        if self._is_fulfilled(best_ask):
            # Insert a new ask if volume is greater than 0.
            self.logger.debug(f"Placing an ask for {next_ask_volume} units @ {next_ask_price}.")
            self.order_handler.place_order(instrument, next_ask_price, next_ask_volume, "ask", "limit")
            self.last_ask_time = time.time()

        elif self._is_expired(self.last_bid_time):
            # Delete the previous ask order and insert a new one.
            self.logger.debug("Last ask expired. Deleting ask.")
            deleted = self.order_handler.delete_order(instrument, best_ask.order_id)
            if not deleted: self.logger.error("Failed to delete ask order.")
            self.logger.debug(f"Placing an ask for {next_ask_volume} units @ {next_ask_price}.")
            self.order_handler.place_order(instrument, next_ask_price, next_ask_volume, "ask", "limit")
            self.last_ask_time = time.time()

        else:
            self.logger.debug("Last ask not expired or fulfilled. No action taken.")

    def _is_expired(self, last_time):
        """
        Returns whether the order is expired.
        Args:
            last_time (float): The time of the last order.
        Returns:
            expired (bool): Whether the order is expired based on the time limit.
        """
        return time.time() - last_time > self.QUOTE_TIME_LIMIT

    def _is_fulfilled(self, order):
        """
        Returns whether the order is fulfilled.
        An order is only fulfilled if it is not inside the team order book, in which case, it is None.
        Args:
            order (OrderStatus): The order to check.
        Returns:
            fulfilled (bool): Whether the order is fulfilled.
        """
        return order is None
        
    def _hedge(self):
        PHILIPS_A_price_book = self.e.get_last_price_book(self.LIQUID_INSTRUMENT)  # Liquid price book
        PHILIPS_B_price_book = self.e.get_last_price_book(self.ILLIQUID_INSTRUMENT)  # Iliquid price book
        liquid_position, illiquid_position = self.calculator.get_positions() # tuple type of (liquid orders, illiquid orders)
        # Sum of all positions
        total_positions = liquid_position + illiquid_position # Hedge CLASS: self.total_positions = self.positions[TICKER_1] + self.positions[TICKER_2]
        # TODO: CHANGE ABOVE TO total_positions = abs(liquid_position) + abs(illiquid_position)
        # TODO: CHANGE THE ABOVE TO SUM THE ABS OF BOTH POSITIONS
        # total volume
        # TODO: ¿REMOVE THE ABOVE AFTER MAKING THE TODO CHANGE ABOVE?
        # self.calculator.get_books() returns the tuple (liquid_book, illiquid_book)
        PHILIPS_A_price_book, PHILIPS_B_price_book = self.calculator.get_books()
        order_type = "ioc"
        if total_positions > 0: # Hedge CLASS: if self.total_positions > 0:
            selected_side = "ask" # Hedge CLASS: self.selected_side = 'ask'
            selected_price = self.calculator.get_best_bid_price(PHILIPS_A_price_book) # Hedge CLASS: self.selected_price = self.spread_dict['PHILIPS_A'].highest_bid # calculator.get_best_bid_price(liquid_book)
        elif total_positions < 0:
            selected_side = "bid"
            selected_price = self.calculator.get_best_ask_price(PHILIPS_B_price_book) # Hedge CLASS: self.selected_price = self.spread_dict['PHILIPS_A'].lowest_ask # calculator.get_best_ask_price(liquid_book)
        else:
            return True
        # self.exchange.insert_order(...) w/ params (instrument_id, price, volume, side, order_type)
        self.order_handler.place_order(instrument_id=self.LIQUID_INSTRUMENT, price=selected_price, volume=abs(total_positions), side=selected_side, order_type=order_type)    
        return False
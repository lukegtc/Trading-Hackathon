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
        order_id = self.exchange.insert_order(instrument_id, price=price, volume=volume, side=side, order_type=order_type)

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
        success = self.exchange.delete_order(instrument_id, order_id=order_id)
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
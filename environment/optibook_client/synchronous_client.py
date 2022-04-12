import logging
import typing

from . import exchange_client
from .exchange_client import InfoClient, ExecClient
from .synchronous_wrapper import SynchronousWrapper
from .common_types import PriceBook, PriceVolume, Trade, TradeTick, OrderStatus, Instrument

logger = logging.getLogger('client')


class Exchange:
    def __init__(self,
                 host: str = None,
                 info_port: int = None,
                 exec_port: int = None,
                 full_message_logging: bool = False,
                 max_nr_trade_history: int = 100):
        """
        Initiate an exchange client instance. This is the class you should use to interact with the exchange, i.e.
        send orders or delete orders, get the newest trades, etc.

        Parameters
        ----------
        host: str
            The network location the Exchange Server runs on.
        info_port: int
            The port of the Info interface exposed by the Exchange.
        exec_port: int
            The port of the Execution interface exposed by the Exchange.
        full_message_logging: bool
            If set to to True enables logging on VERBOSE level, displaying among others all messages sent to and received from the
            exchange.
        max_nr_trade_history: int
            Keep at most this number of trades per instrument in history. Older trades will be removed automatically
        """

        if full_message_logging:
            exchange_client.logger.setLevel('VERBOSE')

        self._i = InfoClient(host=host, port=info_port, max_nr_trade_history=max_nr_trade_history)
        self._e = ExecClient(host=host, port=exec_port, max_nr_trade_history=max_nr_trade_history)
        self._wrapper = SynchronousWrapper([self._i, self._e])

    def is_connected(self) -> bool:
        """
        Tells you if the client is currently connected to the exchange.

        Returns
        -------
        bool
            True if you are connected, otherwise false.
        """
        return self._wrapper.is_connected()

    def connect(self, username: str = None, password: str = None, admin_password: str = None) -> None:
        """
        Attempt to connect to the exchange with specified username and password. Only a single connection can be made on a single username.

        The admin_password field is reserved for dedicated clients only and can be left empty.

        Parameters
        ----------
        username: str
            Your username.
        password: str
            Your password.
        """
        self._wrapper.connect()

        try:
            return self._wrapper.run_on_loop(
                self._e.authenticate(username, password, admin_password)
            )
        except:
            logger.error('''
Unable to authenticate with the server. Please double-check that your username and password are correct
 ''')
            raise

    def disconnect(self) -> None:
        """
        Disconnect from the exchange.
        """
        self._wrapper.disconnect()
            
    def insert_order(self, instrument_id: str, *, price: float, volume: int, side: str, order_type: str = exchange_client.ORDER_TYPE_LIMIT) -> int:
        """
        Insert a limit or IOC order on an instrument.

        Parameters
        ----------
        instrument_id: str
            The instrument_id of the instrument to insert the order on.
        price: float
            The (limit) price of the order.
        volume: int
            The number of lots in the order.
        side: str
            'bid' or 'ask', a bid order is an order to buy while an ask order is an order to sell.
        order_type: str
            'limit' or 'ioc', limit orders stay in the book while any remaining volume of an IOC that is not immediately
            matched is cancelled.

        Returns
        -------
        int
            An order_id which can be used to e.g. delete or amend the limit order later.
        """
        assert self.is_connected(), "Cannot call function until connected. Call connect() first"
        assert(side in exchange_client.ALL_SIDES), f"Invalid value ({side}) for parameter 'side'. Use synchronous_client.BID or synchronous_client.ASK"
        assert order_type in exchange_client.ALL_ORDER_TYPES, f"order_type must be one of {exchange_client.ALL_ORDER_TYPES}"

        return self._wrapper.run_on_loop(
            self._e.insert_order(instrument_id=instrument_id, price=price, volume=volume, side=side, order_type=order_type)
        )

    def amend_order(self, instrument_id: str, *, order_id: str, volume: int) -> bool:
        """
        Amend a specific outstanding limit order on an instrument. E.g. to change its volume.

        Parameters
        ----------
        instrument_id: str
            The instrument_id of the instrument to delete a limit order for.
        order_id: str
            The order_id of the limit order to delete.
        volume: str
            The new volume to change the order to.

        Returns
        -------
        bool
            True if the amend was successful, otherwise false.
        """
        assert self.is_connected(), "Cannot call function until connected. Call connect() first"

        return self._wrapper.run_on_loop(
            self._e.amend_order(instrument_id, order_id, volume)
        )

    def delete_order(self, instrument_id: str, *, order_id: str) -> bool:
        """
        Delete a specific outstanding limit order on an instrument.

        Parameters
        ----------
        instrument_id: str
            The instrument_id of the instrument to delete a limit order for.
        order_id: str
            The order_id of the limit order to delete.

        Returns
        -------
        bool
            True if the delete was successful, otherwise false.
        """
        assert self.is_connected(), "Cannot call function until connected. Call connect() first"

        return self._wrapper.run_on_loop(
            self._e.delete_order(instrument_id, order_id)
        )

    def delete_orders(self, instrument_id: str) -> None:
        """
        Delete all outstanding orders on an instrument.

        Parameters
        ----------
        instrument_id: str
            The instrument_id of the instrument to delete the orders for.
        """
        assert self.is_connected(), "Cannot call function until connected. Call connect() first"

        return self._wrapper.run_on_loop(
            self._e.delete_orders(instrument_id)
        )

    def poll_new_trades(self, instrument_id: str) -> typing.List[Trade]:
        """
        Returns the private trades received for an instrument since the last time this function was called for that instrument.

        Parameters
        ----------
        instrument_id: str
            The instrument_id of the instrument to poll the private trades for.

        Returns
        -------
        typing.List[Trade]
            Returns the private trades received for an instrument since the last time this function was called for that
            instrument.
        """
        assert self.is_connected(), "Cannot call function until connected. Call connect() first"
        return self._e.poll_new_trades(instrument_id)

    def get_trade_history(self, instrument_id: str) -> typing.List[Trade]:
        """
        Returns all private trades received for an instrument since the start of this Exchange Client (but capped by max_nr_total_trades).
        If the total number of trades per instrument is larger than max_nr_total_trades, older trades will not be returned by this function.

        Parameters
        ----------
        instrument_id: str
            The instrument_id of the instrument to obtain the private trade history for.

        Returns
        -------
        typing.List[Trade]
            Returns all private trades received for an instrument since the start of this Exchange Client
            (but capped by max_nr_total_trades).
        """
        assert self.is_connected(), "Cannot call function until connected. Call connect() first"
        return self._e.get_trade_history(instrument_id=instrument_id)

    def poll_new_trade_ticks(self, instrument_id: str) -> typing.List[TradeTick]:
        """
        Returns the public trades received for an instrument since the last time this function was called for that
        instrument. Public trades are trades between two other parties, in which you may or may not have been involved.

        Parameters
        ----------
        instrument_id: str
            The instrument_id of the instrument to poll the trade ticks for.

        Returns
        -------
        typing.List[TradeTick]
            Returns the public trades received for an instrument since the last time this function was called for that
            instrument.
        """
        assert self.is_connected(), "Cannot call function until connected. Call connect() first"
        return self._i.poll_new_trade_ticks(instrument_id)

    def get_trade_tick_history(self, instrument_id: str) -> typing.List[TradeTick]:
        """
        Returns all public trade ticks received for an instrument since the start of this Exchange Client (but capped by max_nr_total_trades).
        If the total number of trades per instrument is larger than max_nr_total_trades, older trades will not be returned by this function.

        Parameters
        ----------
        instrument_id: str
            The instrument_id of the instrument to obtain the trade tick history for.

        Returns
        -------
        typing.List[TradeTick]
            Returns all public trade ticks received for an instrument since the start of this Exchange Client
            (but capped by max_nr_total_trades).
        """
        assert self.is_connected(), "Cannot call function until connected. Call connect() first"
        return self._i.get_trade_tick_history(instrument_id)

    def get_outstanding_orders(self, instrument_id: str) -> typing.List[OrderStatus]:
        """
        Returns the client's currently outstanding limit orders on an instrument.

        Parameters
        ----------
        instrument_id: str
            The instrument_id of the instrument to obtain outstanding orders for.

        Returns
        -------
        typing.List[OrderStatus]
            Returns the client's currently outstanding limit orders on an instrument.
        """
        assert self.is_connected(), "Cannot call function until connected. Call connect() first"
        return self._e.get_outstanding_orders(instrument_id)

    def get_last_price_book(self, instrument_id: str) -> PriceBook:
        """
        Returns the last received limit order book state for an instrument.

        Parameters
        ----------
        instrument_id: str
            The instrument_id of the instrument to obtain the limit order book for.

        Returns
        -------
        PriceBook
             Returns the last received limit order book state for an instrument.
        """
        assert self.is_connected(), "Cannot call function until connected. Call connect() first"
        return self._i.get_last_price_book(instrument_id)

    def get_positions(self) -> typing.Dict[str, int]:
        """
        Get your current positions.

        Returns
        -------
        typing.Dict[str, int]
            Returns a dictionary mapping instrument_id to the current position in the instrument, expressed in
            amount of lots held.
        """
        assert self.is_connected(), "Cannot call function until connected. Call connect() first"
        return self._e.get_positions()

    def get_positions_and_cash(self) -> typing.Dict[str, typing.Any]:
        """
        Get your current positions and cash.

        Returns
        -------
        typing.Dict[str, typing.Any]
            Returns a dictionary mapping instrument_id to dictionary of 'position' and 'cash'. The position is the
            current amount of lots held in the instrument and the cash is the current cash position arising from
            previous buy and sell trades in the instrument.
        """
        assert self.is_connected(), "Cannot call function until connected. Call connect() first"
        return self._e.get_positions_and_cash()

    def get_cash(self) -> float:
        """
        Get your total cash position.

        Returns
        -------
        typing.Dict[str, int]
            Returns total cash position of the client arising from all cash exchanged on previous buy and sell trades in all instruments.
            amount of lots held.
        """
        assert self.is_connected(), "Cannot call function until connected. Call connect() first"
        return self._e.get_cash()

    def get_pnl(self, valuations: typing.Dict[str, float] = None) -> float:
        """
        Calculates PnL based on current instrument and cash positions.

        For any non-zero position:
            If the valuations dictionary is provided, uses the valuation provided.
            If no instrument valuation is provided, falls back on the price of the last public tradetick.
            If valuation is not provided and no public tradetick is available, no PnL can be calculated.

        Parameters
        ----------
        valuations: typing.Dict[str, float]
            Optional, dictionary mapping instrument_id to current instrument valuation.

        Returns
        -------
        float
            Your current PnL, valued at the last-traded price if no valuations are provided.
        """

        assert self.is_connected(), "Cannot call function until connected. Call connect() first"
        if valuations is None:
            valuations = dict()

        positions = self._e.get_positions_and_cash()
        pnl = 0

        for instrument_id, pos in positions.items():
            if pos['volume'] == 0:
                pnl += pos['cash']
                continue

            if instrument_id in valuations:
                valuation = valuations[instrument_id]
            else:
                ltp = self._i.get_last_traded_price(instrument_id)
                if ltp:
                    valuation = ltp
                else:
                    logger.error(f"No public trade-tick found to evaluate '{instrument_id}'-position ({pos['volume']}) against and no valuation provided. "
                                 f"Unable to calculate PnL.")
                    return None

            pnl += valuation * pos['volume'] + pos['cash']

        return pnl

    def get_instruments(self) -> typing.Dict[str, Instrument]:
        """
        Returns all existing instruments on the exchange

        Returns
        -------
        typing.Dict[str, Instrument]
            Dict of instrument_id to the instrument definition.
        """
        assert self.is_connected(), "Cannot call function until connected. Call connect() first"
        return self._i.get_instruments()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

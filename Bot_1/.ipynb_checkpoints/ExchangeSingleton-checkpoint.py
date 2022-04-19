class ExchangeSingleton:
    """
    Singleton class for the exchange
    @author: Nidhish
    """

    __exchange = None
    def __init__(self):
        if ExchangeSingleton.__exchange is None:
            ExchangeSingleton.__exchange = self
        else:
            raise Exception("ExchangeSingleton is a singleton class")

    @staticmethod
    def getInstance():
        if ExchangeSingleton.__exchange is None:
            ExchangeSingleton()
        return ExchangeSingleton.__exchange

    def connect(self):
        self.__exchange.connect()
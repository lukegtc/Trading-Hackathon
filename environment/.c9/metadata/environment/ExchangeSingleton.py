{"filter":false,"title":"ExchangeSingleton.py","tooltip":"/ExchangeSingleton.py","undoManager":{"mark":0,"position":0,"stack":[[{"start":{"row":0,"column":0},"end":{"row":20,"column":33},"action":"insert","lines":["class ExchangeSingleton:","    \"\"\"","    Singleton class for the exchange","    @author: Nidhish","    \"\"\"","","    __exchange = None","    def __init__(self):","        if ExchangeSingleton.__exchange is None:","            ExchangeSingleton.__exchange = self","        else:","            raise Exception(\"ExchangeSingleton is a singleton class\")","","    @staticmethod","    def getInstance():","        if ExchangeSingleton.__exchange is None:","            ExchangeSingleton()","        return ExchangeSingleton.__exchange","","    def connect(self):","        self.__exchange.connect()"],"id":1}]]},"ace":{"folds":[],"scrolltop":0,"scrollleft":0,"selection":{"start":{"row":20,"column":33},"end":{"row":20,"column":33},"isBackwards":false},"options":{"guessTabSize":true,"useWrapMode":false,"wrapToView":true},"firstLineState":0},"timestamp":1648926739527,"hash":"76834c0c7e30f12bdc061c788b99ad057dc402c2"}
import capnp
capnp.remove_event_loop()
capnp.create_event_loop(threaded=True)

from .synchronous_client import Exchange
from .exchange_client import InfoClient, ExecClient
from .exchange_client import ORDER_TYPE_IOC, ORDER_TYPE_LIMIT, SIDE_ASK, SIDE_BID

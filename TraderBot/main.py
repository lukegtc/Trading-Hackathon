from Trader import Trader
from optibook.synchronous_client import Exchange
import logging
import time

if __name__ == '__main__':
    global_logger = logging.getLogger(__name__)
    e = Exchange()
    e.connect()
    global_logger.debug("Connected to the exchange.")
    trader = Trader(e, ['PHILIPS_A', 'PHILIPS_B'], 0.1)
    global_logger.debug("Trader initialized...")
    
    while True:
        # try:
        #     trader.run()
        # except Exception as e:
        #     global_logger.error(f'Exception: {e}')
        
        trader.run()
        time.sleep(0.25)
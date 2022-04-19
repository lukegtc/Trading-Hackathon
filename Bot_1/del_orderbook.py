from optibook.synchronous_client import Exchange

from dataclasses import dataclass
import numpy as np
import time

from constants import *


e = Exchange()
e.connect()



print(e.get_positions())
for s, p in e.get_positions().items():
    if p > 0:
        e.insert_order(s, price=1, volume=p, side='ask', order_type='ioc')
    elif p < 0:
        e.insert_order(s, price=100000, volume=-p, side='bid', order_type='ioc')  
print(e.get_positions())
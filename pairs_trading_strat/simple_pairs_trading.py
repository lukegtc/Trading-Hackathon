import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint, adfuller
# import seaborn as sns; sns.set(style="whitegrid")






def generate_data(params):
    mu = params[0]
    sigma = params[1]
    return np.random.normal(mu, sigma)
    
    
def adfuller_ts_test(ts, cutoff=0.01):
    # stationarity_test
    # H_0 in adfuller is unit root exists (non-stationary)
    # We must observe significant p-value to convince ourselves that the series is stationary
    pvalue = adfuller(ts)[1]
    if pvalue < cutoff:
        # TS is likely stationary
        return True
        print(f"p-val= {pvalue} | Series: {ts.name}")
        # print('p-value = ' + str(pvalue) + ' The series ' + X.name +' is likely stationary.')
    else:
        # TS is likely not stationary
        # return False
        print(f"p-val= {pvalue} | Series: {ts.name}")
        # print('p-value = ' + str(pvalue) + ' The series ' + X.name +' is likely non-stationary.')

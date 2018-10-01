import requests
import krakenex
import config
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from math import floor

import matplotlib.pyplot as plt
import seaborn as sns




class Portfolio:

    def __init__(self, cap, update_lag, update_freq, plot=0):     # plot is only for testing/debugging; not execution!

        self.tether = 'USDT'
        self.tether_name = 'Tether'
        self.fee = .002

        self.cap = cap
        self.initial_cap = cap
        self.update_freq = update_freq
        self.update_lag = update_lag
        self.utc_lag = datetime.utcnow() - datetime.now()

        self.kraken = krakenex.API(key=config.kraken_api_key, secret=config.kraken_private_key)
        self.ensure_funds()

        self.url0 = 'https://min-api.cryptocompare.com/data/histominute' + \
                    '?fsym=' + self.tether + \
                    '&tsym=USD' + \
                    '&aggregate=1'

        self.update_log = pd.DataFrame(columns=['update_time', 'min_threshold', 'max_threshold', 'expected_profit'])

        self.schedule_actions()

        self.plot = plot
        self.plot_recent_minutes(limit=self.update_lag, switch=plot)

        return

    def update(self):

        self.data = self.get_recent_minutes(limit=self.update_lag)
        self.min_threshold, self.max_threshold, _expected_profit, self.sim_data = self.get_optimal_thresholds()

        self.update_time = datetime.now().replace(second=0, microsecond=0) + \
                           timedelta(minutes=self.update_freq)

        self.update_log = self.update_log.append(pd.Series({'update_time': self.update_time,
                                                            'min_threshold': self.min_threshold,
                                                            'max_threshold': self.max_threshold,
                                                            'expected_profit': _expected_profit}),
                                                 ignore_index=True)

        return

    def get_recent_minutes(self, limit):

        try:
            res = requests.get(self.url0 + '&limit=' + str(limit), timeout=10)
            res.raise_for_status()
            data = res.json()['Data']
        except requests.exceptions.HTTPError:
            raise exceptions.ScrapeFailed()

        data = pd.DataFrame(data)
        data['time'] = [datetime.fromtimestamp(d) for d in data['time']]

        return data

    def plot_recent_minutes(self, limit, switch=0):

        if switch == 0:
            return

        y = self.data['close'].iloc[-limit:]

        sns.set_style('darkgrid')

        plt.figure()

        y1 = self.data['close'].iloc[-limit:]
        y2 = self.data['volumefrom'].iloc[-limit:]

        plt.subplot(2, 1, 1)
        plt.plot(y1)
        plt.title(self.tether_name + ' (' + self.tether + ')')
        plt.ylabel('price ($)')

        ytop = np.mean(y2.values) + 1 * np.std(y2.values)

        plt.subplot(2, 1, 2)
        plt.plot(y2)
        plt.gca().set_ylim([0, ytop])
        plt.xlabel('time (m)')
        plt.ylabel('volume ($)')

        plt.show()

        return

    def get_optimal_thresholds(self):

        data = self.get_optimal_threshold_data().head(10)

        min_threshold = round(np.mean(data['min'].values.astype('float32')), 4)
        max_threshold = np.min([round(np.mean(data['max'].values.astype('float32')), 4), .9999])
        expected_profit = np.mean(data['total_profit'].values.astype('float32'))

        return min_threshold, max_threshold, expected_profit, data

    def get_optimal_threshold_data(self):                           # a disgusting brute force approach

        ymin = np.min(self.data['close'].values)
        ymax = 1

        data = pd.DataFrame(columns=['min', 'max', 'trade_profit', 'trades', 'total_profit'])

        for min_threshold in np.arange(ymin, ymax, .0001):
            for max_threshold in np.arange(ymin, ymax, .0001):
                if max_threshold <= min_threshold + self.fee:
                    continue

                check_max = True
                check_min = True
                counter = 0

                for y_t in self.data['close'].values:

                    if check_min == True and y_t <= min_threshold:
                        check_max = True
                        check_min = False
                        counter += 1

                    elif check_max == True and y_t >= max_threshold:
                        check_max = False
                        check_min = True
                        counter += 1

                counter = 0 if counter == 1 else counter

                data = data.append(pd.Series({'min': min_threshold,
                                              'max': max_threshold,
                                              'trade_profit': max_threshold - min_threshold,
                                              'trades': counter,
                                              'total_profit': (max_threshold - min_threshold - .002) * counter}),
                                   ignore_index=True)

        return data.sort_values(by=['total_profit'], ascending=False)

    def ensure_funds(self):

        data = self.kraken.query_private('Balance')
        balance = float(data['result']['ZUSD'])

        if balance < self.cap:
            print('* Insufficient funds in account (${:.2f})'.format(balance))
            print('---------- Salience TETHER has ended ----------')
            quit()

    def schedule_actions(self):

        self.update()
        print(self.update_log)

        #don't do this stuff if the threshold difference is less than .002

        while datetime.now() < self.update_time:

            data_buy = self.kraken.query_private('AddOrder', {'pair': 'USDTZUSD',
                                                              'type': 'buy',                                        #
                                                              'ordertype': 'limit',
                                                              'price': str(self.min_threshold),                     ##
                                                              'volume': str(floor(10000000 * self.cap /
                                                                                  self.min_threshold) / 10000000),  #
                                                              # 'leverage': ,
                                                              # 'oflags': ,
                                                              'expiretm': str(round(self.update_time.timestamp())),
                                                              # ----------
                                                              'close[ordertype]': 'limit',
                                                              'close[price]': str(self.max_threshold)})             ##
            print(data_buy)
            quit()

            # check if order is closed:
                #if so, replace order
                #and update/save # of closed orders and return amounts

        return self.schedule_actions()

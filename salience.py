from portfolio_io.portfolio import Portfolio

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--cap', type=int, help='maximum initial spend for Salience')
parser.add_argument('-l', '--lag', type=int, help='time window (minutes) on which thresholds are optimized')
parser.add_argument('-f', '--freq', type=int, help='frequency of threshold updates (minutes)')
args = parser.parse_args()


def confirm():

    confirmation = input('- Please confirm trading with a cap of ${:.2f} with thresholds '\
                         'updated every {} minutes '\
                         'based on the last {} minutes: '.format(args.cap, args.freq, args.lag))

    if confirmation.lower() not in ['y', 'yes']:
        quit()


def main():

    confirm()

    t = Portfolio(cap=args.cap, update_lag=args.lag, update_freq=args.freq, plot=1)







if __name__ == '__main__':
    main()

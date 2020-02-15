from functions_file import *
# https://pypi.org/project/schedule/
import schedule, warnings
from statistics import mean 
warnings.simplefilter(action = "ignore", category = RuntimeWarning)

def job():
	# Only when internet is available
	coin = 'LTC'
	df = coin_data_function(coin, start=datetime(2018, 1, 1),
									end = datetime.now(), tf='1D')

	# Drop the columns we don't need
	cols = ['Volume', 'Number of trades', 'Buy volume']
	df = df.drop(cols, axis=1)
	df['Coin'] = coin

	inner_list = []

	# Call SMAs function
	sma(df, 'Close')

	# State function: You read it from top to bottom - Using loc
	def states(SMA1, SMA2, SMA3):
		df['State'] = '-'
		df.loc[(SMA1 < SMA2) & (SMA2 < SMA3), 'State'] = '3, 2, 1' # Buy signal pair 2 - First state
		df.loc[(SMA2 < SMA1) & (SMA1 < SMA3), 'State'] = '3, 1, 2' # Buy signal pair 2 - Second state
		df.loc[(SMA2 < SMA3) & (SMA3 < SMA1), 'State'] = '1, 3, 2' # HODL
		df.loc[(SMA3 < SMA2) & (SMA2 < SMA1), 'State'] = '1, 2, 3' # Buy signal pair 1 - Second state
		df.loc[(SMA3 < SMA1) & (SMA1 < SMA2), 'State'] = '2, 1, 3' # Buy signal pair 1 - First state

	states(df['SMA1'].values, df['SMA2'].values, df['SMA3'].values)

	# Buy signal after and before states
	def buy_sma(state):
		df['State shifted'] = df['State'].shift(1)
		df['Buy'] = 0

		# Continuation or reversal case
		#df.loc[(state == '1, 2, 3') & (df['State shifted'].values == '2, 1, 3'), 'Buy'] = 1

		# Bullish confirmation
		df.loc[(state == '1, 2, 3') & (df['State shifted'].values == '1, 3, 2'), 'Buy'] = 1

		# Drop the state shifted
		df.drop('State shifted', axis=1, inplace=True)
	
	buy_sma(df['State'].values)

	# Test signals
	def test_signals():	
		# Test after one day (24h)
		n = 15*24
		df['High shifted'] = df['High'].shift(-n)
		df['Low shifted'] = df['Low'].shift(-n)
		df['Rolling High'] = df['High shifted'].rolling(n).max()
		df['Rolling Low'] = df['Low shifted'].rolling(n).min()
		df['Max Gainz'] = (df['Rolling High'].values - df['Close'].values)/df['Close'].values
		df['Max Drown'] = (df['Rolling Low'].values - df['Close'].values)/df['Close'].values

		avg_gainz = df.loc[df['Buy'] == 1, 'Max Gainz'].mean()
		max_gainz = df.loc[df['Buy'] == 1, 'Max Gainz'].max()
		avg_drown = df.loc[df['Buy'] == 1, 'Max Drown'].mean()
		max_drown = df.loc[df['Buy'] == 1, 'Max Drown'].min()

		print('\n')
		print('Avg gainz:', avg_gainz)
		print('Max gainz:', max_gainz)
		print('Avg drown:', avg_drown)
		print('Max drown', max_drown)
		print('\n')

		# Drop columns
		cols = ['High shifted', 'Low shifted', 'Rolling High', 'Rolling Low']
		for col in cols:
			df.drop(col, axis=1, inplace=True)
	
	#test_signals()

	print('\n')
	def test_fixed_risk(risk = 0.05):
		r, stp = [], []
		print(df.loc[df['Buy'].values == 1, ['Open time', 'Close', 'SMA1', 'SMA2', 'SMA3']])
		print('\n')
		buy_index = df.loc[df['Buy'].values == 1].index
		

		for b_index in buy_index:
			stopped = 1
			open_date = df['Open time'].iloc[b_index]
			entry = df['Close'].iloc[b_index]
			sl = entry*(1-risk)
			print('.....................................')
			try:
				sl_index = df.loc[(df.index > b_index) & (df['Low'].values < sl)].index[0]
				new_df = df.iloc[b_index:sl_index]
			except:
				new_df = df.loc[(df.index > b_index)]
				stopped = 0

			max_price = new_df['High'].max()
			max_r = (((max_price - entry)/entry))/risk
			if stopped == 0:
				r.append(max_r)

			stp.append(stopped)

			try:
				hours_index = df.loc[(df.index > b_index) & (df['High'].values == max_price)].index[0]
			except:
				hours_index = b_index

			hours_to_max = hours_index - b_index
			last_date = new_df['Open time'].iloc[-1]
			
			print('Index:', b_index)
			print('Open date:', open_date)
			print('Entry:', entry)
			print('SL:', sl)
			print('Max price:', max_price)
			print('Max r:', max_r)
			print('Hours to max price:', hours_to_max)
			print('Last date:', last_date)
			print('stopped:', stopped)

			inner_list.append([open_date, coin, entry, sl, max_price, max_r, hours_to_max, last_date, stopped])

			print('.....................................')
			print('\n')

		total_trades = len(stp)
		WR = (len(stp)-sum(stp))/len(stp)
		xpc = WR*mean(r) - (1-WR)
		min_r = (1-WR)/WR

		print('Total trades:', total_trades)
		print('Average winners:', mean(r))
		print('Expectancy:', xpc)
		print('WR:', WR)
		print('Min. R for BE:', min_r )
		print('\n')

	test_fixed_risk()
	last_24h_usd_volume = df['USD volume'].iloc[-24:].sum()
	print('Last 24h USD volume in thousands:', last_24h_usd_volume)
	print('\n')

	name = coin + ' hourly data.xlsx'
	df.to_excel(name, index =  False)

	cols = ['Open date', 'Coin', 'Entry', 'SL', 'Max price', 'Max R', 'Hours to max', 'Last date', 'Stopped']
	df_stats = pd.DataFrame(inner_list, columns = cols)
	name = coin + ' stats data.xlsx'
	df_stats.to_excel(name, index = False)

def dumbass():
	print('Hello Mom!')

job()

'''
#schedule.every(1).minutes.do(job)
#schedule.every().minute.at(":15").do(job)
#schedule.every().minute.at(":2").do(dumbass)
while True:
	schedule.run_pending()
'''
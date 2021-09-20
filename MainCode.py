import MetaTrader5 as mt5
import time
from datetime import datetime, timedelta
import math
import numpy as np
import pandas as pd

if not mt5.initialize():
	print("initialize() failed")
	mt5.shutdown()

# establish MetaTrader 5 connection to a specified trading account
if not mt5.initialize(login=*********, server="ICMarketsEU-Demo",password="*********"):
	print("initialize() failed, error code =",mt5.last_error())
	quit()
print("Connected")

# request connection status and parameters
print(mt5.terminal_info())
# get data on MetaTrader 5 version
print(mt5.version())

timeNow = datetime.today() + timedelta(hours=3)

btcusd_rates = mt5.copy_rates_from("BTCUSD", mt5.TIMEFRAME_M15, timeNow, 100)
#print(btcusd_rates)

# import the 'pandas' module for displaying data obtained in the tabular form
pd.set_option('display.max_columns', 500) # number of columns to be displayed
pd.set_option('display.width', 1500)      # max table width to display

# create DataFrame out of the obtained data
rates_frame = pd.DataFrame(btcusd_rates)
# convert time in seconds into the datetime format
rates_frame['time']=pd.to_datetime(rates_frame['time'], unit='s')
# Get SMA for close
rates_frame['26SMA'] = rates_frame['close'].rolling(window=26).mean()
rates_frame['12SMA'] = rates_frame['close'].rolling(window=12).mean()

# display data
print("\nDisplay dataframe with data")
print(rates_frame)


def getSMA():
	smaSum = 0
	for i in rates_frame.close[100-26:]:
		smaSum = smaSum + i

def getLow():
	P1 = 99999999999
	count = 0
	for low in rates_frame.low:
		if low < P1:
			P1 = low
			position = count
		count = count + 1
	#print("P1 is: " + str(P1) + " at index: " + str(rates_frame.index[position]))
	return position

def getTrendLine():
	angle = 180
	for i in rates_frame.index[getLow()+1:]:
		x = (i - rates_frame.index[getLow()]) * 10
		y = rates_frame.low[i] - rates_frame.low[getLow()]
		angleCheck = math.degrees(math.atan(y/x))
		if angleCheck < angle:
			angle = angleCheck
			#print("Angle202: " + str(angle))
		#print(i)
	return angle

def getP2():
	angle = 180
	p2Count = 0
	P2 = 0
	for i in rates_frame.index[getLow()+1:]:
		x = (i - rates_frame.index[getLow()]) * 10
		y = rates_frame.low[i] - rates_frame.low[getLow()]
		angleCheck = math.degrees(math.atan(y/x))
		p2Count = p2Count + 1
		if angleCheck < angle:
			angle = angleCheck
			P2 = P2 + p2Count
			p2Count = 0
			#print(P2)
	#print(P2)
	return P2

def trade():
	# prepare the buy request structure
	symbol = "BTCUSD"
	symbol_info = mt5.symbol_info(symbol)
	if symbol_info is None:
	    print(symbol, "not found, can not call order_check()")
	    mt5.shutdown()
	    quit()
	 
	# if the symbol is unavailable in MarketWatch, add it
	if not symbol_info.visible:
	    print(symbol, "is not visible, trying to switch on")
	    if not mt5.symbol_select(symbol,True):
	        print("symbol_select({}}) failed, exit",symbol)
	        mt5.shutdown()
	        quit()
	 
	lot = 0.05
	point = mt5.symbol_info(symbol).point
	price = mt5.symbol_info_tick(symbol).ask
	deviation = 50
	request = {
	    "action": mt5.TRADE_ACTION_DEAL,
	    "symbol": symbol,
	    "volume": lot,
	    "type": mt5.ORDER_TYPE_BUY,
	    "price": price,
	    "sl": price - 500,
	    "tp": price + 1250,
	    "deviation": deviation,
	    "magic": 234000,
	    "comment": "python script open",
	    "type_time": mt5.ORDER_TIME_GTC,
	    "type_filling": mt5.ORDER_FILLING_IOC,
	}
	 
	# send a trading request
	result = mt5.order_send(request)
	# check the execution result
	print("1. order_send(): by {} {} lots at {} with deviation={} points".format(symbol,lot,price,deviation));
	if result.retcode != mt5.TRADE_RETCODE_DONE:
	    print("2. order_send failed, retcode={}".format(result.retcode))
	 
	print("2. order_send done, ", result)
	print("   opened position with POSITION_TICKET={}".format(result.order))

P1_Position = getLow()

currentAngle = 180.0
loopCounter = 0
while 1:
	timeNow = datetime.today() + timedelta(hours=3)
	btcusd_rates = mt5.copy_rates_from("BTCUSD", mt5.TIMEFRAME_M15, timeNow, 100)
	#print(btcusd_rates)

	# import the 'pandas' module for displaying data obtained in the tabular form
	pd.set_option('display.max_columns', 500) # number of columns to be displayed
	pd.set_option('display.width', 1500)      # max table width to display

	# create DataFrame out of the obtained data
	rates_frame = pd.DataFrame(btcusd_rates)
	# convert time in seconds into the datetime format
	rates_frame['time']=pd.to_datetime(rates_frame['time'], unit='s')
	# Get SMA for close
	rates_frame['SMA26'] = rates_frame['close'].rolling(window=26).mean()
	rates_frame['SMA12'] = rates_frame['close'].rolling(window=12).mean()
	emaMulti26 = (2/(26 + 1))
	emaMulti12 = (2/(12 + 1))
	EMA26 = [0] * 100
	rates_frame['EMA26'] = EMA26
	rates_frame.EMA26[25]  = rates_frame.SMA26[25]
	EMA12 = [0] * 100
	rates_frame['EMA12'] = EMA12
	rates_frame.EMA12[25]  = rates_frame.SMA12[25]
	count = 0

	for i in rates_frame.close[26:]:
		rates_frame.EMA26[26+count] = (i - rates_frame.EMA26[26+count-1]) * emaMulti26 + rates_frame.EMA26[26+count-1]
		count = count + 1
	count = 0
	for i in rates_frame.close[26:]:
		rates_frame.EMA12[26+count] = (i - rates_frame.EMA12[26+count-1]) * emaMulti12 + rates_frame.EMA12[26+count-1]
		count = count + 1

	macd = [0] * 100
	rates_frame['MACD'] = macd
	macdCount = 0
	for i in rates_frame.EMA12[26:]:
		rates_frame.MACD[26+macdCount] = i - rates_frame.EMA26[26+macdCount]
		macdCount = macdCount + 1
	rates_frame['SignalLine'] = rates_frame['MACD'].rolling(window=9).mean()


	# display data
	print("\nDisplay dataframe with data")
	print(rates_frame)

	if getLow() != P1_Position:
		currentAngle = 180
		trade = False
		P1_Position = getLow()
	print(currentAngle)
	Angle = getTrendLine()
	print("Angle: " + str(Angle))
	if Angle < currentAngle:
		currentAngle = getTrendLine()
		print("New Angle")
		if rates_frame.MACD[99] > rates_frame.SignalLine[99] and loopCounter > 0 and currentAngle > 0 and trade == True:
			trade()
			print("Trade Opened")
		else:
			print("MACD Negative - Trade not opened")
	else:
		print("No Change")
	trade = True
	print("Position 1: " + str(getLow()))
	print("Position 1 Value: " + str(rates_frame.low[getLow()]))
	print("Position 2: " + str((getLow() + getP2())))
	print("Position 2 Value: " + str(rates_frame.low[getLow()+getP2()]))
	loopCounter = loopCounter + 1
	print ("Looped Count: " + str(loopCounter))
	time.sleep(10)


time.sleep(1)
mt5.shutdown()
print("Program Ended..................................")

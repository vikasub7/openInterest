import requests
import json
import pandas as pd
from time import sleep
from datetime import datetime
import os
from datetime import time, timedelta
import numpy as np
from bokeh.plotting import figure, output_file, show, curdoc
from bokeh.models import ColumnDataSource, Span, SingleIntervalTicker, LinearAxis, PreText, Div, Button, LabelSet, Label
from bokeh.models.tools import HoverTool
from bokeh.layouts import row, column
from bokeh.transform import dodge
import time as _time
import numpy

output_file('columndatasource_example.html')

stock = "RELIANCE"
# CPR Calculation
class YahooFinance:
    def __init__(self, ticker, result_range='1mo', start=None, end=None, interval='15m', dropna=True):
        """
        Return the stock data of the specified range and interval
        Note - Either Use result_range parameter or use start and end
        Note - Intraday data cannot extend last 60 days
        :param ticker:  Trading Symbol of the stock should correspond with yahoo website
        :param result_range: Valid Ranges "1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"
        :param start: Starting Date
        :param end: End Date
        :param interval:Valid Intervals - Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
        :return:
        """
        if result_range is None:
            start = int(_time.mktime(_time.strptime(start, '%d-%m-%Y')))
            end = int(_time.mktime(_time.strptime(end, '%d-%m-%Y')))
            # defining a params dict for the parameters to be sent to the API
            params = {'period1': start, 'period2': end, 'interval': interval}

        else:
            params = {'range': result_range, 'interval': interval}

        # sending get request and saving the response as response object
        url = "https://query1.finance.yahoo.com/v7/finance/chart/{}".format(ticker)
        r = requests.get(url=url, params=params)
        data = r.json()
        # Getting data from json
        error = data['chart']['error']
        if error:
            raise ValueError(error['description'])
        self._result = self._parsing_json(data)
        if dropna:
            self._result.dropna(inplace=True)

    @property
    def result(self):
        return self._result

    def _parsing_json(self, data):
        timestamps = data['chart']['result'][0]['timestamp']
        # Formatting date from epoch to local time
        timestamps = [_time.strftime('%a, %d %b %Y %H:%M:%S', _time.localtime(x)) for x in timestamps]
        volumes = data['chart']['result'][0]['indicators']['quote'][0]['volume']
        opens = data['chart']['result'][0]['indicators']['quote'][0]['open']
        opens = self._round_of_list(opens)
        closes = data['chart']['result'][0]['indicators']['quote'][0]['close']
        closes = self._round_of_list(closes)
        lows = data['chart']['result'][0]['indicators']['quote'][0]['low']
        lows = self._round_of_list(lows)
        highs = data['chart']['result'][0]['indicators']['quote'][0]['high']
        highs = self._round_of_list(highs)
        df_dict = {'Open': opens, 'High': highs, 'Low': lows, 'Close': closes, 'Volume': volumes}
        df = pd.DataFrame(df_dict, index=timestamps)
        df.index = pd.to_datetime(df.index)
        return df

    def _round_of_list(self, xlist):
        temp_list = []
        for x in xlist:
            if isinstance(x, float):
                temp_list.append(round(x, 2))
            else:
                temp_list.append(pd.np.nan)
        return temp_list

    def to_csv(self, file_name):
        self.result.to_csv(file_name)


df7 = YahooFinance("^NSEI", result_range='3d', interval='1d', dropna='True').result

pivot = (df7['Low'].iloc[1] + df7['High'].iloc[1] + df7['Close'].iloc[1]) / 3
ppivot = (df7['Low'].iloc[0] + df7['High'].iloc[0] + df7['Close'].iloc[0]) / 3

change = (df7['Close'].iloc[1] - df7['Close'].iloc[0]) / df7['Close'].iloc[0] * 100

pbc = (df7['Low'].iloc[0] + df7['High'].iloc[0]) / 2
ptc = (ppivot - pbc) + ppivot
PTC = max(pbc, ptc)
PBC = min(pbc, ptc)

bc = (df7['Low'].iloc[1] + df7['High'].iloc[1]) / 2
tc = (pivot - bc) + pivot
TC = max(bc, tc).__round__(2)
BC = min(bc, tc).__round__(2)

s1 = 2 * pivot - df7['High'].iloc[1]
r1 = 2 * pivot - df7['Low'].iloc[1]
s2 = pivot - (df7['High'].iloc[1] - df7['Low'].iloc[1])
r2 = pivot + (df7['High'].iloc[1] - df7['Low'].iloc[1])

phigh = df7['High'].iloc[1]
plow = df7['Low'].iloc[1]
cpr_width = (((TC - BC) / pivot) * 100).__round__(2)
print(TC, pivot, BC)
print(cpr_width)
sentiment = 'Neutral'

# Dataframe settings
pd.set_option('display.width', 1500)
pd.set_option('display.max_columns', 75)
pd.set_option('display.max_rows', 1500)

# URL and Headers for getting option data
url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
#url = "https://www.nseindia.com/api/option-chain-equities?symbol=RELIANCE"
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
    'accept-encoding': 'gzip, deflate, br', 'accept-language': 'en-US,en;q=0.9'}

# Method to get option data
r = requests.get(url, headers=headers).json()
ce_values = [data['CE'] for data in r['filtered']['data'] if "CE" in data]
pe_values = [data['PE'] for data in r['filtered']['data'] if "PE" in data]

ce_data = pd.DataFrame(ce_values)
pe_data = pd.DataFrame(pe_values)
ce_data = ce_data.sort_values(['strikePrice'])
pe_data = pe_data.sort_values(['strikePrice'])

# PCR
pcr = (pe_data['openInterest'].sum() / ce_data['openInterest'].sum()).round(decimals=2)
pcr_change = (pe_data['changeinOpenInterest'].sum() / ce_data['changeinOpenInterest'].sum()).round(decimals=2)

# Dataframe with combined OI data
df = pd.DataFrame()
df['CE'] = ce_data['lastPrice']
df['CE_OI'] = ce_data['openInterest']
df['CE_OI_Change'] = ce_data['changeinOpenInterest']
df['strikePrice'] = ce_data['strikePrice']
df['PE'] = pe_data['lastPrice']
df['PE_OI'] = pe_data['openInterest']
df['PE_OI_Change'] = pe_data['changeinOpenInterest']
df['Nifty'] = pe_data['underlyingValue']
max_oi_change = max(df['CE_OI_Change'].max(), df['PE_OI_Change'].max())
max_oi = max(df['CE_OI'].max(), df['PE_OI'].max())
minRange = (df['Nifty'].iloc[1] - 400).round(decimals=0)
maxRange = (df['Nifty'].iloc[1] + 400).round(decimals=0)

print("DF created")

# Bokeh Plot Design
source = ColumnDataSource(df)
# Change in OI Plot
p = figure(x_range=(minRange, maxRange), plot_width=750, plot_height=500, x_minor_ticks=2)
p.vbar(x=dodge('strikePrice', -10, range=p.x_range), top='CE_OI_Change', source=source, color="#e84d60", width=20)
p.vbar(x=dodge('strikePrice', 10, range=p.x_range), top='PE_OI_Change', source=source, color="#718dbf", width=20)
p.background_fill_color = "black"
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
nifty = df['Nifty'].iloc[1]
ltp = Span(location=nifty, dimension='height', line_color='green', line_dash='dashed', line_width=3)
p.add_layout(ltp)
my_label = Label(x=nifty, y=max_oi_change, text=str(nifty), border_line_color='green', border_line_alpha=1.0,
                 y_offset=3, x_offset=-38, text_color='white', text_font_size='8pt',
                 background_fill_color='green', background_fill_alpha=1.0)
p.add_layout(my_label)

# Total OI Plot
p2 = figure(x_range=(minRange, maxRange), plot_width=750, plot_height=500, x_minor_ticks=2)
p2.vbar(x=dodge('strikePrice', -10, range=p2.x_range), top='CE_OI', source=source, color="#e84d60", width=20)
p2.vbar(x=dodge('strikePrice', 10, range=p2.x_range), top='PE_OI', source=source, color="#718dbf", width=20)
p2.background_fill_color = "black"
p2.xgrid.grid_line_color = None
p2.ygrid.grid_line_color = None
nifty = df['Nifty'].iloc[1]
ltp2 = Span(location=nifty, dimension='height', line_color='green', line_dash='dashed', line_width=3)
p2.add_layout(ltp)
my_label2 = Label(x=nifty, y=max_oi, text=str(nifty), border_line_color='green', border_line_alpha=1.0, y_offset=3,
                  x_offset=-38, text_color='white', text_font_size='8pt',
                  background_fill_color='green', background_fill_alpha=1.0)
p2.add_layout(my_label2)

# Buttons
ctime = datetime.now()
hour = (ctime.strftime("%H"))
minute = (ctime.strftime("%M"))
sec = (ctime.strftime("%S"))

timeUpdate = Button(label='Last Updated:' + hour + ':' + minute + ':' + sec, button_type="primary")
pcrButton = Button(label='PCR:' + str(pcr), min_height = 150, sizing_mode = "stretch_width")
if pcr > 1:
    pcrButton.button_type = "success"
else:
    pcrButton.button_type = "danger"

pcrChangeButton = Button(label='PCR Change:' + str(pcr_change), min_height = 150, sizing_mode = "stretch_width")
if pcr_change > pcr:
    pcrChangeButton.button_type = "success"
else:
    pcrChangeButton.button_type = "danger"

sentimentButton = Button(label='Sentiment:' + sentiment, min_height = 150, sizing_mode = "stretch_width")
if TC < PBC:
    sentimentButton.label = 'CPR: Very Bearish'
    sentimentButton.button_type = "danger"
elif BC > PTC:
    sentimentButton.label = 'CPR: Very Bullish'
    sentimentButton.button_type = "success"
elif TC < PTC and PBC < BC:
    sentimentButton.label = 'CPR: Inside Day'
    sentimentButton.button_type = "warning"
elif TC > PTC and PBC > BC:
    sentimentButton.label = 'CPR: Expanded Day'
    sentimentButton.button_type = "warning"
elif TC > PTC and PBC < BC:
    sentimentButton.label = 'CPR: Bullish'
    sentimentButton.button_type = "success"
elif TC < PTC and PBC > BC:
    sentimentButton.label = 'CPR: Bearish'
    sentimentButton.button_type = "danger"
print("Plot settings configured")

# CallBack Method
def callback():
    global ctime, minute
    ctime = datetime.now()
    hour = (ctime.strftime("%H"))
    minute = (ctime.strftime("%M"))
    sec = (ctime.strftime("%S"))
    timeUpdate.label = 'Last Updated:' + hour + ':' + minute + ':' + sec
    try:
        r = requests.get(url, headers=headers).json()
        ce_values = [data['CE'] for data in r['filtered']['data'] if "CE" in data]
        pe_values = [data['PE'] for data in r['filtered']['data'] if "PE" in data]

        ce_data = pd.DataFrame(ce_values)
        pe_data = pd.DataFrame(pe_values)
        ce_data = ce_data.sort_values(['strikePrice'])
        pe_data = pe_data.sort_values(['strikePrice'])

        pcr = (pe_data['openInterest'].sum() / ce_data['openInterest'].sum()).round(decimals=2)
        pcr_change = (pe_data['changeinOpenInterest'].sum() / ce_data['changeinOpenInterest'].sum()).round(decimals=2)
        pcrButton.label = 'PCR:' + str(pcr)
        if pcr > 1:
            pcrButton.button_type = "success"
        else:
            pcrButton.button_type = "danger"

        pcrChangeButton.label = 'PCR Change:' + str(pcr_change)
        if pcr_change > pcr:
            pcrChangeButton.button_type = "success"
        else:
            pcrChangeButton.button_type = "danger"

        df = pd.DataFrame()
        df['CE'] = ce_data['lastPrice']
        df['CE_OI'] = ce_data['openInterest']
        df['CE_OI_Change'] = ce_data['changeinOpenInterest']
        df['strikePrice'] = ce_data['strikePrice']
        df['PE'] = pe_data['lastPrice']
        df['PE_OI'] = pe_data['openInterest']
        df['PE_OI_Change'] = pe_data['changeinOpenInterest']
        df['Nifty'] = pe_data['underlyingValue']
        source.data = df
        ltp.location = df['Nifty'].iloc[1]
        ltp2.location = df['Nifty'].iloc[1]
        max_oi_change = max(df['CE_OI_Change'].max(), df['PE_OI_Change'].max())
        max_oi = max(df['CE_OI'].max(), df['PE_OI'].max())
        my_label.x = df['Nifty'].iloc[1]
        my_label.y = max_oi_change
        my_label.text = str(df['Nifty'].iloc[1])
        my_label2.x = df['Nifty'].iloc[1]
        my_label2.y = max_oi
        my_label2.text = str(df['Nifty'].iloc[1])
    except:
        pass

print("Final step")
curdoc().add_root(column(timeUpdate, row(p, p2), row(pcrButton, pcrChangeButton, sentimentButton)))
print("Running!")
#curdoc().add_periodic_callback(callback, 10000)
#how(column(timeUpdate, row(p, p2), row(pcrButton, pcrChangeButton, sentimentButton)))

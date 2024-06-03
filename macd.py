import pandas as pd
import talib as ta
import datetime
import pandas_datareader.data as web
import glob
import os
import numpy as np
import streamlit as st

# 銘柄コード入力
code = st.number_input('銘柄コードを入力してください', min_value=100, max_value=9999, step=1)
code = str(code)

# 銘柄名取得
stock_list = "stock_list.csv"
df_stock_list = pd.read_csv(stock_list, encoding='utf-8',index_col='コード')
codeName = df_stock_list.loc[code]['銘柄名']

# データ読み込み
data_list = f"data/cap_lists/{code}.csv"
df = pd.read_csv(data_list, encoding='utf-8', index_col='Date', parse_dates=True)

# テクニカル指標計算
# EMA
period = 25
ema_value = ta.EMA((df['Close']), period)
df['EMA'] = ema_value
# 前日との差分を取って、その日が上昇か下降かを判定:ema_trend
# 転換点をtrendの当日を2倍して比較することでGC/DCだけじゃなく上昇も下降も把握
# 上昇=+3, +転換=1, -転換=-1, 下降=-3
ema_trend = df['EMA'] - df['EMA'].shift(1)
ema_change = np.sign(ema_trend)*2 + np.sign(ema_trend.shift(1))
# MACD
macd, macdsignal, macdhist = ta.MACD(df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
df['MACD'] = macd
df['MACD_Signal'] = macdsignal
df['MACD_Hist'] = macdhist
# histのトレンドチェック 当日を2倍して比較することでGC/DCだけじゃなく上昇も下降も把握 上昇=+3, +転換=1, -転換=-1, 下降=-3
macd_change = np.sign(macdhist)*2 + np.sign(macdhist.shift(1))
# MACD,EMAの条件があうdfを抜き出し（練習）
df[((macd_change ==1) & (ema_change == 3))|((macd_change ==3) & (ema_change == 1))|((macd_change ==1) & (ema_change == 1))].tail()
df['MACD_Sign'] = np.where(((macd_change ==1) & (ema_change == 3))|((macd_change ==3) & (ema_change == 1))|((macd_change ==1) & (ema_change == 1)), df['Low'], np.nan)
# 20日高値をrollingで作成、差分を取って、変化日が1、変化しない日は0
high_25d = df["High"].rolling(window=20).max()
high_25d_change = np.sign(high_25d - high_25d.shift(1))
high_25d_change[high_25d_change ==1].tail()
df['25D_High'] = np.where(high_25d_change == 1, df['High'], np.nan)
# 条件に当てはまる行を格納するリスト
matched_rows = []
# takane列が0以上の数値になっている日を見つける(行ごと抜き出し)
takane_days = df[df['25D_High'].notnull() & (df['25D_High'] >= 0)]
for takane_day, raw in takane_days.iterrows():
    # takane日から1週間後までの範囲を選択
    start_date = takane_day - pd.Timedelta(days=9)  # 1週間は7日間なので6を足す
    end_date = takane_day 
    window = df.loc[start_date:end_date] #windowに範囲を格納

    # その範囲内にChange列に0以上の数値が出現したかチェック
    # change_rows = window[window['MACD_Sign'].notnull() & (window['MACD_Sign'] >= 0)]
    
    if any(window['MACD_Sign'] >=0):

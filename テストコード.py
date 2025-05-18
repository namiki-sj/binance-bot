import ccxt
import pandas as pd
import time
import requests
import os
from dotenv import load_dotenv

# .env 読み込み
load_dotenv()

# 環境変数から読み込み
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# 取引設定
symbol = 'BTC/USDT'
max_usdt = 70
timeframe = '15m'

# Binance Futures Testnet 設定
binance = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})
binance.set_sandbox_mode(True)

# Discord 通知
def send_discord_notify(message):
    try:
        if DISCORD_WEBHOOK_URL:
            requests.post(DISCORD_WEBHOOK_URL, json={'content': message})
    except Exception as e:
        print("Discord通知エラー:", e)

# OHLCV取得
def fetch_data():
    ohlcv = binance.fetch_ohlcv(symbol, timeframe, limit=21)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df

# シグナル生成
def signal_generator(df):
    high = df['high'][:-1].max()
    low = df['low'][:-1].min()
    current_price = df['close'].iloc[-1]
    if current_price > high:
        return 'buy'
    elif current_price < low:
        return 'sell'
    return 'hold'

# 注文実行
def execute_order(signal):
    price = binance.fetch_ticker(symbol)['last']
    amount = round(max_usdt / price, 5)

    if signal == 'buy':
        order = binance.create_market_buy_order(symbol, amount)
        send_discord_notify(f'✅ BUY EXECUTED: {order}')
        print('BUY EXECUTED:', order)

    elif signal == 'sell':
        order = binance.create_market_sell_order(symbol, amount)
        send_discord_notify(f'✅ SELL EXECUTED: {order}')
        print('SELL EXECUTED:', order)

# メインループ
while True:
    try:
        df = fetch_data()
        signal = signal_generator(df)
        price = df['close'].iloc[-1]
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Signal: {signal} | Price: {price}")
        if signal in ['buy', 'sell']:
            execute_order(signal)
        time.sleep(900)
    except Exception as e:
        print("Error:", e)
        send_discord_notify(f"⚠️ Error: {e}")
        time.sleep(60)

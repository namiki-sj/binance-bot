import ccxt
import pandas as pd
import time
import requests

# Discord WebhookのURLを入力
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1373277632187076670/rc_XJnxP-7qeWqNrMV8AohohpoNPBCgWRVezBFKpL6dK3f5_1qAfj2vT0qfFssk5YSPP'

# Binance Testnet APIキーとシークレットキー
API_KEY = '99d03e81fd9ae7a829641d0de1dde0ffa63b5ab529ead9d31f76bf6d785d76d6'
API_SECRET = 'd396734d27107a27e5ee1b59ca002dea5f6556da202869620ef4a68647097ef9'

# 取引設定
symbol = 'BTC/USDT'
max_usdt = 70  # 最大70 USDTを使う
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
binance.set_sandbox_mode(True)  # 必ずTestnetに接続

# Discord 通知関数
def send_discord_notify(message):
    try:
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

# 取引実行
def execute_order(signal):
    price = binance.fetch_ticker(symbol)['last']
    amount = round(max_usdt / price, 5)

    if signal == 'buy':
        order = binance.create_market_buy_order(symbol, amount)
        send_discord_notify(f'BUY EXECUTED: {order}')
        print('BUY EXECUTED:', order)

    elif signal == 'sell':
        order = binance.create_market_sell_order(symbol, amount)
        send_discord_notify(f'SELL EXECUTED: {order}')
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
        time.sleep(900)  # 15分ごと

    except Exception as e:
        print("Error:", e)
        send_discord_notify(f"Error: {e}")
        time.sleep(60)
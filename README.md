# Crypto_Smart_Money<br />
<br />

## Objective<br />
Gets a list of top 3000 cryptocurrencies with biggest market cap. Then downloads daily OHLC historical data for all those coins. After that analyzes and compares the returns of those coins 15/30/45/60 days after volume spike. Lastly returns list of coins that are available on Binance, Huobi or Gate.io and matching certain filters.<br />
<br />

## Top_Coin_List_Scrape.py<br />
Scrapes top 3000 cryptocurrencies with biggest market cap with chromedriver and returns them as a pandas dataframe<br />
<br />

## Cryptocmd_OHLC.py<br />
Downloads daily OHLC historical data for 3000 coins.<br />
<br />

## Crypto_Smart_Money.py<br />
Analyzes returns of cryptos 15/30/45/60 days after volume spike. Also returns a list of coins that matches certain filters such as below certain market cap, volume spike magnitude etc if they are available on Binance, Huobi or Gate.io crypto exchanges.

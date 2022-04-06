###INTRODUCTION
#=================================================================================
#cryptocmd library'sini kullanarak coinmarketcap uzerinden historical OHLC 
#datasini ceker.

import os
import pandas as pd
from cryptocmd import CmcScraper
import time


SCRAPE_ALL_INSTEAD_OF_UPDATE = True   #Tum datayi mi indiricez yoksa sadece update mi
ROWS_TO_SCRAPE = 500
SCRAPE_STARTDATE = '01-06-2010'       #lib %d-%m-%Y seklinde date istiyor
SCRAPE_STOPDATE = '20-09-2021'        #Guncelleme yapacaksak bu tarihin onemi yok


#Coinmarketcap Market Datasi
#------------------------------------
market_data = pd.read_csv('MARKET_DATA_LOCATION', index_col=0)



###DOWNLOAD THE OHLC DATA
#================================================================================

#Her bir ticker'in belirlenen tarihler arasindaki OHLC datasini ceker
#---------------------------------------
if SCRAPE_ALL_INSTEAD_OF_UPDATE:
    
    
    scraper = CmcScraper('BTC', SCRAPE_STARTDATE, SCRAPE_STOPDATE)
    
    #BTC OHLC
    df_btc = scraper.get_dataframe()
    df_btc = df_btc.sort_values('Date')

    
    starttime = time.time()
    df_tickers = market_data.iloc[:ROWS_TO_SCRAPE,:]['Symbol']
    counter = 1
    not_scraped = []
    for ticker in df_tickers:
        
        try:
            scraper = CmcScraper(ticker, SCRAPE_STARTDATE, SCRAPE_STOPDATE)
            
            # get raw data as list of list
            # headers, data = scraper.get_data()
            
            #Pandas dataFrame
            df = scraper.get_dataframe()
            df = df.sort_values('Date')
            
            
            #Price in Satoshi
            df['Open'] = df['Open'] / df_btc['Open']
            df['Close'] = df['Close'] / df_btc['Close']
            df['High'] = df['High'] / df_btc['High']
            df['Low'] = df['Low'] / df_btc['Low']
            
            
            df.to_csv(f'SAVE_LOCATION/{ticker}.csv',
                      index = False)
            
            
            print(f'{counter})',ticker,df.iloc[0,1],'\n')
            counter = counter + 1
            time.sleep(0.3)
        
        except:
            print('\n',ticker,'data could not be scraped')
            not_scraped = not_scraped + [ticker]
            
    
    print(time.time() - starttime)
    print('not scraped coins:',not_scraped)




###UPDATE THE OHLC DATA
#==============================================================================
else:
    
    starttime = time.time()
    
    ##Coin listesi
    input_dir = './'
    coin_list = os.listdir(input_dir)
    
    
    print('number of coins to update:',len(coin_list))
    counter = 1
    not_updated = []

    for coin in coin_list:
        
        coin = coin.split('.')[0]
        df_to_update = pd.read_csv(input_dir + coin + '.csv')
        df_to_update['Date'] = pd.to_datetime(df_to_update['Date'])

        #En guncel datanin 5 gun oncesinden itibaren gunumuze kadar gunceller
        start = pd.to_datetime(df_to_update['Date'].max()) - pd.DateOffset(days=5)
        start = start.strftime('%d-%m-%Y')
        stop = pd.Timestamp.today()
        stop = stop.strftime('%d-%m-%Y')

        
        try:
            scraper = CmcScraper(coin, start, stop)
            
            # get raw data as list of list
            # headers, data = scraper.get_data()
            
            #Pandas dataFrame
            df_temp = scraper.get_dataframe()
            
            #Coin datasina ekle
            df_to_update = pd.concat([df_to_update,df_temp],axis = 0)
            df_to_update = df_to_update.drop_duplicates('Date', keep = 'last', ignore_index = True)
            df_to_update = df_to_update.sort_values('Date')
            
            df_to_update.to_csv(f'./{coin}.csv',
                      index = False)
            
            
            print(f'{counter})',coin,df_to_update.iloc[0,1],'\n')
            counter = counter + 1
            time.sleep(0.3)
        
        except:
            print('\n',coin,'data could not be updated')
            not_updated = not_updated + [coin]
            
    
    print(time.time() - starttime)
    print('not updated coins:',not_updated)








import winsound
winsound.Beep(frequency = 2500, duration = 1000 )



###INTRODUCTION
#===============================================================================
#Volume spike yapan coinleri bulup, 15/30/45... sonraki gunlerde artisina bakiyoruz
#15d/30d/45d_max... bu degerler volume spike sonrasi o gunun close'unun kac katina ciktigini
#veriyor.
#Market cap ile ters orantili, top_close_ratio oraniyla dogru orantili bi performans var
#Bu da daha onceden top degeri yuksek olan coinlerin daha cok yukseldigini gosteriyor
#Coinmarketcap'ten bazi coinlerin market cap'i sifir geliyor onu 1000 yaptik
#wanted bolumunde market Cap'i 3 secersen bu coinleri tariyoruz.
#3lukler genelde Market cap 5'e yani 10**5'lik coinlere denk bir performans gosteriyorlar


import os
import pandas as pd
import numpy as np
import talib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.mixture import GaussianMixture
plt.style.use('ggplot')




EMA_PERIOD = 30                 #Volume'deki ema period
MIN_VOL_EMA_RATIO = 3.0         #Volume ema'nin kac kati olanlari secicez
DAY15_MULTIPLIER = 4            #15 gunun katlari seklinde kac zamanda inceliycez
STARTDATE = '2020-08-01'        #Analiz baslangic tarihi
STOPDATE = '01-01-2099'         #Analiz bitis tarihi, min(STOPDATE,today) var kodda


##Coin listesi
input_dir = './'
coin_list = os.listdir(input_dir)



###VOLUME SPIKE DATA
#==============================================================================================
df_results = pd.DataFrame()
#STOPDATE bugunden fazla olunca 15/30/45... bugunu gecse bile sonuc veriyor, onu coz
STOPDATE = min(pd.to_datetime(STOPDATE),pd.Timestamp.today()).strftime('%Y-%m-%d')

for coin in coin_list:
    
    coin = coin.split('.')[0]
    df_ohlc= pd.read_csv(input_dir + coin + '.csv')
    
    
    ###Preprocessing ohlc data
    #--------------------------------------------------
    
    #Parametrelerde belirtilen tarih araliginda analizini yap
    df_ohlc['Date'] = pd.to_datetime(df_ohlc['Date'])
    mask = ( (df_ohlc['Date'] >= pd.to_datetime(STARTDATE)) & 
            (df_ohlc['Date'] <= pd.to_datetime(STOPDATE)))
    df_ohlc = df_ohlc[mask]
    
    #Feature Engineering
    #Market cap'i 0 olanlari 1000 yap, 10**3 oldugu icin kolayca secebiliyoruz analiz icin
    df_ohlc.loc[df_ohlc['Market Cap'] == 0,'Market Cap'] = 1000
    df_ohlc['volume_ema'] = talib.SMA(df_ohlc['Volume'], EMA_PERIOD)
    df_ohlc['vol_ema_ratio'] = df_ohlc['Volume'] / df_ohlc['volume_ema']
    df_ohlc['vol_cap_ratio'] = df_ohlc['Volume'] / df_ohlc['Market Cap']
    
    
    #Volume spike sonrasinda 15/30/45... gun icinde spike gununun close'unun kac katina cikiyor
    #veya iniyor (o zaman araligindaki max_high/close ve min_low/close)
    #--------------------------------------------------
    mask = df_ohlc['vol_ema_ratio'] >= MIN_VOL_EMA_RATIO
    high_vol_df = df_ohlc[mask].copy()
    
    
    for row in high_vol_df.index:
        
        start = high_vol_df.loc[row,'Date']
        
        #Volume spike ve oncesinde ve STARTDATE sonrasi coinin gordugu max deger/close
        high_vol_df.loc[row,'top_close_ratio'] = (df_ohlc[df_ohlc['Date'] <= start]['High'].max() /
                                       high_vol_df.loc[row,'Close'])    

        for i in range(DAY15_MULTIPLIER):
            
            #Volume spike sonrasinda 15/30/45... gun icindeki max ve min performanslar
            stop = start + pd.DateOffset(days= 15 * (i+1) )
            mask = (df_ohlc['Date'] > start) & (df_ohlc['Date'] <= stop)
            
            high_vol_df.loc[row,'{}d_max'.format(15 * (i+1))] = ( df_ohlc[mask]['High'].max() / 
                                                                 high_vol_df.loc[row,'Close'] )
                                                                      
            high_vol_df.loc[row,'{}d_min'.format(15 * (i+1))] = ( df_ohlc[mask]['Low'].min() / 
                                                                 high_vol_df.loc[row,'Close'] )
            
                        
    high_vol_df['coin'] = coin
    df_results = pd.concat([df_results,high_vol_df], axis=0)



###df_results preprocessing
#-------------------------------------------

#Market capi 0 olan data
# df_results = df_results.drop(df_results[(df_results['Market Cap'] == 0)].index, axis=0)


#coin close'u 0 olanlari at
df_results = df_results.drop(df_results[df_results['Close'] == 0].index)
df_results = df_results.reset_index(drop=True)

    

#performansa bakacagimiz aralik analiz tarihini ya da bugunu geciyorsa nan yap
for i in range(DAY15_MULTIPLIER):
    df_results['stop'] = df_results['Date'] + pd.DateOffset(days = 15* (i+1))
    df_results.loc[STOPDATE < df_results['stop'],f'{(15 * (i+1))}d_max'] = np.nan

df_results = df_results.drop('stop',axis=1)


#Volume spiketaki candle green mi red mi
df_results.loc[df_results['Open'] < df_results['Close'],'is_green'] = 1
df_results['is_green'] = df_results['is_green'].fillna(0)


#Open'dan close ve high'a yuzde degisimi
df_results = df_results.drop(df_results[(df_results['Open'] == 0)].index, axis=0)
df_results['close_pct'] = df_results['Close'] / df_results['Open'] - 1
df_results['high_pct'] = df_results['High'] / df_results['Open'] - 1
df_results['high_minus_close'] = (df_results['high_pct'] - df_results['close_pct'])







###PLOTS
#=========================================================================================

#VARIABLE vs Performans Scatterplot
#----------------------------------------------
VARIABLE = 'top_close_ratio'

fig,ax = plt.subplots(2,2)
fig.set_size_inches(18.5, 10.5)
ax = ax.ravel()

for i in range(DAY15_MULTIPLIER):
        ax[i].scatter( df_results[f'{VARIABLE}'], df_results[f'{15*(i+1)}d_max'], s = 10)
        ax[i].set_yscale('symlog')
        ax[i].set_xscale('symlog')
        ax[i].set_title(f'{15*(i+1)} Days')
        
    
fig.suptitle(f'{VARIABLE} vs Kac Katina Cikmis')
fig.text(0.5, 0.04, f'{VARIABLE} (symlog)', ha='center')
fig.text(0.04, 0.5, 'Kac Katina Cikmis (symlog)', va='center', rotation='vertical')

plt.clf





#Market Cap ve VARIABLE duzleminde Scatterplot, artis oranina gore rengi koyulasiyor
#----------------------------------------------
VARIABLE = 'top_close_ratio'

fig,ax = plt.subplots(2,2)
fig.set_size_inches(18.5, 10.5)
ax = ax.ravel()

#Colorbari her bir subplot icin standart hale getirmek icin tum artislarin min ve maxini bul
cols = df_results.columns[df_results.columns.str.contains('d_max')]
v_max = np.log(df_results[cols].max().max())
v_min = np.log(df_results[cols].min().min())

for i in range(DAY15_MULTIPLIER):
    im = ax[i].scatter( df_results['Market Cap'], df_results[f'{VARIABLE}'], 
                c= np.log(df_results[f'{15*(i+1)}d_max']),cmap = 'Reds',
                vmin = v_min, vmax = v_max, s = 10)

    ax[i].set_yscale('symlog')
    ax[i].set_xscale('symlog')
    ax[i].set_title(f'{15*(i+1)} Days')



cb = fig.colorbar(im, ax=ax.tolist())

    
fig.suptitle(f'Market Cap ve {VARIABLE} Duzleminde Artis Orani (Colorbar logscale)')
fig.text(0.5, 0.04, 'Market Cap  (symlog)', ha='center')
fig.text(0.04, 0.5, f'{VARIABLE} (symlog)', va='center', rotation='vertical')


plt.clf





#Market Cap ve VARIABLE duzleminde Scatterplot, artis oranina gore rengi koyulasiyor
#----------------------------------------------
VARIABLE = 'high_minus_close'

fig,ax = plt.subplots(2,2)
fig.set_size_inches(18.5, 10.5)
ax = ax.ravel()

#Colorbari her bir subplot icin standart hale getirmek icin tum artislarin min ve maxini bul
cols = df_results.columns[df_results.columns.str.contains('d_max')]
v_max = np.log(df_results[cols].max().max())
v_min = np.log(df_results[cols].min().min())

for i in range(DAY15_MULTIPLIER):
    im = ax[i].scatter( df_results['Market Cap'], df_results[f'{VARIABLE}'], 
                c= np.log(df_results[f'{15*(i+1)}d_max']),cmap = 'Reds',
                vmin = v_min, vmax = v_max, s = 5)

    ax[i].set_yscale('symlog')
    ax[i].set_xscale('symlog')
    ax[i].set_title(f'{15*(i+1)} Days')



cb = fig.colorbar(im, ax=ax.tolist())

    
fig.suptitle(f'Market Cap ve {VARIABLE} Duzleminde Artis Orani (Colorbar logscale)')
fig.text(0.5, 0.04, 'Market Cap (symlog)', ha='center')
fig.text(0.04, 0.5, f'{VARIABLE} (symlog)', va='center', rotation='vertical')


plt.show()










###CORRELATION HEATMAP
#=======================================================================================================
#input_cols
exclude = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'volume_ema','coin']
exclude = exclude + df_results.columns[df_results.columns.str.contains('d_min')].to_list()
cols = [i for i in df_results.columns.to_list() if i not in exclude]
corr_table = df_results[cols].copy()


#performansi gosteren max kolonlarini one getir
cols = corr_table.columns
cols = (cols[cols.str.contains('d_max')].to_list() + 
        [i for i in cols if i not in cols[cols.str.contains('max')]])
corr_table = corr_table[cols]

#symmetrical log
corr_table[corr_table >= 0] = np.log1p(corr_table[corr_table >= 0])
corr_table[corr_table < 0] = -np.log1p(corr_table[corr_table < 0] * -1.0)


corr_table = corr_table.corr()
sns.heatmap(corr_table, annot=True, cmap = 'RdBu')









###SOFT CLUSTERING
#=========================================================================================

CLUSTER_NUMBER = 10

#input_cols
exclude = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'volume_ema','coin']
exclude = (exclude + df_results.columns[df_results.columns.str.contains('d_min')].to_list() +
            df_results.columns[df_results.columns.str.contains('d_max')].to_list())
cols = [i for i in df_results.columns.to_list() if i not in exclude]

#ya da kendimizin sectigi input kolonlari
cols = ['Market Cap', 'top_close_ratio', 'high_minus_close']

gm = df_results[cols].copy()
#symmetrical log
gm[gm >= 0] = np.log1p(gm[gm >= 0])
gm[gm < 0] = -np.log1p(gm[gm < 0] * -1.0)

gm['cluster'] = GaussianMixture(n_components=CLUSTER_NUMBER, random_state=7).fit_predict(gm)



#Plot
#-------------------------------------------
VARIABLE = 'top_close_ratio'


fig, ax = plt.subplots()
fig.set_size_inches(18.5, 10.5)

colors = ['#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4',
          '#42d4f4', '#f032e6', '#bfef45', '#fabed4', '#469990', '#dcbeff',
          '#9A6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1',
          '#000075', '#a9a9a9', '#ffffff', '#000000']
for i, cluster in gm.groupby('cluster'):
    _ = ax.scatter(cluster['Market Cap'], cluster[f'{VARIABLE}'], color=colors[i])
ax.legend()


    
fig.suptitle(f'Market Cap ve {VARIABLE} Duzleminde {CLUSTER_NUMBER} Cluster')
fig.text(0.5, 0.04, 'Market Cap (symlog)', ha='center')
fig.text(0.04, 0.5, f'{VARIABLE} (symlog)', va='center', rotation='vertical')

plt.clf











###GROUPBY ANALYSIS
#=========================================================================================


###Volume Spike sonrasi o gunun close'unun ortalama kac katina cikiyor
#-----------------------------------------------
df_analysis = df_results.copy()
# df_analysis = df_analysis[df_analysis['vol_ema_ratio'] >= 5]
#Groupby yapabilmek icin np.floor ile categorize ediyoruz, exponential olanlari log10 aliyoruz
df_analysis['market_cap_log'] = np.floor( np.log10(df_analysis['Market Cap']) )
df_analysis['vol_ema_ratio'] = np.floor( df_analysis['vol_ema_ratio'] / 3 )
df_analysis['high_minus_close'] = np.floor( df_analysis['high_minus_close'] * 10 )
df_analysis['top_close_ratio'] = np.floor( df_analysis['top_close_ratio'] / 10 )


#groupby'a 'is_green' kolonu da eklenebilir analiz icin
mean_by_cap = df_analysis.groupby(['market_cap_log']).agg({
    '15d_max' : 'mean',
    '30d_max' : 'mean',
    '45d_max' : 'mean',
    '60d_max' : 'mean',
    'Date'    : 'count',
    })

median_by_cap = df_analysis.groupby(['market_cap_log']).agg({
    '15d_max' : 'median',
    '30d_max' : 'median',
    '45d_max' : 'median',
    '60d_max' : 'median',
    'Date'    : 'count',
    })

mean1 = df_analysis.groupby(['market_cap_log', 'top_close_ratio']).agg({
    '15d_max' : 'mean',
    '30d_max' : 'mean',
    '45d_max' : 'mean',
    '60d_max' : 'mean',
    'Date'    : 'count',
    })

median1 = df_analysis.groupby(['market_cap_log', 'top_close_ratio']).agg({
    '15d_max' : 'median',
    '30d_max' : 'median',
    '45d_max' : 'median',
    '60d_max' : 'median',
    'Date'    : 'count',
    })


mean_by_cap.columns = mean_by_cap.columns[:-1].to_list() + ['count']
median_by_cap.columns = median_by_cap.columns[:-1].to_list() + ['count']
mean1.columns = mean1.columns[:-1].to_list() + ['count']
median1.columns = median1.columns[:-1].to_list() + ['count']
mean1 = mean1[mean1['count'] >= 20]
median1 = median1[median1['count'] >= 20]





###Volume spike olduktan sonra, volume spike oncesi top value'nun yuzde kacina veya 
###kac katina cikiyor.
###Burada percentile hesabi da yapilabilir, yuzde kaci top'un %50sine ulasiyor gibi
#--------------------------------------------------------

df_analysis2 = df_results.copy()

#Volume spike oncesi top degerin nominal degeri (her coin icin farkli degerler geliyor tabii)
df_analysis2['top'] = df_analysis2['top_close_ratio'] * df_analysis2['Close']

#15/30/45d_max... kolonlari, volume spike sonrasi zaman araligi icinde max_high/close oranini
#close ile carparak max_high'in nominal degerini buluyoruz (her coin icin farkli oluyor tabii)
#Daha sonra bu nominal max_high degerini volume spike oncesi top degerine bolerek
#Volume spike sonrasi onceki top degerinin yuzde kacina veya kac katina ciktigini buluyoruz
cols = df_analysis2.columns[df_analysis2.columns.str.contains('d_max')]
for col in cols:
    #Nominal olarak 15/30/45... gun icinde max hangi degeri goruyor
    df_analysis2[col] = df_analysis2[col] * df_analysis2['Close'] 
    df_analysis2[col] = df_analysis2[col] / df_analysis2['top'] 
    


    
#Groupby yapabilmek icin np.floor ile categorize ediyoruz, exponential olanlari log10 aliyoruz
df_analysis2['market_cap_log'] = np.floor( np.log10(df_analysis2['Market Cap']) )
df_analysis2['vol_ema_ratio'] = np.floor( df_analysis2['vol_ema_ratio'] / 3 )
df_analysis2['high_minus_close'] = np.floor( df_analysis2['high_minus_close'] )
df_analysis2['top_close_ratio'] = np.floor( df_analysis2['top_close_ratio'] / 10 )



#groupby'a 'is_green' kolonu da eklenebilir analiz icin
mean_2= df_analysis2.groupby(['market_cap_log', 'top_close_ratio']).agg({
    '15d_max' : 'mean',
    '30d_max' : 'mean',
    '45d_max' : 'mean',
    '60d_max' : 'mean',
    'Date'    : 'count',
    })

median_2= df_analysis2.groupby(['market_cap_log', 'top_close_ratio']).agg({
    '15d_max' : 'median',
    '30d_max' : 'median',
    '45d_max' : 'median',
    '60d_max' : 'median',
    'Date'    : 'count',
    })

mean_2.columns = mean_2.columns[:-1].to_list() + ['count']
median_2.columns = median_2.columns[:-1].to_list() + ['count']
mean_2 = mean_2[mean_2['count'] >= 20]
median_2 = median_2[median_2['count'] >= 20]





###WANTED COINS AND EXCHANGE AVAILABILITY
#==================================================================================


#Input Exchanges
#-----------------------------------------
binance = pd.read_html('./Binance.html')[2]
huobi = pd.read_html('./Huobi.html')[2]
gate = pd.read_html('./Gate-io.html')[2]


#Preprocessing
#--------------------------------------------
binance['exc'] = 'binance'
huobi['exc'] = 'huobi'
gate['exc'] = 'gate'
exchanges = pd.concat([binance,huobi,gate],axis = 0)
exchanges = exchanges.reset_index(drop=True)
exchanges['coin'] = exchanges['Pair'].apply(lambda x: x.split('/')[0])



#Belirli tarihler arasinda market cap'in log10 degerine gore coinleri seciyoruz
temp_wanted = df_results.copy()
temp_wanted = temp_wanted[temp_wanted['Date'] >= pd.to_datetime('2021-06-20')]

temp_wanted['market_cap_log'] = np.floor(np.log10(temp_wanted['Market Cap']))

wanted = pd.DataFrame()
for i in np.arange(3,7):

    wanted = pd.concat([wanted, temp_wanted[temp_wanted['market_cap_log'] == i] ], axis = 0)

wanted = wanted[['Date','coin', 'top_close_ratio', 'Market Cap', 'market_cap_log']]
wanted = wanted.groupby('coin').last()
wanted = wanted.sort_values(['market_cap_log','top_close_ratio'],ascending = [True,False])



#Find which exchanges list the coin
#--------------------------------------------
for ticker in wanted.index:
    
    if len(exchanges[exchanges['coin'] == ticker]) != 0:
        wanted.loc[ticker,'exchange'] = str(exchanges[exchanges['coin'] == ticker]['exc'].unique())

wanted = wanted.dropna(subset = ['exchange'])

#print head of wanted coins
print(wanted)

try:
    import winsound
    winsound.Beep(frequency = 2500, duration = 1000 )
except:
    0


del(ax, binance, cb, cluster, coin, col, colors, cols, df_ohlc, exclude, fig,
    gate, gm, high_vol_df, huobi, i ,im, input_dir, mask, row, start, stop, temp_wanted,
    ticker, v_max, v_min)


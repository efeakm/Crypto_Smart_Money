###INTRODUCTION
#================================================================================
#Coinmarketcap.com'dan istenilen row sayisina kadar, scroll down yaparak 
#coin market tablosunu dataframe'e donusturur ve csv olarak kaydeder.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time


ROW_LIMIT = 3000
SAVE_OUTPUT = True





###WEBDRIVER INITIALIZATION
#=================================================================================
path = 'CHROMEDRIVER-PATH'
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
# options.add_argument('--headless')
driver = webdriver.Chrome(path, chrome_options=options)

driver.get('https://coinmarketcap.com/all/views/all/')






###SCROLL DOWN AND LOAD DATA
#==================================================================================

# last_height = driver.execute_script("return document.body.scrollHeight")
start = time.time()
scroll_location = 0
last_row = -1
#ROW_LIMIT'e ulasana kadar scroll down yapar
while int(last_row) <= ROW_LIMIT:
    #400 birim asagi yaklasik 11 row'a denk geliyor
    scroll_location = scroll_location + 400
    driver.execute_script(f"window.scrollTo(0, {scroll_location});")
    
    time.sleep(0.1)
    soup = BeautifulSoup(driver.page_source, features = 'lxml')
    rows = soup.find_all(class_ = "cmc-table__cell cmc-table__cell--sticky cmc-table__cell--sortable cmc-table__cell--left cmc-table__cell--sort-by__rank")
    
    #son row degismediyse Load More butonuna tikla
    if rows[-1].div.text == last_row:
        
        if int(rows[-1].div.text) >= ROW_LIMIT:
            break
        
        print('loading more')
        driver.find_element_by_class_name('cmc-table-listing__loadmore').click()
        time.sleep(2.5)

    
    last_row = rows[-1].div.text
    
    
    print(last_row)
    


dfs = pd.read_html(driver.page_source)
driver.quit()
print('time elapsed for scrape:',time.time()-start)



###OUTPUT
#================================================================================
output = dfs[2].iloc[:,:10].copy()
if SAVE_OUTPUT:
    output.to_csv('SAVE_LOCATION', index = False)
    print('saved to Outputs/coinmarketcap_market_data.csv')
    
try:
    import winsound
    winsound.Beep(frequency = 2500, duration = 1000 )
except:
    0




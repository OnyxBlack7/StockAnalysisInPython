import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
from matplotlib import pyplot as plt
import mplfinance as mpf

# 4.4.3 맨 뒤 페이지 숫자 구하기
url = f"http://finance.naver.com/item/sise_day.nhn?code=068270&page=1"
with urlopen(url) as doc:
    html = BeautifulSoup(requests.get(url,
        headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/83.0.4103.106 Whale/2.8.108.15 Safari/537.36"}).text, "lxml")
    pgrr = html.find("td", class_="pgRR")
    s = str(pgrr.a['href']).split('=')
    last_page = s[-1]

# 4.4.4 전체 페이지 읽어오기
df = pd.DataFrame()
sise_url = 'https://finance.naver.com/item/sise_day.nhn?code=068270'
for page in range(1, int(last_page)+1):
    page_url = '{}&page={}'.format(sise_url, page)
    df = df.append(pd.read_html(requests.get(page_url,
        headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/83.0.4103.106 Whale/2.8.108.15 Safari/537.36"}).text)[0])

# 차트 출력을 위해 데이터프레임 가공하기
# df = df.dropna()
# df = df.iloc[0:30]
# df = df.sort_values(by='날짜')

# 날짜, 종가 칼럼으로 차트 그리기
# plt.title('Celltrion (close)')
# plt.xticks(rotation=45)
# plt.plot(df['날짜'], df['종가'], 'co-')
# plt.grid(color='gray', linestyle='--')
# plt.show()

# 차트 출력을 위해 데이터프레임 가공하기
df = df.dropna()
df = df.iloc[0:30]
df = df.rename(columns={'날짜': 'Date', '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close', '거래량': 'Volume'})
df = df.sort_values(by='Date')
df.index = pd.to_datetime(df.Date)
df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

# 엠피엘파이낸스로 캔들 차트 그리기
# mpf.plot(df, title='Celltrion candle chart', type='candle')
# mpf.plot(df, title='Celltrion ohlc chart', type='ohlc')
kwargs = dict(title='Celltrion customized chart', type='candle', mav=(2, 4, 6), volume=True, ylabel='ohlc candles')
# kwargs: keyword arguments의 약자, mpf.plot() 함수를 호출할 때 쓰이는 여러 인수를 담는 딕셔너리

mc = mpf.make_marketcolors(up='r', down='b', inherit=True)
# 마켓 색상은 스타일을 지정하는 필수 객체로서, 상승은 빨간색(red)으로 하락은 파란색(blue)으로 지정.

s = mpf.make_mpf_style(marketcolors=mc)
# 마켓 색상을 인수로 넘겨줘서 스타일 객체를 생성한다.

mpf.plot(df, **kwargs, style=s)

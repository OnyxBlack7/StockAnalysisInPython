
import pandas as pd
from bs4 import BeautifulSoup
import pymysql, calendar, time, json
import requests
from datetime import datetime
from threading import Timer

class DBUpdater:  
    def __init__(self):
        """생성자: MariaDB 연결 및 종목코드 딕셔너리 생성"""
        self.conn = pymysql.connect(host='localhost', user='root', password='myPa$$word', db='INVESTAR', charset='utf8')
        # 한글 회사명 사용하기 때문에 인코딩 오류 발생할 수 있다. 따라서 utf8로 인코딩 형식 미리 지정

        with self.conn.cursor() as curs:
            sql = """
            CREATE TABLE IF NOT EXISTS company_info (
                code VARCHAR(20),
                company VARCHAR(40),
                last_update DATE,
                PRIMARY KEY (code))
            """
            curs.execute(sql)
            sql = """
            CREATE TABLE IF NOT EXISTS daily_price (
                code VARCHAR(20),
                date DATE,
                open BIGINT(20),
                high BIGINT(20),
                low BIGINT(20),
                close BIGINT(20),
                diff BIGINT(20),
                volume BIGINT(20),
                PRIMARY KEY (code, date))
            """
            curs.execute(sql)
        self.conn.commit()
        self.codes = dict()
               
    def __del__(self):
        """소멸자: MariaDB 연결 해제"""
        self.conn.close() 
     
    def read_krx_code(self):
        """KRX로부터 상장기업 목록 파일을 읽어와서 데이터프레임으로 반환"""
        url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method='\
            'download&searchType=13'
        krx = pd.read_html(url, header=0)[0]    # 상장법인목록.xls 파일을 read_html()함수로 읽는다.
        krx = krx[['종목코드', '회사명']]          # 종목코드와 회사명 칼럼만 남긴다.
        krx = krx.rename(columns={'종목코드': 'code', '회사명': 'company'})    # 한글 칼럼명을 영문으로 변경
        krx.code = krx.code.map('{:06d}'.format)         # 0이 붙여 6자리로 만든다.
        return krx
    
    def update_comp_info(self):
        """종목코드를 company_info 테이블에 업데이트 한 후 딕셔너리에 저장"""
        sql = "SELECT * FROM company_info"
        df = pd.read_sql(sql, self.conn)    # company_info 테이블을 read_sql() 함수로 읽는다.
        for idx in range(len(df)):
            self.codes[df['code'].values[idx]] = df['company'].values[idx]
            # 위에서 읽은 데이터프레임을 이용해서 종목코드와 회사명으로 codes 딕셔너리를 만든다.

        with self.conn.cursor() as curs:
            sql = "SELECT max(last_update) FROM company_info"
            curs.execute(sql)
            rs = curs.fetchone()    # SELECT max() ~ 구문을 이용해서 DB에서 가장 최근 업데이트 날짜를 가져온다
            today = datetime.today().strftime('%Y-%m-%d')
            if rs[0] == None or rs[0].strftime('%Y-%m-%d') < today:
                krx = self.read_krx_code()
                # 위에서 구한 날짜가 존재하지 않거나 오늘보다 오래된 경우 KRX 상장기업 목록 파일을 읽어서 krx 데이터프레임에 저장한다.

                for idx in range(len(krx)):
                    code = krx.code.values[idx]
                    company = krx.company.values[idx]                
                    sql = f"REPLACE INTO company_info (code, company, last"\
                        f"_update) VALUES ('{code}', '{company}', '{today}')"
                    curs.execute(sql)   # REPLACE INTO 구문을 이용해서 '종목코드, 회사명, 오늘날짜' 행을 DB에 저장한다.
                    self.codes[code] = company  # codes 딕셔너리에 키-값으로 종목코드와 회사명을 추가한다.
                    tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                    print(f"[{tmnow}] #{idx+1:04d} REPLACE INTO company_info "\
                        f"VALUES ({code}, {company}, {today})")
                self.conn.commit()
                print('')              

    def read_naver(self, code, company, pages_to_fetch):
        """네이버에서 주식 시세를 읽어서 데이터프레임으로 반환"""
        try:
            url = f"http://finance.naver.com/item/sise_day.nhn?code={code}"
            html = BeautifulSoup(requests.get(url,
                headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/83.0.4103.106 Whale/2.8.108.15 Safari/537.36"}).text, "lxml")
            pgrr = html.find("td", class_="pgRR")
            if pgrr is None:
                return None
            s = str(pgrr.a["href"]).split('=')
            lastpage = s[-1] # 마지막 페이지
            df = pd.DataFrame()
            pages = min(int(lastpage), pages_to_fetch)
            for page in range(1, pages + 1):
                pg_url = '{}&page={}'.format(url, page)
                df = df.append(pd.read_html(requests.get(pg_url,    # read_html로 읽어 데이터프레임에 추가
                    headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/83.0.4103.106 Whale/2.8.108.15 Safari/537.36"}).text)[0])
                tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                print('[{}] {} ({}) : {:04d}/{:04d} pages are downloading...'.
                    format(tmnow, company, code, page, pages), end="\r")
            df = df.rename(columns={'날짜':'date','종가':'close','전일비':'diff'
                ,'시가':'open','고가':'high','저가':'low','거래량':'volume'})    # 한글 칼럼명을 영문으로 변경
            df['date'] = df['date'].replace('.', '-')
            df = df.dropna()
            # 마리아디비에서 BIGINT형으로 지정한 칼럼들의 데이터형을 int형으로 변경
            df[['close', 'diff', 'open', 'high', 'low', 'volume']] = df[['close',
                'diff', 'open', 'high', 'low', 'volume']].astype(int)
            # 칼럼 순서 변경
            df = df[['date', 'open', 'high', 'low', 'close', 'diff', 'volume']]
        except Exception as e:
            print('Exception occured :', str(e))
            return None
        return df

    def replace_into_db(self, df, num, code, company):
        """네이버에서 읽어온 주식 시세를 DB에 REPLACE"""
        with self.conn.cursor() as curs:
            for r in df.itertuples():   # 데이터프레임을 튜플로 순회처리
                # REPLACE INTO 구문으로 daily_price 테이블을 업데이트
                sql = f"REPLACE INTO daily_price VALUES ('{code}', "\
                    f"'{r.date}', {r.open}, {r.high}, {r.low}, {r.close}, "\
                    f"{r.diff}, {r.volume})"
                curs.execute(sql)
            self.conn.commit()
            print('[{}] #{:04d} {} ({}) : {} rows > REPLACE INTO daily_'\
                'price [OK]'.format(datetime.now().strftime('%Y-%m-%d'\
                ' %H:%M'), num+1, company, code, len(df)))

    def update_daily_price(self, pages_to_fetch):
        """KRX 상장법인의 주식 시세를 네이버로부터 읽어서 DB에 업데이트"""  
        for idx, code in enumerate(self.codes):
            # read_naver() 메서드를 이용하여 종목코드에 대한 일별 시세 데이터프레임을 구함
            df = self.read_naver(code, self.codes[code], pages_to_fetch)
            if df is None:
                continue
            # 일별 시세 데이터프레임이 구해지면 replace_into_db() 메서드로 DB에 저장
            self.replace_into_db(df, idx, code, self.codes[code])            

    def execute_daily(self):
        """실행 즉시 및 매일 오후 다섯시에 daily_price 테이블 업데이트"""
        self.update_comp_info()
        
        try:
            with open('config.json', 'r') as in_file:
                config = json.load(in_file)
                pages_to_fetch = config['pages_to_fetch']
        except FileNotFoundError:
            with open('config.json', 'w') as out_file:
                pages_to_fetch = 100 
                config = {'pages_to_fetch': 1}
                json.dump(config, out_file)
        self.update_daily_price(pages_to_fetch)

        tmnow = datetime.now()
        lastday = calendar.monthrange(tmnow.year, tmnow.month)[1]
        if tmnow.month == 12 and tmnow.day == lastday:
            tmnext = tmnow.replace(year=tmnow.year+1, month=1, day=1,
                hour=17, minute=0, second=0)
        elif tmnow.day == lastday:
            tmnext = tmnow.replace(month=tmnow.month+1, day=1, hour=17,
                minute=0, second=0)
        else:
            tmnext = tmnow.replace(day=tmnow.day+1, hour=17, minute=0,
                second=0)   
        tmdiff = tmnext - tmnow
        secs = tmdiff.seconds
        t = Timer(secs, self.execute_daily)
        print("Waiting for next update ({}) ... ".format(tmnext.strftime
            ('%Y-%m-%d %H:%M')))
        t.start()

if __name__ == '__main__':
    # DBUpdaterEx.py가 단독으로 실행되면 DBUpdater 객체를 생성한다.
    # DBUpdater 생성자 내부에서 마리아디비에 연결한다.
    # company_info 테이블에 오늘 업데이트된 내용이 있는지 확인하고, 없으면 업데이트

    dbu = DBUpdater()
    dbu.execute_daily()

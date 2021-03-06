from datetime import datetime
import backtrader as bt

class MyStrategy(bt.Strategy):  # bt.Strategy 클래스를 상속받아서 MyStrategy 클래스를 작성
    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close)  # MyStrategy 클래스 생성자에서 RSI 지표로 사용할 변수를 지정
    def next(self):  # 주어진 데이터와 지표를 만족시키는 최소 주기마다 자동으로 호출.
        if not self.position:
            if self.rsi < 30:
                self.order = self.buy()
        else:
            if self.rsi > 70:
                self.order = self.sell()

cerebro = bt.Cerebro()  # 데이터를 취합하고 백테스트 또는 라이브 트레이딩을 실행한 뒤 그 결과를 출력하는 클래스
cerebro.addstrategy(MyStrategy)
data = bt.feeds.YahooFinanceData(dataname='036570.KS',  # ⑤
    fromdate=datetime(2017, 1, 1), todate=datetime(2021, 3, 1))
cerebro.adddata(data)
cerebro.broker.setcash(10000000)  # ⑥
cerebro.addsizer(bt.sizers.SizerFix, stake=30)  # 매매 단위 30주. 보유 현금에 비해 총 매수금액 크면 매수 안함

print(f'Initial Portfolio Value : {cerebro.broker.getvalue():,.0f} KRW')
cerebro.run()  # ⑧
print(f'Final Portfolio Value   : {cerebro.broker.getvalue():,.0f} KRW')
cerebro.plot()  # ⑨
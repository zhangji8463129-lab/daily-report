import os
import datetime
import feedparser
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback

# ================== 配置 ==================
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
XAI_API_KEY = os.getenv('XAI_API_KEY')  # 可选，后面再加

# 重点关注资产
MAJOR_STOCKS = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'GOOGL', 'META', 'AMD']
GLOBAL_TICKERS = ['^IXIC', '^GSPC', '^VIX', 'NQ=F', 'ES=F', 'DX=F']

def safe_get_data():
    data = {}
    try:
        # 指数和期货
        tickers = yf.download(GLOBAL_TICKERS, period='1d', interval='1m', progress=False, timeout=15)
        if not tickers.empty:
            latest = tickers['Close'].iloc[-1]
            data.update({
                '纳指': f"{latest.get('^IXIC', 'N/A'):.2f}",
                '标普500': f"{latest.get('^GSPC', 'N/A'):.2f}",
                'VIX': f"{latest.get('^VIX', 'N/A'):.2f}",
                '纳指期货': f"{latest.get('NQ=F', 'N/A'):.2f}",
                '标普期货': f"{latest.get('ES=F', 'N/A'):.2f}",
                '美元指数': f"{latest.get('DX=F', 'N/A'):.2f}",
            })
    except Exception as e:
        print(f"市场数据获取异常: {e}")
        data['市场数据'] = "获取失败（可能休市）"

    # 主要股票
    try:
        stocks_data = yf.download(MAJOR_STOCKS, period='1d', interval='1m', progress=False, timeout=15)
        if not stocks_data.empty:
            data['主要股票'] = {s: f"{stocks_data['Close'][s].iloc[-1]:.2f}" for s in MAJOR_STOCKS}
    except:
        data['主要股票'] = "股票数据获取失败"

    return data

def get_news():
    news = []
    rss_list = [
        'https://feeds.reuters.com/reuters/businessNews',
        'https://feeds.reuters.com/reuters/marketsNews'
    ]
    for url in rss_list:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:6]:
                news.append(entry.title)
        except:
            pass
    return news[:8] or ["暂无最新Reuters新闻"]

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_USER
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_USER, msg.as_string())
        server.quit()
        print("✅ 邮件发送成功")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        traceback.print_exc()
        return False

def main():
    print(f"🚀 开始执行 - {datetime.datetime.now()}")
    
    market = safe_get_data()
    news = get_news()
    
    report = f"""
📊 每日美股盘前AI报告 - {datetime.date.today()}

=== 市场快照 ===
纳指: {market.get('纳指', 'N/A')}
标普500: {market.get('标普500', 'N/A')}
VIX: {market.get('VIX', 'N/A')}
纳指期货: {market.get('纳指期货', 'N/A')}
标普期货: {market.get('标普期货', 'N/A')}
美元指数: {market.get('美元指数', 'N/A')}

=== 主要股票价格 ===
{market.get('主要股票', '暂无数据')}

=== 最新Reuters新闻 ===
{chr(10).join(['• ' + n for n in news])}

=== 当前判断 ===
数据已收集，Grok AI 分析模块待开启。
观察期货与VIX决定仓位。
"""
    
    subject = f"📈 每日美股盘前报告 - {datetime.date.today()}"
    send_email(subject, report)
    print("✅ 工作流执行完成")

if __name__ == "__main__":
    main()

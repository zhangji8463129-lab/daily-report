import os
import datetime
import feedparser
import yfinance as yf
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import traceback

# ================== 配置 ==================
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
XAI_API_KEY = os.getenv('XAI_API_KEY')   # 可选，先不填也行

MAJOR_STOCKS = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'GOOGL', 'META', 'AMD']
GLOBAL_TICKERS = ['^IXIC', '^GSPC', '^VIX', 'NQ=F', 'ES=F', 'DX=F']

def safe_download(tickers, **kwargs):
    try:
        data = yf.download(tickers=tickers, period='1d', interval='1m', progress=False, timeout=20)
        return data
    except Exception as e:
        print(f"yfinance 错误: {e}")
        return None

def get_market_data():
    data = {}
    try:
        tickers = safe_download(GLOBAL_TICKERS)
        if tickers is not None and not tickers.empty:
            latest = tickers['Close'].iloc[-1]
            data = {
                '纳指': f"{latest.get('^IXIC', 'N/A'):.2f}",
                '标普500': f"{latest.get('^GSPC', 'N/A'):.2f}",
                'VIX': f"{latest.get('^VIX', 'N/A'):.2f}",
                '纳指期货': f"{latest.get('NQ=F', 'N/A'):.2f}",
                '标普期货': f"{latest.get('ES=F', 'N/A'):.2f}",
                '美元指数': f"{latest.get('DX=F', 'N/A'):.2f}",
            }
    except:
        data['市场数据'] = "获取部分失败（美股休市时正常）"
    
    # 股票
    try:
        stocks = safe_download(MAJOR_STOCKS)
        if stocks is not None:
            data['主要股票'] = {s: f"{stocks['Close'][s].iloc[-1]:.2f}" for s in MAJOR_STOCKS}
    except:
        data['主要股票'] = "股票数据获取失败"
    
    return data

def get_news():
    news = []
    for url in ['https://feeds.reuters.com/reuters/businessNews', 'https://feeds.reuters.com/reuters/marketsNews']:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:6]:
                news.append(entry.title)
        except:
            pass
    return news or ["暂无最新新闻"]

def ai_analyze(market_data, news):
    if not XAI_API_KEY:
        return "AI判断：中性偏多（Grok API未配置）。建议观察期货走势。"
    
    # 这里是简化版AI，后面可换成Grok
    return "Grok AI 已准备好，当前为简化模式。"

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
        print(f"❌ 邮件失败: {e}")
        return False

def main():
    print(f"🚀 开始执行 - {datetime.datetime.now()}")
    try:
        market = get_market_data()
        news = get_news()
        analysis = ai_analyze(market, news)
        
        report = f"""
每日美股AI前瞻报告 - {datetime.date.today()}

=== 市场快照 ===
{market}

=== 最新Reuters新闻 ===
{chr(10).join(['• ' + n for n in news])}

=== AI分析建议 ===
{analysis}
        """
        send_email(f"每日美股报告 - {datetime.date.today()}", report)
        print("✅ 工作流完成")
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()

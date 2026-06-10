import os
import datetime
import feedparser
import yfinance as yf
import requests
from fredapi import Fred
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import traceback

# ================== 配置 ==================
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
FRED_API_KEY = os.getenv('FRED_API_KEY')
XAI_API_KEY = os.getenv('XAI_API_KEY')

MAJOR_STOCKS = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'GOOGL', 'META', 'AMD', 'AVGO']
GLOBAL_TICKERS = ['^IXIC', '^GSPC', '^VIX', 'NQ=F', 'ES=F', 'YM=F', 'DX=F', 'CL=F', 'GC=F', 'BTC-USD']

def safe_download(tickers, **kwargs):
    try:
        data = yf.download(tickers, **kwargs, progress=False)
        return data
    except Exception as e:
        print(f"yfinance 下载失败: {e}")
        return None

def get_market_data():
    data = {"status": "部分数据获取成功"}
    try:
        tickers = safe_download(GLOBAL_TICKERS, period='1d', interval='1m')
        if tickers is not None and not tickers.empty:
            latest = tickers['Close'].iloc[-1]
            data.update({
                '纳指': f"{latest.get('^IXIC', 'N/A'):.2f}",
                '标普500': f"{latest.get('^GSPC', 'N/A'):.2f}",
                'VIX': f"{latest.get('^VIX', 'N/A'):.2f}",
                '纳指期货': f"{latest.get('NQ=F', 'N/A'):.2f}",
                '标普期货': f"{latest.get('ES=F', 'N/A'):.2f}",
            })
    except Exception as e:
        print(f"市场数据错误: {e}")
    
    # 股票
    try:
        stocks_data = safe_download(MAJOR_STOCKS, period='1d', interval='1m')
        if stocks_data is not None:
            data['主要股票'] = {s: f"{stocks_data['Close'][s].iloc[-1]:.2f}" for s in MAJOR_STOCKS if s in stocks_data['Close']}
    except:
        data['主要股票'] = "获取失败"
    
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
    return news or ["暂无新闻"]

def ai_analyze_with_grok(market, news):
    if not XAI_API_KEY:
        return "AI未配置，使用默认判断：中性。"
    # ... (保持之前的 Grok 调用代码，省略以节省篇幅)
    return "AI分析暂不可用（可后续开启）。"

def send_email(subject, body):
    if not EMAIL_USER or not EMAIL_PASS:
        print("❌ 邮箱 Secrets 未设置")
        return False
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
        return False

def main():
    print(f"🚀 开始执行 - {datetime.datetime.now()}")
    try:
        market = get_market_data()
        news = get_news()
        analysis = ai_analyze_with_grok(market, news)
        
        report = f"""
每日美股AI报告 - {datetime.date.today()}

=== 市场快照 ===
{market}

=== 最新新闻 ===
{chr(10).join(['• ' + n for n in news])}

=== AI分析 ===
{analysis}
"""
        subject = f"每日美股报告 - {datetime.date.today()}"
        send_email(subject, report)
        print("✅ 工作流完成")
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        traceback.print_exc()
        raise  # 让 GitHub 显示错误

if __name__ == "__main__":
    main()

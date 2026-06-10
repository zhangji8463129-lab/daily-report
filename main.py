import os
import datetime
import feedparser
import yfinance as yf
import requests
from fredapi import Fred
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# ================== 配置 ==================
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
FRED_API_KEY = os.getenv('FRED_API_KEY')
XAI_API_KEY = os.getenv('XAI_API_KEY')

# ================== 重点关注资产 ===================
MAJOR_STOCKS = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'GOOGL', 'META', 'AMD', 'AVGO', 'NFLX', 'LLY', 'JPM', 'V', 'MA', 'COST']

# 新增全球/商品指标
GLOBAL_TICKERS = ['^IXIC', '^GSPC', '^VIX', 'NQ=F', 'ES=F', 'YM=F', 'DX=F', 'CL=F', 'GC=F', 'BTC-USD', '^N225', '^HSI', '^GDAXI']

RSS_FEEDS = [
    'https://feeds.reuters.com/reuters/businessNews',
    'https://feeds.reuters.com/reuters/marketsNews',
]

def get_market_data():
    data = {}
    try:
        tickers = yf.download(tickers=GLOBAL_TICKERS, period='1d', interval='1m', progress=False)
        latest = tickers['Close'].iloc[-1] if not tickers.empty else {}
        
        data.update({
            '纳指': f"{latest.get('^IXIC', 'N/A'):.2f}",
            '标普500': f"{latest.get('^GSPC', 'N/A'):.2f}",
            'VIX': f"{latest.get('^VIX', 'N/A'):.2f}",
            '纳指期货': f"{latest.get('NQ=F', 'N/A'):.2f}",
            '标普期货': f"{latest.get('ES=F', 'N/A'):.2f}",
            '道指期货': f"{latest.get('YM=F', 'N/A'):.2f}",
            '美元指数': f"{latest.get('DX=F', 'N/A'):.2f}",
            '原油(WTI)': f"{latest.get('CL=F', 'N/A'):.2f}",
            '黄金': f"{latest.get('GC=F', 'N/A'):.2f}",
            '比特币': f"{latest.get('BTC-USD', 'N/A'):.0f}",
        })
    except:
        data['市场数据'] = "部分获取失败"

    # 主要股票
    try:
        stocks_data = yf.download(MAJOR_STOCKS, period='1d', interval='1m', progress=False)
        data['主要股票'] = {stock: f"{stocks_data['Close'][stock].iloc[-1]:.2f}" for stock in MAJOR_STOCKS}
    except:
        data['主要股票'] = "获取失败"
    
    return data

def get_macro_data():
    if not FRED_API_KEY:
        return {"status": "未设置FRED Key"}
    try:
        fred = Fred(api_key=FRED_API_KEY)
        return {
            "联邦基金利率": fred.get_series_latest_release('FEDFUNDS'),
            "CPI": fred.get_series_latest_release('CPIAUCSL'),
        }
    except:
        return {"status": "宏观数据获取失败"}

def get_news():
    news = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                news.append(entry.title)
        except:
            pass
    return news or ["暂无最新新闻"]

def ai_analyze_with_grok(market_data, macro, news):
    if not XAI_API_KEY:
        return "Grok API 未配置"
    
    prompt = f"""
当前日期：{datetime.date.today()}
市场快照：
{market_data}

宏观数据：{macro}
最新Reuters新闻：{news}

作为专业美股基金经理，请综合以上**全部信息**分析：
1. 对今日美股及纳指的整体利多/利空判断
2. 关键驱动因素（期货、美元、商品、全球市场、新闻等）
3. 具体仓位调整建议（科技/成长 vs 防御/价值、现金比例、风险控制）
4. 今日开盘预测（看涨/看跌/震荡 + 大致幅度/概率）

用中文回复，简洁、专业、有洞见。
"""
    try:
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "grok-4", "messages": [{"role": "user", "content": prompt}], "temperature": 0.6, "max_tokens": 1100},
            timeout=50
        )
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"AI调用失败: {str(e)}"

def send_email(subject, body):
    if not EMAIL_USER or not EMAIL_PASS:
        print("❌ 邮箱配置未设置")
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
        print(f"❌ 邮件失败: {e}")
        return False

def main():
    print(f"开始执行 - {datetime.datetime.now()}")
    market = get_market_data()
    macro = get_macro_data()
    news = get_news()
    analysis = ai_analyze_with_grok(market, macro, news)
    
    report = f"""
每日美股AI前瞻报告 - {datetime.date.today()}

=== 全球市场快照 ===
{ {k: v for k, v in market.items() if k != '主要股票'} }

=== 主要股票价格 ===
{market.get('主要股票')}

=== 宏观数据 ===
{macro}

=== 最新Reuters新闻 ===
{chr(10).join(['• ' + n for n in news])}

=== Grok AI 基金经理深度分析 ===
{analysis}
"""
    subject = f"每日美股AI报告 - {datetime.date.today()}"
    send_email(subject, report)
    print("工作流执行完毕")

if __name__ == "__main__":
    main()

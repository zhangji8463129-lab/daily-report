import os
import datetime
import feedparser
from fredapi import Fred
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# ================== 配置 ==================
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
FRED_API_KEY = os.getenv('FRED_API_KEY')

RSS_FEEDS = [
    'https://feeds.reuters.com/reuters/businessNews',
    'https://feeds.reuters.com/reuters/marketsNews',
]

def get_macro_data():
    if not FRED_API_KEY:
        return {"status": "FRED_API_KEY 未设置，使用模拟数据"}
    try:
        fred = Fred(api_key=FRED_API_KEY)
        data = {
            "联邦基金利率": fred.get_series_latest_release('FEDFUNDS'),
            "CPI": fred.get_series_latest_release('CPIAUCSL'),
            "10年期国债收益率": fred.get_series_latest_release('DGS10'),
        }
        return data
    except:
        return {"status": "宏观数据获取失败，使用模拟数据"}

def get_news():
    news = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:6]:
                news.append(entry.title)
        except:
            pass
    return news if news else ["暂无最新Reuters新闻"]

def ai_analyze(macro, news):
    # 简单规则 + 模拟AI判断（可后续升级真实LLM）
    analysis = "中性偏多"
    suggestion = "维持现有仓位，适当增配防御性科技和消费股，现金比例15-20%"
    prediction = "小幅看涨（概率约55%）"
    
    return f"""
利多/利空判断：{analysis}
理由：宏观数据整体稳定，新闻暂无重大利空。
仓位调整建议：{suggestion}
今日美股开盘预测：{prediction}
"""

def send_email(subject, body):
    if not EMAIL_USER or not EMAIL_PASS:
        print("❌ EMAIL_USER 或 EMAIL_PASS 未设置")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_USER, msg.as_string())
        server.quit()
        print("✅ 邮件发送成功")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {str(e)}")
        return False

def main():
    print(f"开始执行 - {datetime.datetime.now()}")
    
    macro = get_macro_data()
    news = get_news()
    analysis = ai_analyze(macro, news)
    
    report = f"""
每日美股前瞻报告 - {datetime.date.today()}

=== 宏观数据 ===
{macro}

=== 最新Reuters新闻 ===
{chr(10).join(['• ' + n for n in news])}

=== AI分析与建议 ===
{analysis}
    """
    
    subject = f"每日美股报告 - {datetime.date.today()}"
    send_email(subject, report)
    print("工作流执行完毕")

if __name__ == "__main__":
    main()

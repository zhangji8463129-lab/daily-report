import os
import datetime
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
import traceback

EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')

def get_data():
    stocks = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMD']
    data = {}
    for symbol in stocks:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                change = (hist['Close'].iloc[-1] - hist['Open'].iloc[0]) / hist['Open'].iloc[0]
                data[symbol] = change
            else:
                data[symbol] = 0.0
        except:
            data[symbol] = 0.0
    return data

def send_email(report):
    try:
        msg = MIMEText(report, "plain", "utf-8")
        msg["Subject"] = f"📊 美股盘前报告 - {datetime.date.today()}"
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_USER

        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_USER, msg.as_string())
        server.quit()
        print("✅ 邮件发送成功")
    except Exception as e:
        print(f"❌ 邮件失败: {e}")
        traceback.print_exc()

def main():
    print(f"🚀 开始执行 - {datetime.datetime.now()}")
    try:
        data = get_data()
        
        report = f"""
📊 每日美股盘前报告 - {datetime.date.today()}

NVDA: {data.get('NVDA', 0):.2%}
AAPL: {data.get('AAPL', 0):.2%}
TSLA: {data.get('TSLA', 0):.2%}
MSFT: {data.get('MSFT', 0):.2%}
AMD : {data.get('AMD', 0):.2%}

整体倾向：{ "看涨" if sum(data.values()) > 0 else "观望" }
        """
        send_email(report)
        print("✅ 执行完成")
    except Exception as e:
        print(f"❌ 异常: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()

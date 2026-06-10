import os
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback

# 配置
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')

def send_email(subject, body):
    if not EMAIL_USER or not EMAIL_PASS:
        print("❌ Secrets 未设置：EMAIL_USER 或 EMAIL_PASS")
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
        print("✅ 邮件发送成功！")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        traceback.print_exc()
        return False

def main():
    print(f"🚀 开始执行测试 - {datetime.datetime.now()}")
    try:
        report = f"""
测试报告 - {datetime.date.today()}

这是简化测试版本。
如果您收到这封邮件，说明基本框架正常。

后续将逐步加入市场数据和AI分析。
"""
        send_email(f"美股报告测试 - {datetime.date.today()}", report)
        print("✅ 测试完成")
    except Exception as e:
        print(f"❌ 严重错误: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()

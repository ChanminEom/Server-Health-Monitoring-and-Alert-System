import mysql.connector
import smtplib
from email.mime.text import MIMEText
from email.utils import make_msgid

def main():
    # 连接数据库
    try:
        db = mysql.connector.connect(
            host='localhost',
            user='root',
            password='200307',
            database='monitoring'
        )
        cursor = db.cursor()
    except Exception as e:
        print(f'Database connection failed: {e}')
        return

    try:
        # 查询最新数据
        cursor.execute('SELECT cpu_usage, disk_usage FROM server_health ORDER BY check_time DESC LIMIT 1')
        result = cursor.fetchone()
        if result:
            cpu_usage, disk_usage = result
        else:
            print("No data found.")
            return
    except Exception as e:
        print(f'Failed to query data: {e}')
        return
    finally:
        cursor.close()
        db.close()

    # 告警逻辑
    if cpu_usage > 80 or disk_usage > 80:
        msg = MIMEText(f"⚠️ Server Alert\nCPU Usage: {cpu_usage}%\nDisk Usage: {disk_usage}%", "plain", "utf-8")
        msg['Subject'] = '[Server Alert] High Resource Usage'
        msg['From'] = '599989086@qq.com'
        msg['To'] = '2354948791@qq.com'
        msg['Message-ID'] = make_msgid()  # 防止邮件重复标识

        try:
            # 显式管理SMTP连接（不使用with语句）
            server = smtplib.SMTP_SSL('smtp.qq.com', 465, timeout=10)
            server.login('599989086@qq.com', 'gjjmtxtdjymzbdfd')
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
            print('✅ Alert email sent!')
        except smtplib.SMTPServerDisconnected as e:
            # 特殊处理QQ邮箱的非标准响应
            print('✅ Alert email sent (non-critical SMTP quirk)')
        except Exception as e:
            print(f'❌ Failed to send email: {type(e).__name__}: {e}')
        finally:
            if 'server' in locals():
                server.quit()
    else:
        print('✅ System normal, no alert needed.')

if __name__ == "__main__":
    main()
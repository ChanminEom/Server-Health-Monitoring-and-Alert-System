# 服务器健康检查与告警系统

## 项目概述

* 目标：监控一台Linux服务器资源（CPU、内存、磁盘）使用情况，存储到MySQL数据库，当资源超标时通过Python发送邮件告警。

* 技术栈：Linux命令、Python脚本、MySQL基础操作、自动化任务。

## 1. 环境准备

* 操作系统：Ubuntu（或任何Linux发行版，Windows子系统WSL也可）。

* 工具：

  * Python3（安装psutil和mysql-connector-python）。
  * MySQL（简单配置）。
  * 文本编辑器（vim）。

* 安装命令：

  ```bash
  sudo apt update
  sudo apt install python3-pip mysql-server 
  pip3 install psutil mysql-connector-python --break-system-packages
  ```

* MySQL配置：

  ```bash
  sudo mysql
  ```

  ```SQL
  alter user 'root'@'localhost' indentified with mysql_native_password by '200307';
  create database monitoring;
  ```

## 2. 数据库设计

* 数据库：monitoring

* 表：server_health（存储CPU、内存、磁盘数据）

  ```sql
  create table server_health (
  	id int not auto_increment prmary key,
  	cpu_usage float,
  	memory_usage float,
  	disk_usage float,
  	check_time datetime
  );
  ```

## 3. 数据采集脚本

### 3.1 创建脚本

1. 创建文件夹

   ```bash
   mkdir server_monitor
   cd server_monitor
   ```

2. 创建脚本文件：用vim编辑器。

   ```bash
   vim check_server.py
   ```

3. 粘贴以下代码：

   ```python
   import psutil
   import mysql.connector
   from datetime import datetime
   
   # 连接数据库
   try:
       db = mysql.connector.connect(
           host = 'localhost',
           user = 'root',
           password = '200307', # 改成你的MySQL密码
           database = 'monitoring'
       )
       cursor = db.cursor()
   except Exception as e:
       print(f'Database connection failed:{e}')
       exit()
   
   # 采集CPU和磁盘使用率
   cpu_usage = psutil.cpu_percent(interval=1)
   disk_usage = psutil.disk_usage('/').percent
   check_time = datetime.now()
   
   # 存储到数据库
   try:
       sql = 'insert into server_health(cpu_usage, disk_usage, check_time) values(%s, %s, %s)'
       values = (cpu_usage, disk_usage, check_time)
       cursor.execute(sql, values)
       db.commit()
       print(f'Data saved: CPU={cpu_usage}%, Disk={disk_usage}%')
   except Exception as e:
       print(f'Failed to save data:{e}')
   
   # 关闭连接
   cursor.close()
   db.close()
   ```

4. 保存并退出。

### 3.2 测试脚本

1. 运行脚本：

   ```bash
   python3 check_server.py
   ```

   * 成功输出类似：CPU=0.5, Disk=38.3%

2. 检查数据库：

   ```sql
   use monitoring;
   select * from server_health;
   ```

   * 确认是否有一行数据，显示CPU、磁盘使用率和时间。

3. MySQL的时间校正：

   ```sql
   SET GLOBAL time_zone = '+8:00';
   ```

## 4. 告警脚本

### 4.1 配置邮件（使用QQ邮箱）

1. 登录QQ邮箱，进入“设置”→“账号”→“POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务”。

2. 开启服务并生成一个授权码（16位字符串，记录下来）

3. 粘贴代码：

   ```python
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
           msg['From'] = '599989086@qq.com' # 改成你自己的邮箱
           msg['To'] = '2354948791@qq.com' # 改成你自己的邮箱
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
   ```

4. 保存并退出。

### 4.2 测试警告

1. 修改数据触发警告（模拟高负载）：

   ```bash
   mysql -u root -p
   ```

   ```sql
   use monitoring;
   insert into server_health (cpu_usage, disk_usage, check_time) values (85.0, 90.0, now());
   ```

2. 运行脚本：

   ```bash
   python3 alert.py
   ```

   * 成功输出：✅ Alert email sent!
   * 检查你的QQ邮箱，确认收到邮件。

## 5. 自动化任务

1. 编辑crontab：

   ```bash
   crontab -e
   ```

2. 添加定时时钟：

   ```bash
   # 每5分钟检查一次服务器
   */5 * * * * /usr/bin/python3 /home/yann/server_monitor/check_server.py 
   # 每分钟检查一次（告警）
   * * * * * /usr/bin/python3 /home/yann/server_monitor/alert.py
   ```

   * 替换/home/yann/server_monitor/为你的实际路径（用pwd查看）
   * 每5分钟采集数据，每分钟检查告警。

3. 验证：

   ```bash
   tail -f /var/log/syslog |grep CRON
   ```

   * 确认crontab任务运行。
   * 检查数据库，数据应每5分钟增加一行。

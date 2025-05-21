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

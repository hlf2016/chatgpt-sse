import json
import pymysql
import requests
import math
import argparse

# Create argument parser
parser = argparse.ArgumentParser()

# Add arguments
parser.add_argument('--school', type=str, help='将导出数据的学校名称')
parser.add_argument('--start', type=str, help='数据开始日期')
parser.add_argument('--end', type=str, help='数据截止日期')
parser.add_argument('--limit', type=int, help='单次导出数量 最大为10000 一般默认即可')

# Parse the arguments
args = parser.parse_args()
# Access the arguments
school = args.school
start = args.start
end = args.end

if not school:
    print('请输入学校名称 例如：python3 main.py --school=北京大学 --start=2020-01-01 --end=2020-12-31')
    exit()
if not start:
    print('请输入数据开始日期 例如：python3 main.py --school=北京大学 --start=2020-01-01 --end=2020-12-31')
    exit()
if not end:
    print('请输入数据截止日期 例如：python3 main.py --school=北京大学 --start=2020-01-01 --end=2020-12-31')
    exit()
school = str(school)
# 单次取出的数量
limit = args.limit if args.limit else 10000


def esQuery(lastEssayId: int = None):
    # es sql 接口地址
    esUrl = 'http://xxxxx/_sql'
    esHeaders = {'Content-Type': 'application/json'}
    if lastEssayId:
        esQuery = "SELECT essay_id FROM essay where school='%s' and ctime > '%s' and ctime < '%s' and essay_id < %s order by essay_id desc limit %s" % (
            school, start, end, lastEssayId, limit)
    else:
        esQuery = "SELECT essay_id FROM essay where school='%s' and ctime > '%s' and ctime < '%s' order by essay_id desc limit %s" % (
            school, start, end, limit)
    # print(esQuery)
    return requests.post(esUrl, headers=esHeaders, data=esQuery.encode('utf-8')).json()


def mysqlQuery(essayIds: list):
    # Connect to the database
    connection = pymysql.connect(
                                    host='localhost',
                                    user='user',
                                    password='password',
                                    db='db',
                                    charset='utf8mb4',
                                    # 数据库连接时指定返回的数据类型为字典类型，这样查询结果会以字典的形式返回。在对查询结果进行处理时会更加方便，因为字典可以更直观地表示数据。
                                        cursorclass=pymysql.cursors.DictCursor
                                )
    with connection:
        with connection.cursor() as cursor:
            placeholder = ','.join(['%s'] * len(essayIds))
            query = "SELECT * FROM eng_essay where essay_id in ({})".format(
                placeholder)
            cursor.execute(query, essayIds)
            rows = cursor.fetchall()
            # Write the data to a file
            with open(f'{school}_{start}_{end}.txt', 'a', encoding='utf8') as outfile:
                for row in rows:
                    row['tm'] = row['tm'].strftime('%Y-%m-%d %H:%M:%S')
                    json.dump(row, outfile)
                    outfile.write('\n')


esData = esQuery()
total = esData['hits']['total']
if total == 0:
    print('no data')
    exit()
print("共有 %d 条数据" % total)
# 计算 总共还需要几轮 向上取整
rounds = math.ceil(total / 10000)
print("总共需要 %d 轮" % rounds)
dealCount = 0
for i in range(rounds):
    essayIds = [str(item['_source']['essay_id'])
                for item in esData['hits']['hits']]
    dealCount += len(essayIds)
    lastEssayId = essayIds[-1]
    print(lastEssayId, dealCount)
    mysqlQuery(essayIds)
    if dealCount == total:
        print('done')
        break
    esData = esQuery(lastEssayId)


# # Create a cursor object
# cursor = connection.cursor()

# # Execute the SQL query to select data from the table
# cursor.execute('SELECT * FROM member_info where user_id in (%s)', "28223130,28223129,28223128")

# # Fetch all the rows
# rows = cursor.fetchall()

# # Close the cursor and database connection
# cursor.close()
# connection.close()

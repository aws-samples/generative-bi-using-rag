
bulk_questions = [
    # 1. 下面是Sample QA对的例子
    {"question": "医院按年收入最高的是？",
     "sql": '''
     select name, revenue from table_a
     order by
     CASE
        WHEN revenue = '500~1000W' THEN 1
        WHEN revenue = '1000~3000W' THEN 2
     END
     desc
     limit 10
    '''}
]

for q in bulk_questions:
    # 2. 请修改profile_name和Data Profile name一致
    q['profile'] = '<profile_name>'

custom_bulk_questions = {
    'custom': bulk_questions
}
bulk_questions = [
    {"question": "30岁以下女性用户购买商品的平均价格是多少?",
     "sql": '''SELECT AVG(price)
FROM interactions i
JOIN items it ON i.item_id = it.item_id
JOIN users u ON i.user_id = u.user_id
WHERE u.gender = 'female' AND u.age < 30 AND i.event_type = 'purchase'
'''},
    {"question": "40岁以上男性用户浏览次数最多的前3个商品类别是什么?",
     "sql": '''SELECT category_l1, COUNT(*) AS views
FROM interactions i
JOIN items it ON i.item_id = it.item_id
JOIN users u ON i.user_id = u.user_id
WHERE u.gender = 'male' AND u.age > 40 AND i.event_type = 'view'
GROUP BY category_l1
ORDER BY views DESC
LIMIT 3
'''},
    {"question": "18-25岁用户购买打折商品的数量有多少?",
     "sql": '''SELECT COUNT(DISTINCT item_id)
FROM interactions i
JOIN users u ON i.user_id = u.user_id
WHERE u.age BETWEEN 18 AND 25
AND i.event_type = 'purchase'
AND i.discount != ''
'''},
    {"question": "每个商品类别从浏览到购买的转换率是多少?",
     "sql": '''WITH views AS (
  SELECT category_l1, COUNT(*) AS views
  FROM interactions i
  JOIN items it ON i.item_id = it.item_id
  WHERE i.event_type = 'view'
  GROUP BY category_l1
),
purchases AS (
  SELECT category_l1, COUNT(*) AS purchases
  FROM interactions i
  JOIN items it ON i.item_id = it.item_id
  WHERE i.event_type = 'purchase'
  GROUP BY category_l1
)
SELECT v.category_l1, purchases / views AS conversion_rate
FROM views v
JOIN purchases p ON v.category_l1 = p.category_l1
'''},
    {"question": "30岁以下用户浏览次数最多的前5个商品是什么?",
     "sql": '''SELECT item_id, COUNT(*) AS views
FROM interactions i
JOIN users u ON i.user_id = u.user_id
WHERE u.age < 30
AND i.event_type = 'view'
GROUP BY item_id
ORDER BY views DESC
LIMIT 5
'''},
    {"question": "过去30天内,男性和女性用户中有多少人完成了购买?",
     "sql": '''
SELECT gender, COUNT(DISTINCT user_id) AS users
FROM interactions i
JOIN users u ON i.user_id = u.user_id
WHERE i.event_type = 'purchase'
AND i.timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
GROUP BY gender
'''},
    {"question": "购买价格在50美元以上的商品,用户年龄分布如何?",
     "sql": '''SELECT age, COUNT(DISTINCT i.user_id) AS users
FROM interactions i
JOIN users u ON i.user_id = u.user_id 
JOIN items it ON i.item_id = it.item_id
WHERE i.event_type = 'purchase'
AND it.price > 50
GROUP BY age
'''},
    {"question": "25岁以下女性用户购买打折商品最常见的类别是什么?",
     "sql": '''SELECT category_l1, COUNT(*) AS purchases
FROM interactions i
JOIN items it ON i.item_id = it.item_id
JOIN users u ON i.user_id = u.user_id
WHERE u.gender = 'female' AND u.age < 25
AND i.discount != ''
AND i.event_type = 'purchase'
GROUP BY category_l1
ORDER BY purchases DESC
LIMIT 1
'''},
    {"question": "有多少商品被同一用户购买了多次?",
     "sql": '''SELECT COUNT(*)
FROM (
  SELECT item_id, user_id, COUNT(*) AS num_purchases
  FROM interactions
  WHERE event_type = 'purchase'
  GROUP BY item_id, user_id
  HAVING num_purchases > 1
) t
'''},
    {"question": "有哪些商品被浏览过但从未被购买?",
     "sql": '''SELECT item_id
FROM interactions i
WHERE i.event_type = 'view'
AND item_id NOT IN (
  SELECT item_id
  FROM interactions
  WHERE event_type = 'purchase'
)
'''},
    {"question": "30岁至40岁用户的购买总收入是多少?",
     "sql": '''SELECT SUM(price) AS total_revenue
FROM interactions i
JOIN items it ON i.item_id = it.item_id
JOIN users u ON i.user_id = u.user_id
WHERE u.age BETWEEN 30 AND 40
AND i.event_type = 'purchase'
'''},
    {"question": "每个商品被加入购物车的平均次数是多少?",
     "sql": '''SELECT item_id, AVG(added_to_cart) AS avg_cart_adds
FROM (
  SELECT item_id, COUNT(*) AS added_to_cart
  FROM interactions
  WHERE event_type = 'add_to_cart'
  GROUP BY item_id
) t
GROUP BY item_id
'''},
    {"question": "女性用户中低于10美元的购买占所有购买的百分比是多少?",
     "sql": '''WITH purchases AS (
  SELECT *
  FROM interactions i
  JOIN items it ON i.item_id = it.item_id
  WHERE i.event_type = 'purchase' AND price < 10
)

SELECT COUNT(*) / (SELECT COUNT(*) FROM purchases) AS percentage
FROM purchases p
JOIN users u ON p.user_id = u.user_id
WHERE u.gender = 'female'
'''},
    {"question": "从商品浏览到商品详情页面浏览的点击率是多少?",
     "sql": '''WITH product_views AS (
  SELECT COUNT(*) AS views
  FROM interactions
  WHERE event_type = 'view'
),

detail_views AS (
  SELECT COUNT(*) AS detail_views
  FROM interactions
  WHERE event_type = 'detail_view'
)

SELECT detail_views / views AS ctr
FROM product_views, detail_views
'''},
    {"question": "25岁以下用户最常购买的前3个商品类别是什么?每个商品的平均购买次数是多少?",
     "sql": '''SELECT category_l1, COUNT(*) AS purchases
FROM interactions i
JOIN items it ON i.item_id = it.item_id
JOIN users u ON i.user_id = u.user_id
WHERE u.age < 25 AND i.event_type = 'purchase'
GROUP BY category_l1
ORDER BY purchases DESC
LIMIT 3
'''},
    {"question": "每个商品的平均购买次数是多少?",
     "sql": '''SELECT item_id, AVG(purchases) AS avg_purchases
FROM (
  SELECT item_id, COUNT(*) AS purchases
  FROM interactions
  WHERE event_type = 'purchase'
  GROUP BY item_id
) t
GROUP BY item_id
'''},
    {"question": "男性用户中折扣大于30%的购买占所有购买的百分比是多少?",
     "sql": '''WITH male_purchases AS (
  SELECT *
  FROM interactions i
  JOIN users u ON i.user_id = u.user_id
  WHERE u.gender = 'male' AND i.event_type = 'purchase'
)

SELECT COUNT(*) / (SELECT COUNT(*) FROM male_purchases) AS percentage
FROM male_purchases
WHERE CAST(discount AS FLOAT) > 0.3
'''},
    {"question": "只浏览过但从未购买商品的用户有多少?",
     "sql": '''SELECT COUNT(DISTINCT user_id)
FROM interactions
WHERE user_id NOT IN (
  SELECT DISTINCT user_id
  FROM interactions
  WHERE event_type = 'purchase'
)
AND event_type = 'view'
'''},
    {"question": "哪些类别的商品从浏览到购买的转换率最高和最低?",
     "sql": '''WITH views AS (
  SELECT category_l1, COUNT(*) AS views
  FROM interactions i
  JOIN items it ON i.item_id = it.item_id
  WHERE event_type = 'view'
  GROUP BY category_l1
),

purchases AS (
  SELECT category_l1, COUNT(*) AS purchases
  FROM interactions i
  JOIN items it ON i.item_id = it.item_id
  WHERE event_type = 'purchase'
  GROUP BY category_l1
)

SELECT v.category_l1, purchases/views AS conversion_rate
FROM views v
JOIN purchases p ON v.category_l1 = p.category_l1
ORDER BY conversion_rate DESC
LIMIT 1

UNION

SELECT v.category_l1, purchases/views AS conversion_rate
FROM views v
JOIN purchases p ON v.category_l1 = p.category_l1
ORDER BY conversion_rate ASC
LIMIT 1
'''},
    {"question": "哪个商品的浏览转化购买率最高?",
     "sql": '''WITH views AS (
  SELECT item_id, COUNT(*) AS views
  FROM interactions
  WHERE event_type = 'view'
  GROUP BY item_id
),

purchases AS (
  SELECT item_id, COUNT(*) AS purchases
  FROM interactions
  WHERE event_type = 'purchase'
  GROUP BY item_id
)

SELECT v.item_id, purchases/views AS view_to_purchase_pct
FROM views v
JOIN purchases p ON v.item_id = p.item_id
ORDER BY view_to_purchase_pct DESC
LIMIT 1
'''},
]

for q in bulk_questions:
    q['profile'] = 'shopping_guide'

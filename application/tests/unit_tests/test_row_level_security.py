
import unittest

from nlq.business.datasource.mysql import MySQLDataSource
from nlq.business.login_user import LoginUser


class TestRLS(unittest.TestCase):
    def setUp(self):
        self.two_table_join_sql = '''SELECT c.`name`, o.`product`, o.`quantity`, o.`territory`
FROM customer c
JOIN orders o ON c.`id` = o.`customer_id`
LIMIT 100'''

        self.expected_rls_enabled_sql = (
            "WITH\n"
            "/* rls applied */ customer AS (SELECT * FROM customer WHERE created_by = 'admin'),\n"
            "/* rls applied */ orders AS (SELECT * FROM orders WHERE territory = 'Asia')\n"
            f"{self.two_table_join_sql}")

        self.base = MySQLDataSource()

    def test_row_level_security_control(self):
        test_yaml = '''tables:
  - table_name: customer
    columns:
      - column_name: created_by
        column_value: $login_user.username
  - table_name: orders
    columns:
      - column_name: territory
        column_value: Asia'''
        rls_modified_sql = self.base.row_level_security_control(self.two_table_join_sql, test_yaml, LoginUser('admin'))

        self.assertEqual(self.expected_rls_enabled_sql, rls_modified_sql)

    def test_cte_replace1(self):
        original_sql = """SELECT
    offer_id,
    slot,
    total_revenue
FROM
    (
        SELECT
            offer_id,
            slot,
            SUM(revenue_valid) AS total_revenue,
            ROW_NUMBER() OVER (PARTITION BY offer_id ORDER BY SUM(revenue_valid) DESC) AS rn
        FROM
            buzz_base_report
        GROUP BY
            offer_id, slot
    ) AS subquery
WHERE
    rn <= 5
ORDER BY
    offer_id, total_revenue DESC"""

        modified_sql = self.base.replace_table_with_cte(original_sql, {
            'buzz_base_report': "(select * from buzz_base_report where username = 'admin')"
        })

        self.assertEqual("WITH\n/* rls applied */ buzz_base_report AS "
                         f"(select * from buzz_base_report where username = 'admin')\n{original_sql}", modified_sql)

    def test_cte_replace2(self):
        original_sql = self.two_table_join_sql

        modified_sql = self.base.replace_table_with_cte(original_sql, {
            'customer': "(SELECT * FROM customer WHERE created_by = 'admin')",
            'orders': "(SELECT * FROM orders WHERE territory = 'Asia')"
        })

        self.assertEqual(self.expected_rls_enabled_sql, modified_sql)

    def test_cte_replace3(self):
        original_sql = """WITH mycte as (
SELECT c.`name`, o.`product`, o.`quantity`, o.`territory` FROM customer c JOIN orders o ON c.`id` = o.`customer_id`
)
select * from mycte LIMIT 100"""

        modified_sql = self.base.replace_table_with_cte(original_sql, {
            'customer': "(select * from customer where created_by = 'admin')",
            'orders': "(select * from orders where territory = 'Asia')"
        })

        self.assertEqual("WITH\n"
                         "/* rls applied */ customer AS (select * from customer where created_by = 'admin'),\n"
                         "/* rls applied */ orders AS (select * from orders where territory = 'Asia'),\n"
                         " mycte as (\n"
                         "SELECT c.`name`, o.`product`, o.`quantity`, o.`territory`"
                         " FROM customer c"
                         " JOIN orders o ON c.`id` = o.`customer_id`\n"
                         ")\n"
                         "select * from mycte LIMIT 100", modified_sql)

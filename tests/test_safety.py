import unittest

from mcp_sql_lite.safety import check_select, ensure_limit


class SafetyTests(unittest.TestCase):
    def test_plain_select_ok(self):
        self.assertTrue(check_select("SELECT * FROM orders")[0])

    def test_cte_ok(self):
        self.assertTrue(check_select("WITH x AS (SELECT 1) SELECT * FROM x")[0])

    def test_rejects_writes(self):
        for q in ("DELETE FROM orders", "drop table orders",
                  "UPDATE orders SET qty = 0", "PRAGMA table_info(orders)"):
            self.assertFalse(check_select(q)[0], q)

    def test_rejects_stacked(self):
        ok, reason = check_select("SELECT 1; DROP TABLE orders")
        self.assertFalse(ok)
        self.assertIn("multiple", reason)

    def test_keyword_inside_string_is_fine(self):
        self.assertTrue(check_select("SELECT * FROM orders WHERE status = 'delete me'")[0])

    def test_comment_trick(self):
        self.assertFalse(check_select("/* hi */ DELETE FROM orders")[0])

    def test_big_limit(self):
        self.assertFalse(check_select("SELECT * FROM orders LIMIT 5000")[0])

    def test_ensure_limit(self):
        self.assertEqual(ensure_limit("select 1;"), "select 1 LIMIT 50")
        self.assertEqual(ensure_limit("select 1 limit 3"), "select 1 limit 3")


if __name__ == "__main__":
    unittest.main()

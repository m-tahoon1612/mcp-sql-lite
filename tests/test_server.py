import json
import unittest

from mcp_sql_lite.server import Server, serve


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.s = Server()

    def rpc(self, method, params=None, mid=1):
        return self.s.handle({"jsonrpc": "2.0", "id": mid, "method": method,
                              "params": params or {}})

    def call_tool(self, name, args):
        res = self.rpc("tools/call", {"name": name, "arguments": args})["result"]
        return res, json.loads(res["content"][0]["text"]) if not res["isError"] else None

    def test_initialize(self):
        r = self.rpc("initialize")["result"]
        self.assertEqual(r["serverInfo"]["name"], "mcp-sql-lite")
        self.assertIn("tools", r["capabilities"])

    def test_tools_list(self):
        names = [t["name"] for t in self.rpc("tools/list")["result"]["tools"]]
        self.assertEqual(names, ["list_tables", "describe_table", "run_select"])

    def test_list_tables(self):
        _, data = self.call_tool("list_tables", {})
        self.assertEqual({d["table"] for d in data}, {"customers", "products", "orders"})

    def test_describe_unknown(self):
        res, _ = self.call_tool("describe_table", {"table": "users"})
        self.assertTrue(res["isError"])

    def test_run_select(self):
        _, data = self.call_tool("run_select", {"sql": "SELECT count(*) AS n FROM orders"})
        self.assertEqual(data["rows"], [[10]])

    def test_run_select_rejects_delete(self):
        res, _ = self.call_tool("run_select", {"sql": "DELETE FROM orders"})
        self.assertTrue(res["isError"])
        _, data = self.call_tool("run_select", {"sql": "SELECT count(*) FROM orders"})
        self.assertEqual(data["rows"], [[10]])

    def test_unknown_method(self):
        self.assertEqual(self.rpc("resources/list")["error"]["code"], -32601)

    def test_notification_no_response(self):
        self.assertIsNone(self.s.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))


if __name__ == "__main__":
    unittest.main()

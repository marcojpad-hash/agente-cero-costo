import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "puente-lectura" / "puente_mcp.py"


class MCPBusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["PUENTE_MCP_DB"] = str(Path(self.tmp.name) / "test.sqlite3")
        os.environ["PUENTE_MCP_TOKEN"] = "test-token"
        spec = importlib.util.spec_from_file_location("puente_mcp_under_test", MODULE_PATH)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)
        self.mod.init_db()

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("PUENTE_MCP_DB", None)
        os.environ.pop("PUENTE_MCP_TOKEN", None)

    def test_direct_message_ack_and_idempotency(self):
        self.mod.register_agent("A", ["send"])
        self.mod.register_agent("B", ["receive"])
        sent = self.mod.send_message("A", "B", "hola", "TEST", "msg-1")
        duplicate = self.mod.send_message("A", "B", "hola", "TEST", "msg-1")
        self.assertEqual(sent["seq"], duplicate["seq"])
        inbox = self.mod.fetch_inbox("B")
        self.assertEqual(len(inbox["messages"]), 1)
        self.assertEqual(inbox["messages"][0]["body"], "hola")
        self.mod.acknowledge_message("B", "msg-1")
        self.assertEqual(self.mod.fetch_inbox("B")["messages"], [])

    def test_broadcast_visible_to_other_agents_only(self):
        self.mod.register_agent("A")
        self.mod.register_agent("B")
        self.mod.register_agent("C")
        self.mod.send_message("A", "*", "aviso", "BROADCAST", "msg-all")
        self.assertEqual(len(self.mod.fetch_inbox("B")["messages"]), 1)
        self.assertEqual(len(self.mod.fetch_inbox("C")["messages"]), 1)
        self.assertEqual(self.mod.fetch_inbox("A")["messages"], [])

    def test_unknown_recipient_rejected(self):
        self.mod.register_agent("A")
        with self.assertRaises(ValueError):
            self.mod.send_message("A", "missing", "x")


if __name__ == "__main__":
    unittest.main()

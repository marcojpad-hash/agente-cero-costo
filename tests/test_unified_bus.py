import importlib.util, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("bus_core",ROOT/"conector"/"bus_core.py")
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class UnifiedBusTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.bus=mod.Bus(str(Path(self.tmp.name)/"bus.sqlite3"))
        self.bus.register("A",["publish"]); self.bus.register("B",["receive"])
    def tearDown(self): self.tmp.cleanup()

    def test_direct_broadcast_ack_and_idempotency(self):
        first=self.bus.send("A","B","hola","TEST","same-id")
        again=self.bus.send("A","B","hola","TEST","same-id")
        self.assertEqual(first["seq"],again["seq"])
        self.assertEqual(len(self.bus.inbox("B")["messages"]),1)
        self.bus.ack("B","same-id")
        self.assertEqual(self.bus.inbox("B")["messages"],[])
        self.bus.send("A","*","todos","BROADCAST","broadcast-1")
        self.assertEqual(len(self.bus.inbox("B")["messages"]),1)

    def test_context_revision_conflict_and_bootstrap(self):
        saved=self.bus.publish_context("A","global",{"project":"CAPCOT"})
        self.assertEqual(saved["revision"],1)
        self.assertEqual(self.bus.get_context()["document"]["project"],"CAPCOT")
        with self.assertRaises(ValueError):
            self.bus.publish_context("B","global",{"project":"U6"},expected_revision=0)
        boot=self.bus.bootstrap("B")
        self.assertEqual(boot["context"]["revision"],1)
        self.assertEqual(boot["mode"],"LATENCY_READ_ON_ACTIVATION")

    def test_emit_block_ingested_as_data(self):
        result=self.bus.ingest_emit_block("[EMITIR]\nde: ChatGPT\ntipo: hecho\nmensaje: Prueba terminada\n[/EMITIR]")
        self.assertTrue(result["sent"])
        event=self.bus.inbox("B")["messages"][0]
        self.assertEqual(event["topic"],"EMITIR:hecho")
        self.assertIn('"mensaje": "Prueba terminada"',event["body"])

    def test_invalid_emit_block_rejected(self):
        with self.assertRaises(ValueError):
            self.bus.ingest_emit_block("[EMITIR]\nde: X\ntipo: root\nmensaje: nope\n[/EMITIR]")

    def test_cursor_is_durable_and_ack_does_not_leak(self):
        self.bus.send("A","B","one","T","m1")
        self.assertEqual(self.bus.inbox("B")["next_after_seq"],1)
        self.bus.send("A","B","two","T","m2")
        self.assertEqual(len(self.bus.inbox("B")["messages"]),2)

if __name__=="__main__": unittest.main()

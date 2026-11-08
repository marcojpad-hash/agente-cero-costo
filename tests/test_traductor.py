import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "conector"))
from bus_core import Bus
from traductor import Traductor, traducir


class TestTraductor(unittest.TestCase):
    def setUp(self):
        self.bus = Bus(os.path.join(tempfile.mkdtemp(), "t.db"))
        self.bus.register("puta3", ["leer:pdf", "leer:github"])
        self.bus.register("muse", ["leer:github", "escribir:github_pr"])
        self.bus.register("grok", ["escribir:github_pr"])
        self.t = Traductor(self.bus)

    def test_cuatro_idiomas_un_formato(self):
        a = traducir("x [EMITIR]\nde: ChatGPT\ntipo: hecho\nmensaje: listo\n[/EMITIR]")
        b = traducir("listo", titulo="[BUS] hecho - ChatGPT")
        c = traducir('{"de": "ChatGPT", "tipo": "done", "mensaje": "listo"}')
        d = traducir("ChatGPT: listo")
        for x in (a, b, c):
            self.assertEqual((x["de"], x["tipo"], x["mensaje"]), ("ChatGPT", "hecho", "listo"))
        self.assertEqual((d["de"], d["mensaje"]), ("ChatGPT", "listo"))

    def test_hembra_va_al_que_puede(self):
        r = self.t.enchufar({"de": "muse", "tipo": "indicacion", "mensaje": "lee a.pdf", "necesita": "leer:pdf"})
        self.assertEqual(r["para"], "puta3")
        self.assertEqual(len(self.bus.inbox("puta3")["messages"]), 1)

    def test_vuelta_si_falla_pasa_al_siguiente_y_luego_a_mj(self):
        r = self.t.enchufar({"de": "puta3", "tipo": "indicacion", "mensaje": "abre PR", "necesita": "escribir:github_pr"})
        primero = r["para"]
        f1 = self.t.fallo(primero, r["message_id"], "sin permiso")
        self.assertNotIn(f1["para"], (primero, "puta3"))
        f2 = self.t.fallo(f1["para"], f1["message_id"], "tampoco")
        self.assertEqual(f2["para"], "mj")

    def test_sin_necesidad_va_a_todos_y_foquitos(self):
        r = self.t.enchufar("ChatGPT: nuevo estado v5")
        self.assertEqual(r["para"], "*")
        self.bus.ack("muse", r["message_id"])
        luces = self.t.luces()[0]["luces"]
        self.assertEqual(luces["muse"], "🟢"); self.assertEqual(luces["grok"], "🟡")

    def test_externo_no_suplanta(self):
        r = self.t.enchufar("[EMITIR]\nde: Gemini\ntipo: aviso\nmensaje: hola\n[/EMITIR]")
        self.assertTrue(self.bus.inbox("muse")["messages"][0]["sender"].startswith("external:"))

    def test_basura_se_rechaza(self):
        with self.assertRaises(ValueError):
            traducir("sin formato ninguno")


if __name__ == "__main__":
    unittest.main()

import json, os, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bot"))
import gestor  # noqa: E402

LIMPIO = {k: "" for k in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY",
                          "TELEGRAM_ALLOWED_CHAT_IDS", "MOTORES_APAGADOS")}


class TestBot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        p = mock.patch.dict(os.environ, dict(LIMPIO, BOT_DATA_DIR=self.tmp))
        p.start(); self.addCleanup(p.stop)

    def test_motores_sin_clave_se_saltan(self):
        self.assertEqual(gestor.motores_config(), [])
        os.environ["GEMINI_API_KEY"] = "x"
        self.assertEqual([m["nombre"] for m in gestor.motores_config()], ["gemini"])
        os.environ["GROQ_API_KEY"] = "y"
        self.assertEqual(len(gestor.motores_config()), 3)

    def test_merge_paralelo_con_etiquetas(self):
        os.environ.update(GROQ_API_KEY="g", GEMINI_API_KEY="m", OPENROUTER_API_KEY="o")
        def falso(url, payload=None, headers=None, timeout=60):
            if "generativelanguage" in url:
                self.assertEqual(headers["x-goog-api-key"], "m")
                return {"candidates": [{"content": {"parts": [{"text": "resp gemini"}]}}]}
            if payload["messages"][0]["content"].startswith("# Gestor"):
                entrada = payload["messages"][-1]["content"]
                for n in ("groq-gpt-oss", "groq-2", "gemini", "openrouter"):
                    self.assertIn(f"### MOTOR: {n}", entrada)
                return {"choices": [{"message": {"content": "FINAL"}}]}
            return {"choices": [{"message": {"content": "resp " + payload["model"]}}]}
        with mock.patch.object(gestor, "http_json", side_effect=falso):
            final, motores = gestor.gestionar("hola", [], gestor.cargar_prompt())
        self.assertEqual(final, "FINAL")
        self.assertEqual(len(motores), 4)
        self.assertIn("resp gemini", gestor.entrada_gestor("hola", motores))

    def test_motor_caido_no_tumba(self):
        os.environ["GEMINI_API_KEY"] = "m"
        with mock.patch.object(gestor, "http_json", side_effect=OSError("caído")):
            r = gestor.consultar_motores("hola", [])
        self.assertTrue(r["gemini"].startswith("ERROR:"))

    def test_filtro_chats(self):
        self.assertFalse(gestor.permitido(123))  # sin lista: falla cerrado
        os.environ["TELEGRAM_ALLOWED_CHAT_IDS"] = "123, 456"
        self.assertTrue(gestor.permitido(123))
        self.assertFalse(gestor.permitido(999))
        with mock.patch.object(gestor, "gestionar") as g:
            r = gestor.atender("t", {"chat": {"id": 999}, "text": "hola"}, "p", {})
        self.assertIsNone(r); g.assert_not_called()

    def test_partir_mensajes(self):
        texto = ("palabra " * 2000).strip()
        partes = gestor.partir(texto)
        self.assertGreater(len(partes), 1)
        self.assertTrue(all(len(p) <= 4096 for p in partes))
        self.assertEqual(gestor.partir("corto"), ["corto"])

    def test_prompt_cargado(self):
        p = gestor.cargar_prompt()
        for frase in ("Veredicto primero", "no se puede", "JorgeNeural", "244", "merge"):
            self.assertIn(frase, p)

    def test_memoria_corta(self):
        mem = {}
        os.environ["MEMORIA_TURNOS"] = "2"
        for i in range(5):
            gestor.recordar(mem, 1, f"q{i}", f"a{i}")
        self.assertEqual(len(mem["1"]), 4)
        self.assertEqual(mem["1"][-1]["content"], "a4")


if __name__ == "__main__":
    unittest.main()

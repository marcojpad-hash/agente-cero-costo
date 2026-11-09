import json, os, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bot"))
import gestor  # noqa: E402

LIMPIO = {k: "" for k in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY",
                          "TELEGRAM_ALLOWED_CHAT_IDS", "MOTORES_APAGADOS", "NEGATIVAS_REGEX", "CICLOS_MAX",
                          "GITHUB_TOKEN", "GH_TOKEN")}


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

    def test_detecta_negativas(self):
        for t in ("Eso no se puede.", "No es posible hoy", "I can't do that", "es IMPOSIBLE", "no tengo acceso"):
            self.assertTrue(gestor.es_negativa(t), t)
        self.assertFalse(gestor.es_negativa("Listo, ya quedó el PR."))
        os.environ["NEGATIVAS_REGEX"] = "nel"
        self.assertTrue(gestor.es_negativa("nel pastel"))
        self.assertFalse(gestor.es_negativa("no se puede"))

    def test_rotacion(self):
        ms = [{"nombre": n} for n in "abc"]
        self.assertEqual([m["nombre"] for m in gestor.rotar(ms, 1)], ["b", "c", "a"])
        self.assertEqual([m["nombre"] for m in gestor.rotar(ms, 3)], ["a", "b", "c"])

    def test_tope_de_ciclos_y_lideres(self):
        os.environ["CICLOS_MAX"] = "3"
        ms = [{"nombre": n} for n in "abc"]
        lideres = []
        def falso(preg, hist, prompt, motores=None):
            lideres.append(motores[0]["nombre"])
            return "no se puede. ACCION: crear el bot en BotFather", {}
        with mock.patch.object(gestor, "gestionar", side_effect=falso):
            texto, _, bloqueado, ciclos = gestor.resolver("x", [], "p", ms)
        self.assertTrue(bloqueado); self.assertEqual(ciclos, 3)
        self.assertEqual(lideres, ["a", "b", "c", "a"])
        self.assertEqual(gestor.accion_de(texto), "crear el bot en BotFather")

    def test_ciclo_resuelve(self):
        res = iter([("no puedo", {}), ("Sí: usa el equivalente X", {})])
        with mock.patch.object(gestor, "gestionar", side_effect=lambda *a, **k: next(res)):
            texto, _, bloqueado, ciclos = gestor.resolver("x", [], "p", [{"nombre": "a"}])
        self.assertFalse(bloqueado); self.assertEqual(ciclos, 1)

    def test_bloqueo_manda_botones(self):
        os.environ["TELEGRAM_ALLOWED_CHAT_IDS"] = "1"
        with mock.patch.object(gestor, "resolver", return_value=("no se puede", {}, True, 3)):
            r = gestor.atender("t", {"chat": {"id": 1}, "text": "hazlo"}, "p", {})
        self.assertEqual([b["text"] for b in r["botones"]], ["Acepto", "No"])

    def test_boton_registra_decision(self):
        os.environ["TELEGRAM_ALLOWED_CHAT_IDS"] = "1"
        cq = {"id": "q1", "data": "si:abc", "from": {"id": 1}, "message": {"chat": {"id": 1}}}
        with mock.patch.object(gestor, "tg") as t:
            self.assertEqual(gestor.atender_boton("tok", cq), "acepto")
        self.assertEqual(t.call_args[0][1], "answerCallbackQuery")
        linea = json.loads((Path(self.tmp) / "turnos.jsonl").read_text().splitlines()[-1])
        self.assertEqual(linea["decision_mj"], "acepto")
        self.assertEqual(linea["atribucion"], "lo hizo el bot")
        self.assertEqual(linea["turno"], "abc")
        cq["from"]["id"] = 999
        with mock.patch.object(gestor, "tg"):
            self.assertIsNone(gestor.atender_boton("tok", cq))

    def test_comandos_portados(self):
        os.environ["TELEGRAM_ALLOWED_CHAT_IDS"] = "1"
        with mock.patch.object(gestor, "leer_local", return_value="DIGEST OK"):
            self.assertEqual(gestor.atender("t", {"chat": {"id": 1}, "text": "/memoria"}, "p", {}), "DIGEST OK")
        with mock.patch.object(gestor, "ultimos_eventos", return_value=[{"fecha": "hoy", "tipo": "hecho", "de": "Grok", "mensaje": "ok"}]):
            r = gestor.atender("t", {"chat": {"id": 1}, "text": "/bus"}, "p", {})
            self.assertIn("Grok", r)
            self.assertIn("ok", r)
        with mock.patch.object(gestor, "cmd_interpretar", return_value="interpretado"):
            self.assertEqual(gestor.atender("t", {"chat": {"id": 1}, "text": "/interpretar hola"}, "p", {}), "interpretado")

    def test_emitir_bloque(self):
        os.environ["TELEGRAM_ALLOWED_CHAT_IDS"] = "1"
        bloque = "[EMITIR]\nde: Mj\ntipo: hecho\nmensaje: prueba\n[/EMITIR]"
        with mock.patch.object(gestor, "subir_evento_github", return_value=True):
            r = gestor.atender("t", {"chat": {"id": 1}, "text": bloque}, "p", {})
        self.assertIn("Evento", r)
        self.assertIn("subido a GitHub", r)


if __name__ == "__main__":
    unittest.main()

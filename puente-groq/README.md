# Puente local Groq

dsh acepta cualquier endpoint OpenAI-compatible, pero necesita una clave
que no siempre está a la mano (la guardada en la bóveda no se puede leer
de vuelta) y no todo el mundo tiene computadora para ponerla. Este puente
corre en la máquina que corre dsh: dsh apunta a
`http://127.0.0.1:8080/v1` sin clave, y el puente reenvía a Groq usando el
mecanismo del conector. La clave real nunca sale de la bóveda ni pasa por
este archivo.

Endpoints: `GET /v1/models`, `POST /v1/chat/completions` (con y sin
stream).

## Uso

```bash
python3 proxy.py [--port PUERTO]
```

## En dsh

Proveedor personalizado (`dsh/settings-puente.yaml`):

- Provider ID: `groq-puente`
- Base URL: `http://127.0.0.1:8080/v1`
- API protocol: `openai-completions`
- API key: cualquiera o vacía (el puente la ignora)
- Modelos: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`

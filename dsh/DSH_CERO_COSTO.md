# DeepSeek Harness (dsh) a costo cero — verificación

Fecha: 2026-11-08. Sin instalar nada, sin usar ninguna clave, sin crear cuentas, sin descargar modelos. Solo verificación de configuración contra la documentación del repo y el código local.

## Veredicto: SÍ

**DeepSeek Harness corre a costo cero sin clave de pago de DeepSeek.** El error de la evaluación del 2026-11-07 fue pensar que el modelo tenía que ser DeepSeek. No es así: el harness es solo el loop (planear, llamar herramientas, leer resultados, repetir) y el modelo es un ingrediente configurable. Acepta cualquier endpoint OpenAI-compatible mediante "Add a custom provider". Marco tenía razón: el análogo existe.

Ruta recomendada: **Groq** (ruta 1). La ruta 2 (Ollama local) también está verificada en configuración, pero en esta VM sin GPU sería lenta y exige descargar ~13 GB.

## Lo que se verificó (y dónde)

1. **Groq es OpenAI-compatible, verificado en el código local** (`~/workspace/custom-connectors/custom.groq/bin/client.py`):
   - `BASE = "https://api.groq.com/openai/v1"` y el docstring dice: "Groq speaks the OpenAI compatible API".
   - `list_models()` hace `GET /models`; `chat()` hace `POST /chat/completions` con `{"model": ..., "messages": [...]}`.
   - Es exactamente la superficie que dsh necesita: `GET {baseURL}/models` (para "Fetch available models") y `POST {baseURL}/chat/completions`.
2. **El proveedor personalizado de dsh, verificado en la documentación** (guía oficial de proveedores del repo `deepseek-ai/deepseek-harness`, citada por la guía de Apidog y por la guía de integración de Turing; también la guía de AIHubMix y la de GravitexAI):
   - La configuración vive en `$DSH_HOME/settings.yaml` (por defecto `~/.dsh`), bajo `llm-pi-ai: providers:`, o se crea en la Web UI en Settings → Models → Add a custom provider.
   - Campos: Provider ID (minúsculas, permanente), display name, `baseURL`, `api: openai-completions`, credencial (referencia `apiKeyEnv`, nunca la clave en claro) y al menos un modelo con su `id` exacto.
   - dsh añade `/chat/completions` a la baseURL. Los secretos se guardan solo-escritura en `$DSH_HOME/.credentials.yaml`; `settings.yaml` solo guarda referencias.
   - Interruptores de compatibilidad documentados: `supportsDeveloperRole: false` y `maxTokensField: max_tokens`, para endpoints que rechazan el rol `developer` o el campo nuevo de límite de tokens.
3. **dsh ya corrió en esta VM** (evaluación 2026-11-07): `npx -y @deepseek-ai/dsh --version` → 0.2.2-rc.1; `dsh web --no-open` arrancó la Web UI en `http://127.0.0.1:3080/`. Node v24.22.1 presente. Solo faltaba el proveedor.
4. **Ollama, verificado en documentación**: expone API OpenAI-compatible en `http://localhost:11434/v1` y no exige clave en local, aunque el esquema de dsh pide una referencia de credencial (se pone un valor dummy). Los modelos se declaran con su tag exacto (`ollama list`).

## Ruta 1 (recomendada): Groq, API gratuita

Modelo: `openai/gpt-oss-120b` (pesos abiertos, Apache 2.0). Alternativa más ligera: `openai/gpt-oss-20b`. La clave de Groq ya está conectada y verificada (11 modelos en la lista); la API es gratuita y no tiene saldo que se agote.

### Por la Web UI

1. `npx @deepseek-ai/dsh web` (o `dsh web` si está instalado).
2. Settings → Models → **Add a custom provider**:
   - Provider ID: `groq`
   - Display name: `Groq`
   - Base URL: `https://api.groq.com/openai/v1`
   - API protocol: `openai-completions`
   - API key: la clave de Groq (ver "Qué falta" abajo)
   - Models: `openai/gpt-oss-120b` (o usar "Fetch available models": dsh llama a `GET https://api.groq.com/openai/v1/models` y lista los 11).
3. En Settings → Models, elegir `openai/gpt-oss-120b` como modelo por defecto para las sesiones nuevas.

### Por YAML (`$DSH_HOME/settings.yaml`)

```yaml
llm-pi-ai:
  providers:
    groq:
      displayName: Groq
      apiKeyEnv: GROQ_API_KEY
      api: openai-completions
      baseURL: https://api.groq.com/openai/v1
      models:
        - id: openai/gpt-oss-120b
          contextWindow: 131072
        - id: openai/gpt-oss-20b
          contextWindow: 131072
```

Notas:
- `contextWindow: 131072`: gpt-oss tiene 128k de contexto. Los modelos declarados a mano en dsh toman 262.144 por defecto; si se deja así, dsh puede mandar más contexto del que el modelo acepta.
- Si aparecen errores de rol o de campo de tokens, probar primero el interruptor `compat: {supportsDeveloperRole: false}` en el proveedor. El harness infiere el "dialecto de razonamiento" desde la base URL y puede adivinar mal.

## Ruta 2: Ollama local (sin clave, sin nube)

```yaml
llm-pi-ai:
  providers:
    ollama-local:
      displayName: Ollama local
      apiKeyEnv: OLLAMA_API_KEY
      api: openai-completions
      baseURL: http://localhost:11434/v1
      models:
        - id: gpt-oss:20b
          contextWindow: 131072
```

Pasos previos (no hechos aquí): instalar Ollama, `ollama pull gpt-oss:20b` (~13 GB), confirmar que el servidor responde en `http://localhost:11434/v1/models`, y poner un valor dummy en la variable: `export OLLAMA_API_KEY=dummy` (Ollama no exige clave en local, pero el esquema pide la referencia). El `id` del modelo debe coincidir exacto con el tag que muestra `ollama list`.

Advertencia honesta: esta VM no tiene GPU. Un modelo de 20B en CPU es lento, y los agentes hacen loops largos con muchas llamadas a herramientas. Sirve para probar el loop; para trabajo real es frustrante. La guía de Ollama sugiere ~24 GB de VRAM para `qwen3.8:27b` como objetivo cómodo. Por eso la ruta 1 es la recomendada.

## Qué falta para correrlo

Una sola cosa, y la pone Marco una vez:

- **La clave de Groq.** Se mete como variable de entorno en la shell que lanza dsh (`export GROQ_API_KEY=...`) o se pega en la UI de Settings → Models. Pecas no puede ponerla: la clave guardada en la bóveda no se puede leer de vuelta. Marco la crea o la copia en console.groq.com (nivel gratuito), igual que el secreto `GROQ_API_KEY` de GitHub Actions para el orquestador.

Nada más: no hay que pagar DeepSeek, no hay que crear cuentas nuevas, no hay que instalar nada más (Node 24 ya está; dsh corre por npx).

## Cómo comprobar que funciona (sin gastar nada serio)

1. `GET https://api.groq.com/openai/v1/models` con la clave (o en la UI, "Fetch available models"): si lista los modelos, la base URL y la clave están bien.
2. En la UI, elegir `openai/gpt-oss-120b` como defecto y abrir una sesión en un repo de prueba.
3. Pedirle una tarea pequeña con herramientas (leer un archivo, proponer un cambio) y ver que el loop complete sin errores de rol o de contexto.

## Límites honestos

- **dsh es developer preview (alpha/RC).** El README avisa en mayúsculas que habrá cambios que rompen compatibilidad. SAFETY.md advierte que no está auditado para producción. Fijar la versión que se despliegue y leer las notas de cada actualización.
- **El prototipo dsh-superagent no es dsh.** `deepseek-ai/dsh-superagent-prototype` es un prototipo de investigación v0.1.0 (creado 2026-10-31), con advertencia explícita de que no es producto oficial ni está listo para producción. Corre encima de dsh, así que con la ruta 1 también correría, pero hereda sus propios requisitos: cuenta de GitHub dedicada para el agente (nunca la del operador), invitación al repo, CLIs firmados, clon local y revisión horaria. Y su función (agente proactivo que escucha issues y abre PRs) duplica lo que Pecas ya hace con los conectores gratuitos. Para CAPCOT no aporta nada (no es video); para el motor no resuelve los P0 (cron, requirements, calibración).
- **La API gratuita de Groq tiene límites de velocidad** (por minuto y por día). No cobra ni se agota un saldo, pero no es ilimitada. Unas sesiones de agente ocasionales están muy por debajo; un agente corriendo 24/7 sin pausa sí puede toparse con el límite.
- **Lo verificado aquí es la configuración, no una sesión completa.** Nadie ha corrido todavía una sesión larga de agente con gpt-oss-120b en dsh ni medido la tasa de fallos de llamadas a herramientas. La primera sesión real es la prueba que falta.
- **Los modelos pequeños locales planean peor** y pierden llamadas a herramientas con más frecuencia que los modelos grandes. Eso vale para Ollama y, en menor medida, para gpt-oss-20b frente a gpt-oss-120b.

## Fuentes

- `~/workspace/custom-connectors/custom.groq/bin/client.py` (BASE, `/models`, `/chat/completions`).
- `~/workspace/dsh-superagent-evaluacion.md` (evaluación 2026-11-07 del prototipo).
- `~/workspace/deepseek-harness-craft-t3-informe.md` (dsh 0.2.2-rc.1 probado por npx en esta VM).
- Guía oficial de proveedores de dsh (repo `deepseek-ai/deepseek-harness`, `docs/user/guide/providers.md`), citada por la guía de Apidog ("How to Run Any Model in DeepSeek Harness?") y la guía de integración de Turing; guías de AIHubMix y GravitexAI para el mismo formulario.
- Repos: https://github.com/deepseek-ai/deepseek-harness y https://github.com/deepseek-ai/dsh-superagent-prototype

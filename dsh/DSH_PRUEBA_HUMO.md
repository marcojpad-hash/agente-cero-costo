# Prueba de humo: DeepSeek Harness (dsh) a costo cero con el puente local de Groq

Fecha: 2026-11-08 ~02:10–02:25 CST. Máquina: VM de Pecas. Modelo: openai/gpt-oss-20b por el puente local.

## Veredicto: NO de punta a punta a costo cero con Groq gratis

El loop del agente **sí arranca y razona bien**, pero **no completa la tarea**: el segundo llamado al modelo choca con el límite de 8.000 tokens por minuto (TPM) del tier gratis de Groq y dsh lo trata como error fatal, sin reintentar. No es un problema de configuración: es aritmética. El prompt de dsh ya pesa ~4.600 tokens por llamado; dos llamados seguidos suman ~9.000 y el tope es 8.000.

Lo que sí quedó probado: la instalación, la configuración del proveedor personalizado, el puente (la clave nunca sale de la bóveda), el modelo razonando y planeando herramientas correctamente. Lo que falta para que corra de punta a punta es presupuesto de tokens por minuto, no código.

## Lo que se probó

- Puente vivo en `http://127.0.0.1:8080/v1`: `GET /v1/models` y `POST /v1/chat/completions` (con y sin stream) responden.
- dsh 0.2.2-rc.1 por npx (Node v24.22.1). Ya estaba en la caché de npx de la evaluación anterior; no se instaló nada con sudo ni fuera de `~/workspace`.
- Directorio de prueba `~/workspace/dsh-prueba/` (solo un `README.txt` semilla; no se tocaron repos reales).
- Tarea: "Lista los archivos de este directorio y crea un archivo llamado hola.txt con una sola línea que diga: Hola desde dsh."

## Configuración que funcionó (la que quedó)

Parche en `~/.dsh/profiles/headless/cordis.patch.yml` (verificado con `dsh --profile headless --dump-config`, el árbol compuesto muestra el proveedor y el modelo por defecto):

```yaml
- id: llm-pi-ai
  config:
    providers:
      groq-proxy:
        displayName: Groq via puente local
        api: openai-completions
        baseURL: http://127.0.0.1:8080/v1
        apiKeyEnv: DSH_DUMMY_KEY
        models:
          - id: openai/gpt-oss-20b
            name: gpt-oss-20b
            contextWindow: 131072
            maxTokens: 2048
- id: agent-default-model
  config:
    provider: groq-proxy
    model: openai/gpt-oss-20b
```

La forma del config se sacó del esquema del propio paquete (`dsh --profile headless --dump-config-schema`, `config14` de `llm-pi-ai`: `providers` con `apiKeyEnv`, `displayName`, `api: openai-completions | openai-responses | anthropic-messages`, `baseURL`, `models: [{id, name, contextWindow, maxTokens}]`). El plugin `llm-retry` no tiene opciones configurables (esquema vacío), así que no hay reintento con espera que ajustar.

El modelo por defecto se fija con el plugin `agent-default-model` (venía en `deepseek-official` / `deepseek-flash`).

## Comando exacto de la prueba

```bash
cd ~/workspace/dsh-prueba
DSH_DUMMY_KEY=dummy npx --yes @deepseek-ai/dsh --profile headless \
  --permission-mode workspace-write --approval-policy never \
  "Lista los archivos de este directorio y crea un archivo llamado hola.txt con una sola línea que diga: Hola desde dsh."
```

`DSH_DUMMY_KEY=dummy` es una clave falsa: el puente la ignora y reenvía a Groq con el mecanismo del conector. Ninguna clave real se usó ni se pegó en ningún archivo.

## Errores que salieron y cómo se resolvieron

### 1. 400 `max_completion_tokens` debe ser ≤ 65536 (primer intento)

dsh pedía `max_completion_tokens` igual a la ventana de contexto (131.072) y Groq lo rechaza: el máximo para gpt-oss-20b es 65.536.

Resolución: agregar `maxTokens` al modelo en el parche.

### 2. 413 `Request too large` / TPM: pedido 36.991, límite 8.000 (segundo intento, con `maxTokens: 32768`)

Groq cuenta **prompt + max_tokens** en el límite de TPM. Con `maxTokens: 32768` cada request pedía ~37.000 tokens.

Resolución: bajar `maxTokens` a 2048. El request queda en ~6.700 tokens y entra.

### 3. 429 `Rate limit reached` en TPM: usado 4.605, pedido 4.461, límite 8.000 (tercer intento, con `maxTokens: 2048`)

El primer llamado del agente **sí funcionó**: el modelo razonó bien ("We need to list files... use glob to list. Then write to create file... read after creating to verify") y planeó las herramientas correctas. El segundo llamado, segundos después, pidió 4.461 tokens con 4.605 ya usados en la ventana de un minuto: 9.066 > 8.000. dsh lo marcó fatal (`EXIT:1`) y no completó la tarea; `hola.txt` no se creó. Se repitió el intento esperando 45–60 s antes: mismo resultado, porque el problema no es el momento sino la suma de dos llamados seguidos.

**Este error no tiene arreglo a costo cero con Groq**: gpt-oss-120b tiene el mismo límite gratis (30 RPM, 1.000 RPD, 8.000 TPM, 200.000 TPD, confirmado en la página de límites de Groq). El plan Developer sube a 250.000 TPM, pero es de pago.

## Los números que mandan

- Prompt de dsh por llamado: ~4.400–4.600 tokens (system prompt + herramientas + tarea).
- Límite gratis de Groq (20b y 120b): 8.000 TPM, 200.000 TPD, 1.000 requests/día.
- Una tarea mínima de agente necesita 3+ llamados (listar → escribir → responder): ~15.000–25.000 tokens por tarea. Con 200.000 TPD cabrían unas 8 tareas así al día, si el TPM no las matara antes.
- El plugin `llm-retry` de dsh no expone configuración y el 429 fue fatal en los tres intentos.

## Caminos para que sí corra de punta a punta

1. **Groq Developer (pago)**: 250.000 TPM. Ya no es costo cero; es el camino directo si Marco decide pagar.
2. **Ollama local (costo cero, sin límite de TPM)**: dsh acepta `http://localhost:11434/v1` sin clave. No se probó aquí: la VM de Pecas tiene 7,7 GB de RAM con ~0,6 GB libre y el modelo hay que descargarlo (~13 GB para uno de 20B; uno chico de 3B cabe pero sería lento en CPU). Es el análogo a costo cero que queda por probar, en una máquina con más memoria.
3. **Espaciar los llamados**: si dsh esperara ~60 s entre llamados, el TPM se liberaría. dsh no tiene esa opción; habría que poner un proxy con cola y espera entre llamados, o sea más código.

## Archivos

- Reporte: `~/workspace/dsh-prueba-humo.md` (este archivo).
- Configuración: `~/.dsh/profiles/headless/cordis.patch.yml`.
- Directorio de prueba: `~/workspace/dsh-prueba/` (quedó solo con `README.txt`; `hola.txt` no se creó).
- Logs de los intentos: `/tmp/dsh-humo-out.txt`, `/tmp/dsh-humo-err.txt` (400), `/tmp/dsh-humo-out2.txt`, `/tmp/dsh-humo-err2.txt` (413), `/tmp/dsh-humo-out3.txt`, `/tmp/dsh-humo-err3.txt` (429).
- Puente: `~/workspace/groq-proxy/proxy.py` (vivo en `:8080`, no se tocó).

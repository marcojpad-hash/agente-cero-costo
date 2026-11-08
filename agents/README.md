# Agentes canónicos (definición portable)

Cambio de arquitectura (2026-11-08): no necesitamos un agente
distinto por modelo. Compartimos la definición del agente y
cambiamos el motor que la ejecuta.

## Glosario

- **Agente:** definición de identidad, instrucciones,
  responsabilidades, procedimientos y criterios de éxito.
- **Skill:** procedimiento reutilizable que el agente puede cargar.
- **Harness:** entorno que ejecuta al agente (Claude Code, Codex,
  Gemini, OpenCode). Administra herramientas, contexto y ciclos.
- **Modelo:** motor de razonamiento (gpt-oss-120b, gemini-3-flash,
  etc.).
- **Memoria:** información persistente que permite continuar el
  trabajo (memoria-compartida + este repo).
- **Router:** selecciona el modelo o harness adecuado.
- **Protocolo:** permite que aplicaciones, herramientas y agentes se
  comuniquen (MCP para herramientas, ACP para aplicaciones).

El archivo `.md` es la fuente canónica del agente. No contiene sus
herramientas, permisos ni ejecución: eso lo ponen el harness y
`permissions.yaml`.

## Estructura

```
agents/
  sequential-verifiable/   # definición canónica (AGENT.md, workflow,
                           # success-metrics.md, permissions.yaml)
  registry.yaml            # registro de agentes canónicos
adapters/
  generar.py               # canónico -> claude.md, codex.toml, gemini.md
  verificar.py             # prueba: ningún adaptador pierde instrucciones
  salida/                  # archivos generados (no editar a mano)
```

## Proyectos revisados (2026-11-08)

Verificados contra sus repositorios, no solo por la descripción:

- **Agency Agents** (msitarzewski/agency-agents, MIT): definiciones
  de agentes que se instalan en Claude Code, Cursor, Codex, Gemini
  CLI, OpenCode y más. Es la demostración de que la definición
  portable funciona. Adoptar su patrón de conversión.
- **Everything Claude Code / ECC** (affaan-m/everything-claude-code,
  MIT): plataforma de trabajo para agentes (skills, hooks, reglas,
  memoria). Su Memory Vault comparte contexto entre harnesses, pero
  requiere instalar el runtime `ecc-universal`. Integrar
  selectivamente, no copiar el sistema entero.
- **Free Claude Code** (Alishahryar1/free-claude-code, **AGPL v3**):
  proxy de proveedores y modelos, multi-harness. Licencia
  **confirmada AGPL-3.0-only** leyendo su archivo LICENSE (la
  investigación anterior decía MIT y estaba mal). Evaluar como
  proxy, no copiar su código en nuestros repos sin respetar AGPL.
- **AnythingLLM** (Mintplex-Labs/anything-llm): enrutamiento
  dinámico de modelos, memoria, tareas programadas, MCP. Evaluar
  como capa de interfaz y gestión, no como núcleo.
- **Ruflo** (ruvnet/ruflo): harness de orquestación con memoria y
  federación, meta-harness para Claude Code y Codex. Prueba aislada
  antes de adoptar; sus cifras de ahorro no son garantías.

## Prioridad

Primero: que un mismo agente se ejecute en distintos harnesses con
la misma definición, memoria y métricas (esto es este directorio).
Después: conectar esos harnesses por WhatsApp y por el bus de
eventos. No esperar a que todos los modelos aprendan a hablar entre
ellos: que ejecuten el mismo contrato de trabajo y compartan sus
resultados.

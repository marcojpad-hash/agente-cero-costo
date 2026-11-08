# agente-cero-costo

Stack de agente a costo cero. La idea: que ningún modelo salga con que
no puede hacerlo. El harness es solo el loop; el modelo es un ingrediente
configurable; la máquina es la que tengas a la mano. Todo aquí corre sin
pagar DeepSeek, sin pagar VM y sin pagar API.

## La regla

Nunca decir que no se puede sin haber probado el análogo o el fallback y
sin haber dejado el intento en el repo. Cuando algo no se puede aquí, se
dice dónde sí se puede. Cada "no se puede" corregido se vuelve regla.

## Qué hay aquí

- `puente-groq/` — un puente local que deja usar la API gratuita de Groq
  sin que la clave salga nunca de la bóveda. dsh apunta al puente sin
  clave y el puente reenvía a Groq. Verificado: lista de modelos y chat
  con y sin stream.
- `dsh/` — DeepSeek Harness a costo cero: configuración del proveedor
  personalizado (Groq por el puente, o Groq directo, o Ollama local) y
  la verificación completa.
- `modelos/` — TwIL-8B: modelo abierto de 8.8B recién salido (nov 2026),
  qué promete, qué necesita de memoria y dónde cabe a costo cero.
- `orquestador/` — el coordinador de CAPCOT (gpt-oss-120b por Groq,
  gratis) y su workflow de GitHub Actions. Vive en CAPCOT; aquí va el
  apunte.

## Las piezas, en una línea cada una

- **Harness:** DeepSeek Harness (`npx @deepseek-ai/dsh`), developer
  preview. No es Claude Code: es el loop (planear, herramientas, repetir)
  y el modelo se configura aparte.
- **Modelo por API gratis:** `openai/gpt-oss-120b` por Groq (pesos
  abiertos, Apache 2.0, contexto 131072). Alternativa ligera:
  `openai/gpt-oss-20b`.
- **Modelo local:** TwIL-8B (webAI, 8.79B, licencia no comercial) por
  Ollama. Necesita ~10 GB de memoria en uso; en una VM de 7.7 GB no
  cabe. La máquina a costo cero que sí lo corre es Oracle Always Free
  ARM (4 vCPU, 24 GB RAM).
- **Máquina persistente a costo cero:** GitHub Actions en repo público
  (el orquestador corre diario a las 07:00 CDMX) o la VM de Pecas para
  pruebas.

## Reproducir

1. `python3 puente-groq/proxy.py --port 8080` (en la máquina que corre dsh).
2. `npx @deepseek-ai/dsh web`.
3. En dsh, Settings → Models → Add a custom provider, con los valores
   de `dsh/settings-puente.yaml`.
4. Elegir `openai/gpt-oss-120b` como modelo por defecto y abrir una
   sesión en un repo de prueba.

## Límites honestos

- **Groq gratis no alcanza para el loop del agente (medido 2026-11-08).**
  El loop de dsh sí funciona y el modelo planea bien las herramientas,
  pero el tier gratis de Groq tiene 8.000 TPM y el prompt de dsh ya pesa
  ~4.600 tokens por llamado: el segundo llamado da 429 y dsh lo trata
  como fatal. `hola.txt` no se creó en tres intentos. Ver
  `dsh/DSH_PRUEBA_HUMO.md`. El plan Developer (250.000 TPM) es de pago.
  La vía a costo cero que queda es Ollama local (sin TPM), que necesita
  memoria que esta VM no tiene.
- dsh es developer preview alpha/RC: habrá cambios que rompen
  compatibilidad y no está auditado para producción.
- La API gratuita de Groq tiene límites de velocidad; no es ilimitada.
- Lo verificado es la configuración y el puente; falta la prueba de una
  sesión larga de agente.
- TwIL-8B no tiene API hospedada y su licencia es no comercial.

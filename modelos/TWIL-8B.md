# TwIL-8B — modelo abierto de 8.8B, recién salido

Fecha: 2026-11-08. Fuentes: model card en Hugging Face y cobertura de
noviembre de 2026. Los benchmarks son de webAI, sin verificación
independiente.

## Qué es

**TwIL-8B** (webAI, publicado 2026-11-04): 8.79B parámetros, post-entrenado
de IBM Granite 4.2 8B, pesos abiertos en Hugging Face
(`webAI-Official/TwIL-8B`), contexto de 131.072 tokens, variantes
balanced (por defecto) y verbose. Razonamiento para matemáticas, código e
instrucciones.

## Lo que afirma (de ellos, sin verificar)

- MATH-500: 98.2; LiveCodeBench: 81.6 (variante verbose).
- ~93% del mejor modelo de frontera en código, 92% en instrucciones,
  90% en matemáticas de concurso.
- Débil en conocimiento: GPQA Diamond 70.2, MMLU-Pro 76.5, HLE 12.6.

## Licencia y disponibilidad

- Licencia **webAI Non-Commercial v1.0** (la base Granite es Apache 2.0).
  Uso para investigación y estudio, no para productos de pago.
- **Sin API hospedada**: no hay proveedor que lo sirva; solo se baja y
  se corre local.
- Pesos: bf16 ~16.4 GiB; Q4_K_M (GGUF) ~5 GiB.

## Qué necesita para correr

Prueba real (llama.cpp, Mac M4 Pro 24 GB, Q4_K_M): ~10 GB de memoria en
uso, ~36 tokens/s, 15 tareas de código en 65 minutos (Claude Haiku 5.5
hizo las mismas en 1.6 minutos y pasó 15/15; TwIL-8B pasó 11/15).

La VM de Pecas tiene 7.7 GB de RAM total y ~0.6 GB libre: **TwIL-8B no
cabe aquí**. El análogo a costo cero que sí lo corre es **Oracle Always
Free ARM: 4 vCPU y 24 GB de RAM**, con Ollama (`ollama pull` del modelo
y servidor en `http://localhost:11434/v1`).

## Con dsh

Ollama expone API OpenAI-compatible en `http://localhost:11434/v1`, así
que dsh lo usa como proveedor personalizado (ver `dsh/` para el esquema;
el `id` del modelo debe coincidir exacto con el tag de `ollama list`).

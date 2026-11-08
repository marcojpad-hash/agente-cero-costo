# La máquina, definida en el repo

Este directorio ES la máquina virtual que se pedía, pero en código: no
hay que crearla a mano, se reproduce desde aquí. Cualquier host que use
estas definiciones se vuelve la máquina agente.

## Dos formas de levantarla

1. **Docker** (donde haya Docker): `docker build -t agente-cero-costo
   -f maquina/Dockerfile .` y `docker run -p 8080:8080 agente-cero-costo`.
   El puente queda en `http://127.0.0.1:8080/v1` y dsh se corre con
   `npx @deepseek-ai/dsh web` (puerto 3080).
2. **VM limpia** (por ejemplo Oracle Always Free ARM, 24 GB): copiar
   `maquina/setup.sh` a la VM y correr `bash setup.sh`. Instala Python
   3.12, Node 24, git, ffmpeg, tmux, Ollama y el stack, y arranca el
   puente.

## Qué lleva

- Python 3.12, Node 24 (lo que pide dsh), git, ffmpeg, tmux.
- El puente Groq (`puente-groq/`), el orquestador (`orquestador/`) y la
  configuración de dsh (`dsh/`).
- Ollama opcional, para modelos locales (TwIL-8B).

## Qué NO lleva

- Pesos de modelos: TwIL-8B pesa ~5 GB en Q4 y ~16 GB completo; no van
  en la imagen ni en ningún repo (GitHub bloquea archivos de más de
  100 MB). Se bajan en ejecución con `ollama pull`.
- Claves: nunca van en la imagen ni en el repo. La de Groq vive en la
  bóveda y se usa por el conector (o por el puente, que la resuelve).

## Límites honestos

- Sin GPU: aquí el trabajo es texto, código y coordinación, no video.
- La VM de Pecas no tiene Docker y su swap no se puede ampliar (ver
  `memoria/swap.md`): esta imagen se prueba en la máquina que la corra,
  no aquí.

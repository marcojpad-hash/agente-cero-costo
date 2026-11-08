# Máquina del agente, definida en el repo
#
# Esta imagen ES la máquina virtual que se pedía: Linux + todas las
# herramientas del stack, definidas en código. Cualquier host que
# construya esta imagen (o corra maquina/setup.sh en una VM limpia) se
# vuelve la máquina agente: corre el puente, el orquestador y dsh, y
# trabaja en los repos como un agente que programa.
#
# No lleva pesos de modelos adentro (TwIL-8B pesa ~5-16 GB y no cabe en
# un repo ni en una imagen chica): los modelos se bajan en ejecución con
# Ollama, o se usan por API (Groq, gratis).
# Sin GPU: aquí el trabajo es texto, código y coordinación, no video.

FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates ffmpeg tmux \
    && rm -rf /var/lib/apt/lists/*

# Node 24 (lo que pide dsh)
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && node --version && npm --version

# dsh (DeepSeek Harness) por npx, sin instalar global: se corre con
# npx @deepseek-ai/dsh cuando hace falta.

WORKDIR /stack
COPY puente-groq/ ./puente-groq/
COPY orquestador/ ./orquestador/
COPY dsh/ ./dsh/

# Ollama (opcional, para modelos locales): se instala en ejecución con
# curl -fsSL https://ollama.com/install.sh | sh
# y el modelo se baja con: ollama pull <modelo>

EXPOSE 8080 3080

# 8080: puente Groq. 3080: Web UI de dsh.
CMD ["python3", "puente-groq/proxy.py", "--port", "8080"]

#!/usr/bin/env bash
# setup.sh — convierte una VM Linux limpia (Ubuntu/Debian) en la máquina
# agente. Es el mismo contenido del Dockerfile, pero para una VM real
# (por ejemplo la Oracle Always Free ARM de 24 GB, que sí corre TwIL-8B).
#
# Uso (en la VM, como usuario con sudo):
#   bash setup.sh
#
# Lo que instala: Python 3.12, Node 24, git, ffmpeg, tmux, Ollama
# (opcional) y el stack (puente + orquestador + dsh). No instala pesos
# de modelos: se bajan aparte con ollama pull.
set -euo pipefail

echo "== Máquina agente: instalando base =="
sudo apt-get update
sudo apt-get install -y git curl ca-certificates ffmpeg tmux python3 python3-pip

if ! command -v node >/dev/null 2>&1; then
  echo "== Instalando Node 24 =="
  curl -fsSL https://deb.nodesource.com/setup_24.x | sudo bash -
  sudo apt-get install -y nodejs
fi
node --version

if ! command -v ollama >/dev/null 2>&1; then
  echo "== Instalando Ollama (opcional, para modelos locales) =="
  curl -fsSL https://ollama.com/install.sh | sh
fi

echo "== Clonando el stack =="
mkdir -p ~/stack
cd ~/stack
if [ ! -d agente-cero-costo ]; then
  git clone https://github.com/marcojpad-hash/agente-cero-costo.git
fi
if [ ! -d baterias-tokens ]; then
  git clone https://github.com/marcojpad-hash/baterias-tokens.git
fi

echo "== Puente Groq (puerto 8080) =="
cd ~/stack/agente-cero-costo
nohup python3 puente-groq/proxy.py --port 8080 > puente.log 2>&1 &
echo "Puente en http://127.0.0.1:8080/v1 (revisar puente.log)"

echo "== dsh (DeepSeek Harness) =="
npx --yes @deepseek-ai/dsh --version
echo "Para arrancar dsh: cd ~/stack/agente-cero-costo && npx @deepseek-ai/dsh web"
echo "Proveedor: ver dsh/settings-puente.yaml (apunta al puente, sin clave)"
echo "== Listo =="

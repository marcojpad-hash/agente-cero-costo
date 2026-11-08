#!/bin/bash
# Arranca el bot de Telegram. El token se lee de la bóveda y se pasa
# por variable de entorno (nunca va en este archivo ni en el repo).
# Uso: TELEGRAM_BOT_TOKEN=... bash run.sh
set -e
cd "$(dirname "$0")"
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  echo "Falta TELEGRAM_BOT_TOKEN"
  exit 1
fi
exec python3 bot.py >> bot.log 2>&1

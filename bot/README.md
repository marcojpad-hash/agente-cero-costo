# Bot gestor (Telegram)

Un solo bot que habla por todos: tu mensaje (texto o voz) va a varios motores gratis en paralelo (Groq gpt-oss-120b, Groq gpt-oss-20b, Gemini 3.8 Flash, y OpenRouter si pones clave) y el **gestor final** (`PROMPT_GESTOR.md`) junta todo y te contesta con una sola voz. Comandos: `/motores`, `/estado`, `/reset`.

Necesita una máquina siempre prendida (la VM persistente o cualquier VM gratis). GitHub Actions no sirve para un bot 24/7.

## Tus únicos pasos
1. En Telegram, habla con **@BotFather** → `/newbot` → copia el token.
2. Claves gratis: **console.groq.com** (API Keys) y **aistudio.google.com** (Get API key).
3. Tu chat id: escríbele a **@userinfobot** y copia el número `Id`.

## Correr con Docker (un bloque)
```bash
git clone https://github.com/marcojpad-hash/agente-cero-costo && cd agente-cero-costo/bot
cp .env.example .env && nano .env   # pega token, chat id y claves
docker build -t bot-gestor . && docker run -d --restart=always --env-file .env -v bot-datos:/app/datos --name bot-gestor bot-gestor
```

## Correr con Python (un bloque)
```bash
git clone https://github.com/marcojpad-hash/agente-cero-costo && cd agente-cero-costo/bot
cp .env.example .env && nano .env   # pega token, chat id y claves
set -a && . ./.env && set +a && nohup python3 gestor.py > bot.log 2>&1 &
```

## Correr en la máquina siempre prendida (un bloque)
```bash
cd ~ && git clone https://github.com/marcojpad-hash/agente-cero-costo && cd agente-cero-costo/bot && cp .env.example .env && nano .env
mkdir -p ~/.config/systemd/user && cp gestor.service ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable --now gestor && loginctl enable-linger $USER
```
Sin systemd: `cd ~/agente-cero-costo/bot && set -a && . ./.env && set +a && nohup python3 gestor.py >> bot.log 2>&1 &`

Si un borrador dice "no se puede", el bot no lo manda: corre hasta 3 ciclos de resolución rotando motores. Solo si sigue bloqueado te llega un mensaje con botones **Acepto / No**.

Las claves viven solo en `.env` (no se sube al repo). Memoria y bitácora quedan en `datos/`.

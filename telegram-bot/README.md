# Bot de Telegram: el host en línea y el gestor final

El host que los modelos pueden alcanzar y la voz que habla por
todos ellos. No necesita servidor público ni puertos de entrada: el
bot consulta a Telegram por polling (salida HTTPS), así que corre
en la VM de Pecas.

## La arquitectura: Router/Aggregator

Tres capas, como el motor de DeepSeek que describe Marco: varios
motores y un gestor final que reúne todo.

1. **Recepción:** este bot en Telegram. Recibe la pregunta.
2. **Procesamiento:** los motores, en paralelo (ver `agregador.py`).
   - Groq `openai/gpt-oss-20b`: razonamiento y respuesta corta.
   - Gemini `gemini-3-flash-preview`: contexto grande y verificación.
3. **Gestión final:** el gestor, Groq `openai/gpt-oss-120b` con el
   system prompt del gestor. Lee la pregunta y las respuestas de los
   motores, quita contradicciones y repeticiones, y da UNA respuesta
   clara y directa. Nunca menciona a los otros motores; no inventa
   datos ni fuentes.

Cualquier mensaje que no sea comando es una pregunta: el bot
consulta a los motores y responde con la voz del gestor.

## El intérprete

`/interpretar <texto>`: toma la respuesta de otro modelo (Grok,
ChatGPT, el que sea), la pasa por el gestor y la devuelve en una
sola voz. Este bot es de Marco: él es el dueño (lo crea en
@BotFather con su cuenta), y el bot interpreta a cualquier otro.

## Voz (gratis, offline, 2026-11-08)

El bot también escucha y habla. Mándale un mensaje de voz y te
contesta con voz.

- **Entender:** faster-whisper `base` en español (open source,
  offline). La voz de Telegram llega en ogg opus; ffmpeg la pasa
  a wav 16 kHz mono y faster-whisper la transcribe.
- **Contestar:** el agregador (Groq + Gemini, gratis) responde y
  Piper `es_MX-ald-medium` (offline) la dice; ffmpeg la pasa a
  ogg opus y se manda con `sendVoice`.
- Todo corre en la VM de Pecas, sin pagar nada. Piper y
  faster-whisper viven en `~/workspace/piper-venv/` (el venv ya
  tiene los dos). `voz.py` es el módulo; `bot.py` lo usa si está
  disponible y sigue sin voz si no lo está.
- Detalle: faster-whisper 1.2.1 con av 19 falla en `decode_audio`
  (`metadata_errors`); por eso `voz.py` decodifica con ffmpeg +
  `wave` a un arreglo numpy y se lo pasa a `transcribe`, no la
  ruta. Probado: Piper genera la voz y faster-whisper base la
  transcribe bien en español (solo los nombres propios raros como
  "Mpemba" salen deformados).
- Medición objetiva (`medir_voz.py`, escrita por Gemini): la voz
  de Piper sale a 0 dBFS de pico (muy fuerte) y tono medio
  (162–167 Hz). `voz.py` la baja 6 dB (`volume=0.5`) antes de
  mandarla: queda en −6 dB de pico, −19 dB RMS, tono medio,
  LISTA: SI. Sin una voz de referencia no se puede medir si "se
  parece" a otra voz; lo que se mide es su propio tono y volumen.

## Qué hace

- Pregunta en texto libre: responde con la voz del gestor final.
- Mensaje de voz: lo transcribe, consulta a los motores y te
  contesta con voz.
- `/interpretar <texto>`: interpreta la respuesta de otro modelo.
- `/estado`: estado vigente del equipo.
- `/memoria`: resumen público de la memoria.
- `/bus`: últimos eventos del bus.
- Un bloque `[EMITIR]` por mensaje: lo aplica al bus y lo sube a
  GitHub. Esa es la vía de emisión para cualquier modelo que pueda
  escribirle al bot en Telegram.

## Cómo se crea (lo hace Marco, 1 minuto, gratis)

1. En Telegram, busca `@BotFather` y mándale `/newbot`.
2. Ponle nombre (p. ej. `Equipo Cero Costo`) y usuario (tiene que
   terminar en `bot`, p. ej. `equipo_cero_costo_bot`).
3. BotFather te da el token. **No lo pegues en ningún chat.**
   Pégalo en la entrada segura que te da Pecas (bóveda).

## Cómo arranca

Con el token en la bóveda, Pecas lo arranca en su VM:

```
TELEGRAM_BOT_TOKEN=... python3 telegram-bot/bot.py
```

O con el servicio (reinicia solo si se cae):

```
systemctl --user enable --now telegram-bot.service
```

## Quién puede entrar a Telegram (verificado 2026-11-08)

Revisado por búsqueda antes de pedir la clave a BotFather:

- **Grok: sí, el único con bot oficial.** @GrokAI, verificado, del
  acuerdo xAI–Telegram de mayo 2025 (300 M USD). Es un chat 1:1
  para el usuario, no un bot que se meta a nuestro grupo ni que le
  hable a nuestro bot. Una prueba de octubre 2026 lo encontró
  silencioso (no respondió), así que su fiabilidad no está
  garantizada.
- **ChatGPT: no.** No hay bot oficial. Solo envoltorios de terceros
  (p. ej. @GPT4Telegrambot), de pago, con tope, y no son el ChatGPT
  de Marco: son otro bot con la API. Su superficie oficial de
  mensajería es WhatsApp, no Telegram.
- **Gemini: no.** No hay bot oficial. Solo envoltorios de terceros.
- **Copilot: no.** Tenía bot oficial verificado (@CopilotOfficialBot)
  pero salió de Telegram en enero de 2026 y está apagado.
- **Claude, DeepSeek: no.** Solo envoltorios de terceros.

## Por qué nuestro bot no puede hablar directo con los bots de los modelos

Por defecto, un bot nunca ve los mensajes de otro bot (regla de
Telegram contra bucles). Telegram sí tiene ahora un modo de
comunicación bot-a-bot (se activa en @BotFather), pero solo funciona
entre bots cuyos dueños lo activan. Nosotros no somos dueños del bot
de Grok ni de ningún modelo, así que no podemos activarlo en ellos.

## Entonces, ¿cómo se meten todos?

Por el bus. Nuestro bot lee el bus y escribe en él; los modelos
leen el bus por el resumen público y emiten por el bloque [EMITIR]
o por Issue. Telegram es la puerta en vivo para Marco (y para Grok
en 1:1); el bus sigue siendo el punto de encuentro universal. El
bot es una puerta, no toda la casa.

- El bot corre en la VM de Pecas. Si la VM se reemplaza, el bot se
  detiene hasta que Pecas lo vuelva a arrancar. No es un servidor
  dedicado; es un host en línea que se mantiene con un arranque.
- El token es un secreto: va en la bóveda, nunca en el repo ni en
  el chat.
- El bot no sustituye al bus ni a la memoria: es la puerta de
  entrada en vivo a ellos.

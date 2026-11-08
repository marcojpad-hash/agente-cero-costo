# Bot de Telegram: el host en línea

El host que los modelos pueden alcanzar. No necesita servidor
público ni puertos de entrada: el bot consulta a Telegram por
polling (salida HTTPS), así que corre en la VM de Pecas.

## Qué hace

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

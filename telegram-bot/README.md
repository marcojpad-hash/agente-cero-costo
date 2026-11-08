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

## Límites honestos

- El bot corre en la VM de Pecas. Si la VM se reemplaza, el bot se
  detiene hasta que Pecas lo vuelva a arrancar. No es un servidor
  dedicado; es un host en línea que se mantiene con un arranque.
- El token es un secreto: va en la bóveda, nunca en el repo ni en
  el chat.
- El bot no sustituye al bus ni a la memoria: es la puerta de
  entrada en vivo a ellos.

# Organigrama de modelos (costo cero para el Grok Bot)

Regla: Puta3 (Grok Bot) NO programa. Solo deja órdenes en el bus y revisa por encima.
Bus: Issues con título `[BUS] indicacion - <emisor>` (tipos válidos: actualizacion, indicacion, aviso, hecho). Cuerpo con `para:` `tipo:` `mensaje:`.

| Rol | Quién | Cuándo | Cómo recibe / entrega |
|---|---|---|---|
| Coordinador (solo órdenes y revisión) | Puta3 (Grok Bot) | cuando Mj escribe | deja Issues `[BUS] indicacion - Puta3` |
| Programador principal | Grok en grok.com (SuperGrok, automatización "Obrero de Mj — GitHub bus") | diario 9:00 CDMX | lee conector/bus/, rama + PR sin merge, cierra con `[BUS] hecho - Grok` |
| Motor U6 (diseño y revisión) | ChatGPT (lo maneja Mj directo) | cuando Mj lo abre | lee el repo motor-u6-storage; deja informes en informes/ |
| Ayudantes de código gratis | Groq (gpt-oss-20b/120b, qwen, Whisper) | bajo demanda de Grok o del Gestor | API gratuita, clave solo en el servidor, nunca en el repo |
| Interfaz con Mj | Gestor Mj @gestor_mj_bot (Telegram, Groq gratis) | siempre prendido | Mj le dicta; los bloques [EMITIR] se suben al bus |
| CAPCOT cápsulas | bots Imaginantes / CAPCOT Métricas / Pantallas | sus horarios propios | sin cambios |

Prohibido para todos: tocar Engine/244, merge a main sin "merge" de Mj, claves en el repo (es público), cambiar la voz JorgeNeural, inventar datos.

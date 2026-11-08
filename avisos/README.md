# Avisos

El callback de actualización. Cada vez que se da una indicación o
cambia la información, se avisa: los otros modelos, aunque no estén en
la interacción directa con el usuario, reciben la indicación de que hay
actualización. Así, si el usuario cambia de aplicación, el modelo que
le toque ya tiene los datos actualizados.

## Cómo funciona

Patrón verificado por búsqueda (2026-11-08): Hermes Agent usa un
**watermark** y polling; Composio inyecta el issue en el prompt del
agente; IssueClaw y harnext usan Issues + Actions. Nadie empuja nada
dentro de un modelo de API: el aviso es el watermark + el contexto
inyectado.

1. `avisar.py "mensaje"` escribe la actualización en
   `ACTUALIZACIONES.md` (solo se agrega, nunca se borra).
2. Sube `VERSION` (el watermark): cualquier modelo compara su copia
   con este número y sabe si está desactualizado.
3. Regenera `ULTIMA_ACTUALIZACION.md` (la nota corta que se adjunta a
   cada encargo) y el paquete de transmigración.
4. Los canales que leen el repo ven la actualización en su siguiente
   corrida: orquestador diario, relevo cada hora. El issue de GitHub
   (workflow `avisos.yml`, por navegador) la publica para Copilot.

## Los modelos de API no tienen buzón

Gemini y Groq no reciben notificaciones: su aviso es el contexto que
la sanguijuela adjunta automáticamente a cada encargo (versión +
últimas actualizaciones). Por eso la sanguijuela ya no depende de que
el orquestador se acuerde de poner el contexto: viaja solo.

## Uso

```bash
python3 avisar.py "Se reprogramó la cápsula Mpemba para el 9-nov 07:00"
```

## Límites honestos

- El aviso no es instantáneo para los agentes programados: lo ven en
  su siguiente corrida (orquestador diario, relevo cada hora).
- El issue de GitHub necesita el workflow `avisos.yml` subido por
  navegador (la app no tiene permiso Workflows).
- El registro es solo del stack agente-cero-costo. El tablero de
  CAPCOT tiene su propio aviso (callback-aviso.yml); los dos registros
  no se fusionan solos: el orquestador los lee a los dos.

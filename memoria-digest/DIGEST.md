# Memoria compartida (resumen público)

Generado: 2026-11-08 05:28. Fuente: repo privado memoria-compartida (sigue privado). Este archivo es público: solo lleva hechos del proyecto, sin datos personales, sin claves, sin secretos.

Lee `INDICE.md` en el repo privado si tienes acceso; si no, este resumen es lo vigente.

# Proyectos

- **CAPCOT** (marcojpad-hash/capcot-capsulas-imaginantes, público):
  cápsulas científicas verticales 9:16 de 60-90 s, serie «Datos y
  ociosidades», en español es-MX. Imaginantes monta el MP4 oficial
  con voz es-MX-JorgeNeural, corre QA y programa.
- **Motor U6** (marcojpad-hash/motor-u6-storage, privado): proyecto
  aparte, no parte de CAPCOT. Engine V5 canónico y catálogo 244 son
  la referencia fija.
- **agente-cero-costo** (público): stack de agente a costo cero —
  puente Groq, dsh, orquestador, puente de lectura, máquina en el
  repo, transmigración, sanguijuela, avisos, conector.
- **baterias-tokens** (privado): proveedores gratuitos, rotación,
  puente Groq, protocolo de relevo.
- **baterias-memoria** (privado): máquinas, modelos y memoria.
- **ChatGPT-migracion** (privado): bandeja entre modelos.
- **orquestador-central** (público): contrato transversal
  multi-modelo; lo está armando alguien más.
- **memoria-compartida** (privado, este repo): la memoria persistente
  y consistente de los modelos.

# Decisiones

- El motor U6 y CAPCOT son dos proyectos diferentes. El callback no
  va en el motor. (2026-11-07)
- El montaje oficial, QA y programación son de Imaginantes. Pecas no
  monta MP4 final ni publica. (2026-11-06)
- Todo el contenido CAPCOT en español es-MX. (2026-11-06)
- No inventar datos, fuentes ni DOIs. (siempre)
- La app de GitHub no tiene permiso Workflows: los workflows van por
  navegador con la cuenta de Marco. (2026-11-07)
- Las claves guardadas no se pueden leer de vuelta: se usan por
  conector, nunca se pegan en un repo. (2026-11-07)
- El relevo: cuando el agente se queda sin tokens, gpt-oss-120b toma
  el tablero en Actions cada hora. (2026-11-08)
- El que orquesta no gasta sus tokens: el trabajo pesado lo hacen los
  gratuitos (sanguijuela). (2026-11-08)
- Cada indicación o cambio genera un aviso con versión (avisos).
  (2026-11-08)
- No se clona el personaje, se clonan las capacidades
  (transmigración). (2026-11-08)
- Los modelos que viven en su app leen el estado público y emiten
  con el bloque [EMITIR] (conector). (2026-11-08)

# Correcciones

Lo que se corrigió y qué reemplaza. Un hecho viejo no se borra: se
marca como reemplazado.

- **La app de GitHub SÍ puede crear repos por API** si tiene el
  permiso `Repository creation`. Reemplaza: "la creación de repos no
  se puede automatizar". Lo que falta es el permiso, no la
  capacidad. (2026-11-08, investigación)
- **El motor SÍ tiene 8 workflows en GitHub Actions.** Reemplaza:
  "CAPCOT y el motor no tienen automatización". CAPCOT tiene cero.
  (2026-11-07, auditoría)
- **La cola CAPCOT tiene 16 paquetes**, no 14. (2026-11-08)
- **Free Claude Code: licencia por verificar.** La investigación
  decía MIT; el puente la leyó como AGPL v3. No copiar nada de FCC
  hasta verificar. (2026-11-08)
- **Cerebras NO es $0 permanente.** Desde 2026-07-16 es Free Trial
  con tarjeta, $5, 30 días. Reemplaza: "Cerebras gratis".
  (2026-11-08, investigación)
- **El texto del issue de escala está desactualizado**: dice que la
  creación de repos "no se puede automatizar". Ver la primera
  corrección de esta lista. (2026-11-08)

# Tokens

- Muse gratis: 100% usado al 2026-11-07, reinicio 2026-11-13 a las
  17:24 CST. Fondo aparte de tokens adicionales: 2% usado, 983M
  restantes. La generación de video es el principal costo.
- Groq gratis: 8.000 TPM. El prompt de dsh pesa ~4.600 tokens: la
  segunda llamada da 429. (2026-11-08, prueba de humo)
- Gemini gratis: 1M TPM (según IssueClaw). Es el primario para
  tareas largas.
- El trabajo de texto va con Gemini/Groq, no con el modelo caro.
  El montaje no cuesta tokens.

# Estado

Foto del 2026-11-08. El estado vivo está en el tablero de CAPCOT
(ajustes_entre_modelos/DELEGACIONES.md) y en el estado público
(agente-cero-costo, conector/ESTADO.md).

## Pendientes (tablero CAPCOT, 5)

1. Montar la cápsula Mpemba (Imaginantes, pausado por créditos).
2. Montar la cápsula Barreleye con 2 arreglos de texto (Imaginantes,
   pausado por créditos).
3. Subir los workflows de seguridad de CAPCOT (Marco, por navegador).
4. Activar la seguridad nativa en GitHub (Marco, manual).
5. Crear cuenta gratuita de Clayzo (Marco).

## Stack agente-cero-costo (versión 4, 2026-11-08)

Transmigración v0.1, sanguijuela, avisos v4, conector macho-hembra,
estado público (el foquito), puente de lectura, puente Groq,
orquestador, dsh, máquina en el repo.

# Personas

Roles, sin datos personales. Nada de correos, claves ni cuentas aquí.

- **Marco**: el usuario. Solo celular Android, sin computadora.
  Dicta por voz: las palabras salen deformadas; interpretar por
  contexto. Sus mensajes son analogías, no especificaciones exactas.
  Prefiere que se resuelva sin preguntar y prefiere duplicados antes
  que algo falte.
- **Pecas**: el agente. Coordina, prepara borradores y paquetes,
  verifica. No monta el MP4 final ni publica.
- **Imaginantes**: monta el MP4 oficial con voz es-MX-JorgeNeural,
  corre QA oficial y programa/publica.
- **ChatGPT / Grok**: modelos externos que investigan y preparan
  paquetes en la cola de CAPCOT.
- **Copilot**: modelo nativo de GitHub con el encargo del repo
  CAPCOT.


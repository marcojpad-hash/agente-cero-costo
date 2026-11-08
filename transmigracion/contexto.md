# Contexto
Foto del estado tomada el 2026-11-08 04:48 por empaquetar.py.
## Quiénes somos
- **Marco Antonio Juárez (Marco)**: solo celular Android, sin computadora. Depende del agente para GitHub, subidas y YouTube Studio. Dicta por voz: las palabras salen deformadas; interpretar por contexto.
- **Pecas**: el agente. Coordina, prepara borradores y paquetes, verifica. No monta el MP4 final ni publica.
## Proyectos
- **CAPCOT** (marcojpad-hash/capcot-capsulas-imaginantes, público): cápsulas científicas verticales 9:16 de 60-90 s, serie «Datos y ociosidades», en español es-MX. Imaginantes monta el MP4 oficial con voz es-MX-JorgeNeural, corre QA y programa.
- **Motor U6** (marcojpad-hash/motor-u6-storage, privado): proyecto aparte, no parte de CAPCOT. Engine V5 canónico y catálogo 244 son la referencia fija.
- **agente-cero-costo** (este repo, público): stack de agente a costo cero — puente Groq, dsh, orquestador, puente de lectura, máquina en el repo, transmigración.
- **baterias-tokens** (privado): proveedores gratuitos, rotación, puente Groq, protocolo de relevo.
- **baterias-memoria** (privado): máquinas, modelos y memoria.
- **ChatGPT-migracion** (privado): bandeja entre modelos.
- **orquestador-central** (público): contrato transversal multi-modelo; lo está armando alguien más. No confundir con el orquestador de este repo.
## Tablero (delegaciones pendientes)
Fuente: copia local de CAPCOT, archivo del 2026-11-07 23:46. Si la copia es vieja, hacer git pull y regenerar.

# Delegaciones entre modelos

Tablero vivo del callback. Quien delega escribe aquí. Quien recibe lee aquí.
Reglas en `PROTOCOLO_CALLBACK.md`.

Este tablero es de CAPCOT. El motor U6 es un proyecto aparte y no lleva
delegaciones aquí. Si el callback se implementa en el motor después, será
su propio tablero.

## Pendientes

### 1. Montar la cápsula Mpemba
- DE: ChatGPT / Grok
- PARA: Imaginantes
- QUÉ: montar el MP4 oficial con voz es-MX-JorgeNeural, correr QA oficial y programar. Paquete en `cola/entrada/2026-11-07_comida-hielo-caliente/`
- PARA CUÁNDO: slot 2026-11-07 13:30 (ya pasó; reprogramar)
- ESTADO: PENDIENTE
- NOTA: Imaginantes pausado por ahorro de créditos

### 2. Montar la cápsula Barreleye
- DE: ChatGPT / Grok
- PARA: Imaginantes
- QUÉ: montar el MP4 oficial con los 2 arreglos de texto (scene_002: "frente a la costa de California"; scene_004: quitar "verdes" o citar Robison y Reisenbichler 2008), correr QA oficial y programar. Paquete en `cola/entrada/2026-11-07_barreleye-4k/`
- PARA CUÁNDO: primera cápsula de la semana 8-14 nov (propuesto, sin confirmar)
- ESTADO: PENDIENTE
- NOTA: Imaginantes pausado por ahorro de créditos

### 3. Subir los workflows de seguridad de CAPCOT
- DE: Pecas
- PARA: Marco (por navegador, la app de Muse no tiene permiso Workflows)
- QUÉ: subir `gitleaks.yml` y `semgrep.yml` (CAPCOT). Archivos listos en `~/workspace/security-upload/`
- PARA CUÁNDO: cuanto antes
- ESTADO: PENDIENTE

### 4. Activar la seguridad nativa en GitHub
- DE: Pecas
- PARA: Marco (manual en Settings)
- QUÉ: secret scanning y CodeQL en CAPCOT, alertas de Dependabot en CAPCOT
- PARA CUÁNDO: cuanto antes
- ESTADO: PENDIENTE

### 5. Crear cuenta gratuita de Clayzo
- DE: Pecas
- PARA: Marco
- QUÉ: crear la cuenta gratuita para probar el render del documento Mpemba (1080x1920, capas de texto/dato/mapa)
- PARA CUÁNDO: sin fecha
- ESTADO: PENDIENTE

## En progreso

(nada)

## Hechas

(nada registrado aún en este tablero)

## Decisiones y correcciones
- El motor U6 y CAPCOT son dos proyectos diferentes. El callback no va en el motor.
- El montaje oficial, QA y programación son de Imaginantes. Pecas no monta MP4 final ni publica.
- Todo el contenido CAPCOT en español es-MX.
- No inventar datos, fuentes ni DOIs.
- La app de GitHub no tiene permiso Workflows: los workflows van por navegador con la cuenta de Marco. La app sí puede crear repos por API si tiene el permiso Repository creation.
- Las claves guardadas no se pueden leer de vuelta: se usan por conector, nunca se pegan en un repo.
- El relevo: cuando el agente se queda sin tokens, gpt-oss-120b toma el tablero en Actions cada hora.
## Tokens (foto)
- Muse gratis: 100% usado al 2026-11-07, reinicio 2026-11-13 a las 17:24 CST. Fondo aparte de tokens adicionales: 2% usado, 983M restantes. La generación de video es el principal costo; el texto va con Gemini/Groq.
- Groq gratis: 8.000 TPM. El prompt de dsh pesa ~4.600 tokens: la segunda llamada da 429.
- Gemini gratis: 1M TPM (según IssueClaw). Es el primario para tareas largas.

Skill de cómo trabajar con Marco: archivo del 2026-11-08 02:10.

Este paquete no lleva claves, contraseñas ni datos personales.

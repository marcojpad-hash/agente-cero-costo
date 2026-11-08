# Permisos: quién puede qué

Auditoría del 2026-11-08. La pregunta: ¿tienen permiso los demás
modelos, o solo el que lo creó? Respuesta corta: **leer el repo
público sí pueden todos; emitir por Issue solo los que tienen
escritura en GitHub; la memoria privada solo la leen por la conexión
autorizada de Marco.**

## Leer (recibir)

| Modelo | agente-cero-costo (público) | memoria-compartida (privado) |
|---|---|---|
| Cualquiera con navegación (ChatGPT, Grok, Gemini) | Sí, por la URL cruda | Solo con el vínculo autorizado |
| Grok con el conector GitHub conectado | Sí | Sí, si Marco autorizó ese repo |
| ChatGPT con la app de GitHub autorizada por Marco | Sí | Sí, si Marco autorizó ese repo |
| Gemini con Import code (manual, computadora) | Sí | Sí, un repo por chat, congelado |
| Copilot (en GitHub) | Sí | Sí |
| Pecas (app de GitHub) | Sí | Sí |

El repo público se lee por web sin cuenta. El privado solo lo lee
quien tenga acceso autorizado: Marco, la app de Muse, Copilot, y
cualquier modelo cuya conexión de GitHub haya autorizado Marco para
ese repo. Los pasos y la prueba de cada vínculo están en
`VINCULOS.md`.

## Emitir (crear un Issue `[BUS]`)

El workflow `github-native-agent-bus.yml` solo acepta Issues cuyo
autor sea OWNER, MEMBER o COLLABORATOR. No se agregó ningún
colaborador a estos repos: solo Marco es propietario.

| Modelo | Puede crear el Issue | Si no, cómo emite |
|---|---|---|
| Marco (navegador) | Sí (OWNER) | — |
| Pecas (app de GitHub) | Sí (actúa como marcojpad-hash) | — |
| Copilot (agente de código) | Sí (tiene escritura en el repo) | — |
| Grok con el conector GitHub conectado | Sí (el conector tiene escritura en issues) | Bloque [EMITIR] |
| ChatGPT, app estándar de GitHub | No (la app es de solo lectura, verificado 2026-11-08) | Bloque [EMITIR] |
| ChatGPT vía Codex | Sí (Codex escribe) | — |
| Gemini, app | No (sin escritura en GitHub; solo Import code) | Bloque [EMITIR] |

Corrección del 2026-11-08 ~05:24: antes se dijo que Grok no podía
emitir. Verificado por búsqueda: el conector GitHub de Grok
(`grok.com/connectors`) tiene lectura y escritura, incluyendo
issues, y funciona en el nivel gratis. Una vez conectado y autorizado
el repo, Grok sí puede crear el Issue `[BUS]`.

## El fallback universal

Cualquier modelo puede emitir con el bloque `[EMITIR]` (ver
`emitir-bloque.md`): lo produce, el usuario pega la respuesta y
`aplicar.py` la escribe en el bus. Esa vía no necesita permiso de
escritura en GitHub y funciona para todos.

## La restricción que sí hay que decidir

La memoria compartida (`memoria-compartida`) es privada. Eso protege
la privacidad, pero un modelo sin la conexión autorizada no la puede
leer. Dos vías, decide Marco:

1. **Queda privada y se autoriza por app**: en cada modelo (ChatGPT,
   etc.) Marco autoriza la app de GitHub para ese repo. Más trabajo,
   más privacidad.
2. **Se hace pública**: no tiene secretos ni datos personales, solo
   hechos del proyecto. Entonces cualquier modelo la lee por la URL
   cruda, igual que el estado público. Más simple, menos privado.

## Qué no se puede verificar desde aquí

- Si Marco ya autorizó la app de GitHub en ChatGPT/Grok/Gemini y para
  qué repos. Eso solo se ve en cada aplicación, y solo Marco lo puede
  confirmar.
- La lista de colaboradores no se pudo leer por API desde aquí (la
  herramienta exige aprobación); lo que sí se sabe es que nunca se
  agregó a nadie: los repos los crearon Marco y Pecas y nadie más
  fue añadido.

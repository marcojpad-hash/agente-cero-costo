# Vínculos: cómo cada app se conecta al repo

La memoria queda privada y se autoriza por app. Cada app tiene su
vínculo. Aquí están los pasos y la prueba para cada una. Solo Marco
puede autorizar en sus apps: la autorización vive en su cuenta, no
en el repo.

## Grok — sí tiene vínculo (conector GitHub)

- Dónde: `grok.com/connectors` → pestaña Connectors → tarjeta GitHub
  → Connect.
- Qué autorizar: **Only select repositories** y marca
  `memoria-compartida` y `agente-cero-costo`. (No "All repositories"
  si no quieres darle todo.)
- Qué puede: leer repos y código, ver issues y PRs, y escribir
  (crear issues, ramas, subir archivos). Es el MCP de GitHub, no
  solo lectura. Funciona en el nivel gratis.
- Prueba: en un chat nuevo con Grok, pídele: "lee el archivo
  INDICE.md del repo privado marcojpad-hash/memoria-compartida y
  dime qué temas tiene". Si lo lee, el vínculo funciona. Si dice que
  no tiene acceso, falta autorizar el repo.
- Emitir: una vez conectado, Grok puede crear el Issue `[BUS]` él
  mismo (tiene escritura en issues). Si no, usa el bloque [EMITIR].

## ChatGPT — sí tiene vínculo (app de GitHub + Codex)

- App estándar: conecta GitHub en ChatGPT y autoriza los repos
  (`memoria-compartida` y `agente-cero-costo`). Es **de solo
  lectura**: lee el repo, no escribe. Sirve para recibir.
- Codex: conecta en `chatgpt.com/codex` y autoriza el repo. Codex
  **sí escribe**: puede crear issues, ramas, archivos y PRs. Sirve
  para emitir y para programar.
- Prueba (app): "lee el archivo INDICE.md del repo privado
  marcojpad-hash/memoria-compartida y dime qué temas tiene".
- Emitir (app estándar): no puede crear el Issue; usa el bloque
  [EMITIR]. Emitir (Codex): crea el Issue `[BUS]` directamente.

## Copilot — sí tiene vínculo (está en GitHub)

- Vive dentro de GitHub: lee y escribe en los repos que tiene
  asignados. Puede crear el Issue `[BUS]` y puede programar.
- Pendiente: activar su agente de código en Settings > Copilot.

## Gemini — vínculo débil (importar código, manual)

- En la app/web: Add files → More uploads → Import code, con la
  cuenta de GitHub vinculada. Lee el repo (solo lectura), un repo
  por chat, y queda congelado: hay que re-importar para refrescar.
- Límite: es manual por chat y, según la documentación, solo en
  computadora. En el celular de Marco probablemente no está.
- Prueba: importa `memoria-compartida` y pregúntale por el índice.
- Emitir: no puede crear el Issue; usa el bloque [EMITIR].

## Pecas (Muse) — sí tiene vínculo (app de GitHub)

- La app de Muse tiene acceso a todos los repos, lee y escribe
  código, issues y PRs. Lee la memoria privada y emite por Issue o
  por el bus. No tiene permiso Workflows (los workflows van por
  navegador).

## Si una app no tiene vínculo

Recibe por la URL pública del estado (versión + última
actualización) y emite por el bloque [EMITIR]. Eso funciona para
todas, sin autorización. El vínculo completo (leer la memoria y
emitir por Issue) necesita la autorización de arriba.

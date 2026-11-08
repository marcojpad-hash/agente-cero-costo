# Conector de agentes

El contrato y el estado público están en:
- Estado vigente: ESTADO.md
- Instrucción para emitir desde un chat: emitir-bloque.md

El conector tiene dos modos compatibles:

1. **Universal, sin instalación:** cualquier modelo con navegación lee la URL pública; cuando no tiene escritura GitHub, produce un bloque [EMITIR] que se aplica mediante aplicar.py.
2. **Bidireccional MCP:** hosts compatibles usan puente_mcp.py y SQLite para publicar/recibir mensajes, recuperar continuidad en una llamada y confirmar ACK.

La implementación MCP y sus límites están documentados en PUENTE_UNIFICADO.md. El bus Git público y SQLite no se sincronizan automáticamente todavía: no confundir ambos almacenes.

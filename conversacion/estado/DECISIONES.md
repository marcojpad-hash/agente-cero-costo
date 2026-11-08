# Decisiones vigentes

1. Cada agente conserva su runtime, sistema operativo, identidad y credenciales.
2. La interoperabilidad ocurre mediante contratos abiertos y adaptadores; no se fuerza un sistema operativo común.
3. Todo evento de repositorio autorizado se considera input de trabajo para los agentes suscritos.
4. El evento se persiste antes de confirmar recepción; la entrega es al menos una vez y debe deduplicarse.
5. GitHub y el diario son memoria durable; WhatsApp es transporte conversacional, no repositorio de verdad.
6. La conversación solo se registra automáticamente si el cliente que la contiene publica sus turnos reales al endpoint de ingesta.
7. No se declaran agentes conectados hasta probar recepción, ejecución, ACK y persistencia.
8. No guardar credenciales, QR ni tokens en Git.
9. No modificar main ni fusionar PR sin autorización explícita.

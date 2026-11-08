# VM Linux compartida para agentes

Estado: **preparación lista; VM real todavía no identificada ni provisionada**.

## Objetivo
Una sola máquina Linux persistente para agentes autorizados. Cada agente entra con su propia cuenta SSH; todos comparten un espacio de trabajo común. GitHub sigue siendo el plano de coordinación y versionado. La VM aporta ejecución Linux, dependencias y almacenamiento persistente.

No todos los chats tienen SSH o terminal. Un agente solo puede conectarse si su host ofrece SSH/SFTP o un adaptador equivalente y tiene una clave propia instalada de forma segura.

## Diseño
- `/srv/agentes/compartido`: archivos comunes del grupo Linux `agentes`.
- `/srv/agentes/repos`: clones y áreas de trabajo.
- Una cuenta Linux por agente; no compartir usuarios ni claves privadas.
- Claves públicas por agente en `/root/agent-keys/<usuario>.pub` durante el bootstrap.
- Claves privadas solo en el almacén seguro del entorno que se conecta.
- GitHub bus: coordinación y registro; VM: ejecución y archivos.
- Ningún secreto ni clave privada se guarda en Git.

## Preparación
Recomendación inicial: Ubuntu Server 24.04 LTS x86_64, 2 vCPU, 4 GB RAM y 40 GB SSD como punto de partida; ajustar tras medir cargas. Se requiere IP/DNS estable y SSH limitado por firewall a orígenes autorizados.

1. Crear la VM en el proveedor elegido y conservar acceso administrativo de recuperación.
2. Copiar `infra/vm/bootstrap.sh` a la VM.
3. Generar una clave SSH por agente en el propio entorno de ese agente. Copiar únicamente la clave pública a `/root/agent-keys/<usuario>.pub`.
4. Ejecutar como root: `sudo AGENT_USERS="chatgpt,muse,gemini,grok,copilot" bash infra/vm/bootstrap.sh`.
5. Probar cada agente desde su entorno real; una prueba no demuestra conectividad de los demás.
6. Clonar repositorios necesarios en `/srv/agentes/repos` con deploy keys limitadas o credenciales de solo lectura.
7. Registrar solo resultados en `infra/vm/REGISTRO_CONEXIONES.md`; nunca claves ni tokens.

## Controles
- Crear esta rama no crea ni paga una VM.
- No hay proveedor, IP/DNS ni claves privadas configuradas todavía; no se declara máquina activa.
- SSH por clave, cuenta individual y permisos mínimos. Configurar firewall y actualizaciones antes de exponer SSH.
- Acceso a la VM no autoriza por sí mismo cambios en repositorios protegidos, publicación, compras ni acciones externas.
- Respaldar `/srv/agentes/compartido` y los repositorios de trabajo.

## Criterio de aceptación
1. VM persistente e IP/DNS verificados.
2. Dos agentes distintos conectan con cuentas y claves distintas.
3. Ambos leen y escriben un archivo de prueba en `/srv/agentes/compartido`.
4. Los cambios sobreviven a reconexión y reinicio.
5. El registro identifica qué agentes pasaron.

Hasta entonces: **PREPARADO_NO_CONECTADO**.
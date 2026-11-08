# Runtime Linux worker

## Estado operativo — 2026-11-08

Este componente añade un primer worker Linux reproducible para el runtime.

- Repositorio: `marcojpad-hash/agente-cero-costo`
- Rama aislada: `runtime-linux-worker-20261108`
- Workflow: `.github/workflows/runtime-linux-worker.yml`
- Probe: `runtime/linux_probe.py`
- Runner solicitado: GitHub-hosted `ubuntu-24.04`
- Activación: push a esta rama cuando cambia el workflow o el probe; también admite `workflow_dispatch`.
- Resultado: genera `runtime-result.json` con CPU, RAM detectada, disco, versión de Python, hash determinista y fecha; lo conserva como artifact durante 30 días.

## Qué queda habilitado

La rama contiene un trabajo Linux acotado que mide el host real y comprueba reproducibilidad local de la operación determinista. No ejecuta instrucciones arbitrarias ni usa secretos.

## Integración pendiente con el runtime multiagente

Este worker todavía no reclama jobs de Postgres ni envía callbacks al runtime Floot. Para eso se necesitan los endpoints de claim/complete, su validación OIDC, y publicar la aplicación runtime. El puente OIDC de eventos existente en el PR #13 es un transporte de eventos, no un ejecutor de jobs.

## Restricciones

- GitHub Actions es efímero: cada job recibe un host nuevo; no acumula RAM entre repositorios ni mantiene procesos entre ejecuciones.
- El probe mide recursos del runner real, no promete 8/16 GB.
- La máquina Oracle ARM de 24 GB sigue siendo una provisión externa pendiente; no se crea desde este workflow.
- No se modifican CAPCOT ni Motor U6.

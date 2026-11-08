# Runtime Linux worker

## Estado operativo — 2026-11-08

<badge>PASS — primera ejecución real</badge>

Este componente ya ejecutó un trabajo en un host Linux de GitHub Actions y guardó evidencia.

- Repositorio: `marcojpad-hash/agente-cero-costo`
- Rama: `runtime-linux-worker-20261108`
- Workflow: `.github/workflows/runtime-linux-worker.yml`
- Probe: `runtime/linux_probe.py`
- Runner: GitHub-hosted `ubuntu-24.04`
- Ejecución: [run 42514758321](https://github.com/marcojpad-hash/agente-cero-costo/actions/runs/42514758321)
- Resultado persistido: `runtime/evidence/2026-11-08-linux-probe-42514758321.json`
- Artifact: [runtime-linux-probe-42514758321](https://github.com/marcojpad-hash/agente-cero-costo/actions/runs/42514758321/artifacts/13630364569), disponible hasta 2026-12-08.

## Recursos medidos en el host real

- RAM total visible: 16,760,344,576 bytes (≈15.61 GiB / 16.76 GB).
- RAM disponible durante la prueba: 15,798,530,048 bytes.
- CPU: 4.
- Disco total: 154,894,188,544 bytes; libre: 92,125,200,384 bytes.
- SO: Ubuntu 24.04.5 LTS; Python 3.12.16; Azure, región chilecentral.
- Prueba determinista: PASS. SHA-256: `5288a09b87518e21e896d41d696226cf38ae65f0d7ac026ca1c7bc2aad8ecb12`.
- Job y todos sus pasos: SUCCESS.

La prueba ejecutó el script en Linux real, midió RAM/CPU/disco desde `/proc/meminfo` y el sistema de archivos, verificó dos veces el mismo cálculo determinista y subió el JSON como artifact. La evidencia JSON quedó además versionada en esta rama.

## Uso y alcance

Esta es la primera capacidad Linux real utilizable para ejecuciones acotadas de código, tests, análisis y preparación de artefactos. El workflow corre en un host efímero nuevo por ejecución; no es una VM persistente ni reserva RAM entre repositorios.

## Integración con el runtime multiagente

Pendiente el tramo de control: el runtime Floot debe reclamar jobs y recibir su resultado mediante endpoints autenticados OIDC (claim/complete). El PR #13 actual solo transporta eventos y sigue draft; no se presenta como cola ejecutora.

La máquina Oracle ARM de 24 GB sigue sin provisionarse. No se modifican CAPCOT ni Motor U6.

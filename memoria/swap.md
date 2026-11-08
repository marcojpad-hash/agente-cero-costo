# Memoria virtual (swap) en la VM de Pecas — intento y bloqueo

Fecha: 2026-11-08.

## Qué se intentó

La idea era la de Marco: memoria RAM no física, más lenta, para alimentar
el trabajo de producción. En Linux eso es swap: un archivo en disco que el
sistema usa como memoria virtual. Se crearon dos archivos de 8 GB:

```bash
sudo fallocate -l 8G ~/swapfile1
sudo fallocate -l 8G ~/swapfile2
sudo chmod 600 ~/swapfile1 ~/swapfile2
sudo mkswap ~/swapfile1 ~/swapfile2
sudo swapon ~/swapfile1 ~/swapfile2
```

## Qué pasó

Los archivos se crearon y se formatearon bien, pero `swapon` falló:

```
swapon: /home/hatch/swapfile1: swapon failed: Operation not permitted
```

El contenedor bloquea `swapon` aunque se tenga sudo. Esta VM no puede
agregar memoria virtual.

## Qué significa

- **Un repo no es RAM.** Un repo de GitHub es almacenamiento (disco),
  no memoria para correr programas. Crear uno o dos repos más da más
  espacio en disco, no más memoria. La memoria vive en la máquina que
  corre el trabajo.
- **El análogo que sí da más memoria** es una máquina con más RAM real:
  Oracle Always Free ARM (4 vCPU, 24 GB de RAM, $0). Ahí sí corre
  TwIL-8B y los loops de agente con memoria de verdad.
- La VM de Pecas tiene 7.7 GB de RAM total y ~0.5 GB libre; su swap
  actual es 1 GB (una partición /dev/loop0) y no se puede ampliar.

## Limpieza

Los dos archivos swap se borraron (`sudo rm -f`). Disco de vuelta a 3.3 GB
usados de 150 GB. No quedó nada a medias.

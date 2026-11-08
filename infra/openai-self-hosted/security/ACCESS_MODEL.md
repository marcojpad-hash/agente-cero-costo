# Modelo de acceso

## OpenAI executor
- Un environment ID y una clave restringida por sesión de entorno.
- La clave de aplicación con permisos de sesiones/modelo permanece fuera del contenedor.
- La clave del executor solo registra/conecta el entorno; no debe tener permisos generales de API.
- El executor inicia conexiones salientes; no publicar SSH ni puertos del executor.

## Agentes externos
- Cada agente externo tendrá usuario Linux o identidad de servicio propia.
- No compartir claves privadas ni tokens personales.
- Compartir solo el directorio de intercambio aprobado; no montar el home ni secretos del executor.
- Los permisos de escritura en GitHub siguen siendo independientes de los permisos de la VM.

## Datos y persistencia
- El volumen de trabajo contiene archivos de proyecto; respaldarlo y limitar acceso.
- No escribir credenciales en el volumen compartido, Issues, logs o commits.
- Registrar cada conexión con agente, identidad pública, fecha, alcance y resultado de prueba.

## Aislamiento
El ejemplo de Compose usa un único volumen de trabajo para el executor de una sesión. No desplegar varios agentes no confiables dentro del mismo contenedor o volumen. Para sesiones separadas, usar contenedores/volúmenes separados y compartir solo un directorio de intercambio con permisos explícitos.

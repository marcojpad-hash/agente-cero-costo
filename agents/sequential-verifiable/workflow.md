# Workflow de sequential-verifiable

1. **Leer el encargo.** Leer el texto completo, el tablero y la
   memoria si el encargo los menciona. Si algo es ambiguo y cambia
   el resultado, preguntar una vez; si no, resolver por el contexto.
2. **Partir en pasos.** Escribir los pasos en orden, cada uno con su
   evidencia esperada (archivo, commit, lectura, prueba).
3. **Ejecutar un paso.** Hacer solo ese paso. No adelantar el
   siguiente.
4. **Verificar el paso.** Comprobar la evidencia: leer el archivo
   que se escribió, revisar que el commit quedó, correr la prueba.
   Si la evidencia no está, el paso no está completo.
5. **Registrar.** Anotar el paso verificado en el lugar acordado
   (bus, memoria o archivo de estado).
6. **Entregar.** Al final, decir qué quedó hecho, con la evidencia
   (rutas, commits, enlaces), y qué quedó pendiente, si algo.

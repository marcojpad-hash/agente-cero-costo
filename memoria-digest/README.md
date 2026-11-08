# Memoria digest (el VTunnel)

Resumen público de la memoria privada, para que cualquier modelo
pueda entrar a leerla sin vínculo y sin autorización por app.

## Por qué existe

Un repo privado exige una identidad de GitHub con acceso. El otro
modelo, en su propia app, no tiene esa identidad a menos que Marco
la conecte (el vínculo). No es un bloqueo de red, es de
autenticación: ningún proxy lo salta sin credenciales. En la época
de VTunnel la página estaba negada por la red, no por contraseña;
aquí la página está negada por contraseña.

El VTunnel aquí es este resumen: el repo privado sigue privado, pero
los hechos se publican en este archivo público, donde cualquier
modelo los lee por web. Es lo mismo que ya es público en
`transmigracion/contexto.md`, solo que completo y al día.

## Qué lleva y qué no lleva

- Lleva: los hechos del proyecto (proyectos, decisiones,
  correcciones, tokens, estado, personas como roles).
- No lleva: datos personales, correos, claves, secretos. Nada de eso
  va en la memoria privada y, por tanto, tampoco aquí.

## Cómo se actualiza

`python3 sincronizar.py` lee la memoria privada y regenera
`DIGEST.md`. Se corre cada vez que cambia la memoria privada.

## Si no quieres que un hecho sea público

No lo pongas en la memoria privada sin más: marca el hecho como
privado en su archivo y `sincronizar.py` no lo copiará. (Hoy no hay
ningún hecho marcado así.)

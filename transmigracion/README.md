# Transmigración

## La idea

Que el sistema viaje, no la sesión. Que cualquier modelo, en cualquier
sesión, de cualquier empresa, pueda cargar este paquete y tener la misma
información y resolver lo mismo. Eso es la inteligencia general
unificada que quiere Marco: no una sola mente, sino una conciencia
unificada entre modelos que se apoyan.

Mientras eso se logra, esto es la clonación que sí nos interesa: **no
se clona el personaje, se clonan las capacidades**. No es un prompt que
imita a Pecas. Es un paquete con el método, las herramientas (código
real) y el estado (qué está pendiente, qué se decidió, qué se aprendió).

## Qué hay en este paquete

- `metodo.md` — cómo se trabaja aquí (equivalencia funcional, el
  bypass, veredicto primero, resolver sin preguntar, cuidar tokens).
- `capacidades.md` — inventario de capacidades: qué se puede hacer y
  con qué herramienta real se hace.
- `contexto.md` — el estado del proyecto: quiénes somos, qué repos,
  qué está pendiente, qué se decidió. Se regenera con `empaquetar.py`.
- `arranque.md` — lo que lee un modelo cuando toma el relevo: cómo
  cargar el paquete, hacer el trabajo y dejar el estado para el
  siguiente.
- `MANIFIESTO.md` — versión, fecha y contenido del paquete. Se
  regenera con `empaquetar.py`.
- `empaquetar.py` — construye el paquete desde las fuentes vivas
  (la skill, el tablero, el árbol de este repo).

## Límites honestos

- Esto no es conciencia. Es memoria compartida + método + herramientas.
  Da continuidad, no identidad. El modelo que lo carga no se vuelve
  Pecas: actúa con la misma información y las mismas capacidades.
- Solo funciona si el modelo que toma el relevo **lee el paquete**.
  Un modelo que no lo lee no tiene la información, por más que el
  paquete exista.
- El paquete no lleva claves, contraseñas ni datos personales. Las
  claves se resuelven por los conectores de cada máquina; nunca van
  en un repo, ni privado.
- El estado es una foto: hay que regenerarlo con `empaquetar.py`
  cada vez que algo cambie, o el relevo trabaja con información vieja.

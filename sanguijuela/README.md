# Sanguijuela

El que orquesta no gasta sus tokens. El trabajo pesado lo hacen los
modelos gratuitos, con sus tokens, y las herramientas que ya existen
(sus MCP, sus aplicaciones, sus cableados). El orquestador solo pone
la capa fina: decidir, verificar, unificar.

## Archivos

- `PROTOCOLO_SANGUIJUELA.md` — el protocolo: reglas, tabla de
  enrutado, límites honestos.
- `sanguijuela.py` — la sanguijuela en código: recibe el encargo, lo
  enruta al modelo gratuito que corresponde y trae el resultado.

## Uso

```bash
python3 sanguijuela.py --tipo texto --tarea "resume en 5 puntos..."
python3 sanguijuela.py --tipo texto-largo --tarea "..."
python3 sanguijuela.py --tipo lectura --tarea "https://github.com/..."
python3 sanguijuela.py --tipo codigo --tarea "..." --solo-enrutar
```

`--solo-enrutar` no ejecuta: solo dice a quién le tocaría y con qué
comando.

## La regla en una línea

El orquestador no genera: escribe el encargo corto y lo manda al
modelo que corresponde. Si no hay modelo gratuito que lo haga, se dice
dónde se puede hacer y qué cuesta.

# Puente de lectura

Cuando Pecas no puede leer algo, lo leen los otros modelos y lo unifican.
Los modelos que tenemos son otras arquitecturas de otras compañías, con
capacidades diferentes: si uno no puede leer un texto, otro sí puede.

## Cómo funciona

1. **Trae el texto por varias rutas**: raw.githubusercontent.com para
   archivos de GitHub, la API de GitHub (`get_file_contents`) como
   respaldo, y lectura directa con User-Agent de navegador para el resto.
   Si ninguna ruta trae el texto, lo dice y no inventa nada.
2. **Lo leen dos modelos**: Gemini (`gemini-3-flash-preview`) y Groq
   (`openai/gpt-oss-20b`). Cada uno extrae lo mismo: qué problema
   resuelve, cómo funciona, qué cuesta, qué se puede copiar y los
   límites honestos.
3. **Lo unifican**: Gemini une las dos lecturas en una sola nota, sin
   repetir, marcando donde discrepen. Si un modelo falla, la nota usa
   al otro y dice cuál falló y por qué.

## Uso

```bash
python3 leer.py <URL> [<URL> ...] [--salida ARCHIVO]
```

## Límites honestos

- El texto se trunca a 12.000 caracteres para que quepa en el minuto
  gratis de Groq (8.000 TPM). La nota dice si hubo truncamiento.
- Las claves nunca pasan por el script: los clientes de los conectores
  las resuelven solos.
- La unificación la hace un modelo, no una persona: si las lecturas
  discrepan, la nota lo marca para que se revise.

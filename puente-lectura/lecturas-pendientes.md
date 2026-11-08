# Lecturas por el puente

## https://github.com/Alishahryar1/free-claude-code

Ruta: API de GitHub (get_file_contents). Truncado: sí.

### Nota unificada (Gemini + Groq)

Esta es la nota unificada del proyecto **Free Claude Code (FCC)** basada en las dos lecturas proporcionadas.

---

### **Resumen de Free Claude Code (FCC)**

#### **1. Qué problema resuelve**
Centraliza y unifica el uso de diversas herramientas y agentes de programación (como Claude Code, Aider, Cline, VS Code Chat, Codex, Pi y otros) permitiendo conectarlos con cualquier proveedor de modelos de IA. Su objetivo es evitar la dependencia de suscripciones costosas y únicas, permitiendo el uso de modelos gratuitos, locales o de pago mediante una gestión centralizada de APIs.

#### **2. Cómo funciona (Mecanismo concreto)**
El sistema opera como un **servidor proxy local y enrutador** compatible con la API de OpenAI.
1.  **Instalación:** Se instala el servidor (`fcc-server`) y se accede a una interfaz de administración (UI).
2.  **Configuración:** En la UI se cargan las llaves API de los proveedores (OpenRouter, Groq, NVIDIA NIM, Google AI Studio, etc.) y se definen estrategias de "fallback" (respaldo) y límites de tasa.
3.  **Optimización:** Permite activar **RTK y Headroom** para reducir el consumo de tokens hasta en un 90%.
4.  **Ejecución:** El usuario lanza comandos específicos (ej. `fcc-claude`, `fcc-codex`) o conecta cualquier aplicación al endpoint local `http://127.0.0.1:8082/v1`.
5.  **Procesamiento:** El servidor recibe la petición, gestiona el streaming, el uso de herramientas y, si un proveedor falla, activa automáticamente los reintentos o el cambio de modelo/llave.

#### **3. Costos**
*   **Software:** Gratuito y de código abierto (licencia AGPL v3).
*   **Uso de modelos:** Depende totalmente del proveedor elegido. La herramienta facilita el acceso a más de **1.3 mil millones de tokens gratuitos al mes** a través de niveles gratuitos, aunque permite conectar cuentas de pago existentes sin cargos adicionales por parte de FCC.

#### **4. Elementos adaptables para un stack a "costo cero"**
*   **Arquitectura de enrutamiento:** Lógica de reintentos automáticos y cambio de proveedor ante caídas o límites de tasa (*rate limits*).
*   **Optimización de tokens:** Integración de las herramientas **RTK y Headroom**.
*   **Interfaz de administración:** Sistema para gestionar múltiples llaves y modelos en una capa local.
*   **Compatibilidad:** Uso de un proxy local que traduce formatos de API para que herramientas estándar funcionen con modelos gratuitos o locales.
*   **Herramientas de desarrollo:** Uso de paquetes como `uv`, `pytest`, `Ruff` y `Loguru` mencionados en la estructura del proyecto.

#### **5. Límites y advertencias (Límites honestos)**
*   **Dependencia de terceros:** La disponibilidad y los límites de los niveles gratuitos son volátiles y dependen de cada proveedor.
*   **Cumplimiento de Términos (TOS):** El proyecto elimina integraciones si los proveedores dejan de permitirlas.
*   **Mantenimiento:** Requiere que el usuario mantenga el servidor ejecutándose en una terminal local; no es "plug-and-play" total y requiere configuración manual de llaves.
*   **Soporte:** No existe soporte oficial; depende totalmente de la comunidad.
*   **Rendimiento:** No se detalla el comportamiento bajo carga muy alta o latencias específicas.

> [!CAUTION]
> **ADVERTENCIA DE LECTURA:** Ambas lecturas advierten que el texto original proporcionado estaba incompleto, truncándose en la sección de la lista de proveedores (específicamente en la tabla de proveedores o al llegar a Hugging Face).

#### **6. Discrepancias encontradas**
*   **Modelos Locales:** 
    *   La **Lectura 1** afirma que el sistema es compatible con proveedores locales para lograr un "costo cero total" y mayor privacidad.
    *   La **Lectura 2** sostiene que la herramienta "no incluye entrenamiento o inferencia de modelos locales" y que solo se encarga de llamar a APIs externas.
*   **Alcance de Proveedores:**
    *   La **Lectura 2** es más específica al cuantificar que el sistema soporta un total de **61 proveedores** (entre gratuitos, de pago y locales), detalle que la Lectura 1 no menciona.

## https://github.com/free-ai-things/issueclaw

Ruta: API de GitHub (get_file_contents). Truncado: sí.

### Nota unificada (Gemini + Groq)

Esta es la síntesis de ambas lecturas sobre **IssueClaw**, un sistema para gestionar agentes de IA utilizando la infraestructura de GitHub.

### **1. Problemas que resuelve**
*   **Costos elevados:** Elimina la suscripción mensual de asistentes como ChatGPT Plus ($20) o Copilot ($10).
*   **Pérdida de contexto:** Evita que la IA "olvide" la conversación al cerrar la sesión, ya que el historial se persiste en Git.
*   **Fricción en el flujo de trabajo:** Sustituye el "copiar y pegar" código; la IA puede editar archivos directamente.
*   **Complejidad técnica:** Elimina la necesidad de configurar servidores, GPUs, Docker o infraestructura compleja para tener un agente propio.

### **2. Mecanismo de funcionamiento**
*   **Interfaz:** Utiliza **GitHub Issues** como canal de comunicación y sistema de tickets.
*   **Ejecución:** Se dispara mediante **GitHub Actions** cada vez que se crea un issue o un comentario.
*   **Lógica de Modos (por etiquetas):**
    *   **Sin etiqueta:** Entra en *Chat Mode* (responde como un chat convencional).
    *   **Etiqueta `agent`:** Activa el *Agent Mode* (capacidad para leer archivos, ejecutar comandos bash, realizar cambios en el código y hacer *commits*).
    *   **Etiqueta `hatch`:** Inicia el flujo de personalización de la "personalidad" del agente.
*   **Procesamiento:** Utiliza un runtime basado en **Bun** para ejecutar scripts de TypeScript/JavaScript de forma rápida.
*   **Memoria y Persistencia:**
    *   **Discrepancia de ubicación:** La **Lectura 1** especifica que el estado de la personalidad se guarda en un archivo Markdown específico (`state/personality.md`). La **Lectura 2** señala de forma más general que los mensajes y el historial se almacenan en el historial de commits del repositorio.

### **3. Costos y Proveedores**
*   **Costo total:** **$0/mes**, aprovechando las capas gratuitas de los proveedores.
*   **Infraestructura:** GitHub Actions (nivel gratuito).
*   **Modelos/APIs compatibles:**
    *   **Groq:** Para respuestas rápidas (Límite: 12k TPM).
    *   **Gemini:** Para tareas con ventanas de contexto grandes (Límite: 1M TPM).
    *   **Cerebras:** (Límite: 60k TPM).
    *   **OpenRouter:** También mencionado como opción de conexión.

### **4. Elementos adaptables para un Stack "Costo Cero"**
*   **GitHub Actions como motor de ejecución:** Reemplaza el uso de servidores dedicados.
*   **Git como base de datos:** Uso del historial de commits y archivos Markdown para persistir memoria sin bases de datos externas.
*   **GitHub Issues como UI:** Interfaz de chat persistente y gratuita.
*   **Combinación de APIs:** Uso de Groq para chat fluido (~500 tokens/mensaje) y Gemini para tareas complejas de codificación.

### **5. Límites honestos y advertencias**
*   **Falla del Modo Agente en Groq:** Ambas lecturas coinciden en que el "Modo Agente" no funciona en Groq debido al error 413 (límite de tokens); para esta función es obligatorio usar Gemini o Cerebras.
*   **Acceso restringido:** Por seguridad, solo responde a dueños (*owners*), miembros o colaboradores del repositorio.
*   **Latencia:** No es instantáneo; el arranque de GitHub Actions tarda aproximadamente 5 segundos o más.
*   **Configuración manual:** Requiere que el usuario configure manualmente los "Secrets" de GitHub con las API Keys; de lo contrario, el flujo fallará con el error “Provider requires API_KEY”.
*   **Permisos de Bash:** El uso de comandos de consola está sujeto a los permisos otorgados a GitHub Actions (la Lectura 2 advierte que no se mencionan soportes para entornos con restricciones adicionales).

## https://github.com/QualityUnit/harnext

Ruta: API de GitHub (get_file_contents). Truncado: no.

### Nota unificada (Gemini + Groq)

Aquí tienes la información unificada de ambas lecturas sobre la herramienta **harnext**, estructurada de forma coherente y sin repeticiones:

### **NOTA UNIFICADA: HARNEXT**

**1. Problema que resuelve**
Automatiza la interacción con proyectos de software directamente desde la terminal (CLI). Actúa como un agente de IA que puede leer, crear y editar archivos, ejecutar comandos de shell (terminal) y gestionar servidores MCP. Además, genera flujos de trabajo (workflows) de GitHub Actions para resolver *issues* de forma automática.

**2. Cómo funciona (Mecanismo técnico)**
*   **Base:** Es un agente interactivo basado en **Node.js** (requiere versión ≥ 20).
*   **Integración de IA:** Utiliza la librería `pi-ai` para conectarse a más de 20 proveedores de modelos de lenguaje (Anthropic, OpenAI, Google, Ollama, etc.).
*   **Gestión de Credenciales:** Al iniciar, solicita al usuario una clave API que se almacena localmente en `~/.harnext/agent/auth.json`.
*   **Interfaz:** Ofrece un REPL interactivo y comandos rápidos como `harnext -p`, `harnext setup` y `harnext runner status`.
*   **Ejecución:** Las tareas se procesan mediante GitHub Actions, pudiendo usar la infraestructura en la nube de GitHub o un *runner* autohospedado en la PC del usuario.

**3. Costo**
*   **Software:** Es gratuito y de código abierto bajo la licencia **MIT**.
*   **Operación:** El costo depende del uso de los proveedores de LLM y de los flujos de GitHub Actions. El README no especifica tarifas, ya que estas dependen de las claves API externas de cada proveedor.

**4. Adaptación para un stack a "Costo Cero"**
Para operar sin costos, se pueden aprovechar los siguientes elementos:
*   **Modelos locales:** Soporte para **Ollama** (ejecución de IA en local).
*   **Infraestructura propia:** Uso de **runners autohospedados** (*self-hosted*) para evitar pagar por cómputo en la nube.
*   **Código abierto:** Reutilizar el patrón CLI de `harnext`, su lógica de almacenamiento de credenciales y la integración multi-proveedor de `pi-ai`.
*   **Protocolos abiertos:** Integración con servidores **MCP** (Model Context Protocol).

**5. Límites honestos y advertencias**
*   **Ausencia de información:** Ambas lecturas coinciden en que el texto original **no menciona limitaciones explícitas**, fallos conocidos ni tareas específicas que el agente no pueda realizar.
*   **Discrepancias en la interpretación de límites:**
    *   **Lectura 1:** Se limita estrictamente a lo que dice el texto: no hay limitaciones mencionadas.
    *   **Lectura 2:** Infiere límites lógicos basados en el diseño: la herramienta no funciona sin un LLM, requiere conexión a internet (salvo modelos locales), está sujeta a las cuotas de los proveedores de API y no posee interfaz gráfica (solo terminal).
*   **Advertencia de lectura:** No se reportaron secciones ilegibles en el documento original, pero se advierte que la descripción se centra en capacidades y omite restricciones de uso.

## https://github.com/Rohith-s-hub/Oblivion-agent

Ruta: API de GitHub (get_file_contents). Truncado: no.

### Nota unificada (Gemini + Groq)

Aquí tienes la nota unificada, consolidando la información de ambas lecturas y detallando las precisiones adicionales de cada una:

### **Nota Unificada: Oblivion AI**

**1. Problema que resuelve**
*   **Privacidad y Autonomía:** Ofrece un asistente de ingeniería y programación de código abierto, totalmente local y privado.
*   **Alternativa Gratuita:** Sustituye herramientas de pago como Cursor, GitHub Copilot y Claude Code.
*   **Independencia:** Elimina la necesidad de suscripciones, cuentas en la nube o el envío de código a servidores externos, operando directamente desde la terminal (CLI).

**2. Funcionamiento y Mecanismos Concretos**
*   **Motor M.E.E.R.A.:** Utiliza un ciclo de razonamiento estilo **ReAct** (planificación, ejecución de herramientas, observación e iteración).
*   **Herramientas:** Cuenta con **38 herramientas** (especificado por Lectura 2), incluyendo búsqueda de símbolos, `batch_edit` y ejecución de pruebas.
*   **Búsqueda Híbrida de 3 Capas:**
    *   Símbolos/Exacta (SQLite con FTS5).
    *   Texto completo.
    *   Semántica/Vectorial (ChromaDB + MiniLM).
*   **Cadena de Respaldo (Fallback):** Sistema automático que rota entre 13 opciones (Ollama, Gemini, Groq, OpenRouter, etc.) para evitar bloqueos por límites de tasa (*rate-limits*).
*   **Sistema de Seguridad de 3 Niveles:** 
    1.  **Lectura:** Sin confirmación.
    2.  **Mutación:** Requiere vista previa de "diff" y aprobación.
    3.  **Destrucción:** Exige confirmación explícita (la Lectura 2 aclara que esto aplica solo a eliminación de archivos o ramas).
*   **Interfaz e Interacción:** 
    *   TUI (Interfaz de Usuario de Terminal) construida con la librería *Textual* de Python.
    *   **Voz:** Soporte para STT con `faster-whisper` y TTS con `Edge-TTS` o `ElevenLabs` (opcional).
*   **Protocolo MCP:** Actúa como servidor MCP para exponer herramientas de análisis a editores externos (Claude Desktop, Cursor, Zed).

**3. Costo**
*   **Cero costo:** Diseñado para funcionar con modelos locales y capas gratuitas de APIs. Licencia MIT.
*   **Opciones Premium:** Solo para servicios externos opcionales como voces de ElevenLabs.

**4. Elementos adaptables para un Stack "Costo Cero"**
*   Lógica de rotación de modelos (fallback) con gestión de *cooldowns*.
*   Indexación híbrida local con **chunking AST-aware** (mencionado por Lectura 2) en hardware modesto.
*   Integración de voz local (`faster-whisper` + `Edge-TTS`).
*   Uso de SQLite FTS5 y ChromaDB para gestión de contexto técnica.

**5. Límites y Advertencias**
*   **No es un IDE:** Es una herramienta de terminal; no sustituye la interfaz visual de un editor completo.
*   **Hardware:** Validado en equipos con **13GB de RAM**. La Lectura 2 añade que el rendimiento depende de hardware modestamente potente y menciona la ausencia de necesidad de GPU (o el uso de CPU).
*   **Voz:** No soporta interrupciones (*barge-in*) ni ajuste de tono emocional.
*   **Dependencia Externa:** En modo no-local, depende de la disponibilidad de las APIs gratuitas de terceros.

**Discrepancias y precisiones específicas:**
*   **Sobre las herramientas:** La Lectura 2 es más específica al cuantificar **38 herramientas** totales, mientras que la Lectura 1 se centra en el funcionamiento general.
*   **Limitaciones de paquetes:** Solo la Lectura 2 menciona que el número de paquetes de dominio es pequeño (14), limitados a 2 por petición, y que solo hay **10 herramientas MCP** disponibles (todas de solo lectura).
*   **Calidad del código:** La Lectura 2 advierte explícitamente que no se garantiza la calidad de la generación ni la cobertura total de todos los lenguajes/frameworks.
*   **Acciones destructivas:** La Lectura 2 especifica que la categoría de "destrucción" se limita a borrar archivos o ramas de Git.
*   **Fallback:** La Lectura 1 menciona "13 opciones" generales; la Lectura 2 especifica que la cadena inicia con "Ollama Cloud" (posible referencia a Ollama local + proveedores Cloud).

*Nota: No se reportaron partes ilegibles en ninguna de las dos lecturas.*

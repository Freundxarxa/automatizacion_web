# Monitor de disponibilidad web

Programa en Python que comprueba cada día a las 9:00 una lista de URLs, guarda el resultado en un registro y avisa por Telegram cuando una página falla o vuelve a funcionar.

No usa inteligencia artificial: todas las decisiones son reglas fijas.

---

## 1. Diseño

| Pieza | En este proyecto |
|---|---|
| **Evento** | El Programador de tareas de Windows ejecuta `monitor.py` todos los días a las 9:00. Para probar, se lanza a mano con `py monitor.py`. |
| **Entrada** | Las URLs de `urls.txt`, el tiempo máximo (`MONITOR_TIEMPO_MAXIMO`) y el último estado guardado en `estado.json`. |
| **Acción** | Pedir cada URL, medir el tiempo y añadir una fila a `registro.csv`. |
| **Decisión** | ¿La URL ha fallado? ¿Ha cambiado respecto a la última vez? |
| **Verificación** | Telegram confirma el envío; solo entonces se actualiza `estado.json`. |
| **Salida** | `registro.csv` con el histórico y, si hay un cambio, un mensaje en Telegram. |

### Condiciones

Una URL **falla** si ocurre una de estas tres cosas:

| Estado | Cuándo |
|---|---|
| `ERROR HTTP` | El servidor responde con un código 400 o superior (404, 500...). |
| `ERROR DE CONEXION` | No se puede conectar: servidor apagado, dominio inexistente, sin Internet... |
| `TIEMPO EXCEDIDO` | La respuesta tarda más que el tiempo máximo configurado. |

En cualquier otro caso el estado es `OK`.

### Cuándo se envía un aviso

| Estado anterior | Estado actual | Qué hace |
|---|---|---|
| OK | OK | Solo guarda el registro. |
| OK | FALLO | Guarda el registro y **avisa del fallo**. |
| FALLO | FALLO | Solo guarda el registro (no repite el aviso). |
| FALLO | OK | Guarda el registro y **avisa de la recuperación**. |

Si el aviso no se puede enviar (sin Internet, token incorrecto...), el estado no cambia y se volverá a intentar en la siguiente ejecución.

### Alcance y límites

- Solo comprueba las URLs escritas en `urls.txt`. No recorre la web ni busca enlaces rotos.
- No detecta errores visuales ni de contenido.
- **Una respuesta HTTP correcta no garantiza que todas las funciones de la página funcionen.** Un formulario, un carrito o un inicio de sesión pueden fallar aunque la página cargue con código 200.
- Para ejecutarse a las 9:00, el ordenador o servidor debe estar **encendido y conectado a Internet**.

---

## 2. Estructura de carpetas

```text
automatizacion_web/
├── .gitignore         # Archivos que no se suben a Git
├── README.md          # Este documento
├── MFU.md             # Manual de uso rápido
├── FICHA-DISENO.md    # Ficha de diseño de la automatización
├── monitor.py         # Programa
├── requirements.txt   # Dependencias
├── urls.txt           # URLs que se comprueban
├── registro.csv       # Se crea al ejecutar (histórico)
└── estado.json        # Se crea al ejecutar (último estado de cada URL)
```

`registro.csv` y `estado.json` no se suben a Git: son datos de cada equipo.

---

## 3. Instalación

Requisitos: Windows con Python 3.10 o superior.

Abre PowerShell en la carpeta del proyecto:

```powershell
py --version
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

La única dependencia es `requests`, que sirve para hacer peticiones HTTP.

---

## 4. Configuración

### URLs

Edita `urls.txt` y escribe una URL completa por línea, con `https://` o `http://`. Las líneas vacías y las que empiezan por `#` se ignoran.

```text
https://mi-web.com/
https://mi-web.com/contacto
```

### Tiempo máximo (opcional)

Por defecto son 10 segundos. Para cambiarlo:

```powershell
setx MONITOR_TIEMPO_MAXIMO 5
```

### Telegram

1. En Telegram, abre un chat con **@BotFather**, escribe `/newbot` y sigue los pasos. Al final te dará un **token**.
2. Abre el chat con tu nuevo bot y pulsa **Iniciar** (o escríbele cualquier mensaje).
3. En el navegador abre `https://api.telegram.org/bot<TOKEN>/getUpdates`, sustituyendo `<TOKEN>`. Busca `"chat":{"id":` y copia ese número: es tu **chat_id**.
4. Guarda los dos datos como variables de entorno de tu usuario:

   ```powershell
   setx TELEGRAM_BOT_TOKEN "123456789:ABC..."
   setx TELEGRAM_CHAT_ID "123456789"
   ```

5. Cierra y vuelve a abrir PowerShell (y VS Code) para que lean las variables nuevas.

El token **nunca** se escribe en el código ni en ningún archivo del proyecto. Así no se sube a GitHub por error.

Para comprobarlo:

```powershell
echo $env:TELEGRAM_CHAT_ID
```

---

## 5. Ejecución manual

```powershell
.venv\Scripts\python.exe monitor.py
```

Salida de ejemplo:

```text
OK: https://mi-web.com/ (182 ms) HTTP 200
ERROR HTTP: https://mi-web.com/contacto (95 ms) HTTP 404 Not Found
  Aviso enviado por Telegram
```

---

## 6. Programar la ejecución diaria (Programador de tareas)

1. Abre **Programador de tareas** desde el menú Inicio.
2. Pulsa **Crear tarea básica**.
3. Nombre: `Monitor web`. Siguiente.
4. Desencadenador: **Diariamente**, a las **9:00:00**, cada 1 día.
5. Acción: **Iniciar un programa**.
   - **Programa o script:** `C:\Users\TU_USUARIO\Desktop\automatizacion_web\.venv\Scripts\python.exe`
   - **Agregar argumentos:** `monitor.py`
   - **Iniciar en:** `C:\Users\TU_USUARIO\Desktop\automatizacion_web`
6. Finaliza el asistente.
7. Abre las propiedades de la tarea, pestaña **Configuración**, y marca **Ejecutar la tarea lo antes posible después de perder un inicio programado**. Así, si el ordenador estaba apagado a las 9:00, se ejecutará al encenderlo.
8. Haz clic derecho en la tarea y pulsa **Ejecutar** para probarla. Comprueba que se ha añadido una fila nueva en `registro.csv`.

Si la tarea no envía avisos pero desde PowerShell sí, cierra sesión en Windows y vuelve a entrar para que la tarea lea las variables de Telegram.

---

## 7. Prueba manual

Esta prueba usa un servidor web local que viene con Python, así no hace falta tocar una web real. Necesitas dos ventanas de PowerShell abiertas en la carpeta del proyecto.

**Preparación** (ventana 1):

```powershell
mkdir web_prueba
Set-Content web_prueba\index.html "Inicio"
py -m http.server 8000 --bind 127.0.0.1 --directory web_prueba
```

Deja esa ventana abierta. En `urls.txt` escribe solo:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/contacto.html
```

**Pasos** (ventana 2):

| Paso | Qué hago | Resultado esperado | Evidencia |
|---|---|---|---|
| 1 | `.venv\Scripts\python.exe monitor.py` | `/` da `OK`. `contacto.html` da `ERROR HTTP 404`. | Llega **un aviso de FALLO** de `contacto.html`. |
| 2 | Vuelvo a ejecutar el monitor | Los mismos resultados. | **No llega ningún mensaje** (no se repite). |
| 3 | `Set-Content web_prueba\contacto.html "Contacto"` y ejecuto el monitor | Las dos URLs dan `OK`. | Llega **un aviso de RECUPERADA**. |
| 4 | Ejecuto el monitor otra vez | Las dos dan `OK`. | No llega ningún mensaje. |
| 5 | Paro el servidor (`Ctrl+C` en la ventana 1) y ejecuto el monitor | Las dos dan `ERROR DE CONEXION`. | Llegan **dos avisos de FALLO**. |
| 6 | Arranco el servidor de nuevo y ejecuto el monitor | Las dos dan `OK`. | Llegan **dos avisos de RECUPERADA**. |

En cada paso, abre `registro.csv` y comprueba que hay una fila nueva por URL con la fecha, el estado y el tiempo.

Para probar el tiempo máximo, ejecuta en la ventana 2 `$env:MONITOR_TIEMPO_MAXIMO="0.001"` y después el monitor: el estado será `TIEMPO EXCEDIDO`. Cierra esa ventana al terminar para volver al valor normal.

Al terminar, vuelve a poner tus URLs reales en `urls.txt` y borra `estado.json` y `registro.csv` si quieres empezar de cero.

---

## 8. Presentación del proyecto

> He creado una automatización que vigila mi web sin que yo tenga que entrar a mirarla.
>
> **El evento** es una hora: el Programador de tareas de Windows lanza el programa cada día a las 9:00.
>
> **La acción** es pedir cada URL de una lista, medir cuánto tarda y guardar en un CSV la fecha, la URL, el estado y el tiempo.
>
> **La decisión** son reglas fijas: si hay un error HTTP, no hay conexión o tarda demasiado, es un fallo. Además se compara con el estado del día anterior, guardado en un archivo JSON. Solo aviso por Telegram cuando algo cambia: cuando empieza a fallar y cuando se recupera. Así no recibo el mismo mensaje cada día.
>
> **La verificación**: el estado solo se actualiza si Telegram confirma que el mensaje se ha enviado. Si falla el envío, se reintenta al día siguiente.
>
> **Los límites**: solo comprueba las URLs que yo indico, y que una página responda bien no significa que todo funcione dentro de ella. Además, el ordenador tiene que estar encendido y conectado.
>
> Lo he probado con un servidor local: una página que funciona, una que da 404, su recuperación y el servidor apagado.

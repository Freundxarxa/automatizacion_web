# Monitor de disponibilidad web

## Diseno

- **Desencadenante:** el Programador de tareas de Windows inicia `monitor.py` todos los dias a las 9:00.
- **Acciones:** lee las URLs de `urls.txt`, hace una peticion HTTP a cada una, mide el tiempo y anade el resultado a `checks.csv`.
- **Condiciones:** un error HTTP (codigo 400 o superior), un problema de conexion o superar el tiempo limite configurable se considera un fallo. Solo se envia un aviso cuando una URL pasa de funcionar a fallar. Se envia otro cuando vuelve a funcionar.

La comprobacion solo cubre las URLs indicadas. Una respuesta HTTP correcta no garantiza que todas las funciones, contenidos o elementos visuales de la pagina funcionen.

## Estructura

```text
monitor-web/
|-- .gitignore
|-- README.md
|-- monitor.py
|-- requirements.txt
|-- urls.txt
|-- checks.csv   (se crea al ejecutar)
|-- state.json   (se crea al ejecutar)
```

## Instalacion

Abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activacion del entorno, puedes instalar y ejecutar Python sin activarlo:

```powershell
py -m pip install -r requirements.txt
py monitor.py
```

## Configuracion

### URLs y tiempo limite

Edita `urls.txt`: escribe una URL completa por linea, incluyendo `https://` o `http://`. Las lineas vacias y las que empiezan por `#` se ignoran. Cambia `https://example.com` por las URLs de tu sitio.

El limite por defecto es de 10 segundos. Para cambiarlo, define la variable de entorno `REQUEST_TIMEOUT_SECONDS`, por ejemplo:

```powershell
[Environment]::SetEnvironmentVariable("REQUEST_TIMEOUT_SECONDS", "5", "User")
```

Cierra y vuelve a abrir las aplicaciones para que lean las variables de entorno actualizadas.

### Telegram

1. En Telegram, habla con `@BotFather`, usa `/newbot` y guarda el token que te entrega.
2. Abre una conversacion con tu nuevo bot y pulsa **Iniciar**.
3. Obtiene tu `chat_id` consultando `https://api.telegram.org/bot<TU_TOKEN>/getUpdates` y leyendo `message.chat.id` en la respuesta. No compartas el token ni lo guardes en este proyecto.
4. En Windows, busca **Editar las variables de entorno de tu cuenta** y crea estas dos variables de usuario:
   - `TELEGRAM_BOT_TOKEN`: el token del bot.
   - `TELEGRAM_CHAT_ID`: el identificador de tu conversacion.
5. Cierra y vuelve a abrir VS Code y PowerShell. Si el Programador de tareas no ve las variables, cierra la sesion de Windows y vuelve a iniciarla.

El token no se escribe en el codigo ni en `urls.txt`. Si falta alguna variable, los resultados se siguen registrando y el aviso pendiente se intentara de nuevo en la siguiente ejecucion.

## Ejecucion manual

```powershell
py monitor.py
```

Cada ejecucion agrega una fila a `checks.csv`. `state.json` guarda si cada URL estaba fallando, para evitar repetir avisos durante el mismo fallo y detectar la recuperacion.

## Prueba manual

Configura Telegram antes de esta prueba para recibir los dos avisos. La prueba utiliza el servidor HTTP incluido con Python y solo escucha en tu propio equipo.

1. En `urls.txt`, deja esta URL:

   ```text
   http://127.0.0.1:8000/
   ```

2. En una ventana de PowerShell abierta en la carpeta del proyecto, inicia el servidor:

   ```powershell
   py -m http.server 8000 --bind 127.0.0.1
   ```

3. En otra ventana, ejecuta `py monitor.py`. Debe registrar `OK` en `checks.csv` y no enviar un aviso.
4. Deten el servidor con `Ctrl+C` y vuelve a ejecutar `py monitor.py`. Debe registrar `ERROR DE CONEXION` y enviar un aviso de fallo.
5. Inicia de nuevo el servidor con el comando del paso 2 y ejecuta el monitor. Debe registrar `OK` y enviar el aviso de recuperacion.
6. Ejecuta el monitor una vez mas mientras el servidor siga activo. Debe registrar el resultado sin enviar otro mensaje.

Al terminar, puedes detener el servidor con `Ctrl+C`. Los resultados y el estado de la prueba permanecen en `checks.csv` y `state.json`; para empezar una prueba desde cero, elimina esos archivos manualmente.

## Programador de tareas de Windows

1. Abre **Programador de tareas** desde el menu Inicio y selecciona **Crear tarea basica**.
2. Ponle un nombre, por ejemplo `Monitor web`, y elige el desencadenador **Diariamente** a las **9:00**.
3. Como accion, elige **Iniciar un programa**.
4. En **Programa o script**, indica la ruta completa a Python. Si usaste el entorno virtual, sera algo parecido a `C:\ruta\al\proyecto\.venv\Scripts\python.exe`.
5. En **Agregar argumentos**, escribe la ruta completa a `monitor.py`, por ejemplo `"C:\ruta\al\proyecto\monitor.py"`.
6. En **Iniciar en**, indica la carpeta del proyecto, por ejemplo `C:\ruta\al\proyecto`.
7. Termina el asistente y usa **Ejecutar** desde la tarea para comprobar que funciona.

Para ejecutarse a la hora prevista, el ordenador o servidor debe estar encendido, despierto y conectado a Internet. Si esta tarea no encuentra las variables de Telegram, vuelve a iniciar la sesion de Windows o configura la tarea para ejecutarse con la misma cuenta de usuario.

## GitHub

Git y GitHub CLI (`gh`) permiten publicar este proyecto en tu cuenta. Primero autentica GitHub CLI desde PowerShell:

```powershell
gh auth login
```

Cuando hayas elegido el nombre y la visibilidad del repositorio, desde la carpeta del proyecto puedes crearlo y subir los archivos con:

```powershell
git init
git add .
git commit -m "Crear monitor de disponibilidad web"
gh repo create automatizacion_web --public --source . --remote origin --push
```

Este comando crea el repositorio publico `automatizacion_web` en tu cuenta y sube el proyecto. `.gitignore` evita subir los registros y el estado de ejecucion. Revisa siempre que no hayas agregado tokens ni otros secretos antes de publicar. El codigo sera visible para cualquier persona; no publiques tokens ni datos privados.

## Presentacion del proyecto

Este proyecto comprueba una lista concreta de paginas una vez al dia. Guarda la fecha, la URL, el estado y el tiempo de respuesta en un CSV. Si una pagina falla, envia un aviso por Telegram; conserva el estado anterior para no repetir el aviso mientras siga fallando y avisa cuando se recupera. No recorre el sitio ni comprueba su aspecto visual, y una respuesta HTTP correcta no demuestra que todas sus funciones trabajen bien. La tarea depende de que el ordenador o servidor este encendido y conectado a Internet a la hora programada.
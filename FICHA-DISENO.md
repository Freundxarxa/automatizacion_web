# Ficha de diseño de una automatización

**Nombre del proyecto:** Monitor de disponibilidad web  
**Autor/a:** __________ · **Versión y fecha:** 1.0 · 2026-10-01

## 1. Problema

Cuando mi web deja de funcionar, tengo que darme cuenta yo entrando a mirarla.

Hoy lo hago así: abro las páginas en el navegador de vez en cuando, y a veces me entero del fallo días después.

## 2. Valor de la mejora

Quiero mejorar el tiempo que tardo en enterarme de que una página falla.

Ocurre 1 vez por día. Cada vez dedico unos 5 minutos a revisar las páginas a mano.

Lo mediré con el tiempo entre el fallo y el aviso. Mi punto de partida es que no lo sé: depende de cuándo me acuerde de mirar.

¿El proceso está suficientemente claro o primero debo simplificarlo? Está claro: pedir cada página y mirar si responde bien y a tiempo.

## 3. Evento

El proceso empezará cuando el Programador de tareas de Windows lo lance cada día a las 9:00.

En la primera prueba lo iniciaré manualmente mediante `py monitor.py` en PowerShell.

## 4. Entrada

| Dato necesario | De dónde viene | Ejemplo ficticio | Qué hago si falta |
|---|---|---|---|
| Lista de URLs | `urls.txt` | `https://mi-web.com/contacto` | El programa se para y lo indica. |
| Tiempo máximo | Variable `MONITOR_TIEMPO_MAXIMO` | `10` segundos | Usa 10 segundos. |
| Token y chat de Telegram | Variables `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` | `123456:ABC...` | Guarda el registro, no envía el aviso y lo reintenta otro día. |
| Último estado | `estado.json` | `{"https://mi-web.com/": "OK"}` | Supone que todas estaban OK. |

## 5. Decisiones

| Condición | Camino que debe seguir | Regla, IA o persona | Motivo |
|---|---|---|---|
| Código HTTP 400 o superior | Estado `ERROR HTTP` | Regla | Es un dato objetivo. |
| No hay conexión | Estado `ERROR DE CONEXION` | Regla | Es un dato objetivo. |
| Tarda más del máximo | Estado `TIEMPO EXCEDIDO` | Regla | Límite configurable. |
| El estado cambia respecto al anterior | Enviar aviso | Regla | Evitar mensajes repetidos. |
| Qué hacer para arreglar la web | Revisar la web | Persona | El programa solo avisa. |

## 6. Acciones, verificación y salida

| Acción | Qué cambia | Cómo lo comprobaré |
|---|---|---|
| Comprobar cada URL | Nada (solo lectura) | La salida de la consola muestra el estado. |
| Guardar el resultado | Añade una fila en `registro.csv` | Abro el CSV y veo la fila con fecha, URL, estado y tiempo. |
| Enviar aviso | Un mensaje en Telegram | Lo recibo en el móvil. |
| Guardar el estado | Actualiza `estado.json` | Solo cambia si el aviso se ha enviado. |

El resultado final será un histórico en `registro.csv` y avisos en Telegram, y lo utilizaré yo para revisar la web.

Si no puede terminar, debe dejar el estado sin cambiar para que la siguiente ejecución continúe y reintente el aviso.

## 7. Estado e identificación

Identificaré cada caso mediante la URL.

Los estados posibles serán `OK` y `FALLO` (en `estado.json`); en el registro se detalla `OK`, `ERROR HTTP`, `ERROR DE CONEXION` o `TIEMPO EXCEDIDO`.

Guardaré el estado en `estado.json`.

Si recibo el mismo caso otra vez (la URL sigue fallando), solo lo registro; no repito el aviso.

Si recibo el mismo identificador con información diferente (por ejemplo, pasa de 404 a error de conexión), sigue siendo `FALLO` y no se envía otro aviso; el cambio queda en el registro.

## 8. Permisos e intervención humana

Puede leer `urls.txt`, `estado.json`, las variables de entorno y las páginas de la lista (peticiones GET).

Puede crear o modificar `registro.csv` y `estado.json` en la carpeta del proyecto, y enviar mensajes a mi chat de Telegram.

Necesita una decisión humana antes de cambiar la lista de URLs o actuar sobre la web.

El límite técnico que lo aplicará será el propio código: solo hace peticiones GET y solo escribe en dos archivos de su carpeta. La tarea se ejecuta con mi usuario, sin permisos de administrador.

Una instrucción escrita y un permiso técnico cumplen funciones distintas: lo compruebo revisando que en `monitor.py` no hay `os.remove`, `subprocess`, `os.system` ni peticiones distintas de `requests.get` (a las URLs) y `requests.post` (solo a Telegram).

## 9. Pruebas de aceptación

| Caso | Entrada de ejemplo | Resultado esperado | Evidencia | Resultado real |
|---|---|---|---|---|
| Normal | `http://127.0.0.1:8000/` con servidor activo | `OK`, sin aviso | Fila en `registro.csv` | |
| Error HTTP | `http://127.0.0.1:8000/contacto.html` sin el archivo | `ERROR HTTP 404`, un aviso | Mensaje en Telegram | |
| Repetido | Ejecutar otra vez con el mismo fallo | Se registra, sin aviso | No llega mensaje nuevo | |
| Recuperación | Crear `contacto.html` y ejecutar | `OK`, aviso de recuperación | Mensaje en Telegram | |
| Fallo de conexión | Servidor parado | `ERROR DE CONEXION`, un aviso por URL | Mensaje en Telegram | |
| Lenta | `MONITOR_TIEMPO_MAXIMO=0.001` | `TIEMPO EXCEDIDO` | Fila en `registro.csv` | |
| Sin Telegram | Variables sin configurar | Registra, no avisa, reintenta después | Consola: `Aviso no enviado` | |

## 10. Funcionamiento y mantenimiento

¿Dónde se ejecutará? En mi ordenador con Windows, mediante el Programador de tareas.

¿Qué sucede si el equipo está apagado? No se comprueba a las 9:00. Con la opción *Ejecutar lo antes posible después de perder un inicio programado*, se ejecuta al encenderlo.

¿Cómo sabré que algo ha fallado? Por Telegram si falla la web; si falla el propio monitor, porque no habrá filas de ese día en `registro.csv` o por el historial de la tarea.

¿Quién lo revisará y podrá detenerlo? Yo, deshabilitando la tarea en el Programador de tareas.

¿Qué coste o consumo debo observar? Ninguno: una petición por URL al día y la API de Telegram es gratuita. El CSV crece una fila por URL y día.

## 11. Primera versión y siguiente mejora

Mi primera versión hará la comprobación diaria de una lista de URLs con aviso por Telegram.

Consideraré que funciona cuando pase todas las pruebas de la sección 9.

La siguiente mejora será comprobar también que la página contiene un texto concreto porque un código 200 no garantiza que el contenido sea correcto.

## 12. Registro de decisiones

| Fecha | Qué he cambiado | Por qué | Qué prueba lo comprueba |
|---|---|---|---|
| 2026-10-01 | Estado guardado en `estado.json` | No repetir avisos | Repetido |
| 2026-10-01 | El estado solo cambia si Telegram confirma el envío | No perder avisos si falla Internet | Sin Telegram |
| 2026-10-01 | Token en variables de entorno | No subirlo a GitHub | Revisión de `git status` |

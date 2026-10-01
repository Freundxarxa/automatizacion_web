# MFU.md — Manual para el usuario (Monitor web)

## ¿Qué hace?

Cada día a las 9:00 comprueba las URLs de `urls.txt`. Guarda el resultado en `registro.csv` y te escribe por Telegram solo cuando una URL empieza a fallar o cuando vuelve a funcionar.

Solo lee páginas: no modifica nada en tu web.

## Archivos

| Archivo | Para qué sirve | ¿Lo edito yo? |
|---|---|---|
| `urls.txt` | Lista de URLs a comprobar | Sí |
| `monitor.py` | El programa | No |
| `registro.csv` | Histórico de comprobaciones | No (solo leer) |
| `estado.json` | Último estado de cada URL | No |

## Uso diario

No tienes que hacer nada: se ejecuta solo. Si no recibes mensajes, todo está bien.

## Ejecutar a mano

```powershell
cd C:\Users\TU_USUARIO\Desktop\automatizacion_web
.venv\Scripts\python.exe monitor.py
```

## Añadir o quitar una URL

Abre `urls.txt`, añade o borra una línea y guarda. Para desactivar una URL sin borrarla, pon `#` delante.

## Ver el histórico

Abre `registro.csv` con Excel o con el editor. Cada fila es una comprobación:

```text
fecha,url,estado,tiempo_ms,detalle
2026-10-01 09:00:02,https://mi-web.com/,OK,182,HTTP 200
```

## Pausar o quitar la automatización

En el Programador de tareas, clic derecho sobre **Monitor web**:

- **Deshabilitar**: la pausa.
- **Habilitar**: la reanuda.
- **Eliminar**: la quita (el proyecto sigue en la carpeta).

También desde PowerShell:

```powershell
Disable-ScheduledTask -TaskName "Monitor web"
Enable-ScheduledTask -TaskName "Monitor web"
Unregister-ScheduledTask -TaskName "Monitor web" -Confirm:$false
```

Para volver a crearla: `powershell -ExecutionPolicy Bypass -File .\instalar.ps1`.

## Comprobar Telegram

```powershell
.venv\Scripts\python.exe monitor.py --probar-telegram
```

## Si algo falla

| Síntoma | Qué mirar |
|---|---|
| No llega ningún aviso aunque una URL falla | ¿Es la primera vez que falla? Si ya fallaba ayer, no se repite el aviso. Mira `estado.json`. |
| Pone `Aviso no enviado: faltan TELEGRAM_BOT_TOKEN...` | Configura las variables de entorno y abre una ventana nueva de PowerShell. |
| Pone `Aviso no enviado: Telegram respondió con error` | Token o chat_id incorrectos, o no has pulsado **Iniciar** en el chat del bot. |
| `registro.csv` no tiene filas de hoy | El ordenador estaba apagado o la tarea está deshabilitada. Revisa el **Historial** de la tarea. |
| `No hay URLs en urls.txt` | Todas las líneas están vacías o empiezan por `#`. |
| `No se pudo leer la configuración` | Falta `urls.txt` o `estado.json` está dañado. Borra `estado.json` y vuelve a ejecutar. |

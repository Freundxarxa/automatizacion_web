"""Monitor de disponibilidad web.

Comprueba las URLs de urls.txt, guarda cada resultado en registro.csv
y avisa por Telegram cuando una URL empieza a fallar o se recupera.
"""

import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from time import perf_counter

import requests


# --- Configuración ---------------------------------------------------------

CARPETA = Path(__file__).resolve().parent
ARCHIVO_URLS = CARPETA / "urls.txt"
ARCHIVO_REGISTRO = CARPETA / "registro.csv"
ARCHIVO_ESTADO = CARPETA / "estado.json"

# Segundos máximos que puede tardar una respuesta. Se cambia con la
# variable de entorno MONITOR_TIEMPO_MAXIMO (por defecto, 10 segundos).
TIEMPO_MAXIMO = float(os.getenv("MONITOR_TIEMPO_MAXIMO", "10"))


# --- Lectura de la configuración -------------------------------------------

def leer_urls():
    """Devuelve las URLs de urls.txt, sin líneas vacías ni comentarios."""
    urls = []
    with ARCHIVO_URLS.open(encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if linea and not linea.startswith("#"):
                urls.append(linea)
    return urls


# --- Comprobación de una URL -----------------------------------------------

def comprobar_url(url):
    """Hace una petición a la URL y devuelve un diccionario con el resultado.

    Estados posibles: OK, ERROR HTTP, TIEMPO EXCEDIDO y ERROR DE CONEXION.
    """
    inicio = perf_counter()
    try:
        respuesta = requests.get(url, timeout=TIEMPO_MAXIMO)
    except requests.Timeout:
        estado = "TIEMPO EXCEDIDO"
        detalle = f"Sin respuesta en {TIEMPO_MAXIMO:g} s"
    except requests.RequestException as error:
        estado = "ERROR DE CONEXION"
        detalle = type(error).__name__
    else:
        segundos = perf_counter() - inicio
        if respuesta.status_code >= 400:
            estado = "ERROR HTTP"
            detalle = f"HTTP {respuesta.status_code} {respuesta.reason}"
        elif segundos > TIEMPO_MAXIMO:
            estado = "TIEMPO EXCEDIDO"
            detalle = f"Tardó {segundos:.1f} s (máximo {TIEMPO_MAXIMO:g} s)"
        else:
            estado = "OK"
            detalle = f"HTTP {respuesta.status_code}"

    tiempo_ms = round((perf_counter() - inicio) * 1000)
    return {"url": url, "estado": estado, "tiempo_ms": tiempo_ms, "detalle": detalle}


# --- Registro y estado -----------------------------------------------------

def guardar_en_registro(resultado):
    """Añade una fila a registro.csv. Crea la cabecera la primera vez."""
    es_nuevo = not ARCHIVO_REGISTRO.exists()
    with ARCHIVO_REGISTRO.open("a", newline="", encoding="utf-8") as archivo:
        columnas = ["fecha", "url", "estado", "tiempo_ms", "detalle"]
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        if es_nuevo:
            escritor.writeheader()
        fila = dict(resultado)
        fila["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        escritor.writerow(fila)


def leer_estado():
    """Devuelve el último estado conocido de cada URL: "OK" o "FALLO"."""
    if not ARCHIVO_ESTADO.exists():
        return {}
    with ARCHIVO_ESTADO.open(encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_estado(estado):
    with ARCHIVO_ESTADO.open("w", encoding="utf-8") as archivo:
        json.dump(estado, archivo, indent=2, ensure_ascii=False)


# --- Telegram --------------------------------------------------------------

def enviar_telegram(texto):
    """Envía un mensaje al chat configurado. Devuelve True si se envió."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("  Aviso no enviado: faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
        return False

    try:
        respuesta = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": texto},
            timeout=10,
        )
        respuesta.raise_for_status()
    except requests.RequestException as error:
        # No se muestra el error completo porque la URL contiene el token.
        print(f"  Aviso no enviado: Telegram respondió con error ({type(error).__name__})")
        return False
    return True


def avisar_si_cambia(resultado, estado):
    """Envía un aviso solo cuando la URL pasa de OK a FALLO o de FALLO a OK."""
    url = resultado["url"]
    anterior = estado.get(url, "OK")
    actual = "OK" if resultado["estado"] == "OK" else "FALLO"

    if actual == anterior:
        return  # Sin cambios: no se repite el aviso.

    if actual == "FALLO":
        texto = f"FALLO en {url}\nProblema: {resultado['estado']} - {resultado['detalle']}"
    else:
        texto = f"RECUPERADA {url}\nVuelve a responder ({resultado['detalle']})"

    # El estado solo cambia si el aviso se ha enviado. Si Telegram falla,
    # se volverá a intentar en la siguiente ejecución.
    if enviar_telegram(texto):
        estado[url] = actual
        guardar_estado(estado)
        print("  Aviso enviado por Telegram")


# --- Programa principal ----------------------------------------------------

def main():
    if TIEMPO_MAXIMO <= 0:
        print("MONITOR_TIEMPO_MAXIMO debe ser mayor que cero", file=sys.stderr)
        return 1

    try:
        urls = leer_urls()
        estado = leer_estado()
    except (OSError, json.JSONDecodeError) as error:
        print(f"No se pudo leer la configuración: {error}", file=sys.stderr)
        return 1

    if not urls:
        print("No hay URLs en urls.txt", file=sys.stderr)
        return 1

    for url in urls:
        resultado = comprobar_url(url)
        guardar_en_registro(resultado)
        print(f"{resultado['estado']}: {url} ({resultado['tiempo_ms']} ms) {resultado['detalle']}")
        avisar_si_cambia(resultado, estado)

    return 0


if __name__ == "__main__":
    sys.exit(main())

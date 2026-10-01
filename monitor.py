import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from time import perf_counter

import requests


PROJECT_DIR = Path(__file__).resolve().parent
URLS_FILE = PROJECT_DIR / "urls.txt"
LOG_FILE = PROJECT_DIR / "checks.csv"
STATE_FILE = PROJECT_DIR / "state.json"
TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))


def load_urls():
    with URLS_FILE.open("r", encoding="utf-8") as file:
        return [
            line.strip()
            for line in file
            if line.strip() and not line.strip().startswith("#")
        ]


def check_url(url):
    started_at = perf_counter()
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        elapsed_seconds = perf_counter() - started_at
        response_ms = round(elapsed_seconds * 1000, 2)

        if elapsed_seconds > TIMEOUT_SECONDS:
            return {
                "url": url,
                "status": "TIEMPO AGOTADO",
                "response_ms": response_ms,
                "detail": f"La respuesta supero el limite de {TIMEOUT_SECONDS:g} segundos",
            }

        if response.status_code >= 400:
            return {
                "url": url,
                "status": f"ERROR HTTP {response.status_code}",
                "response_ms": response_ms,
                "detail": f"HTTP {response.status_code} {response.reason}",
            }

        return {
            "url": url,
            "status": "OK",
            "response_ms": response_ms,
            "detail": f"HTTP {response.status_code}",
        }
    except requests.Timeout:
        response_ms = round((perf_counter() - started_at) * 1000, 2)
        return {
            "url": url,
            "status": "TIEMPO AGOTADO",
            "response_ms": response_ms,
            "detail": f"La respuesta supero el limite de {TIMEOUT_SECONDS:g} segundos",
        }
    except requests.RequestException as error:
        response_ms = round((perf_counter() - started_at) * 1000, 2)
        return {
            "url": url,
            "status": "ERROR DE CONEXION",
            "response_ms": response_ms,
            "detail": str(error),
        }


def append_result(result):
    file_exists = LOG_FILE.exists()
    with LOG_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["fecha", "url", "estado", "tiempo_ms", "detalle"],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(
            {
                "fecha": datetime.now().astimezone().isoformat(timespec="seconds"),
                "url": result["url"],
                "estado": result["status"],
                "tiempo_ms": result["response_ms"],
                "detalle": result["detail"],
            }
        )


def load_state():
    if not STATE_FILE.exists():
        return {}
    with STATE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=2, ensure_ascii=False)


def send_telegram(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError(
            "Configura las variables TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID"
        )

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": message},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    telegram_result = response.json()
    if not telegram_result.get("ok"):
        raise RuntimeError("Telegram no pudo enviar el mensaje")


def notify_on_change(result, state):
    url = result["url"]
    was_failing = state.get(url, False)
    is_failing = result["status"] != "OK"

    if is_failing != was_failing:
        if is_failing:
            message = (
                f"FALLO: {url}\n"
                f"Problema: {result['detail']}\n"
                f"Estado: {result['status']}"
            )
        else:
            message = (
                f"RECUPERADA: {url}\n"
                f"La pagina vuelve a responder ({result['detail']})."
            )

        try:
            send_telegram(message)
        except (requests.RequestException, RuntimeError, ValueError) as error:
            print(f"No se pudo enviar el aviso de {url}: {error}", file=sys.stderr)
            return

    state[url] = is_failing
    save_state(state)


def main():
    if TIMEOUT_SECONDS <= 0:
        print("REQUEST_TIMEOUT_SECONDS debe ser mayor que cero", file=sys.stderr)
        return 1

    try:
        urls = load_urls()
        state = load_state()
    except (OSError, json.JSONDecodeError) as error:
        print(f"No se pudo leer la configuracion: {error}", file=sys.stderr)
        return 1

    if not urls:
        print("No hay URLs configuradas en urls.txt", file=sys.stderr)
        return 1

    for url in urls:
        result = check_url(url)
        append_result(result)
        print(
            f"{result['status']}: {url} "
            f"({result['response_ms']} ms) - {result['detail']}"
        )
        notify_on_change(result, state)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
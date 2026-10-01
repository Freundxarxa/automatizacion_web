"""Pruebas automáticas del monitor.

Levantan un servidor web local y sustituyen el envío a Telegram por una
lista, así no hace falta Internet ni token. Los archivos de registro y
estado se crean en una carpeta temporal.

Ejecutar:  .venv\\Scripts\\python.exe -m unittest -v
"""

import csv
import functools
import tempfile
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import monitor


class SilencioHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class PruebasMonitor(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        carpeta = Path(self.temporal.name)
        self.web = carpeta / "web"
        self.web.mkdir()
        (self.web / "index.html").write_text("Inicio", encoding="utf-8")

        handler = functools.partial(SilencioHandler, directory=str(self.web))
        self.servidor = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{self.servidor.server_port}"
        self.inicio = f"{base}/"
        self.contacto = f"{base}/contacto.html"

        # Archivos del monitor en la carpeta temporal
        self.originales = (monitor.ARCHIVO_URLS, monitor.ARCHIVO_REGISTRO,
                           monitor.ARCHIVO_ESTADO, monitor.enviar_telegram)
        monitor.ARCHIVO_URLS = carpeta / "urls.txt"
        monitor.ARCHIVO_REGISTRO = carpeta / "registro.csv"
        monitor.ARCHIVO_ESTADO = carpeta / "estado.json"
        monitor.ARCHIVO_URLS.write_text(
            f"# comentario\n{self.inicio}\n\n{self.contacto}\n", encoding="utf-8"
        )

        # Telegram falso: guarda los mensajes en una lista
        self.mensajes = []
        self.telegram_funciona = True

        def telegram_falso(texto):
            if self.telegram_funciona:
                self.mensajes.append(texto)
            return self.telegram_funciona

        monitor.enviar_telegram = telegram_falso

    def tearDown(self):
        self.servidor.shutdown()
        self.servidor.server_close()
        (monitor.ARCHIVO_URLS, monitor.ARCHIVO_REGISTRO,
         monitor.ARCHIVO_ESTADO, monitor.enviar_telegram) = self.originales
        self.temporal.cleanup()

    def filas_registro(self):
        with monitor.ARCHIVO_REGISTRO.open(encoding="utf-8") as archivo:
            return list(csv.DictReader(archivo))

    def test_lee_urls_sin_comentarios_ni_lineas_vacias(self):
        self.assertEqual(monitor.leer_urls(), [self.inicio, self.contacto])

    def test_pagina_disponible_no_avisa(self):
        resultado = monitor.comprobar_url(self.inicio)
        self.assertEqual(resultado["estado"], "OK")
        monitor.avisar_si_cambia(resultado, {})
        self.assertEqual(self.mensajes, [])

    def test_error_repetido_y_recuperacion(self):
        # 1. contacto.html no existe: un aviso de fallo
        monitor.main()
        self.assertEqual(len(self.mensajes), 1)
        self.assertIn("FALLO", self.mensajes[0])
        self.assertIn("404", self.mensajes[0])

        # 2. Sigue fallando: no se repite el aviso
        monitor.main()
        self.assertEqual(len(self.mensajes), 1)

        # 3. Se crea la página: aviso de recuperación
        (self.web / "contacto.html").write_text("Contacto", encoding="utf-8")
        monitor.main()
        self.assertEqual(len(self.mensajes), 2)
        self.assertIn("RECUPERADA", self.mensajes[1])

        # Cada ejecución guarda una fila por URL
        filas = self.filas_registro()
        self.assertEqual(len(filas), 6)
        self.assertEqual(set(filas[0]), {"fecha", "url", "estado", "tiempo_ms", "detalle"})

    def test_error_de_conexion(self):
        self.servidor.shutdown()
        self.servidor.server_close()
        resultado = monitor.comprobar_url(self.inicio)
        self.assertIn(resultado["estado"], ("ERROR DE CONEXION", "TIEMPO EXCEDIDO"))

    def test_tiempo_excedido(self):
        original = monitor.TIEMPO_MAXIMO
        monitor.TIEMPO_MAXIMO = 0.000001
        try:
            resultado = monitor.comprobar_url(self.inicio)
        finally:
            monitor.TIEMPO_MAXIMO = original
        self.assertEqual(resultado["estado"], "TIEMPO EXCEDIDO")

    def test_si_telegram_falla_se_reintenta(self):
        self.telegram_funciona = False
        monitor.main()
        self.assertEqual(monitor.leer_estado(), {})  # El estado no cambia

        self.telegram_funciona = True
        monitor.main()
        self.assertEqual(len(self.mensajes), 1)  # Se envía en la siguiente
        self.assertEqual(monitor.leer_estado()[self.contacto], "FALLO")


if __name__ == "__main__":
    unittest.main()

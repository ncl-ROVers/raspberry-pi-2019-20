"""
TODO: Document
"""
from src import *
import threading
import time


def _handle_surface(s: Server):
    """
    TODO: Document
    """
    while True:
        s.accept()
        while s.is_surface_connected:
            time.sleep(CONNECTION_CHECK_DELAY)
        s.cleanup()


def _handle_arduino(a: Arduino):
    """
    TODO: Document
    """
    a.connect()
    while True:
        while a.connected:
            time.sleep(CONNECTION_CHECK_DELAY)
        a.reconnect()


if __name__ == '__main__':
    dm = DataManager()
    server = Server(dm)
    threading.Thread(target=_handle_surface, args=(server,)).start()
    for ard in server.arduinos:
        threading.Thread(target=_handle_arduino, args=(ard,)).start()

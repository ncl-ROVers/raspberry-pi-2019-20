"""
Main
====

Main execution module.

Creates the data manager and server instances, as well as starts separate threads for each communication channel.

To run the code, call::
    python raspberry-pi

where `python` is Python3.8.1 version and `raspberry-pi` is relative or absolute path to the directory in which this
file is.
"""
from src import *
import threading
import time


def _handle_surface(s: Server):
    """
    Helper function used to keep communicating with surface.

    :param s: Server's instance
    """
    while True:
        s.accept()
        while s.surface_connected:
            time.sleep(CONNECTION_CHECK_DELAY)
        s.cleanup()


def _handle_arduino(a: Arduino):
    """
    Helper function used to keep communicating with an Arduino.

    :param s: Arduino's instance
    """
    a.connect()
    while True:
        while a.connected:
            time.sleep(CONNECTION_CHECK_DELAY)
        a.reconnect()


if __name__ == '__main__':

    # Create instances of the data manager and the server, and pass the former to the latter
    dm = DataManager()
    server = Server(dm)

    # Create a thread for each communication channel - 1 for surface and multiple ones for arduino-s
    threading.Thread(target=_handle_surface, args=(server,)).start()
    for ard in server.arduinos:
        threading.Thread(target=_handle_arduino, args=(ard,)).start()

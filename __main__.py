"""
TODO: Document
"""
from src import *
from time import sleep

if __name__ == '__main__':
    dm = DataManager()
    server = Server(dm)
    while True:
        process = server.accept()
        while server.is_surface_connected:
            print("still alive...")
            sleep(1)
        server.cleanup()

"""
Connection
==========

Module storing an implementation of a socket-based connection with the ROV.
"""
import socket as _socket
import json as _json
import multiprocessing as _mp
import typing as _typing
from . import data_manager as _dm, Log as _Log


class Server:
    """
    TODO: Document
    """

    def __init__(self, dm: _dm.DataManager, *, ip: str = "localhost", port: int = 50000):
        """
        TODO: Document
        """
        self._dm = dm
        self._ip = ip
        self._port = port
        self._address = self._ip, self._port

        # Initialise the socket and the connection status
        self._socket = self._new_socket()

        # Initialise the process for sending and receiving the data
        self._process = self._new_process()

        # For hinting, declare some values
        self._client_socket: _typing.Union[None, _socket.socket] = None
        self._client_address: _typing.Union[None, _typing.Tuple] = None

        # --= Set up communication with Arduino-s =--
        # TODO

    @property
    def is_surface_connected(self) -> bool:
        """
        TODO: Document
        """
        return self._process.is_alive()

    def accept(self):
        """
        TODO: Document
        """
        try:
            _Log.info(f"{self._socket.getsockname()} is waiting for a client connection...")

            # Wait for a connection (accept function blocks the program until a client connects to the server)
            self._client_socket, self._client_address = self._socket.accept()

            # Once the client is connected, start the data exchange process
            _Log.info(f"Client with address {self._client_address} connected")
            self._process.start()

        except (ConnectionError, OSError) as e:
            _Log.error(f"Failed to listen to incoming connections - {e}")
            self.cleanup(ignore_errors=True)

    def cleanup(self, ignore_errors: bool = False):
        """
        TODO: Document
        """
        try:
            self._dm.set(_dm.Device.SURFACE, set_default=True)
            if self._process.is_alive():
                self._process.terminate()
            self._process = self._new_process()
            self._client_socket.shutdown(_socket.SHUT_RDWR)
            self._client_socket.close()
        except (ConnectionError, OSError) as e:
            if not ignore_errors:
                raise e
            else:
                _Log.debug(f"Server ignoring the following error - {e}")

    def _communicate(self):
        """
        TODO: Document
        """
        while True:
            try:
                _Log.debug("Receiving data from surface")
                data = self._client_socket.recv(4096)

                # Exit if connection closed by client
                if not data:
                    _Log.info("Connection closed by client")
                    break

                try:
                    data = _json.loads(data.decode("utf-8").strip())
                except (UnicodeError, _json.JSONDecodeError) as e:
                    _Log.debug(f"Failed to decode following data: {data} - {e}")

                # Only handle valid, non-empty data
                if data and isinstance(data, dict):
                    self._dm.set(_dm.Device.SURFACE, **data)

                # Encode the transmission data as JSON and send the bytes to the server
                _Log.debug("Sending data to surface")
                self._client_socket.sendall(bytes(_json.dumps(self._dm.get(_dm.Device.SURFACE)), encoding="utf-8"))

            except (ConnectionError, OSError) as e:
                _Log.error(f"An error occurred while communicating with the client - {e}")
                break

    def _new_socket(self) -> _socket.socket:
        """
        TODO: Document
        """
        socket = _socket.socket()

        try:
            socket.bind(self._address)
        except _socket.error:
            print("Failed to bind socket to the given address {}:{} ".format(self._ip, self._port))

        socket.listen(1)
        return socket

    def _new_process(self) -> _mp.Process:
        """
        TODO: Document
        """
        return _mp.Process(target=self._communicate)

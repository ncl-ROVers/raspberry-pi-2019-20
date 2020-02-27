"""
Server
======

Module storing an implementation of a socket-based and serial-based server, to exchange data with surface and the
Arduino-s.
"""
import socket as _socket
import json as _json
import threading as _threading
import typing as _typing
import serial as _serial
from . import data_manager as _dm, Log as _Log
from .utils import Device as _Device, ARDUINO_PORTS as _ARDUINO_PORTS, \
    SERIAL_READ_TIMEOUT as _SERIAL_READ_TIMEOUT, SERIAL_WRITE_TIMEOUT as _SERIAL_WRITE_TIMEOUT


class Arduino:
    """
    Arduino class used to handle serial communication between the ROV and an Arduino.

    Functions
    ---------

    The following list shortly summarises each function:

        * __init__ - a constructor to create and initialise serial and process related constructs
        * connected - a getter to check if the communication is still happening
        * connect - a method used to connect to Arduino
        * disconnect - a method used to disconnect with the Arduino
        * reconnect - a helper method used to disconnect and connect in one step
        * _communicate - a private method which does the actual communication with the Arduino
        * _new_thread - a private method which re-initialises the thread

    Usage
    -----

    The Arduino-s are created via server, and can be accessed in the following way::

        arduinos = server.arduinos

    While working, the code should check if the communication is happening, to detect when it stops::

        if not arduino.connected():
            arduino.reconnect()

    .. warning::

        The calling functions must handle when the attempts to connect, disconnect etc. should be made, and detect when
        the communication stops (for example by checking the status). This is NOT handled internally.

    .. note::

        You should check __main__.py to see how the surface-rov and rov-arduino(s) connections are kept alive.
    """

    def __init__(self, dm: _dm.DataManager, port: str):
        """
        Standard constructor.

        Initialises the socket and the processes, as well as create instances of Arduino.

        :param dm: DataManager's instance to share the data correctly
        :param port: Arduino port
        """
        self._dm = dm
        self._port = port
        self._thread = self._new_thread()

        # Setup the PySerial structure
        self._serial = _serial.Serial(baudrate=115200)
        self._serial.port = self._port
        self._serial.write_timeout = _SERIAL_WRITE_TIMEOUT
        self._serial.timeout = _SERIAL_READ_TIMEOUT

        # The device field will be used to determine how to parse the data
        self._device = _Device.UNKNOWN

    @property
    def connected(self):
        """
        Getter to check if the communication is happening.
        """
        return self._thread.is_alive()

    def connect(self):
        """
        Method used to connect to the Arduino and start exchanging the data.

        The steps are as follows:

            1. Open a serial connection (while loop to handle serial-related issues and make sure it opens correctly)
            2. Start the communication thread

        """
        if self.connected:
            _Log.error(f"Can't connect - already connected to {self._port}")
            return

        _Log.info(f"Connecting to {self._port}...")
        while True:
            try:
                if not self._serial.is_open:
                    self._serial.open()
                    break
            except _serial.SerialException as e:
                _Log.debug(f"Failed to connect to {self._port} - {e}")
        _Log.info(f"Connected to {self._port}")
        self._thread.start()

    def disconnect(self):
        """
        Method used to disconnect from the Arduino and stop exchanging the data.

        The steps are as follows:

            1. Close the serial connection
            2. Re-initialise the thread
            3. Forget the device's ID it was connected to

        """
        if not self._serial.is_open:
            _Log.error(f"Can't disconnect from {self._port} - not connected")

        # Clean up the serial connection
        try:
            if self._serial.is_open:
                self._serial.close()
        except _serial.SerialException as e:
            _Log.error(f"Failed to close the connection with {self._port}")

        # Clean up the communication thread
        self._thread = self._new_thread()

        # Set the connection status to disconnected, if the id was known
        if self._device != _Device.UNKNOWN:
            self._dm.set(self._device, **{self._device.value: False})

        # Forget the device id
        self._device = _Device.UNKNOWN

    def reconnect(self):
        """
        Method used to reconnect to the Arduino (disconnect and connect).
        """
        self.disconnect()
        self.connect()

    def _communicate(self):
        """
        Function used to exchange the data with the Arduino.

        Pre-communicates to retrieve the ID and set the device's ID, starts processing data immediately after.

        Being a separate process, it is safe to let this function run in an infinite while loop, because to stop this
        communication it is sufficient to stop (terminate) the process (OS-level interruption).

        Breaks the infinite loops on errors, leaving the calling code to accommodate for them.
        """
        # Pre-communication to determine the ID (listening only), ignore time-outs and invalid data
        while True:
            try:
                data = self._serial.read_until().strip()
                if not data:
                    continue
                else:
                    try:
                        self._device = _Device(_json.loads(data.decode("utf-8"))["id"])
                        _Log.info(f"Detected a valid device at {self._port} - {self._device.name}")

                        # Knowing the id, set the connection status to connected (True)
                        self._dm.set(self._device, **{self._device.value: True})
                        break
                    except (UnicodeError, _json.JSONDecodeError, KeyError, ValueError) as e:
                        _Log.error(f"Failed to decode (and assign device id) following data: {data} - {e}")
                        return

            except _serial.SerialException as e:
                _Log.error(f"Lost connection to {self._port} - {e}")
                return
            except ValueError as e:
                _Log.error(f"Invalid device ID received from {self._port} - {e}")
                return

        while True:
            try:
                if data:
                    _Log.debug(f"Received data from {self._port} - {data}")

                    try:
                        data = _json.loads(data.decode("utf-8").strip())

                        # Remove ID from the data to avoid setting it upstream, disconnect in case of errors
                        if "id" not in data or data["id"] != self._device.value:
                            _Log.error(f"ID key not in {data} or key doesn't match {self._device.value}")
                            break
                        else:
                            del data["id"]

                        self._dm.set(self._device, **data)
                    except (UnicodeError, _json.JSONDecodeError) as e:
                        _Log.warning(f"Failed to decode following data: {data} - {e}")

                else:
                    _Log.debug(f"Timed out reading from {self._port}, clearing the buffer")
                    self._serial.reset_output_buffer()

                data = bytes(_json.dumps(self._dm.get(self._device)) + "\n", encoding="utf-8")
                _Log.debug(f"Writing data to {self._port} - {data}")
                self._serial.write(data)

                data = self._serial.read_until().strip()
            except _serial.SerialException as e:
                _Log.error(f"Lost connection to {self._port} - {e}")
                break

    def _new_thread(self) -> _threading.Thread:
        """
        Function used as a default communication thread generator.

        :return: New, correctly configured Thread object
        """
        return _threading.Thread(target=self._communicate)


class Server:
    """
    Server class used as a two-way data exchange medium (with both the surface and the Arduino-s).

    Handles TCP-based transmission with surface and Serial-based transmission(s) with Arduino-s

    Functions
    ---------

    The following list shortly summarises each function:

        * __init__ - a constructor to create and initialise socket, serial and process related constructs
        * surface_connected - a getter to check if the communication is still happening
        * arduinos - a getter to retrieve the set of Arduino instances
        * accept - a method used to accept connections from surface
        * cleanup - a method used to (attempt to) clean-up the resources
        * _communicate - a private method which does the actual communication with surface (recv and send)
        * _new_socket - a private method which re-initialises the socket
        * _new_thread - a private method which re-initialises the thread
        * _new_arduino - a private method which creates a new Arduino

    Usage
    -----

    The server should be created as follows (data manager required)::

        dm = DataManager()
        server = Server(dm)

    While working, the code should check if the communication is happening, to detect when it stops::

        if not server.surface_connected:
            server.cleanup()
            server.accept()

    .. warning::

        The calling functions must handle when the attempts to connect, disconnect etc. should be made, and detect when
        the communication stops (for example by checking the status). This is NOT handled internally.

    .. note::

        You should check __main__.py to see how the surface-rov and rov-arduino(s) connections are kept alive.
    """

    def __init__(self, dm: _dm.DataManager, *, ip: str = "0.0.0.0", port: int = 50000):
        """
        Standard constructor.

        Initialises the socket and the processes, as well as create instances of Arduino.

        :param dm: DataManager's instance to share the data correctly
        :param ip: Host ip
        :param port: Host port
        """
        self._dm = dm
        self._ip = ip
        self._port = port
        self._address = self._ip, self._port

        # Initialise the socket and the connection status
        self._socket = self._new_socket()

        # Initialise the process for sending and receiving the data
        self._thread = self._new_thread()

        # For hinting, declare some values
        self._client_socket: _typing.Union[None, _socket.socket] = None
        self._client_address: _typing.Union[None, _typing.Tuple] = None

        # Set up communication with Arduino-s
        self._arduinos = {self._new_arduino(port) for port in _ARDUINO_PORTS}

    @property
    def surface_connected(self) -> bool:
        """
        Helper getter used to check if the communication with surface is still happening.
        """
        return self._thread.is_alive()

    @property
    def arduinos(self) -> _typing.Set[Arduino]:
        """
        Getter for the set of Arduino-s.
        """
        return self._arduinos

    def accept(self):
        """
        Method used to accept incoming connections from surface.

        On errors, the cleanup function is called.
        """
        try:
            _Log.info(f"{self._socket.getsockname()} is waiting for a client connection...")

            # Wait for a connection (accept function blocks the program until a client connects to the server)
            self._client_socket, self._client_address = self._socket.accept()

            # Once the client is connected, start the data exchange process
            _Log.info(f"Client with address {self._client_address} connected")
            self._thread.start()

        except (ConnectionError, OSError) as e:
            _Log.error(f"Failed to listen to incoming connections - {e}")
            self.cleanup(ignore_errors=True)

    def cleanup(self, ignore_errors: bool = False):
        """
        Method used to cleanup the connection and the communication process.

        The steps are as follows:

            1. Set the default values and send them to connected Arduino-s
            2. Create a new thread
            3. Shutdown and close the client socket

        Errors can be optionally ignored with the `ignore_errors` flag.

        :param ignore_errors: Boolean determining whether the errors should be propagated or not
        """
        try:
            self._dm.set(_Device.SURFACE, set_default=True)
            self._thread = self._new_thread()
            self._client_socket.shutdown(_socket.SHUT_RDWR)
            self._client_socket.close()
        except (ConnectionError, OSError) as e:
            if not ignore_errors:
                raise e
            else:
                _Log.debug(f"Server ignoring the following error - {e}")

    def _communicate(self):
        """
        Function used to exchange the data with surface.

        Being a separate process, it is safe to let this function run in an infinite while loop, because to stop this
        communication it is sufficient to stop (terminate) the process (OS-level interruption).

        Breaks the infinite loop on errors, leaving the calling code to accommodate for that.
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
                    _Log.warning(f"Failed to decode following data: {data} - {e}")

                # Only handle valid, non-empty data
                if data and isinstance(data, dict):
                    self._dm.set(_Device.SURFACE, **data)

                # Encode the transmission data as JSON and send the bytes to the server
                data = self._dm.get(_Device.SURFACE)
                _Log.debug(f"Sending data to surface - {data}")
                self._client_socket.sendall(bytes(_json.dumps(data), encoding="utf-8"))

            except (ConnectionError, OSError) as e:
                _Log.error(f"An error occurred while communicating with the client - {e}")
                break

    def _new_socket(self) -> _socket.socket:
        """
        Function used as a default socket generator.

        :return: New, correctly configured socket object
        """
        socket = _socket.socket()

        try:
            socket.bind(self._address)
        except _socket.error:
            _Log.error("Failed to bind socket to the given address {}:{} ".format(self._ip, self._port))

        socket.listen(1)
        return socket

    def _new_thread(self) -> _threading.Thread:
        """
        Function used as a default communication thread generator.

        :return: New, correctly configured Thread object
        """
        return _threading.Thread(target=self._communicate)

    def _new_arduino(self, port: str) -> Arduino:
        """
        Function used as a default Arduino instance generator.

        :return: New, correctly configured Arduino instance
        """
        return Arduino(self._dm, port)

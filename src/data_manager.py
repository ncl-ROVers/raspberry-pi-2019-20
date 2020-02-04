"""
Data manager
============

Module storing an implementation of a data manager, exposing some common values via a dictionary.
"""
from .utils import Device as _Device, DEFAULTS as _DEFAULTS, RAMP_KEYS as _RAMP_KEYS, RAMP_RATE as _RAMP_RATE
from .logger import Log as _Log


class DataManager:
    """
    Class representing a data manager which has access to internal per-device-dictionaries.

    Provides getter and setter methods to each dictionary.

    Functions
    ---------

    The following list shortly summarises each function:

        * __init__ - a constructor to create the dictionaries and populate them with the default values
        * get - a getter controlling access to the internal dictionaries
        * set - a setter controlling access to the internal dictionaries
        * _handle_data_from_surface - a helper method used to gradually modify some values

    Usage
    -----

    You should import the module and create the data manager::

        from .data_manager import DataManager
        dm = DataManager()

    To use it, you must pass a reference to the manager to other parts of the code::

        def func(dm: DataManager):
            dm.set(Device.SURFACE, test=5)
            print(dm.get(Device.ARDUINO_A))
    """

    def __init__(self):
        """
        Standard constructor.

        Creates a data dictionary for each device connected to the server. The data represents values to send to the
        device it is registered under.
        """
        self._surface = dict()

        # Create a dictionary mapping each index to a corresponding location
        self._data = {
            _Device.SURFACE: _DEFAULTS[_Device.SURFACE].copy(),
            _Device.ARDUINO_A: _DEFAULTS[_Device.ARDUINO_A].copy()
        }

    def get(self, device: _Device, *args) -> dict:
        """
        Method used to access the cached values.

        Returns selected data or full dictionary if no args passed. The data is sent to a selected device in the server,
        meaning that retrieving data for a specific device means retrieving the target values it should internally
        store.

        :param device: Device to specify which device to retrieve the data from
        :param args: Keys to retrieve (returns all keys if no args are passed)
        :return: Dictionary with the data
        """
        _Log.debug(f"Retrieving data manager values from {device.name}")

        # Return full dictionary if no args passed
        if not args:
            return self._data[device].copy()

        # Raise error early if any of the keys are not registered
        if not set(args).issubset(set(self._data[device].keys())):
            raise KeyError(f"{set(args)} is not a subset of {set(self._data[device].keys())}")
        else:
            _Log.debug(f"Specific args passed - {args}")
            return {key: self._data[device][key] for key in args}

    def set(self, from_device: _Device, set_default: bool = False, **kwargs):
        """
        Function used to modify the internal data.

        If the values are coming from surface, they are dispatched into separated dictionaries, specific to each
        Arduino. Otherwise, the values from the Arduino override specific values in surface transmission data.

        Keep in mind that if the keys received are within the RAMP_KEYS constant, the values will not be changed to the
        target values, but rather be modified by a small value multiple times.

        `set_default` argument is treated with a priority, and if set to True the data is replaced with default values
        immediately, ignoring kwargs and simply setting all values possible to default (surface only).

        :param from_device: Source device which attempts to set the data
        :param set_default: If set to true then the default data is used to set the values (from surface)
        :param kwargs: Key, value pairs of data to modify.
        """
        _Log.debug(f"Setting data manager values from {from_device.name}")
        if set_default:
            _Log.debug("Setting the values to default")

        # Surface will dispatch the values to different dictionaries
        if from_device == _Device.SURFACE:

            # Override each Arduino dictionary with the defaults
            if set_default:
                self._data[_Device.ARDUINO_A] = _DEFAULTS[_Device.ARDUINO_A]

            for k, v in kwargs.items():
                if k in self._data[_Device.ARDUINO_A]:
                    self._handle_data_from_surface(_Device.ARDUINO_A, k, v)
                else:
                    raise KeyError(f"Couldn't find {k} key in any of the Arduino dictionaries")

        # Arduino-s will simply override relevant values in surface dictionary
        else:
            if set_default:
                _Log.error(f"Setting the default values is only supported for surface, not {from_device.name}")
            else:
                if not set(kwargs.keys()).issubset(set(self._data[_Device.SURFACE].keys())):
                    raise KeyError(f"{set(kwargs.keys())} is not a subset of {set(self._data[_Device.SURFACE].keys())}")
                else:
                    for k, v in kwargs.items():
                        self._data[_Device.SURFACE][k] = v

    def _handle_data_from_surface(self, device: _Device, key: str, value: int):
        """
        Helper method used to ramp up/down a specific value within Arduino dictionary, or set it to a specific value.

        :param device: Device to update the values of
        :param key: Key under which the value should change
        :param value: Value to set or calculate the difference and determine positive (up) or negative (down) ramping
        """
        if key in _RAMP_KEYS:
            difference = self._data[device][key] - value

            if difference > 0:
                self._data[device][key] -= _RAMP_RATE
            elif difference < 0:
                self._data[device][key] += _RAMP_RATE

        else:
            self._data[_Device.ARDUINO_A][key] = value

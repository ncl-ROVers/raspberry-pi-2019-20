"""
Data manager
============

Module storing an implementation of a data manager, exposing some common values via a dictionary.
"""
from .utils import *
from .logger import Log


class DataManager:
    """
    TODO: Document
    """

    def __init__(self):
        """
        Standard constructor.

        Creates a data dictionary for each device connected to the server.
        """
        self._surface = dict()

        # Create a dictionary mapping each index to a corresponding location
        self._data = {
            Device.SURFACE: DEFAULTS[Device.SURFACE].copy(),
            Device.ARDUINO_A: DEFAULTS[Device.ARDUINO_A].copy()
        }

        # Create a key to ID lookup for performance reasons
        # self._keys_lookup = {v: k for k, values in self._transmission_keys.items() if k != SURFACE for v in values}

    def get(self, device: Device, *args) -> dict:
        """
        Method used to access the cached values.

        Returns selected data or full dictionary if no args passed.

        :param device: Device to specify which device to retrieve the data from
        :param args: Keys to retrieve (returns all keys if no args are passed)
        :return: Dictionary with the data
        """
        Log.debug(f"Retrieving data manager values from {device.name}")

        # Return full dictionary if no args passed
        if not args:
            return self._data[device].copy()

        # Raise error early if any of the keys are not registered
        if not set(args).issubset(set(self._data.keys())):
            raise KeyError(f"{set(args)} is not a subset of {set(self._data.keys())}")
        else:
            Log.debug(f"Specific args passed - {args}")
            return {key: self._data[device][key] for key in args}

    def set(self, from_device: Device, set_default: bool = False, **kwargs):
        """
        Function used to modify the internal data.

        If the values are coming from surface, they are dispatched into separated dictionaries, specific to each
        Arduino. Otherwise, the values from the Arduino override specific values in surface transmission data.

        `set_default` argument is treated with a priority, and if set to True the data is replace with default values
        immediately, ignoring kwargs and simply setting all values possible to default.

        :param from_device: Source device which attempts to set the data
        :param set_default: If set to true then the default data is used to set the values
        :param kwargs: Key, value pairs of data to modify.
        """
        Log.debug(f"Setting data manager values from {from_device.name}")
        if set_default:
            Log.debug("Setting the values to default")

        # Surface will dispatch the values to different dictionaries
        if from_device == Device.SURFACE:

            # Overriding the kwargs with default values is enough on surface side, as all values get dispatched anyway
            if set_default:
                kwargs = DEFAULTS[Device.SURFACE]

            for k, v in kwargs.items():
                if k in self._data[Device.ARDUINO_A]:
                    self._handle_data_from_surface(Device.ARDUINO_A, k, v)
                else:
                    raise KeyError(f"Couldn't find {k} key in any of the Arduino dictionaries")

        # Arduino-s will simply override relevant values in surface dictionary
        else:
            if set_default:
                for k, v in DEFAULTS[from_device].items():
                    self._data[Device.SURFACE][k] = v
            else:
                if not set(kwargs.keys()).issubset(set(self._data.keys())):
                    raise KeyError(f"{set(kwargs.keys())} is not a subset of {set(self._data.keys())}")
                else:
                    for k, v in kwargs.items():
                        self._data[Device.SURFACE][k] = v

    def _handle_data_from_surface(self, device: Device, key: str, value: int):
        """
        Helper method used to ramp up/down a specific value within Arduino dictionary, or set it to a specific value.

        :param device: Device to update the values of
        :param key: Key under which the value should change
        :param value: Value to set or calculate the difference and determine positive (up) or negative (down) ramping
        """
        if key in RAMP_KEYS:
            difference = self._data[device][key] - value

            if difference > 0:
                self._data[device][key] -= RAMP_RATE
            elif difference < 0:
                self._data[device][key] += RAMP_RATE

        else:
            self._data[Device.ARDUINO_A][key] = value

"""
Utils
=====

Standard utils module storing common classes, functions, constants, and other objects.
"""
import os as _os
import enum as _enum

# Declare path to the root folder (raspberry-pi) and the src and logs folders
ROOT_DIR = _os.path.normpath(_os.path.join(_os.path.dirname(__file__), ".."))
SRC_DIR = _os.path.join(ROOT_DIR, "src")
LOG_DIR = _os.path.join(ROOT_DIR, "log")
TESTS_DIR = _os.path.join(ROOT_DIR, "tests")
TESTS_ASSETS_DIR = _os.path.join(TESTS_DIR, "assets")

# Declare Arduino-related constants TODO: Remove COM5 (testing port)
ARDUINO_PORTS = {"/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyACM2", "COM5"}
SERIAL_WRITE_TIMEOUT = 1
SERIAL_READ_TIMEOUT = 1

# Declare the constant to determine how often should the connections be checked
CONNECTION_CHECK_DELAY = 1

# Declare constant for slowly changing up all values and keys affected
RAMP_RATE = 2
RAMP_KEYS = {
    "T_HFP",
    "T_HFS",
    "T_HAP",
    "T_HAS",
    "T_VFP",
    "T_VFS",
    "T_VAP",
    "T_VAS",
    "T_M"
}


class Device(_enum.Enum):
    """
    Device enumeration storing different device definitions.

    A device must be a surface or arduino, or otherwise it is undefined (unknown) and has to be identified first.
    """
    UNKNOWN = "UNKNOWN_DEVICE"
    SURFACE = "SURFACE"
    ARDUINO_O = "A_O"
    ARDUINO_I = "A_I"


# Declare the transmission sets with the default values as initial values
THRUSTER_IDLE = 1500
GRIPPER_IDLE = 1500
CORD_IDLE = 1500
DEFAULTS = {
    Device.SURFACE: {
        "A_O": False,
        "A_I": False,
        "S_O": 0,
        "S_I": 0
    },
    Device.ARDUINO_O: {
        "T_HFP": THRUSTER_IDLE,
        "T_HFS": THRUSTER_IDLE,
        "T_HAP": THRUSTER_IDLE,
        "T_HAS": THRUSTER_IDLE,
        "T_VFP": THRUSTER_IDLE,
        "T_VFS": THRUSTER_IDLE,
        "T_VAP": THRUSTER_IDLE,
        "T_VAS": THRUSTER_IDLE,
        "T_M": THRUSTER_IDLE,
        "M_G": GRIPPER_IDLE,
        "M_C": CORD_IDLE
    },
    Device.ARDUINO_I: {}
}

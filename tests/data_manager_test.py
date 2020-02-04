"""
Data manager related tests.

The tests are first reconfiguring the loggers to use the local assets folder instead of the production environment.
"""
import pytest
import os
from src import *

# Initialise the data manager to None, will get overridden at run time
dm = None


def get_log_files() -> set:
    """
    Helper function used to retrieve a set of absolute paths to the log files.

    :return: A set of paths
    """
    files = set()
    for file in os.listdir(TESTS_ASSETS_DIR):
        if file.endswith(".log"):
            files.add(os.path.join(TESTS_ASSETS_DIR, file))
    return files


def test_getting_default_values():
    """
    Test that data is set to default values at first.
    """
    assert dm.get(Device.SURFACE) == DEFAULTS[Device.SURFACE]
    assert dm.get(Device.ARDUINO_A) == DEFAULTS[Device.ARDUINO_A]


def test_getting_specific_values():
    """
    Test that specific parts of the data can be retrieved.
    """
    assert dm.get(Device.ARDUINO_A, "T_HFP", "T_HFS") == {"T_HFP": 1500, "T_HFS": 1500}


def test_setting_specific_values():
    """
    Test that specific parts of the data can be modified.
    """
    dm.set(Device.SURFACE, T_HFP=0)
    assert dm.get(Device.ARDUINO_A, "T_HFP") == {"T_HFP": 1500 - RAMP_RATE}
    assert dm.get(Device.ARDUINO_A, "T_HFS") == {"T_HFS": 1500}

    dm.set(Device.ARDUINO_A, test=10)
    assert dm.get(Device.SURFACE) == {"test": 10}


def test_setting_default_values():
    """
    Setting the values to default should only work for surface.
    """
    dm.set(Device.SURFACE, set_default=True)
    assert dm.get(Device.ARDUINO_A, "T_HFP") == {"T_HFP": 1500}
    dm.set(Device.ARDUINO_A, set_default=True)
    with open(os.path.join(TESTS_ASSETS_DIR, "error.log")) as f:
        assert "Setting the default values is only supported for surface, not ARDUINO_A" in f.read()


@pytest.fixture(scope="module", autouse=True)
def config():
    """
    PyTest fixture for the configuration function - used to execute config before any test is ran.

    `scope` parameter is used to share fixture instance across the module session, whereas `autouse` ensures all tests
    in session use the fixture automatically.
    """
    # Initialise the data manager
    global dm
    dm = DataManager()

    # Remove all log files from the assets folder.
    for log_file in get_log_files():
        os.remove(log_file)

    # Reconfigure the logger to use a separate folder (instead of the real logs)
    Log.reconfigure(Logger.MAIN, os.path.join(LOG_DIR, "config_main.json"),
                    log_directory=TESTS_ASSETS_DIR)

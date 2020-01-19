"""
TODO: Document
"""
from src import DataManager, Device

if __name__ == '__main__':
    dm = DataManager()
    dm.set(Device.ARDUINO_A, test=0)
    print(dm.get(Device.SURFACE))

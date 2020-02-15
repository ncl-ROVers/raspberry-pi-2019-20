# raspberry-pi
Middle-level

# TODO: Refactor later

Images setup + connection instructions

First steps on your pc:
1. Get Raspbian Buster **lite**
2. Flash it onto SD card
3. Add an empty ssh file into there called `ssh`
4. Connect - `ssh pi@raspberrypi.local`, password `raspberry`

Next steps on PI:
1. `sudo raspi-config` -> config network (wifi connection to get to the internet)
2. `sudo raspi-config` -> advanced -> expand filesystem
3. `sudo apt-get update`
4. Install python 3.8.1:
```
sudo -i
apt-get install python3-dev libffi-dev libssl-dev -y
wget https://www.python.org/ftp/python/3.8.1/Python-3.8.1.tar.xz
tar xJf Python-3.8.1.tar.xz
cd Python-3.8.1
./configure
make
make install
```
5. Update python tools `sudo python3.8 -m pip install --upgrade pip setuptools`
6. Install git `sudo apt-get install git`
7. Pull raspberry-pi code `git clone https://github.com/ncl-ROVers/raspberry-pi.git`
8. Install the code `cd raspberry-pi/ && sudo python3.8 -m pip install .`
9. Add the following `startup.service` into `/etc/systemd/system`:
```
[Unit]
Description=Running ncl_rovers
ConditionPathExists=/usr/local/lib/python3.8/site-packages/ncl_rovers/.autostart

[Service]
Type=forking
ExecStart=/bin/sh /usr/local/lib/python3.8/site-packages/ncl_rovers/.autostart start
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```
10. Run the following commands:
```
sudo systemctl daemon-reload
sudo systemctl enable startup.service
```
11. Reboot `sudo reboot`
12. Verify everything is fine: `ps aux | grep ncl_rovers` or `netstat -tulpn`
13. Connect from surface - you can find out IP with `hostname -I` command (will start with `192`)
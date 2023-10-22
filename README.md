# dbus-wks-inverter Service

### Purpose

This service is meant to be run on a raspberry Pi with Venus OS from Victron.

The Python script cyclically reads data from the WKS Inverter via the MQTT info provided by WKSUpdate Service and publishes information on the dbus, using the service name com.victronenergy.multi. This makes the Venus OS work as if you had a physical Victron RS Multi 48V 6KvA installed.

### Configuration

In the Python file, you should put the IP of your MQTT source that hosts publihed Data.

### Installation

`/data/dbus-wks-inverter/install.sh`

### Debugging

You can check the status of the service with svstat:

`svstat /service/dbus-wks-inverter`

It will show something like this:

`/service/dbus-wks-inverter: up (pid 10078) 325 seconds`

If the number of seconds is always 0 or 1 or any other small number, it means that the service crashes and gets restarted all the time.

When you think that the script crashes, start it directly from the command line:

`python /data/dbus-wks-inverter/dbus-wks-inverter.py`

and see if it throws any error messages.

If the script stops with the message


#### Restart the script

If you want to restart the script, for example after changing it, just run the following command:

`/data/dbus-wks-inverter/restart.sh`

The daemon-tools will restart the scriptwithin a few seconds.

### Hardware

In my installation at home, I am using the following Hardware:

- WKS II (single phase)
- Raspberry Pi 3B+ - For running Venus OS
- Pylontech US2000 Plus - LiFePO Battery


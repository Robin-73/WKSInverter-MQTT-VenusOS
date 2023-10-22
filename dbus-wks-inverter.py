#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

from gi.repository import GLib
import platform
import argparse
import logging
import sys
import os

import dbus
import datetime 
from time import sleep, time
import paho.mqtt.client as mqtt
import configparser  # for config/ini file
import _thread

# import Victron Energy packages
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))
#sys.path.insert(1, os.path.join(os.path.dirname(__file__), './ext/velib_python'))
from vedbus import VeDbusService, VeDbusItemImport
import ve_utils

softwareVersion = '0.10'


# get values from config.ini file
try:
    config_file = (os.path.dirname(os.path.realpath(__file__))) + "/config.ini"
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        if (config['MQTT']['broker_address'] == "IP_ADDR_OR_FQDN"):
            print("ERROR:The \"config.ini\" is using invalid default values like IP_ADDR_OR_FQDN. The driver restarts in 60 seconds.")
            sleep(60)
            sys.exit()
    else:
        print("ERROR:The \"" + config_file + "\" is not found. Did you copy or rename the \"config.sample.ini\" to \"config.ini\"? The driver restarts in 60 seconds.")
        sleep(60)
        sys.exit()

except Exception:
    exception_type, exception_object, exception_traceback = sys.exc_info()
    file = exception_traceback.tb_frame.f_code.co_filename
    line = exception_traceback.tb_lineno
    print(f"Exception occurred: {repr(exception_object)} of type {exception_type} in {file} line #{line}")
    print("ERROR:The driver restarts in 60 seconds.")
    sleep(60)
    sys.exit()

    # Get logging level from config.ini
# ERROR = shows errors only
# WARNING = shows ERROR and warnings
# INFO = shows WARNING and running functions
# DEBUG = shows INFO and data/values
if 'DEFAULT' in config and 'logging' in config['DEFAULT']:
    if config['DEFAULT']['logging'] == 'DEBUG':
        logging.basicConfig(level=logging.DEBUG)
    elif config['DEFAULT']['logging'] == 'INFO':
        logging.basicConfig(level=logging.INFO)
    elif config['DEFAULT']['logging'] == 'ERROR':
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.WARNING)


# get timeout
if 'DEFAULT' in config and 'timeout' in config['DEFAULT']:
    timeout = int(config['DEFAULT']['timeout'])
else:
    timeout = 30

# set variables
connected = 0
last_changed = 0
last_updated = 0

Grid_Voltage=0
Grid_Frequency=0
Grid_Power=0
Grid_Current=0

AC_Output_Voltage=0
AC_Output_Frequency=0
AC_Output_Active_Power=0
AC_Output_Power=0
AC_Output_Current=0
AC_Output_Energy=0

DC_Voltage=0
DC_Current=0
DC_Energy_From=0
DC_Energy_To=0

PV_Voltage=0
PV_Power=-1
PV_Energy=0

# MQTT requests
def on_disconnect(client, userdata, rc):
    global connected
    logging.warning("MQTT client: Got disconnected")
    if rc != 0:
        logging.warning('MQTT client: Unexpected MQTT disconnection. Will auto-reconnect')
    else:
        logging.warning('MQTT client: rc value:' + str(rc))

    while connected == 0:
        try:
            logging.warning("MQTT client: Trying to reconnect")
            client.connect(config['MQTT']['broker_address'])
            connected = 1
        except Exception as err:
            logging.error(f"MQTT client: Error in retrying to connect with broker ({config['MQTT']['broker_address']}:{config['MQTT']['broker_port']}): {err}")
            logging.error("MQTT client: Retrying in 10 seconds")
            connected = 0
            sleep(10)


def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        logging.info("MQTT client: Connected to MQTT broker!")
        connected = 1
        client.subscribe("Grid_Voltage/#")
        client.subscribe("Grid_Frequency/#")

        client.subscribe("AC_Output_Voltage/#")
        client.subscribe("AC_Output_Frequency/#")
        client.subscribe("AC_Output_Current/#")
        client.subscribe("AC_Output_Active_Power/#")
        client.subscribe("AC_Output_Power/#")
        client.subscribe("AC_Output_Energy/#")

        client.subscribe("DC_Voltage/#")
        client.subscribe("DC_Current/#")
        client.subscribe("DC_Energy_From/#")
        client.subscribe("DC_Energy_To/#")

        client.subscribe("PV_current/#")
        client.subscribe("PV_Voltage/#")
        client.subscribe("PV_Power/#")
        client.subscribe("PV_Energy/#")

        client.subscribe("Device_Status/#")
        #client.subscribe(config['MQTT']['topic'])
    else:
        logging.error("MQTT client: Failed to connect, return code %d\n", rc)

def on_message(client, userdata, msg):
    try:

        global \
            last_changed, \
            Grid_Voltage, Grid_Frequency, Grid_Power, Grid_Current, \
            AC_Output_Voltage, AC_Output_Frequency, AC_Output_Active_Power, AC_Output_Power, AC_Output_Current, AC_Output_Energy,\
            DC_Voltage, DC_Current, \
            PV_Voltage, PV_Power, Yield

        if msg.topic=="Grid_Voltage":
            if msg.payload != '' and msg.payload != b'':
                Grid_Voltage=float(msg.payload)
                last_changed = int(time())
        if msg.topic=="Grid_Frequency":
            if msg.payload != '' and msg.payload != b'':
                Grid_Frequency=float(msg.payload)
                last_changed = int(time())
        if msg.topic=="Grid_Current":
            if msg.payload != '' and msg.payload != b'':
                Grid_Current=float(msg.payload)
                last_changed = int(time())
        if msg.topic=="Grid_Power":
            if msg.payload != '' and msg.payload != b'':
                Grid_Power=float(msg.payload)
                last_changed = int(time())


        if msg.topic=="AC_Output_Voltage":
            if msg.payload != '' and msg.payload != b'':
                AC_Output_Voltage=float(msg.payload)
                last_changed = int(time())
        if msg.topic=="AC_Output_Frequency":
            if msg.payload != '' and msg.payload != b'':
                AC_Output_Frequency=float(msg.payload)
                last_changed = int(time())
        if msg.topic=="AC_Output_Active_Power":
            if msg.payload != '' and msg.payload != b'':
                AC_Output_Active_Power=float(msg.payload)
                last_changed = int(time())
        if msg.topic=="AC_Output_Power":
            if msg.payload != '' and msg.payload != b'':
                AC_Output_Power=float(msg.payload)
                last_changed = int(time())
        if msg.topic=="AC_Output_Current":
            if msg.payload != '' and msg.payload != b'':
                AC_Output_Current=float(msg.payload)
                last_changed = int(time())
        if msg.topic=="AC_Output_Energy":
            if msg.payload != '' and msg.payload != b'':
                AC_Output_Energy=float(msg.payload)
                last_changed = int(time())

        if msg.topic=="DC_Voltage":
            if msg.payload != '' and msg.payload != b'':
                DC_Voltage=float(msg.payload)
                last_changed = int(time())
        if msg.topic=="DC_Current":
            if msg.payload != '' and msg.payload != b'':
                DC_Current=float(msg.payload)
                last_changed = int(time())

        if msg.topic=="PV_Voltage":
            if msg.payload != '' and msg.payload != b'':
                PV_Voltage=float(msg.payload)
                last_changed = int(time())
        if msg.topic=="PV_Power":
            if msg.payload != '' and msg.payload != b'':
                PV_Power=float(msg.payload)
                last_changed = int(time())
        if msg.topic=="PV_Energy":
            if msg.payload != '' and msg.payload != b'':
                Yield=float(msg.payload)
                last_changed = int(time())

    except Exception as e:
        logging.error("Exception occurred: %s" % e)
        logging.debug("MQTT payload: " + str(msg.payload)[1:])



class DbusWKSService:
    def __init__(self, servicename, deviceinstance, paths, productname='Multi RS Solar 48V/6000VA/100A', connection='MQTT'):  
                                                                                                                              
        self._dbusservice = VeDbusService(servicename)                                                                            
        self._paths = paths                                                                                                       
                                                                                                                              
        logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))                                             
    
    
        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path('/Mgmt/ProcessVersion', 'Unkown version, and running on Python 3')
        self._dbusservice.add_path('/Mgmt/Connection', connection)                                                                
                                                                                                                      
        # Create the mandatory objects                                                                                            
        self._dbusservice.add_path('/DeviceInstance', deviceinstance)                                                             
        self._dbusservice.add_path('/ProductId', 42049) 
        self._dbusservice.add_path('/ProductName', 'Multi RS Solar 48V/6000VA/100A')
        self._dbusservice.add_path('/FirmwareVersion', '1.13')
        self._dbusservice.add_path('/HardwareVersion', '2')
        self._dbusservice.add_path('/Connected', 1)
        self._dbusservice.add_path('/Latency', None)
        self._dbusservice.add_path('/Serial', '123456')
                                                                                         
        for path, settings in self._paths.items():                                                                     
            self._dbusservice.add_path(                                                                                  
                path, settings['initial'], writeable=True, onchangecallback=self._handlechangedvalue)                      
    
        GLib.timeout_add(10000, self._update)                                                                          
                                                                                                                   
    def _update(self):
        global \
            last_changed, last_updated

        now = int(time())

        if last_changed != last_updated:

                
                self._dbusservice['/Ac/In/1/L1/V'] = round(Grid_Voltage, 2)
                self._dbusservice['/Ac/In/1/L1/F'] = round(Grid_Frequency, 2)
                self._dbusservice['/Ac/In/1/L1/I'] = round(Grid_Current, 2)
                self._dbusservice['/Ac/In/1/L1/P'] = round(Grid_Power, 2)
                
                self._dbusservice['/Ac/Out/L1/V'] = round(AC_Output_Voltage, 2)
                self._dbusservice['/Ac/Out/L1/F'] = round(AC_Output_Frequency, 2)
                self._dbusservice['/Ac/Out/L1/I'] = round(AC_Output_Current, 2)
                self._dbusservice['/Ac/Out/L1/P'] = round(AC_Output_Power, 2)
                self._dbusservice['/Ac/Out/L1/S'] = round(AC_Output_Active_Power, 2)
                self._dbusservice['/Energy/InverterToAcOut'] = round(AC_Output_Energy, 8)
                
                self._dbusservice['/Dc/0/Voltage'] = round(DC_Voltage, 2)
                self._dbusservice['/Dc/0/Current'] = round(DC_Current, 2)
                self._dbusservice['/Dc/0/Power'] = round(DC_Voltage*DC_Current, 2)
                
                self._dbusservice['/Pv/0/V'] = round(PV_Voltage, 2)
                if PV_Voltage != 0:
                	self._dbusservice['/Pv/0/I'] = round(PV_Power/PV_Voltage, 2)
                else:
                	self._dbusservice['/Pv/0/I'] = 0
			
                self._dbusservice['/Pv/0/P'] = round(PV_Power, 2)
                self._dbusservice['/Pv/V'] = round(PV_Voltage, 2)
                
                self._dbusservice['/State'] = 9
                self._dbusservice['/Soc'] = 80

                self._dbusservice['/Yield/Power'] = round(PV_Power, 2)
                self._dbusservice['/Yield/User'] = round(PV_Energy, 2)
                #self._dbusservice['/Yield/System'] = 0

		

                last_updated = last_changed

        # quit driver if timeout is exceeded
        if timeout != 0 and (now - last_changed) > timeout:
            logging.error("Driver stopped. Timeout of %i seconds exceeded, since no new MQTT message was received in this time." % timeout)
            sys.exit()

        # increment UpdateIndex - to show that new data is available
        #index = self._dbusservice['/UpdateIndex'] + 1  # increment index
        #if index > 255:   # maximum value of the index
        #    index = 0       # overflow from 255 to 0
        #self._dbusservice['/UpdateIndex'] = index
        return True

                                                                                                                                                                                                                                                         
    def _handlechangedvalue(self, path, value):
        logging.debug("someone else updated %s to %s" % (path, value))
        return True # accept the change
   
def main():

    _thread.daemon = True  # allow the program to quit

    from dbus.mainloop.glib import DBusGMainLoop  # pyright: ignore[reportMissingImports]
    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)

    # MQTT setup
    client = mqtt.Client("MqttPv_" + str(config['MQTT']['device_instance']))
    client.on_disconnect = on_disconnect
    client.on_connect = on_connect
    client.on_message = on_message

    # check tls and use settings, if provided
    if 'tls_enabled' in config['MQTT'] and config['MQTT']['tls_enabled'] == '1':
        logging.info("MQTT client: TLS is enabled")

        if 'tls_path_to_ca' in config['MQTT'] and config['MQTT']['tls_path_to_ca'] != '':
            logging.info("MQTT client: TLS: custom ca \"%s\" used" % config['MQTT']['tls_path_to_ca'])
            client.tls_set(config['MQTT']['tls_path_to_ca'], tls_version=2)
        else:
            client.tls_set(tls_version=2)

        if 'tls_insecure' in config['MQTT'] and config['MQTT']['tls_insecure'] != '':
            logging.info("MQTT client: TLS certificate server hostname verification disabled")
            client.tls_insecure_set(True)

    # check if username and password are set
    if 'username' in config['MQTT'] and 'password' in config['MQTT'] and config['MQTT']['username'] != '' and config['MQTT']['password'] != '':
        logging.info("MQTT client: Using username \"%s\" and password to connect" % config['MQTT']['username'])
        client.username_pw_set(username=config['MQTT']['username'], password=config['MQTT']['password'])

    # connect to broker
    logging.info(f"MQTT client: Connecting to broker {config['MQTT']['broker_address']} on port {config['MQTT']['broker_port']}")
    client.connect(
        host=config['MQTT']['broker_address'],
        port=int(config['MQTT']['broker_port'])
    )
    client.loop_start()

    # wait to receive first data, else the JSON is empty and phase setup won't work
    i = 0
    while PV_Power == -1:
        if i % 12 != 0 or i == 0:
            logging.info("Waiting 5 seconds for receiving first data...")
        else:
            logging.warning("Waiting since %s seconds for receiving first data..." % str(i * 5))
        sleep(2)
        i += 1

    # formatting
    def _kwh(p, v): return (str("%.2f" % v) + "kWh")
    def _a(p, v): return (str("%.1f" % v) + "A")
    def _w(p, v): return (str("%i" % v) + "W")
    def _v(p, v): return (str("%.2f" % v) + "V")
    def _hz(p, v): return (str("%.4f" % v) + "Hz")
    def _n(p, v): return (str("%i" % v))

    paths_dbus = {
        '/Ac/In/1/L1/V': {'initial': 0},
        '/Ac/In/1/L1/F': {'initial': 0},
        '/Ac/In/1/L1/I': {'initial': 0},
        '/Ac/In/1/L1/P': {'initial': 0},
        '/Ac/In/1/CurrentLimit': {'initial': 40},
        '/Ac/In/1/Type': {'initial': 1},
        '/Ac/Out/L1/V': {'initial': 0},
        '/Ac/Out/L1/F': {'initial': 0},
        '/Ac/Out/L1/I': {'initial': 0},
        '/Ac/Out/L1/P': {'initial': 0},
        '/Ac/Out/L1/S': {'initial': 0},
        '/Ac/ActiveIn/ActiveInput': {'initial': 0},
        '/Ac/NumberOfPhases': {'initial': 1},
        '/Ac/NumberOfAcInput': {'initial': 1},
        '/Alarms/LowSoc': {'initial': 0},
        '/Alarms/LowVoltage': {'initial': 0},
        '/Alarms/HighVoltage': {'initial': 0},
        '/Alarms/LowVoltageAcOut': {'initial': 0},
        '/Alarms/HighVoltageAcOut': {'initial': 0},
        '/Alarms/HighTemperature': {'initial': 0},
        '/Alarms/Overload': {'initial': 0},
        '/Alarms/Ripple': {'initial': 0},
        '/Dc/0/Voltage': {'initial': 0},
        '/Dc/0/Current': {'initial': 0},
        '/Dc/0/Power': {'initial': 0},
        '/Dc/0/Temperature': {'initial': 15},
        '/Mode': {'initial': 3},
        '/State': {'initial': 0},
        '/Soc': {'initial': 0},
        '/ErrorCode': {'initial': 0},
        '/Relay/0/State': {'initial': 0},
        '/NrOfTrackers': {'initial': 1},
        '/Pv/0/V': {'initial': 0},
        '/Pv/0/I': {'initial': 0},
        '/Pv/0/P': {'initial': 0},
        '/Pv/V': {'initial': 0},
        '/Pv/0/MppOperationMode': {'initial': 2},
        '/Yield/Power': {'initial': 0},
        '/Yield/User': {'initial': 0},
        '/Yield/System': {'initial': 0},
        '/Energy/InverterToAcOut': {'initial':0.00},
        '/Energy/SolarToAcOut': {'initial':0.00},
        '/Energy/SolarToBattery': {'initial':0.00}
    }

    DbusWKSService(
        servicename='com.victronenergy.multi.wksinverter_'+ str(config['MQTT']['device_instance']),
        deviceinstance=int(config['MQTT']['device_instance']),
        productname=config['MQTT']['device_name'],
        paths=paths_dbus
    )

    logging.info('Connected to dbus, and switching over to gobject.MainLoop() (= event based)')
    mainloop = GLib.MainLoop()
    mainloop.run()

if __name__ == "__main__":
  main()

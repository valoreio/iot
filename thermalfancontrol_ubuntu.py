#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  Code styled according to pycodestyle


__author__ = "Marcos Aurelio Barranco"
__copyright__ = "Copyright 2016, The MIT License (MIT)"
__credits__ = ["Marcos Aurelio Barranco", ]
__license__ = "MIT"
__version__ = "3"
__maintainer__ = "Marcos Aurelio Barranco"
__email__ = ""
__status__ = "Production"


'''
Code to control electric fan of Raspberry Pi
according to internal and external temperatures.

-DHT22 sensor is reading external temperatura
-Internal temperature is reading cpu temperature
     through linux commands
-SQLite3 maintain fixed value to handle as a
     minimal temperature to start the fan

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
# ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
# THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import os
if os.geteuid() != 0:
    print("You need to have root privileges to run this script.")
    print("Please try again, this time using 'sudo'.")
    exit("Exiting... Done it!")

'''
pid is to prevent two codes running
at same time at same name space
check-to-see-if-python-script-is-running
'''

try:
    from pid import PidFile
    with PidFile():
        import subprocess
        import sys
        import time
        import re
        import logging
        import signal
        import RPi.GPIO as GPIO

        try:
            import Adafruit_DHT as dht
        except ImportError:
            sys.exit("""You need Adafruit_DHT
                install it from http://pypi.python.org/
                or run pip3 install Adafruit_DHT""")

        try:
            import sqlite3
        except ImportError:
            sys.exit("""You need sqlite3
                install it from http://pypi.python.org/
                or run pip3 install sqlite3""")

        from security_connections_data2 import sqlite3_host2

        class GracefulKiller(object):

            kill_now = False

            def __init__(self):

                signal.signal(signal.SIGINT, self.exit_gracefully)
                signal.signal(signal.SIGTERM, self.exit_gracefully)
                signal.signal(signal.SIGHUP, self.exit_gracefully)

            def exit_gracefully(self, signum, frame):

                self.kill_now = True

        killer = GracefulKiller()

        filepath = '/home/ubuntu/projs/iot/'
        filenameonly = 'thermalfancontrol.log'
        filenamefull = filepath + filenameonly

        """file rotate by Linux logrotate command
           https://www.digitalocean.com/community/
           tutorials/how-to-manage-
           logfiles-with-logrotate-on-ubuntu-16-04"""

        logging.basicConfig(filename=filenamefull,
                            level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='[%d/%m/%Y-%H:%M:%S]',
                            filemode='a')

        def measure_tempCPU():

            try:
                '''
                formato para o Ubuntu IoT
                '''
                result = subprocess.run(
                    ['cat', '/sys/class/thermal/thermal_zone0/temp'],
                    stdout=subprocess.PIPE)

                m = (int(result.stdout.decode('utf-8')) / 1000)
                return float(m)

            except Exception as e:
                '''
                formato para o Raspbian
                '''
                try:
                    raw = subprocess.run(
                        ['vcgencmd', 'measure_temp'],
                        stdout=subprocess.PIPE)

                    m = re.match(r"temp=(\d+\.?\d*)'C", raw)
                    return float(m.group(1))

                except Exception as e:
                    '''
                    Assume o valor 34. Não iremos testar
                    centenas de Linux disponíveis
                    '''
                    m = 34
                    return float(m)

        def measure_tempSQLite():
            try:
                conn = sqlite3.connect(sqlite3_host2)
                cursor = conn.cursor()
                cursor.execute("""select cputemperaturevalue
                    from cputemperature
                    where ID = 1""")

                for i in cursor.fetchone():
                    return i

            except Exception as e:
                logging.debug("ErroSQLite: {0}".format(e))
                sys.exit(1)

            finally:
                if conn:
                    conn.close()

        """GPIO 26 ou pino 37 fisico,
           ou penultimo pino da linha 3,3V"""
        LEDpin = 26

        """GPIO 22 ou pino 15 fisico,
           ou 8o. pino da linha 3,3V"""
        DHT22pin = 22
        sensor = dht.DHT22

        """ GPIO 18 ou pino 12 fisico,
            ou 6o. pino da linha 5V"""
        FANpin = 18
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(FANpin, GPIO.OUT)
        GPIO.setup(LEDpin, GPIO.OUT)

        # Inicia a FAN desligado
        GPIO.output(FANpin, False)
        # Inicia o LED vermelho ligado
        GPIO.output(LEDpin, True)

        # Lê temperatura no SQLite DB
        try:
            temp_sqlite = measure_tempSQLite()

        except Exception as e:
            temp_sqlite = 34
            logging.debug(
                "Unexpected Exception while reading SQLite temp : %s", e)
            logging.info("Temp sqlite was settled to 34")

        # Lê temperatura e humidade do sensor DHT22
        try:
            humidity, temperature = dht.read_retry(sensor, DHT22pin)

        except Exception as e:
            humidity, temperature = 40, 40
            logging.debug(
                "Unexpected Exception while reading DHT22 sensor : %s", e)
            logging.info("humidity and temperature was settled to 40")

        # Lê temperatura inicial e interna da CPU
        # do Raspberry via comando Linux
        try:
            temp = measure_tempCPU()

        except Exception as e:
            temp = 34
            logging.debug(
                "Unexpected Exception while reading CPU temp : %s", e)
            logging.info("CPU temp was settled to 34")

        temp_control = temp + 5

        logging.info("****************B E G I N*********")
        logging.debug("File Path                        : %s", filepath)
        logging.debug("File Name                        : %s", filenameonly)
        logging.debug("GPIO pin DHT22                   : %s", DHT22pin)
        logging.debug("GPIO pin Fan                     : %s", FANpin)
        logging.debug("External Initial Temperature   C : %s", temperature)
        logging.debug("External Humidity percentual     : %s", humidity)
        logging.debug("temp - CPU Initial Tempe       C : %s", temp)
        logging.debug("temp_sqlite - Temp in SQLite   C : %s", temp_sqlite)
        logging.debug("temp_control - Temp of Control C : %s", temp_control)
        logging.info("***************** E N D **************")

        while True:

            try:
                if killer.kill_now:
                    logging.info("Exit by Signal Shutdown")
                    # resets all GPIO ports used by this program
                    GPIO.cleanup()
                    sys.exit(0)

            except Exception as e:
                logging.debug("Unexpected while killing : %s", e)

            try:
                temp = measure_tempCPU()
                logging.debug("Temp read NOW from the RPi board : %s", temp)

            except Exception as e:
                temp = 34
                logging.info("Unexpected while reading CPU temp")

            if temp > temp_control or temp > temp_sqlite:
                if not GPIO.input(FANpin):

                    logging.info(">>>")
                    logging.debug(
                        "Temp read from external env  : %s", temperature)

                    logging.debug(
                        "External Humidity percentual : %s", humidity)

                    logging.debug(
                        "Temp read from the RPi board : %s", temp)

                    logging.debug(
                        "temp_sqlite - Temp SQLite  C : %s", temp_sqlite)

                    #  Liga a fan
                    GPIO.output(FANpin, True)
                    #  Desliga o LED
                    GPIO.output(LEDpin, False)
                    logging.debug("turning ON GPIO: %s", FANpin)

            else:

                if GPIO.input(FANpin):

                    logging.info("<<<")
                    logging.debug(
                        "Temp read from external env  : %s", temperature)

                    logging.debug(
                        "External Humidity percentual : %s", humidity)

                    logging.debug(
                        "Temp read from the RPi board : %s", temp)

                    logging.debug(
                        "temp_sqlite - Temp SQLite  C : %s", temp_sqlite)

                    #  Desliga a fan
                    GPIO.output(FANpin, False)
                    #  Liga o LED
                    GPIO.output(LEDpin, True)
                    logging.debug("turning OFF GPIO: %s", FANpin)

                    try:
                        humidity, temperature = dht.read_retry(
                            sensor, DHT22pin)

                    except Exception as e:
                        humidity, temperature = 40, 40
                        logging.debug(
                            "Unexpected Exception DHT22 sensor : %s", e)

                    try:
                        temp_sqlite = measure_tempSQLite()

                    except Exception as e:
                        temp_sqlite = 32
                        logging.debug(
                            "Unexpected Exception SQLite3 temp : %s", e)

            if temperature > 35:
                for i in range(80):
                    time.sleep(.0001)

            else:

                if temperature > 33:
                    for i in range(160):
                        time.sleep(.0001)

                else:

                    if temperature > 31:
                        for i in range(240):
                            time.sleep(.0001)

                    else:

                        if temperature > 29:
                            for i in range(320):
                                time.sleep(.0001)

                        else:

                            if temperature > 27:
                                for i in range(400):
                                    time.sleep(.0001)

                            else:

                                if temperature > 25:
                                    for i in range(480):
                                        time.sleep(.0001)

                                else:

                                    if temperature > 23:
                                        for i in range(640):
                                            time.sleep(.0001)
                                    else:
                                        for i in range(3000):
                                            time.sleep(.0001)


except Exception as e:
    print('The program is already running.')
    print('It is not allowed two programs running at same time')
    raise Exception('{}'.format(e))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Code styled according to pycodestyle


__author__ = "Marcos Aurelio Barranco"
__copyright__ = "Copyright 2016, The MIT License (MIT)"
__credits__ = ["Marcos Aurelio Barranco", ]
__license__ = "MIT"
__version__ = "3"
__maintainer__ = "Marcos Aurelio Barranco"
__email__ = ""
__status__ = "Production"


'''
Code to control the electric fan of Raspberry Pi
according to internal and external temperatures.

DHT22 sensor is reading external temperatura

CPU internal temperature is read by linux commands

SQLite3 maintain fixed value to handle as a
 minimal temperature to start the fan

The green led turn on and off through the this code

The blue led turn on and off through the hardware
setup using transistors, diodes,
'''

# access-gpio-pins-without-root-no-access-to-dev-mem-try-running-as-root
#import os
#if os.geteuid() != 0:
#    print("You need to have root privileges to run this script.")
#    print("Please try again, this time using 'sudo'.")
#    exit("Exiting... Done it!")

'''
pid is to prevent two codes running
at same time at same name space
check-to-see-if-python-script-is-running
'''
try:
    from pid import PidFile
    with PidFile(piddir="./prevents"):
        import subprocess
        import sys
        import time
        import re
        import logging
        import signal
        from security_connections_data2 import sqlite3_host2

        try:
            import RPi.GPIO as GPIO

        except ImportError:
            sys.exit("""You need RPi
                install it from http://pypi.python.org/
                or run pip3 install RPi""")

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

        class GracefulKiller(object):
            kill_now = False

            def __init__(self):
                signal.signal(signal.SIGINT, self.exit_gracefully)
                signal.signal(signal.SIGTERM, self.exit_gracefully)
                signal.signal(signal.SIGHUP, self.exit_gracefully)

            def exit_gracefully(self, signum, frame):
                self.kill_now = True

        killer = GracefulKiller()

        filepath = './'
        filenameonly = 'thermalfancontrol.log'
        filenamefull = filepath + filenameonly

        """
        file rotate by Linux logrotate command
        https://www.digitalocean.com/community/
        tutorials/how-to-manage-
        logfiles-with-logrotate-on-ubuntu-16-04
        """

        logging.basicConfig(
            filename=filenamefull,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='[%d/%m/%Y-%H:%M:%S]',
            filemode='a')

        def measure_tempCPU():
            try:
                '''
                formato para o Ubuntu IoT
                '''
                out = subprocess.Popen(
                    ['cat', '/sys/class/thermal/thermal_zone0/temp'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)

                stdout, stderr = out.communicate()

                if stderr is None:
                    tempCPU = int(stdout) / 1000
                else:
                    tempCPU = 35

            except Exception as e:
                try:
                    '''
                    formato para o Raspbian
                    '''
                    out = subprocess.Popen(
                        ['vcgencmd', 'measure_temp'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT)

                    stdout, stderr = out.communicate()

                    if stderr is None:
                        tempCPU = re.match(r"temp=(\d+\.?\d*)'C", out)
                        tempCPU = tempCPU.group(1)
                    else:
                        tempCPU = 35

                except Exception as e:
                    '''
                    Assume o valor abaixo. Não iremos testar
                    centenas de Linux disponíveis
                    '''
                    tempCPU = 35

            finally:
                return float(tempCPU)

        def measure_tempSQLite():
            try:
                conn = sqlite3.connect(sqlite3_host2)
                cursor = conn.cursor()
                cursor.execute("""select cputemperaturevalue
                    from cputemperature
                    where ID = 1""")

                for i in cursor.fetchone():
                    tempSQLite = i

            except Exception as e:
                try:
                    conn = sqlite3.connect(sqlite3_host2)
                    cursor = conn.cursor()

                    cursor.execute("""CREATE TABLE if not EXISTS
                        cputemperature (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        cputemperaturevalue INTEGER);""")

                    logging.info("table cputemperature was created")

                except Exception as e1:
                    raise Exception("ErrCreateTable-1 : {0}".format(e1))

                finally:
                    if conn:
                        conn.close()

                try:
                    conn = sqlite3.connect(sqlite3_host2)
                    cursor = conn.cursor()

                    try:
                        cursor.execute("""INSERT INTO cputemperature
                            (cputemperaturevalue) VALUES (35)""")

                        conn.commit()

                        logging.info(
                            "record was inserted in table cputemperature")

                        tempSQLite = 35

                    except Exception as e3:
                        raise Exception("ErrIns-1 : {0}".format(e3))

                except Exception as e4:
                    raise Exception("ErrIns-2 : {0}".format(e4))

            finally:
                if conn:
                    conn.close()

                return tempSQLite

        """
        GPIO 18 ou pino 12 fisico,
        ou 6o. pino da linha 5V
        """
        FANpin = 18

        """
        GPIO 26 ou pino 37 fisico,
        ou penultimo pino da linha 3,3V
        """
        LEDpin = 26

        """
        GPIO 22 ou pino 15 fisico,
        ou 8o. pino da linha 3,3V
        """
        DHT22pin = 22
        sensor = dht.DHT22

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
            temp_sqlite = 35
            logging.debug(
                "Unexpected Exception while reading SQLite temp : %s", e)
            logging.info("Temp sqlite was settled to 35")

        # Lê temperatura e humidade do sensor DHT22
        try:
            humidity, temperature = dht.read_retry(sensor, DHT22pin)

        except Exception as e:
            humidity, temperature = 35, 35
            logging.debug(
                "Unexpected Exception while reading DHT22 sensor : %s", e)
            logging.info("humidity and temperature was settled to 35")

        # Lê temperatura inicial e interna da CPU
        # do Raspberry via comando Linux
        try:
            temp = measure_tempCPU()

        except Exception as e:
            temp = 35
            logging.debug(
                "Unexpected Exception while reading CPU temp : %s", e)
            logging.info("CPU temp was settled to 34")

        logging.info("****************B E G I N*********")
        logging.debug("File Path                        : %s", filepath)
        logging.debug("File Name                        : %s", filenameonly)
        logging.debug("GPIO pin DHT22                   : %s", DHT22pin)
        logging.debug("GPIO pin Fan                     : %s", FANpin)
        logging.debug("External Initial Temperature   C : %s", temperature)
        logging.debug("External Humidity percentual     : %s", humidity)
        logging.debug("temp - CPU Initial Tempe       C : %s", temp)
        logging.debug("temp_sqlite - Temp in SQLite   C : %s", temp_sqlite)
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

            # Liga a fan se a temperatura for maior do que a temperatura
            # de controle armazenada no SQLite
            if temp > temp_sqlite:
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

                    # Liga a fan
                    GPIO.output(FANpin, True)
                    # Desliga o LED vermelho
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

                    # Desliga a fan
                    GPIO.output(FANpin, False)
                    # Liga o LED vermelho
                    GPIO.output(LEDpin, True)
                    logging.debug("turning OFF GPIO: %s", FANpin)

            try:
                temp = measure_tempCPU()
                logging.debug("Temp read NOW from the RPi board : %s", temp)

            except Exception as e:
                temp = 35
                logging.info("Unexpected while reading CPU temp")

            try:
                temp_sqlite = measure_tempSQLite()
                logging.debug(
                    "temp_sqlite - Temp in SQLite   C : %s", temp_sqlite)

            except Exception as e:
                temp_sqlite = 35
                logging.debug(
                    "Unexpected Exception SQLite3 temp : %s", e)

            try:
                temperature_old = temperature

                humidity, temperature = dht.read_retry(
                    sensor, DHT22pin)

                logging.debug(
                    "Temp read from external env      : %s", temperature)

                logging.debug(
                    "External Humidity percentual     : %s", humidity)

            except Exception as e:
                humidity, temperature = 35, 35
                logging.debug(
                    "Unexpected Exception DHT22 sensor : %s", e)

            # O sensor de temperatura é de baixo custo e pode 'bugar'
            # e dessa forma retornar um valor lido não real.
            # A precisão do sensor não é de 100%
            if temperature is not None:
                minimal_temperature = temperature * (50/100)

            if temperature is not None and temperature < minimal_temperature:
                logging.debug(
                    ">>>>>>>temp read unreal          : %s", temperature)

                temperature = temperature_old

                logging.debug(
                    ">>>>>>>temp setted to old one    : %s", temperature)

            # O sensor de temperatura é de baixo custo e pode 'bugar'
            # e dessa forma retornar None quando diversas consultas
            # são feitas com intervalo de poucos segundos
            if temperature is None and temperature_old is not None:
                logging.debug(
                    ">>>>>>>None temp is not good     : %s", temperature)

                temperature = temperature_old

                logging.debug(
                    ">>>>>>>temp setted to old one    : %s", temperature)
            else:
                try:
                    temp_sqlite = measure_tempSQLite()
                    logging.debug(
                        "temp_sqlite - Temp in SQLite   C : %s", temp_sqlite)

                except Exception as e:
                    temperature = 35
                    logging.debug(
                        "Unexpected Exception SQLite3 temp : %s", e)

            # A temperatura externa, lida pelo sensor DHT22, controla
            # o tempo que o sleep irá aguardar
            # quanto maior a temperatura externa, menor o tempo aguardando
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

            logging.info("**********************************")

except Exception as e:
    print('The program is already running.')
    print('It is not allowed two programs running at same time')
    print(e)
    exit('Exiting... Done it!')

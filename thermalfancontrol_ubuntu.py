#!/usr/bin/env python3
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
# -*- coding: utf-8 -*-
# Code styled according to pycodestyle
# Code parsed, checked possible errors according to pyflakes and pylint

__author__ = "Marcos Aurelio Barranco"
__copyright__ = "Copyright 2016, The MIT License (MIT)"
__credits__ = ["Marcos Aurelio Barranco", ]
__license__ = "MIT"
__version__ = "4"
__maintainer__ = "Marcos Aurelio Barranco"
__email__ = ""
__status__ = "Production"

# access-gpio-pins-without-root-no-access-to-dev-mem-try-running-as-root
import os
import sys
if os.geteuid() != 0:
    print("You need to have root privileges to run this script.")
    print("Please try again, this time using 'sudo'.")
    sys.exit("Exiting... Done it!")


try:
    # pid is to prevent two codes running
    # at same time at same name space
    #check-to-see-if-python-script-is-running
    from pid import PidFile
    with PidFile(piddir="./prevents"):
        import subprocess
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

        class GracefulKiller():
            '''
            Graceful Killer
            '''
            kill_now = False

            def __init__(self):
                signal.signal(signal.SIGINT, self.exit_gracefully)
                signal.signal(signal.SIGTERM, self.exit_gracefully)
                signal.signal(signal.SIGHUP, self.exit_gracefully)

            def exit_gracefully(self, signum, frame):
                '''
                Exit Gracefully
                '''
                self.kill_now = True

        killer = GracefulKiller()

        def measure_cpu_temp():
            '''
            Measure CPU temperature
            '''
            try:
                # formato para o Ubuntu IoT
                out = subprocess.Popen(
                    ['cat', '/sys/class/thermal/thermal_zone0/temp'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)

                stdout, stderr = out.communicate()

                if stderr is None:
                    cpu_temp = int(stdout) / 1000
                else:
                    cpu_temp = 32

            except Exception:
                try:
                    # formato para o Raspbian
                    out = subprocess.Popen(
                        ['vcgencmd', 'measure_temp'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT)

                    stdout, stderr = out.communicate()

                    if stderr is None:
                        cpu_temp = re.match(r"temp=(\d+\.?\d*)'C", out)
                        cpu_temp = cpu_temp.group(1)
                    else:
                        cpu_temp = 32

                except Exception:
                    # Não iremos testar centenas de Linux disponíveis
                    # Assume o valor abaixo.
                    cpu_temp = 32

            finally:
                return float(cpu_temp)

        def select_sqlite_temp():
            '''
            select the default control temperature
            stored on SQLite
            '''
            try:
                conn = sqlite3.connect(sqlite3_host2)
                cursor = conn.cursor()
                cursor.execute("""select cputemperaturevalue
                    from cputemperature
                    where ID = 1""")

                for i in cursor.fetchone():
                    sqlite_temp = i

            except Exception:
                try:
                    conn = sqlite3.connect(sqlite3_host2)
                    cursor = conn.cursor()

                    cursor.execute("""CREATE TABLE if not EXISTS
                        cputemperature (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        cputemperaturevalue INTEGER);""")

                    logging.info("table cputemperature was created")

                except Exception as err:
                    raise Exception("ErrCreateTable-1 : {0}".format(err))

                finally:
                    if conn:
                        conn.close()

                try:
                    conn = sqlite3.connect(sqlite3_host2)
                    cursor = conn.cursor()

                    try:
                        cursor.execute("""INSERT INTO cputemperature
                            (cputemperaturevalue) VALUES (32)""")

                        conn.commit()

                        logging.info(
                            "record was inserted in table cputemperature")

                        sqlite_temp = 32

                    except Exception as err:
                        raise Exception("ErrIns-1 : {0}".format(err))

                except Exception as err:
                    raise Exception("ErrIns-2 : {0}".format(err))

            finally:
                if conn:
                    conn.close()

                return sqlite_temp

        # GPIO 18 ou pino 12 fisico,
        # ou 6o. pino da linha 5V
        FANpin = 18

        # GPIO 26 ou pino 37 fisico,
        # ou penultimo pino da linha 3,3V
        LEDpin = 26

        # GPIO 22 ou pino 15 fisico,
        # ou 8o. pino da linha 3,3V
        DHT22pin = 22
        sensor = dht.DHT22

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(FANpin, GPIO.OUT)
        GPIO.setup(LEDpin, GPIO.OUT)

        # Inicia a FAN desligada
        GPIO.output(FANpin, False)
        # Inicia o LED vermelho ligado
        GPIO.output(LEDpin, True)

        # file rotate by Linux logrotate command
        # https://www.digitalocean.com/community/
        # tutorials/how-to-manage-
        # logfiles-with-logrotate-on-ubuntu-16-04
        filepath = './'
        filenameonly = 'thermalfancontrol.log'
        filenamefull = filepath + filenameonly

        logging.basicConfig(
            filename=filenamefull,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='[%d/%m/%Y-%H:%M:%S]',
            filemode='a')

        logging.info("****************B E G I N*********************")
        logging.info("* Turn the fan ON when the CPU temperature   *")
        logging.info("* is greater than the temperature of control *")
        logging.info("* stored in SQLite                           *")
        logging.info("**********************************************")
        logging.debug("File Path      : %s", filepath)
        logging.debug("File Name      : %s", filenameonly)
        logging.debug("GPIO pin DHT22 : %s", DHT22pin)
        logging.debug("GPIO pin Fan   : %s", FANpin)

        while True:

            try:
                if killer.kill_now:
                    logging.info("Exit by Signal Shutdown")
                    logging.info(
                        "****************  E N D  *********************")

                    # resets all GPIO ports used by this program
                    GPIO.cleanup()
                    sys.exit(0)

            except Exception as err:
                logging.debug("Unexpected while killing : %s", err)

            # SQLite DB temperature
            try:
                sqlite_temp = select_sqlite_temp()

            except Exception as err:
                sqlite_temp = 32
                logging.debug(
                    "Unexpected Exception while reading SQLite temp : %s", err)
                logging.debug(
                    "Temp sqlite was settled to : %s", sqlite_temp)

            # CPU temperature by Linux command
            try:
                cpu_temp = measure_cpu_temp()

            except Exception as err:
                cpu_temp = 32
                logging.debug(
                    "Unexpected Exception while reading CPU cpu_temp: %s", err)
                logging.debug(
                    "CPU temp was settled to : %s", cpu_temp)

            # DHT22 sensor temperature
            try:
                humidity, temperature = dht.read_retry(sensor, DHT22pin)

            except Exception as err:
                humidity, temperature = 32, 32
                logging.debug(
                    "Unexpected Exception while reading DHT22 sensor : %s", err)
                logging.debug(
                    "humidity and temperature was settled to         : %s", temperature)

            # Liga a fan se a temperatura for maior do que a temperatura
            # de controle armazenada no SQLite
            if cpu_temp > sqlite_temp:
                if not GPIO.input(FANpin):
                    # Liga a fan
                    GPIO.output(FANpin, True)
                    # Desliga o LED vermelho
                    GPIO.output(LEDpin, False)

                    logging.info(
                        "**********************************************")

                    logging.debug(
                        ">>> turning ON GPIO          : %s", FANpin)

                    logging.debug(
                        "Humidity percentual          : %s", humidity)

                    logging.debug(
                        "Environment temperature    C : %s", temperature)

                    logging.debug(
                        "CPU temperature            C : %s", cpu_temp)

                    logging.debug(
                        "SQLite temperature stored  C : %s", sqlite_temp)
            else:
                # Desliga a fan porque a temperatura da CPU está abaixo
                # da temperatura de controle armazenada no SQLite
                if GPIO.input(FANpin):
                    # Desliga a fan
                    GPIO.output(FANpin, False)
                    # Liga o LED vermelho
                    GPIO.output(LEDpin, True)

                    logging.info(
                        "**********************************************")

                    logging.debug(
                        "<<< turning OFF GPIO         : %s", FANpin)

                    logging.debug(
                        "Humidity percentual          : %s", humidity)

                    logging.debug(
                        "Environment temperature    C : %s", temperature)

                    logging.debug(
                        "CPU temperature            C : %s", cpu_temp)

                    logging.debug(
                        "SQLite temperature stored  C : %s", sqlite_temp)

            # O sensor de humidade e temperatura é de baixo custo e pode 'bugar'
            # A precisão do sensor não é de 100%
            if temperature is None:
                # O sensor fez a leitura e deu erro. O valor retornado foi "None",
                # isso pode acontecer quando diversas consultas são feitas com
                # intervalo de poucos segundos
                logging.debug(
                    ">>>>>>>The temperature read from the sensor is None        : %s", temperature)

                try:
                    temperature = select_sqlite_temp()
                    logging.debug(
                        ">>>>>>>The temperature was set to default stored on SQLite : %s", temperature)

                except Exception as err:
                    temperature = 32
                    logging.debug(
                        "Unexpected Exception SQLite3 temp : %s", err)
                    logging.debug(
                        ">>>>>>>The temperature was set to : %s", temperature)
            else:
                minimal_temperature = temperature * (50/100)
                maximal_temperature = temperature * (1+(50/100))

                if temperature < minimal_temperature or temperature > maximal_temperature:
                    # O sensor fez a leitura de um valor incorreto
                    logging.debug(
                        ">>>>>>>The temperature read from the sensor is UNREAL      : %s", temperature)

                    try:
                        temperature = select_sqlite_temp()
                        logging.debug(
                            ">>>>>>>The temperature was set to default stored on SQLite : %s", temperature)

                    except Exception as err:
                        temperature = 32
                        logging.debug(
                            "Unexpected Exception SQLite3 temp : %s", err)
                        logging.debug(
                            ">>>>>>>temp set to NEW one        : %s", temperature)

            # A temperatura externa, lida pelo sensor DHT22, controla
            # o tempo do sleep, quanto maior a temperatura externa,
            # menor o tempo aguardando
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

except Exception as err:
    print('The program is already running.')
    print('It is not allowed two programs running at same time')
    print(err)
    sys.exit('Exiting... Done it!')

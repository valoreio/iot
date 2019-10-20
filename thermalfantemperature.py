#!/usr/bin/env python3
# -*- coding: utf- -*-
#  Style coded according to pycodestyle


__author__ = "Marcos Aurelio Barranco"
__copyright__ = "Copyright 2016, The MIT License (MIT)"
__credits__ = ["Marcos Aurelio Barranco", ]
__license__ = "MIT"
__version__ = "1"
__maintainer__ = "Marcos Aurelio Barranco"
__email__ = ""
__status__ = "Production"


import sys
from security_connections_data2 import sqlite3_host2

try:
    import sqlite3

except ImportError:
    sys.exit("""You need sqlite3
        install it from http://pypi.python.org/
        or run pip3 install sqlite3""")


def createdb():
    try:
        conn = sqlite3.connect(sqlite3_host2)
        cursor = conn.cursor()

        cursor.execute("""CREATE TABLE if not EXISTS cputemperature (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            cputemperaturevalue INTEGER);""")

    except Exception as e1:
        raise Exception("ErrCreateTable-1 : {0}".format(e1))

    finally:
        if conn:
            conn.close()


def list_all_records():
    try:
        conn = sqlite3.connect(sqlite3_host2)
        cursor = conn.cursor()
        cursor.execute("""select * from cputemperature""")

        for linha in cursor.fetchall():
            print(linha)

    except Exception as e2:
        raise Exception("ErrSel-1 : ".format(e2))

    finally:
        if conn:
            conn.close()


def insertdb():
    try:
        conn = sqlite3.connect(sqlite3_host2)
        cursor = conn.cursor()

        try:
            cursor.execute("""INSERT INTO cputemperature (cputemperaturevalue)
                VALUES (32)""")

            conn.commit()

        except Exception as e3:
            raise Exception("ErrIns-1 : {0}".format(e3))

    except Exception as e4:
        raise Exception("ErrIns-2 : {0}".format(e4))

    finally:
        if conn:
            conn.close()


def alter_thermal_value(vcpu):
    try:
        conn = sqlite3.connect(sqlite3_host2)
        cursor = conn.cursor()

        try:
            cursor.execute("""UPDATE cputemperature
                SET cputemperaturevalue = ?
                where ID = 1""", (vcpu,))

            conn.commit()

        except Exception as e5:
            raise Exception("ErrUpd-1 : {0}".format(e5))

    except Exception as e6:
        raise Exception("ErrUpd-2 : {0}".format(e6))

    finally:
        if conn:
            conn.close()


if __name__ == '__main__':

    while True:

        try:
            print('\r\n****************************************************')
            print('                    M E N U                         ')
            print('1-Create a NEW SQLite DB named thermalfantemperature')
            print('2-Insert a record with temperature equal 32C')
            print('3-List all records on thermalfantemperature DB')
            print('4-Alter thermal value on thermalfantemperature DB')
            print('5-End')

            varinput = int(input("Select Menu option :"))
            if varinput < 1 or varinput > 5:
                print("Select a valid value among: 1,2,3,4 or 5")

            if varinput == 1:
                createdb()

            if varinput == 2:
                insertdb()
                print("32 was inserted into cputemperature table")

            if varinput == 3:
                list_all_records()

            if varinput == 4:
                vcpu = None
                while not vcpu:
                    try:
                        vcpu = int(input("What does the new value is?"))

                        alter_thermal_value(vcpu)

                        print("Temp {0}C was changed".format(vcpu))

                        list_all_records()

                    except Exception as e7:
                        print("ErrWhile-1 : {0}".format(e7))
                        print("in this time inform a valid value.")

            if varinput == 5:
                sys.exit(0)

        except Exception as e8:
            print("ErrWhile-2 : {0}".format(e8))
            print("Value informed is not valid")

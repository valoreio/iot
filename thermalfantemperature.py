#!/usr/bin/env python3
'''
to handle cputemperature table on sqlite3 database
'''
# -*- coding: utf-8 -*-
# Code styled according to pycodestyle
# Code parsed, checked possible errors according to pyflakes and pylint

import sys
from security_connections_data2 import sqlite3_host2

try:
    import sqlite3

except ImportError:
    sys.exit("""You need sqlite3
        install it from http://pypi.python.org/
        or run pip3 install sqlite3""")


__author__ = "Marcos Aurelio Barranco"
__copyright__ = "Copyright 2016, The MIT License (MIT)"
__credits__ = ["Marcos Aurelio Barranco", ]
__license__ = "MIT"
__version__ = "1"
__maintainer__ = "Marcos Aurelio Barranco"
__email__ = ""
__status__ = "Production"


def createdb():
    '''
    Create table cputemperature
    '''
    try:
        conn = sqlite3.connect(sqlite3_host2)
        cursor = conn.cursor()

        cursor.execute("""CREATE TABLE if not EXISTS cputemperature (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            cputemperaturevalue INTEGER);""")

    except Exception as err:
        raise Exception("ErrCreateTable-1 : {0}".format(err))

    finally:
        if conn:
            conn.close()


def list_all_records():
    '''
    List all records in cputemperature table
    '''
    try:
        conn = sqlite3.connect(sqlite3_host2)
        cursor = conn.cursor()
        cursor.execute("""select * from cputemperature""")

        for linha in cursor.fetchall():
            print(linha)

    except Exception as err:
        raise Exception("ErrSel-1 : ".format(err))

    finally:
        if conn:
            conn.close()


def insertdb():
    '''
    Insert one record in cputemperature table with value 32
    '''
    try:
        conn = sqlite3.connect(sqlite3_host2)
        cursor = conn.cursor()

        try:
            cursor.execute("""INSERT INTO cputemperature (cputemperaturevalue)
                VALUES (32)""")

            conn.commit()

        except Exception as err:
            raise Exception("ErrIns-1 : {0}".format(err))

    except Exception as err:
        raise Exception("ErrIns-2 : {0}".format(err))

    finally:
        if conn:
            conn.close()


def alter_thermal_value(cpu_value):
    '''
    Update record in cputemperature table
    '''
    try:
        conn = sqlite3.connect(sqlite3_host2)
        cursor = conn.cursor()

        try:
            cursor.execute("""UPDATE cputemperature
                SET cputemperaturevalue = ?
                where ID = 1""", (cpu_value,))

            conn.commit()

        except Exception as err:
            raise Exception("ErrUpd-1 : {0}".format(err))

    except Exception as err:
        raise Exception("ErrUpd-2 : {0}".format(err))

    finally:
        if conn:
            conn.close()


if __name__ == '__main__':

    while True:

        try:
            print('**********************M E N U************************')
            print('* 1-Create a NEW SQLite DB thermalfantemperature    *')
            print('* 2-Insert a record with temperature equal 32C      *')
            print('* 3-List all records on thermalfantemperature DB    *')
            print('* 4-Alter thermal value on thermalfantemperature DB *')
            print('* 5-End                                             *')
            print('*****************************************************')

            opcao = int(input("Select Menu option :"))

            if opcao < 1 or opcao > 5:
                print("Select a valid value among: 1,2,3,4 or 5")

            if opcao == 1:
                createdb()

            if opcao == 2:
                insertdb()
                print("Record inserted into cputemperature table")

            if opcao == 3:
                list_all_records()

            if opcao == 4:
                cpu_value = None
                while not cpu_value:
                    try:
                        cpu_value = int(input("What does the new value is? : "))

                        alter_thermal_value(cpu_value)

                        print("Temp {0}C was changed to".format(cpu_value))

                        list_all_records()

                    except Exception as err:
                        print("ErrWhile-1 : {0}".format(err))
                        print("in this time inform a valid value.")

            if opcao == 5:
                sys.exit(0)

        except Exception as err:
            print("ErrWhile-2 : {0}".format(err))
            print("Value informed is not valid")

#!/usr/bin/env python3
# -*- coding: utf- -*-
#  Style coded according to pycodestyle


import sys
from security_connections_data2 import sqlite3_host2
import sqlite3


def createdb():
    try:
        conn = sqlite3.connect(sqlite3_host2)
        cursor = conn.cursor()

        cursor.execute("""CREATE TABLE if not EXISTS cputemperature (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            cputemperaturevalue INTEGER);""")

    except Exception as e1:
        raise Exception("Erro1 : {0}".format(e1))

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
        raise Exception("Erro2 : ".format(e2))

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
            raise Exception("Erro3 : {0}".format(e3))

    except Exception as e4:
        raise Exception("Erro4 : {0}".format(e4))

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
            raise Exception("Erro5 : {0}".format(e5))

    except Exception as e6:
        raise Exception("Erro6 : {0}".format(e6))

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
            print('5-Fim')

            varinput = int(input("Selecione uma opção do Menu :"))
            if varinput < 1 or varinput > 5:
                print("Selecione um valor válido do menu: 1,2,3,4 ou 5")

            if varinput == 1:
                createdb()

            if varinput == 2:
                insertdb()
                print("32 foi inserido na tabela cputemperature")

            if varinput == 3:
                list_all_records()

            if varinput == 4:
                vcpu = None
                while not vcpu:
                    try:
                        vcpu = int(input("Qual o novo valor?"))

                        alter_thermal_value(vcpu)

                        print("Temp {0}C alterada".format(vcpu))

                        list_all_records()

                    except Exception as e7:
                        print("Erro7 : {0}".format(e7))
                        print("Valor informado não é valido.")

            if varinput == 5:
                sys.exit(0)

        except Exception as e8:
            print("Erro8 : {0}".format(e8))
            print("Valor informado não é valido")

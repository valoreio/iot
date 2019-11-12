# iot
## IOT project

The python code will control the electric fan installed apart turning it on and off according to internal (cpu) and outside (ambienty) temperatures.

The internal temperature is read by linux command.

The outside temperature, read by the DHT22 (AM2302) sensor, controls the time waiting, the higher the outside temperature, the shorter the waiting time and more queries checking the internal CPU temperature.

When the outside temperature remain in 25.4 degrees centigrade, the internal CPU temperature of the RPi reaches 56.92 degrees centigrade. By turning on forced ventilation, the CPU temperature drops to 34.862 degrees centigrade and remains stable.

> Remarks:
>* 1. This code was made to run on Raspbian Linux and Ubuntu core IoT.
>* 2. The code will control the electric fan installed apart according to internal and external temperatures.
>* 3. On Ubuntu core you need root privileges to run it OR set up the following steps to run as a normal user:
raspberrypi.stackexchange.com/questions/40105/access-gpio-pins-without-root-no-access-to-dev-mem-try-running-as-root.
>* 3.1 Reboot the server to confirm that setups were persistency.
>* 4. It has two main dependencies: Adafruit_DHT and sqlite3


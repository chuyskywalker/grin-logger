FROM python:3

RUN pip install --no-cache-dir minimalmodbus pynmea2 adafruit-circuitpython-ssd1306 pillow numpy rpi.gpio

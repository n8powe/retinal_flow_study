
# To be renamed main.py

from machine import Pin

led = Pin(15, Pin.OUT)
led.value(0)

def on():
    led.value(1)

def off():
    led.value(0)
    

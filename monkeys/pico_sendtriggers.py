
import select
import sys
import time
from machine import Pin

led = Pin(15, Pin.OUT)
led.value(0)

serial = select.poll() #new select object
serial.register(sys.stdin) #register the stdin

while True:
    time.sleep(0.1)
    if serial.poll(0):
        while serial.poll(0):
            res = sys.stdin.read(1)
            print(res)
        if res=='S':
            print('Starting')
            led.value(1)
        elif res=='E':
            print('Ending')
            led.value(0)
        else:
            sys.stdout.write(res)

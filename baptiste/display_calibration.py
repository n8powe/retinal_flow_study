

import numpy as np
import time, serial
from psychopy import core, event, visual, monitors
import cv2


screenRes = np.array([1920, 1080])
targetNumber = 5

targetITIMin = 0.1
targetITIMax = 0.5
targetTargetMin = 1.5
targetTargetMax = 3.0

targetSizePixMin = 20
targetSizePixMax = 40
targetSizePixFreq = 0.5

targetFlickerFreq = 2

arucoSizePix = 75
arucoGapPix = 2*arucoSizePix


# Connect to arduino
try:
    print('Opening serial port')
    arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=.1)
    # Flush serial port
    while arduino.in_waiting:
        arduino.read()

    def arduino_write(x):
        lastSend = 0.0
        while 1:
            if time.time() - lastSend > 1:
                arduino.write(bytes(x, 'utf-8'))
                lastSend = time.time()
            if arduino.in_waiting:
                data = chr(int(arduino.readline()))
                if data == x:
                    break
    print('Done')
except:
    print('Failed')


# Generate aruco markers
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
markersNumber = 4

# Setup window
monitor = monitors.Monitor('MonkeyCalib', width=53, distance=50)
win = visual.Window(screenRes, screen=0, units="pix", fullscr=True, monitor=monitor)

clock = core.Clock()


for target in range(0, targetNumber):
    durITI = targetITIMin + np.random.rand()*(targetITIMax-targetITIMin)
    durTarget = targetTargetMin + np.random.rand()*(targetTargetMax-targetTargetMin)
    tgPos = 0.75*screenRes*(np.random.rand(2)-0.5)
    randPhase = np.random.rand()*2*np.pi

    clock.reset()
    while clock.getTime() < durITI:
        win.flip()

    image_stim = []
    for mm in range(0, markersNumber):
        img = 2 * ((cv2.aruco.drawMarker(dictionary, mm, 6) / 255) - 0.5)
        arucoPos = tgPos + arucoGapPix * np.array([np.fix(mm / 2) - 0.5, (mm % 2) - 0.5])
        image_stim.append(visual.ImageStim(win, image=img, mask=None, units='pix', pos=arucoPos, size=50))

    try:
        arduino_write('C')
        print('Pulses ended')
    except:
        print('No arduino')

    clock.reset()
    while clock.getTime() < durTarget:
        targetSizeCurr = targetSizePixMin + (targetSizePixMax-targetSizePixMin) * 0.5 * \
                         (np.sin(clock.getTime()*targetSizePixFreq*2*np.pi+randPhase)+1)
        targetColCurr = (+np.sign(np.cos(clock.getTime()*targetFlickerFreq*2*np.pi)),
                         -np.sign(np.cos(clock.getTime()*targetFlickerFreq*2*np.pi)),
                         -1)

        for mm in range(0, markersNumber):
            image_stim[mm].draw()

        target_stim = visual.Circle(win, pos=tgPos, radius=0.5*targetSizeCurr, edges=100, units='pix',
                                    lineWidth=0.5*targetSizeCurr, lineColor=targetColCurr, fillColor=None)
        target_stim.draw()

        win.flip()

try:
    arduino_write('E')
    print('Pulses ended')
    arduino.close()
except:
    print('No arduino')

win.close()
core.quit()



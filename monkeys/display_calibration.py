import numpy as np
import time, serial
from psychopy import core, event, visual, monitors
from psychopy.hardware import crs
import cv2

# serialAddress = '/dev/ttyACM1'
serialAddress = 'COM3'

screenNum = 1
screenRes = np.array([1920, 1080])
targetNumber = 3

targetITIMin = 0.25
targetITIMax = 0.75
targetTargetMin = 1.5
targetTargetMax = 3.0

targetSizePixMin = 20
targetSizePixMax = 40
targetSizePixFreq = 0.5
targetGapPix = 150

targetFlickerFreq = 2

arucoSizePix = 75
arucoGapPix = 2 * arucoSizePix

tgPosMatX, tgPosMatY = np.meshgrid(np.linspace(-0.5*screenRes[0]+targetGapPix, +0.5*screenRes[0]-targetGapPix, targetNumber),
                                   np.linspace(-0.5*screenRes[1]+targetGapPix, +0.5*screenRes[1]-targetGapPix, targetNumber))
tgOrder = np.random.permutation(targetNumber ** 2)
tgPosMatX = tgPosMatX.flatten()[tgOrder]
tgPosMatY = tgPosMatY.flatten()[tgOrder]


class Talker:
    TERMINATOR = '\r'.encode('UTF8')

    def __init__(self, timeout=1):
        self.serial = serial.Serial(serialAddress, baudrate=9600, timeout=timeout)
        while self.serial.in_waiting:
            self.serial.read()

    def send(self, text: str):
        line = '%s\r\f' % text
        self.serial.write(line.encode('utf-8'))
        reply = self.receive()
        reply = reply.replace('>>> ', '')  # lines after first will be prefixed by a propmt
        print('Sent %s received %s' % (text, reply))
        if reply != text:  # the line should be echoed, so the result should match
            raise ValueError('Wrong reply')

    def receive(self) -> str:
        line = self.serial.read_until(self.TERMINATOR)
        return line.decode('UTF8').strip()

    def close(self):
        self.serial.close()


def check_key():
    if 'escape' in event.getKeys():
        core.quit()


# Connect to arduino
try:
    print('Opening serial port')
    arduino = Talker()
    print('Done')
except Exception as e:
    print(e)
    print('Failed')

# Generate aruco markers
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
markersNumber = 4

# Generate charuco board
# board = cv2.aruco.CharucoBoard_create(7, 5, 1, .8, dictionary)
board = cv2.aruco.CharucoBoard((7, 5), 1, .8, dictionary)
# imboard = 2.0*board.draw((1400, 1000))/255.0-1
imboard = 2.0*board.generateImage((1400, 1000))/255.0-1

# Setup window
monitor = monitors.Monitor('MonkeyCalib', width=53, distance=50)
win = visual.Window(screenRes, screen=screenNum, units="pix", fullscr=False, monitor=monitor)

# Store info about the experiment session
# expName = 'crsTest'  # from the Builder filename that created this script
# expInfo = {'Device': 'Display++',
#            'Analog': 'No',
#            'Touch screen': 'Yes',
#            'Button box': 'CB6',
#            'Monitor': 'Display++160',
#            'LUTfile': 'invGammaLUT.txt',
#            'Screen': '1'}
#
# # Setup the Window
# print("Open window")
# win = visual.Window(
#     size=(800, 600), fullscr=True, screen=int(expInfo['Screen']),
#     allowGUI=False, allowStencil=False,
#     monitor=expInfo['Monitor'], color=[0,0,0], colorSpace='rgb',
#     blendMode='avg', useFBO=True,
#     units='deg')
clock = core.Clock()


# First display charuco board
im_bg = visual.Rect(win, width=1400, height=1000, units='pix', fillColor=[-1,-1,-1])
im_stim = visual.ImageStim(win, image=imboard, mask=None, units='pix', pos=[0,0], size=[1400,1000])

clock.reset()
while clock.getTime() < 10:
    im_bg.draw()
    im_stim.draw()
    win.flip()
    check_key()

for target in range(0, targetNumber ** 2):
    print('Display target %d' % target)
    durITI = targetITIMin + np.random.rand() * (targetITIMax - targetITIMin)
    durTarget = targetTargetMin + np.random.rand() * (targetTargetMax - targetTargetMin)
    tgPos = [tgPosMatX[target], tgPosMatY[target]]
    randPhase = np.random.rand() * 2 * np.pi

    clock.reset()
    while clock.getTime() < durITI:
        win.flip()
        check_key()

    image_stim = []
    for mm in range(0, markersNumber):
        img = 2 * ((cv2.aruco.drawMarker(dictionary, mm, 6) / 255) - 0.5)
        arucoPos = tgPos + arucoGapPix * np.array([np.fix(mm / 2) - 0.5, (mm % 2) - 0.5])
        image_stim.append(visual.ImageStim(win, image=img, mask=None, units='pix', pos=arucoPos, size=50))

    try:
        arduino.send('on()')
    except Exception as e:
        print(e)

    clock.reset()
    while clock.getTime() < durTarget:
        targetSizeCurr = targetSizePixMin + (targetSizePixMax - targetSizePixMin) * 0.5 * \
                         (np.sin(clock.getTime() * targetSizePixFreq * 2 * np.pi + randPhase) + 1)
        targetColCurr = (+np.sign(np.cos(clock.getTime() * targetFlickerFreq * 2 * np.pi)),
                         -np.sign(np.cos(clock.getTime() * targetFlickerFreq * 2 * np.pi)),
                         -1)

        for mm in range(0, markersNumber):
            image_stim[mm].draw()

        target_stim = visual.Circle(win, pos=tgPos, radius=0.5 * targetSizeCurr, edges=100, units='pix',
                                    lineWidth=0.5 * targetSizeCurr, lineColor=targetColCurr, fillColor=None)
        target_stim.draw()

        win.flip()
        check_key()

    try:
        arduino.send('off()')
    except Exception as e:
        print(e)

arduino.close()
win.close()
core.quit()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Monkey Retinal Flow project
3. retinocentric:
In this script we use the pupil position extracted in step 1 and calibration targets
position extracted in step 2 to calibrate eye position and compute images in retino-
centric coordinates.
"""

import time
import os
import cv2
import numpy as np
import pandas as pd
from scipy import interpolate
from sklearn.linear_model import RANSACRegressor
import statsmodels.api as sm
import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt

displayResults = 0
saveTrackingVideo = 1

# Load datasets
dataPath = '../../retinal_flow_data/'
vidName = 'scene_2023-01-16_15-30-50'
eyeFile = 'eye_2023-01-16_15-30-50_eyePosition.csv'
sceneFile = 'scene_2023-01-16_15-30-50_targetPosition.csv'
# vidName = 'scene_2022-12-19_16-33-16'
# eyeFile = 'eye_2022-12-19_16-33-16_eyePosition.csv'
# sceneFile = 'scene_2022-12-19_16-33-16_targetPosition.csv'

eyeDat = pd.read_csv(dataPath+eyeFile, sep=',', names=['F',	'T', 'I', 'X', 'Y', 'D', 'C'], header=0, skiprows=0).values
sceneDat = pd.read_csv(dataPath+sceneFile, sep=',', names=['T', 'I', 'X', 'Y'], header=0, skiprows=0).values

# remove blinks and data points with low confidence
mask = np.logical_or(eyeDat[:, 3] < 10, eyeDat[:, 4] < 10, eyeDat[:, 6] < 0.9)
eyeDat = np.delete(eyeDat, mask, axis=0)

# Find trigger times
eyeTrigOn, = np.where(eyeDat[1:, 2]-eyeDat[:-1, 2] > 0.5)
eyeTrigOff, = np.where(eyeDat[1:, 2]-eyeDat[:-1, 2] < -0.5)
sceneTrigOn, = np.where(sceneDat[1:, 1]-sceneDat[:-1, 1] > 0.5)
sceneTrigOff, = np.where(sceneDat[1:, 1]-sceneDat[:-1, 1] < -0.5)
eyeStart = eyeTrigOn[0]
eyeStop = eyeTrigOff[-1]
sceneStart = sceneTrigOn[0]
sceneStop = sceneTrigOff[-1]

plt.plot(eyeDat[eyeStart-10:eyeStop+10, 1]-eyeDat[eyeStart, 1], eyeDat[eyeStart-10:eyeStop+10, 2],
         sceneDat[sceneStart-10:sceneStop+10, 0]-sceneDat[sceneStart, 0], sceneDat[sceneStart-10:sceneStop+10, 1])
plt.xlabel('Time (msec)')
plt.ylabel('Trigger')
plt.title("Triggers")
plt.legend(['Eye', 'Scene'])
plt.show()


# Focus on the calibration task
eyeCalibStart = eyeTrigOn[0]
eyeCalibStop = eyeTrigOff[-1]
sceneCalibStart = sceneTrigOn[0]
sceneCalibStop = sceneTrigOff[-1]

# Plot eye at target positions as a function of time
plt.subplot(221)
plt.plot(eyeDat[eyeCalibStart:eyeCalibStop, 1]-eyeDat[eyeStart, 1], eyeDat[eyeCalibStart:eyeCalibStop, 3]),
plt.ylabel('Eye X')
plt.subplot(222)
plt.plot(eyeDat[eyeCalibStart:eyeCalibStop, 1]-eyeDat[eyeStart, 1], eyeDat[eyeCalibStart:eyeCalibStop, 4]),
plt.ylabel('Eye Y')
plt.subplot(223)
plt.plot(sceneDat[sceneCalibStart:sceneCalibStop, 0]-sceneDat[sceneStart, 0], sceneDat[sceneCalibStart:sceneCalibStop, 2])
plt.xlabel('Time (msec)')
plt.ylabel('Target X')
plt.subplot(224)
plt.plot(sceneDat[sceneCalibStart:sceneCalibStop, 0]-sceneDat[sceneStart, 0], sceneDat[sceneCalibStart:sceneCalibStop, 3])
plt.xlabel('Time (msec)')
plt.ylabel('Target Y')
plt.show()


# Eye and target positions are resampled at the same FPS. Because most data points are missing for the target,
# I use nearest interpolation
resamplingTimes = np.arange(0, round(eyeDat[eyeCalibStop, 1]-eyeDat[eyeCalibStart, 1]))
feyeX = interpolate.interp1d(eyeDat[eyeCalibStart:eyeCalibStop, 1]-eyeDat[eyeCalibStart, 1],
                             eyeDat[eyeCalibStart:eyeCalibStop, 3], kind='nearest',
                             bounds_error=False)
eyeXresampled = feyeX(resamplingTimes)
fsceneX = interpolate.interp1d(sceneDat[sceneCalibStart:sceneCalibStop, 0]-sceneDat[sceneCalibStart, 0],
                               sceneDat[sceneCalibStart:sceneCalibStop, 2], kind='nearest',
                             bounds_error=False)
sceneXresampled = fsceneX(resamplingTimes)
feyeY = interpolate.interp1d(eyeDat[eyeCalibStart:eyeCalibStop, 1]-eyeDat[eyeCalibStart, 1],
                             eyeDat[eyeCalibStart:eyeCalibStop, 4], kind='nearest',
                             bounds_error=False)
eyeYresampled = feyeY(resamplingTimes)
fsceneY = interpolate.interp1d(sceneDat[sceneCalibStart:sceneCalibStop, 0]-sceneDat[sceneCalibStart, 0],
                               sceneDat[sceneCalibStart:sceneCalibStop, 3], kind='nearest',
                             bounds_error=False)
sceneYresampled = fsceneY(resamplingTimes)

# now perform robust regression of target by eye using ransac
mask = np.logical_not(np.logical_or(np.isnan(sceneXresampled), np.isnan(sceneYresampled)))
regX = RANSACRegressor(random_state=0).fit(sm.add_constant(np.stack((eyeXresampled[np.where(mask)],
                                                                     eyeYresampled[np.where(mask)]), axis=1),
                                                           has_constant='add'),
                                           sceneXresampled[np.where(mask)])
regXpredX = np.stack((np.arange(0, 400), 150*np.ones(400)), axis=1)
regXpredY = regX.predict(sm.add_constant(regXpredX, has_constant='add'))

regY = RANSACRegressor(random_state=0).fit(sm.add_constant(np.stack((eyeXresampled[np.where(mask)],
                                                                     eyeYresampled[np.where(mask)]), axis=1),
                                                           has_constant='add'),
                                           sceneYresampled[np.where(mask)])
regYpredX = np.stack((200*np.ones(400), np.arange(0, 400)), axis=1)
regYpredY = regY.predict(sm.add_constant(regYpredX, has_constant='add'))

# Plot target as a function of eye, correlation should be obvious
plt.subplot(121)
plt.plot(eyeXresampled, sceneXresampled, '.', regXpredX, regXpredY)
plt.xlabel('Eye X')
plt.ylabel('Target X')
plt.subplot(122)
plt.plot(eyeYresampled, sceneYresampled, '.', regYpredX, regYpredY)
plt.xlabel('Eye Y')
plt.ylabel('Target Y')
plt.show()

# Now we replot target positions and predicted eye position
predEyePosX = regX.predict(sm.add_constant(eyeDat[eyeCalibStart:eyeCalibStop, 3:5], has_constant='add'))
predEyePosY = regY.predict(sm.add_constant(eyeDat[eyeCalibStart:eyeCalibStop, 3:5], has_constant='add'))

plt.subplot(211)
plt.plot(eyeDat[eyeCalibStart:eyeCalibStop, 1]-eyeDat[eyeStart, 1], predEyePosX,
         sceneDat[sceneCalibStart:sceneCalibStop, 0]-sceneDat[sceneStart, 0], sceneDat[sceneCalibStart:sceneCalibStop, 2], 'o')
plt.xlabel('Time (msec)')
plt.ylabel('Target X')
plt.subplot(212)
plt.plot(eyeDat[eyeCalibStart:eyeCalibStop, 1]-eyeDat[eyeStart, 1], predEyePosY,
         sceneDat[sceneCalibStart:sceneCalibStop, 0]-sceneDat[sceneStart, 0], sceneDat[sceneCalibStart:sceneCalibStop, 3], 'o')
plt.xlabel('Time (msec)')
plt.ylabel('Target Y')
plt.show()

# # Predict eye position during the headfix session for comparison with eyelink
# resamplingTimes = np.arange(0, round(eyeDat[eyeStop, 1]-eyeDat[eyeStart, 1]))
# feyeX = interpolate.interp1d(eyeDat[eyeStart:(eyeStop+1), 1]-eyeDat[eyeStart, 1],
#                              eyeDat[eyeStart:(eyeStop+1), 3], kind='nearest',
#                              bounds_error=False)
# eyeXresampled = feyeX(resamplingTimes)
# feyeY = interpolate.interp1d(eyeDat[eyeStart:(eyeStop+1), 1]-eyeDat[eyeStart, 1],
#                              eyeDat[eyeStart:(eyeStop+1), 4], kind='nearest',
#                              bounds_error=False)
# eyeYresampled = feyeY(resamplingTimes)
#
# predHFX = regX.predict(sm.add_constant(eyeXresampled))
# predHFY = regY.predict(sm.add_constant(eyeYresampled))
#
# pd.DataFrame(np.concatenate(([predHFX], [predHFY]), axis=0).T, columns=['eyeX', 'eyeY']).to_csv(dataPath+'eyeCalib.csv')


# Now regress the whole resampled eye trace
resamplingTimes = np.arange(eyeDat[0, 1], eyeDat[-1, 1])
feyeX = interpolate.interp1d(eyeDat[:, 1], eyeDat[:, 3], kind='nearest', bounds_error=False)
eyeXresampled = feyeX(resamplingTimes)
feyeY = interpolate.interp1d(eyeDat[:, 1], eyeDat[:, 4], kind='nearest', bounds_error=False)
eyeYresampled = feyeY(resamplingTimes)

allEyeX = regX.predict(sm.add_constant(np.stack((eyeXresampled, eyeYresampled), axis=1), has_constant='add'))
allEyeY = regY.predict(sm.add_constant(np.stack((eyeXresampled, eyeYresampled), axis=1), has_constant='add'))

plt.subplot(211)
plt.plot(resamplingTimes, allEyeX)
plt.subplot(212)
plt.plot(resamplingTimes, allEyeY)
plt.show()

# Generate a video with the eye-position on it

# Open video and trigger files
vidIn = cv2.VideoCapture('%s/%s_processed.mp4' % (dataPath, vidName))
fps = 30
frameWidth = int(vidIn.get(cv2.CAP_PROP_FRAME_WIDTH))
frameHeight = int(vidIn.get(cv2.CAP_PROP_FRAME_HEIGHT))
frameSize = (frameWidth, frameHeight)
vidOut = cv2.VideoWriter('{0}/{1}_eyePos.mp4'.format(dataPath, vidName),
                             cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), fps, frameSize)


predX = regX.predict(sm.add_constant(eyeDat[:, 3:5], has_constant='add'))
predY = regY.predict(sm.add_constant(eyeDat[:, 3:5], has_constant='add'))

ff = -1
while 1:
    ret, frame = vidIn.read()
    if ret:
        ff = ff+1
        eyeSample = np.where(eyeDat[:, 1]-eyeDat[eyeStart, 1] > sceneDat[ff, 0]-sceneDat[sceneStart, 0])[0][0]
        print(eyeSample)
        gazeX = predX[eyeSample]
        gazeY = predY[eyeSample]
        cv2.circle(frame, (int(gazeX), int(gazeY)), 10, (0, 0, 255), -1)

        if displayResults:
            cv2.imshow('picture', frame)
            cv2.waitKey(10)
        if saveTrackingVideo:
            vidOut.write(frame)
    else:
        break
vidIn.release()
vidOut.release()
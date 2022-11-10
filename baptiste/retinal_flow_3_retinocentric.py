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
import matplotlib.pyplot as plt

# Load datasets
dataPath = '../../retinal_flow_data/'
eyeFile = 'eye_2022-11-08_19-54-09_eyePosition.csv'
sceneFile = 'scene_2022-11-08_19-54-09_targetPosition.csv'

eyeDat = pd.read_csv(dataPath+eyeFile, sep=',', names=['F',	'T', 'I', 'X', 'Y', 'D', 'C'], header=0, skiprows=0).values
sceneDat = pd.read_csv(dataPath+sceneFile, sep=',', names=['T', 'I', 'X', 'Y'], header=0, skiprows=0).values

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
eyeCalibStart = eyeTrigOn[1]
eyeCalibStop = eyeTrigOff[1]
sceneCalibStart = sceneTrigOn[1]
sceneCalibStop = sceneTrigOff[1]

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
regX = RANSACRegressor(random_state=0).fit(sm.add_constant(eyeXresampled[np.where(1-np.isnan(sceneXresampled))[0]]),
                                           sceneXresampled[np.where(1-np.isnan(sceneXresampled))[0]])
regXpredX = np.arange(100, 200)
regXpredY = regX.predict(sm.add_constant(regXpredX))

regY = RANSACRegressor(random_state=0).fit(sm.add_constant(eyeYresampled[np.where(1-np.isnan(sceneYresampled))[0]]),
                                           sceneYresampled[np.where(1-np.isnan(sceneYresampled))[0]])
regYpredX = np.arange(100, 200)
regYpredY = regY.predict(sm.add_constant(regYpredX))

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
predEyePosX = regX.predict(sm.add_constant(eyeDat[eyeCalibStart:eyeCalibStop, 3]))
predEyePosY = regY.predict(sm.add_constant(eyeDat[eyeCalibStart:eyeCalibStop, 4]))

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

# Predict eye position during the headfix session for comparison with eyelink
resamplingTimes = np.arange(0, round(eyeDat[eyeStop, 1]-eyeDat[eyeStart, 1]))
feyeX = interpolate.interp1d(eyeDat[eyeStart:(eyeStop+1), 1]-eyeDat[eyeStart, 1],
                             eyeDat[eyeStart:(eyeStop+1), 3], kind='nearest',
                             bounds_error=False)
eyeXresampled = feyeX(resamplingTimes)
feyeY = interpolate.interp1d(eyeDat[eyeStart:(eyeStop+1), 1]-eyeDat[eyeStart, 1],
                             eyeDat[eyeStart:(eyeStop+1), 4], kind='nearest',
                             bounds_error=False)
eyeYresampled = feyeY(resamplingTimes)

predHFX = regX.predict(sm.add_constant(eyeXresampled))
predHFY = regY.predict(sm.add_constant(eyeYresampled))

pd.DataFrame(np.concatenate(([predHFX], [predHFY]), axis=0).T, columns=['eyeX', 'eyeY']).to_csv(dataPath+'eyeCalib.csv')



# Now regress the whole eye trace
resamplingTimes = np.arange(eyeDat[0, 1], eyeDat[-1, 1])
notBlinks = (eyeDat[:, 3]>0)
feyeX = interpolate.interp1d(eyeDat[notBlinks, 1], eyeDat[notBlinks, 3], kind='nearest', bounds_error=False)
eyeXresampled = feyeX(resamplingTimes)
allEyeX = regX.predict(sm.add_constant(eyeXresampled))
feyeY = interpolate.interp1d(eyeDat[notBlinks, 1], eyeDat[notBlinks, 4], kind='nearest', bounds_error=False)
eyeYresampled = feyeY(resamplingTimes)
allEyeY = regY.predict(sm.add_constant(eyeYresampled))

plt.subplot(211)
plt.plot(resamplingTimes, allEyeX)
plt.subplot(212)
plt.plot(resamplingTimes, allEyeY)
plt.show()



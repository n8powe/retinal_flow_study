#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Monkey Retinal Flow project
1. Process eye:
This script reads an eye video and extracts eye position
"""

import time
import cv2
import numpy as np
import pandas as pd
import scipy.linalg as la
from cv2 import data
from pupil_detectors import Detector2D
# from pye3d.detector_3d import CameraModel, Detector3D, DetectorMode
import logging

# logging.basicConfig(filename='pitracker_pupil_tracking.log', level=logging.INFO)
# logging.info('Starting')

# Various settings
makePupilVideo = 1

# Eye video name and path
dataPath = '../../retinal_flow_data/'
fileName = 'eye_2022-11-08_19-54-09'

# Open eye video and triggers file
vidIn = cv2.VideoCapture('{0}/{1}.mjpeg'.format(dataPath, fileName))
triggersData = pd.read_csv('{0}/{1}.txt'.format(dataPath, fileName), sep=',', names=['frameTimes', 'trigger'],
                           header=0, skiprows=0).values

if not vidIn.isOpened():
    print("Failed to open video")

# Get eye video parameters
fps = 90
frameCount = vidIn.get(cv2.CAP_PROP_FRAME_COUNT)
frameWidth = int(vidIn.get(cv2.CAP_PROP_FRAME_WIDTH))
frameHeight = int(vidIn.get(cv2.CAP_PROP_FRAME_HEIGHT))
frameSize = (frameWidth, frameHeight)
print('Frames per second : ', fps, 'FPS')
print('Frame size :', frameSize)
print('Frame count : ', frameCount)

# Illumination of the eye video is not homogenous, images are detrended to improve results
x, y = np.meshgrid(range(-frameHeight//2, frameHeight//2),
                range(-frameWidth//2, frameWidth//2), indexing='ij')
regressors = np.vstack([np.ravel(x), np.ravel(y), np.sqrt(np.power(x, 2)+np.power(y, 2)).ravel()]).T

# create 2D detector from pupillabs
detector_2d = Detector2D()

# # create pye3D detector from pupillabs (I think unused for now)
# camera = CameraModel(focal_length=561.5, resolution=frameSize)
# detector_3d = Detector3D(camera=camera, long_term_mode=DetectorMode.blocking)

# This is the regular processed video
vidOut = cv2.VideoWriter('{0}/{1}_processed.mp4'.format(dataPath, fileName),
                         cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), fps, frameSize)
# This is a video with pupil fits
if makePupilVideo:
    vidPupil = cv2.VideoWriter('%s/%s_pupil.mp4' % (dataPath,fileName),
                              cv2.VideoWriter_fourcc('M','J','P','G'), 90, frameSize, 1)

# Panda frame with eye positions
eyePosition = pd.DataFrame(columns = ['X','Y','D','C'])


for frameNum in range(0, triggersData.shape[0]):
    print("Rewriting ... %3.1f%%" % (100*frameNum/triggersData.shape[0]))
    ret, frame = vidIn.read()

    # First write the raw frame in processed video
    vidOut.write(frame)

    # Here detrend and normalize the image
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    logging.info('Converted to gray')
    # cv2.imshow("gray", gray)

    solution = la.lstsq(regressors, gray.ravel())
    grayDetrended = gray + np.reshape(np.dot(regressors, solution[0]), gray.shape)
    grayDetrended = grayDetrended - np.min(grayDetrended)
    grayDetrended = np.uint8(255 * np.divide(grayDetrended, np.max(grayDetrended)))
    logging.info('Detrended image')

    # cv2.imshow("detrend", grayDetrended)

    # Next denoise the image
    # grayDenoised = cv2.GaussianBlur(grayDetrended,(5,5),0)
    grayDenoised = cv2.medianBlur(grayDetrended, 5)
    logging.info('Denoised image')

    # Run the pupil_detector
    result2d = detector_2d.detect(grayDenoised)
    eyePosition.loc[len(eyePosition.index)] = [result2d["ellipse"]['center'][0], result2d["ellipse"]['center'][1],
                                               result2d['diameter'], result2d['confidence']]
    logging.info('Detected pupil')

    if makePupilVideo:
        drawing = np.copy(cv2.cvtColor(grayDenoised, cv2.COLOR_GRAY2BGR))
        # purkinjeEllipse = cv2.fitEllipse(purkinjeContours[mostCircular])
        cv2.ellipse(drawing, np.array(result2d["ellipse"]['center'], dtype='int'),
                    (0.5 * np.array(result2d["ellipse"]['axes'])).astype('int'), result2d["ellipse"]['angle'], 0, 360,
                    color=(0, 0, 255))

        # cv2.imshow("Pupil", drawing)
        # cv2.waitKey(1)
        vidPupil.write(drawing)


# save the dataframe as a csv file
eyePosition.to_csv('%s/%s_eyePosition.csv' % (dataPath, fileName))

# Close videos
vidIn.release()
vidOut.release()
if makePupilVideo:
    vidPupil.release()
# cv2.destroyAllWindows()


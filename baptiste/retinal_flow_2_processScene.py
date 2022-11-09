#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Monkey Retinal Flow project
2. Process scene:
This script reads a scene video. It extracts the position of the target
during the calibration task
"""

import time
import os
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Scene video name and path
dataPath = '../../retinal_flow_data/'
fileName = 'scene_2022-11-08_19-54-09'

# Open video and trigger files
vidIn = cv2.VideoCapture('%s/%s_processed.avi' % (dataPath, fileName))
data = pd.read_csv('%s/%s.txt' % (dataPath, fileName), sep=',', names=['frameTimes', 'trigger'], header=0,
                   skiprows=0).values

imageSize = (int(vidIn.get(cv2.CAP_PROP_FRAME_WIDTH)), int(vidIn.get(cv2.CAP_PROP_FRAME_HEIGHT)))

fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
writer = cv2.VideoWriter('%s/%s_trimmed.mp4' % (dataPath, fileName), fourcc, 30, imageSize)

# Detect when tasks started and ended (from the trigger)
trigOn, = np.where(data[1:, 1] - data[:-1, 1] > 0.5)
trigOff, = np.where(data[1:, 1] - data[:-1, 1] < -0.5)
trigDur = trigOff - trigOn
taskStart = trigOn[trigDur > 80]
taskStop = trigOff[trigDur > 80]


# Generate the same charuco board used for calibration
gridSize = (14, 7)
boxWidthPix = 8 * 16
cornerThreshold = 4
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
board = cv2.aruco.CharucoBoard_create(gridSize[0], gridSize[1], boxWidthPix, 0.75 * boxWidthPix, dictionary)

# Extract frames from the 1st trigger where the charuco was displayed and detect it
print("Detect charuco board")
allCharucoCorners = []
allCharucoIds = []
vidIn.set(cv2.CAP_PROP_POS_FRAMES, taskStart[0] + 1)
for ff in range(taskStart[0] + 1, taskStop[0]):
    ret, frame = vidIn.read()
    arucoCorners, arucoIds, arucoRejected = cv2.aruco.detectMarkers(frame, dictionary)
    cv2.aruco.drawDetectedMarkers(frame, arucoCorners, arucoIds, borderColor=(0, 0, 255))
    writer.write(frame)

    if len(arucoCorners) > 0:
        charucoNumber, charucoCorners, charucoIds = cv2.aruco.interpolateCornersCharuco(arucoCorners, arucoIds, frame,
                                                                                        board)

        if charucoNumber > cornerThreshold:
            allCharucoCorners.append(charucoCorners)
            allCharucoIds.append(charucoIds)

    cv2.imshow('picture', frame)
    cv2.waitKey(1)

writer.release()
cv2.destroyAllWindows()

# Perform camera calibration from charuco board
print("Perform camera calibration")
retval, cameraMatrix, distCoeffs, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(allCharucoCorners, allCharucoIds,
                                                                                  board, imageSize, None, None)
newcameramtx, roi = cv2.getOptimalNewCameraMatrix(cameraMatrix, distCoeffs, imageSize, 1, imageSize)

# For now, this simply allow testing the undistorsion
print("Undistort images")
vidIn.set(cv2.CAP_PROP_POS_FRAMES, taskStart[0]+1)
for ff in range(taskStart[0]+1,taskStop[0]):
    ret, frame = vidIn.read()
    undistorted = cv2.undistort(frame, cameraMatrix, distCoeffs, None, newcameramtx)
    cv2.imshow('picture', undistorted)
    cv2.waitKey(10)
cv2.destroyAllWindows()


# Now extract frames where the eye calibration target was displayed. The eye calibration
# target is a black bullseye surrounded by 4 arucos. Compute the center of the 4 arucos
# and save it for later steps

print("Detect targets")
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

targetPosition = pd.DataFrame(data=data)
targetPosition = targetPosition.assign(tgX=np.full(targetPosition.shape[0], np.nan))
targetPosition = targetPosition.assign(tgY=np.full(targetPosition.shape[0], np.nan))

# Move video to start of task 2 (calibration)
vidIn.set(cv2.CAP_PROP_POS_FRAMES, taskStart[1] + 1)
for ff in range(taskStart[1] + 1, taskStop[1]):
    ret, frame = vidIn.read()

    arucoCorners, arucoIds, arucoRejected = cv2.aruco.detectMarkers(frame, dictionary)
    cv2.aruco.drawDetectedMarkers(frame, arucoCorners, arucoIds, borderColor=(0, 0, 255))

    # if all 4 arucos are detected
    if len(arucoCorners) == 4:
        targetX = np.empty(4)
        targetY = np.empty(4)
        # compute the center of each aruco
        for aa in range(0, 4):
            targetX[aa] = 0.25 * (arucoCorners[aa][0][0][0] + arucoCorners[aa][0][1][0] +
                                  arucoCorners[aa][0][2][0] + arucoCorners[aa][0][3][0])
            targetY[aa] = 0.25 * (arucoCorners[aa][0][0][1] + arucoCorners[aa][0][1][1] +
                                  arucoCorners[aa][0][2][1] + arucoCorners[aa][0][3][1])
        # and the center of all 4
        targetPosition['tgX'].loc[ff] = np.mean(targetX)
        targetPosition['tgY'].loc[ff] = np.mean(targetY)
        cv2.circle(frame, (int(np.mean(targetX)), int(np.mean(targetY))), 10, (0, 0, 255), -1)

    cv2.imshow('picture', frame)
    cv2.waitKey(10)

# save the dataframe as a csv file
targetPosition.to_csv('%s/%s_targetPosition.csv' % (dataPath, fileName))

vidIn.release()
cv2.destroyAllWindows()

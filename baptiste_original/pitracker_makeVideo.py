#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 11 10:28:36 2022

@author: bremmerlab
"""

import time
import cv2
import numpy as np
import pandas as pd


dataPath = '/mnt/Data/pitracker'
fileName = 'eye_2022-08-08_20-25-30'

duplicateFrames = 0

vidIn = cv2.VideoCapture('{0}/{1}.mjpeg'.format(dataPath,fileName))
data = pd.read_csv('{0}/{1}.txt'.format(dataPath,fileName), sep=',', names=['frameTimes','trigger'], header=0, skiprows=0).values




if not vidIn.isOpened():
    print("Failed opening video")
    
else:
    if fileName.__contains__("eye"):
        fps = 90
    else:
        fps = 30
        
            
    frameCount = vidIn.get(cv2.CAP_PROP_FRAME_COUNT)
    frameWidth = int(vidIn.get(cv2.CAP_PROP_FRAME_WIDTH))
    frameHeight = int(vidIn.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frameSize = (frameWidth,frameHeight)
    print('Frames per second : ', fps,'FPS')
    print('Frame size :', frameSize)
    print('Frame count : ', frameCount)
    
    vidOut = cv2.VideoWriter('{0}/{1}_processed.avi'.format(dataPath,fileName), cv2.VideoWriter_fourcc('M','J','P','G'), fps, frameSize)
    
    frameIn = 0
    frameOut = -1
    # while not(np.isnan(data[frameIn,0])):
        # frameOut = frameOut+1
        # if (frameOut*1000/fps>data[frameIn,0]-0.5*1000/fps) or (duplicateFrames==0):
        #     ret,frame = vidIn.read()
        #     frameIn = frameIn+1
        # vidOut.write(frame)
    
    for frameIn in range(0,data.shape[0]):
        print("Rewriting ... %3.1f%%"%(100*frameIn/data.shape[0]))
        ret,frame = vidIn.read()
        if (duplicateFrames==1):
            while (frameOut*1000/fps<data[frameIn,0]):
                frameOut = frameOut+1
                vidOut.write(frame)
        else:
            vidOut.write(frame)

vidIn.release()
vidOut.release()

# cv2.destroyAllWindows()


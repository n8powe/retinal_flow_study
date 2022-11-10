#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Monkey Retinal Flow project
3b. eyelinkComparison:
For recordings where eyelink data was also recorded, compares accuracy between
the pitracker and eyelink
"""

import time
import os
import cv2
import numpy as np
from parse import parse
import pandas as pd
import matplotlib.pyplot as plt

dataPath = '../../retinal_flow_data/'
fileName = 'pitracker_08-11-2022_19-47-59'


# process eyelink file if not done already
if not os.path.exists(dataPath+fileName+'.csv'):
    fid = open(dataPath+fileName+'.asc', 'r')
    fileTxt = fid.read().splitlines(True)   # split into lines
    fileTxt = list(filter(None, fileTxt))   # remove emptys
    fileTxt = np.array(fileTxt)             # concert to np array for simpler indexing
    fid.close()

    sample = 0
    samplesMat = np.empty((0, 5), float)
    for line in range(0, fileTxt.shape[0]):
        print('Parsing asc file %.1f' % (100*line/fileTxt.shape[0]))
        try:
            if fileTxt[line].__contains__('...'):
                samplesMat = np.append(samplesMat,
                          np.array([parse('{:d}\t{:4.1f}\t{:4.1f}\t{:4.1f}\t{:4.1f}\t...\n', fileTxt[line]).fixed]),
                          axis=0)
        except:
            pass

    df = pd.DataFrame(samplesMat, columns=['Time', 'EyeX', 'EyeY', 'EyeP', 'Input'])
    df.to_csv(dataPath + fileName + '.csv')

# otherwise just load it
else:
    df = pd.read_csv(dataPath+fileName+'.csv')

# plot the eyelink data
plt.subplot(311)
plt.plot(df.Time-df.Time[0], df.EyeX)
plt.xlabel('Time (msec)')
plt.ylabel('Eye X')
plt.subplot(312)
plt.plot(df.Time-df.Time[0], df.EyeY)
plt.xlabel('Time (msec)')
plt.ylabel('Eye Y')
plt.subplot(313)
plt.plot(df.Time-df.Time[0], df.EyeP)
plt.xlabel('Time (msec)')
plt.ylabel('Pupil')
plt.show()

# Now load the preprocessed eye and scene data from pitracker


# plt.subplot(311)
# plt.plot(df.Time-df.Time[0], df.EyeX)
# plt.xlabel('Time (msec)')
# plt.ylabel('Eye X')
# plt.subplot(312)
# plt.plot(df.Time-df.Time[0], df.EyeY)
# plt.xlabel('Time (msec)')
# plt.ylabel('Eye Y')
# plt.subplot(313)
# plt.plot(df.Time-df.Time[0], df.EyeP)
# plt.xlabel('Time (msec)')
# plt.ylabel('Pupil')
# plt.show()


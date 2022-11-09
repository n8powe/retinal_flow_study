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
import matplotlib.pyplot as plt

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Monkey Retinal Flow project
4. posture:
Here we read each tracking video and run deeplabcut on it. Then we compute 3D position of each marker
and fit a skeletal body in them.
"""

import time
import os
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

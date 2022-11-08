# retinal_flow

**This project contains the codebase for post-processing and analysis of eye tracking and neural recording data collected from freely moving Macaques in a constrained environment.**

# Downloading code requirements
* python version?
* requirements file [run python -m requirements.txt from vir env.] etc. 

# Description of the task
* What were the macaques doing?
*  Fixation task
*  Movement task
*  etc.


# Data Description

## Contents
1. Eye-tracking videos:
- Eye videos: 320x320 @ 90Hz.
- Scene videos: 1920x1080 @ 30Hz.
2. Posture videos:
- 6 cameras at 1440×1080 @ 25Hz.
3. Optitrack:
- 3D position and orientation of the head at 1000Hz.
4. Headstage:
- Accelerometer and gyrometer at 40kHz, upsampled from 100Hz.
- Neural data, TBD.

## Downloading Data
*Probably a link to the data that requires explicit access or emailing one of the authors*


# Processing pipeline

Data should be processed in order: (1) Eye, (2) Scene, (3) Retinocentric, (4) Posture (including head) and (5) Neural data.
All data is resampled at 1kHz.

## Eye
1. Extract frames
2. Detect pupil
3. Resample data and fill missing frames

## Scene
1. Extract frames
2. Detect Arucos in calibration frames
3. Rectify videos from fixed calibration
4. Resample data and fill missing frames
5. Compute head-centric optic-flow

## Retinocentric
1. Compute eye-calibration from pupil position, aruco position and calibration file
2. Project rectified scene images into retinal coordinate
4. Compute retino-centric optic-flow

## Posture
1. Get limbs position from deeplabcut
2. Compute 3D position of limbs from stereo
3. Get head-position from Optitrack
4. Get inertial measurements from headstage
5. Fuse head-position, intertial measurement and skeletal model

## Neural data
1. Spike-sorting (Kilosort)
2. TBD


# Running the analyses
*Make different section for each analysis*

## Eye tracking analysis
*Descriptive statistics about gaze behavior*

## Retinal Flow Analysis
*Description of retinal flow analysis/visualization*

### Curl & Divergence signals
## Description of neural recording data

*Description of how analyses were conducted* 

**Correct these brain areas recorded from if incorrect**

### VIP

### LIP

### MST

## Relating Retinal Flow and Neural recordings

*Description of how analyses were conducted* 

### VIP

### LIP

### MST



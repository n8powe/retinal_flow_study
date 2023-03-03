# session must be in format YYYY-mm-dd
#

# import os
import configparser
# import datetime
from configparser import ConfigParser
import cv2
import numpy as np
import pandas as pd
import scipy.linalg as la
from pupil_detectors import Detector2D


class RetinalFlowProcessor:
    config: ConfigParser

    def __init__(self, session, profile='default'):

        # Load parameters
        self.config = configparser.ConfigParser()
        self.config.read('%s.ini' % profile)

        # Extract parameters
        self.dataPath = self.config.get('general', 'dataPath')

        # Find session files
        self.calibrationVideoRaw = -1
        self.calibrationVideoProcessed = -1
        self.calibrationMatrices = -1
        self.eyeVideoRaw = -1
        self.eyeVideoProcessed = -1
        self.eyeVideoPupil = -1
        self.eyePositionFile = -1
        self.sceneVideoRaw = -1
        self.sceneVideoProcessed = -1

        # self.find_files(session)

    # def find_files(self, session):
    #     sessionDate = datetime.datetime.strptime(session, '%Y-%m-%d').date()
    #     fileList = os.listdir(self.dataPath)
    #     for file in fileList:
    #         if file.__contains__('calibration') and \
    #                 file.__contains__(datetime.datetime.strftime(sessionDate, '%YYYY-%mm-%dd')):
    #             self.calibFile = file
    #         elif file.__contains__(datetime.datetime.strftime(sessionDate, 'eye_%YYYY-%mm-%dd')):
    #             if file.__contains__('.mjpeg'):
    #                 self.eyeVideoRaw = file
    #             elif file.__contains__('processed'):
    #                 self.eyeVideoProcessed = file
    #             elif file.__contains__('pupil'):
    #                 self.eyeVideoPupil = file
    #             elif file.__contains__('eyePos'):
    #                 self.eyePosFile = file
    #         elif file.__contains__(datetime.datetime.strftime(sessionDate, 'scene_%YYYY-%mm-%dd')):
    #             if file.__contains__('.mjpeg'):
    #                 self.sceneVideoRaw = file
    #             elif file.__contains__('processed'):
    #                 self.sceneVideoProcessed = file

    def do_calibration(self, force_reprocess=0, starting_frame=0, stopping_frame=np.inf):
        if (self.config.has_option('calib', 'calibrationMatrices')) and not force_reprocess:
            self.calibrationMatrices = self.config.get('calib', 'calibrationMatrices')
            print('Calibration matrix already provided: {}\nCall do_calibration with force_reprocess=1'.format(
                self.config.get('calib', 'calibrationMatrices')))
            return
        if self.calibrationVideoRaw == -1:
            raise ValueError('Provide a calibration video file as calibrationVideoRaw')

        displayResults = 0
        if self.config.has_option('calib', 'displayResults'):
            displayResults = int(self.config.get('calib', 'displayResults'))
        makeVideo = 0
        if self.config.has_option('calib', 'makeVideo'):
            makeVideo = int(self.config.get('calib', 'makeVideo'))

        # open calibration video
        vidIn = cv2.VideoCapture('%s%s.mjpeg' % (self.dataPath, self.calibrationVideoRaw))
        if not vidIn.isOpened():
            print('Failed to open video file: %s' % self.calibrationVideoRaw)
            return
        frameRate = 30  # fixed the framerate because cv2.CAP_PROP_FPS is broken with mjpeg
        frameWidth = int(vidIn.get(cv2.CAP_PROP_FRAME_WIDTH))
        frameHeight = int(vidIn.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frameSize = (frameWidth, frameHeight)

        # Generate the same charuco board used for calibration
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        board = cv2.aruco.CharucoBoard_create(int(self.config.get('calib', 'gridSizeWidth')),
                                              int(self.config.get('calib', 'gridSizeHeight')),
                                              int(self.config.get('calib', 'boxWidthPix')),
                                              0.75 * int(self.config.get('calib', 'boxWidthPix')),
                                              dictionary)

        # Extract frames and try to detect charuco board
        print("Detect charuco board")
        allCharucoCorners = []
        allCharucoIds = []
        # vidIn.set(cv2.CAP_PROP_POS_FRAMES, starting_frame - 1)
        fn = -1
        while 1:
            ret, frame = vidIn.read()
            fn = fn + 1

            if not ret or (fn > stopping_frame):
                break

            if fn >= starting_frame:
                arucoCorners, arucoIds, arucoRejected = cv2.aruco.detectMarkers(frame, dictionary)
                cv2.aruco.drawDetectedMarkers(frame, arucoCorners, arucoIds, borderColor=(0, 0, 255))

                if len(arucoCorners) > 0:
                    charucoNumber, charucoCorners, charucoIds = \
                        cv2.aruco.interpolateCornersCharuco(arucoCorners, arucoIds, frame, board)

                    if charucoNumber > int(self.config.get('calib', 'cornerThreshold')):
                        allCharucoCorners.append(charucoCorners)
                        allCharucoIds.append(charucoIds)

                if displayResults:
                    cv2.imshow('picture', frame)
                    cv2.waitKey(1)

        vidIn.release()
        cv2.destroyAllWindows()

        # Perform camera calibration from charuco board
        print("Performing camera calibration")
        retval, cameraMatrix, distCoeffs, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(allCharucoCorners,
                                                                                          allCharucoIds, board,
                                                                                          frameSize, None, None)
        newCameraMatrix, roi = cv2.getOptimalNewCameraMatrix(cameraMatrix, distCoeffs, frameSize, 1, frameSize)

        # retval, cameraMatrix, distCoeffs, rvecs, tvecs = \
        #     cv2.aruco.calibrateCameraCharuco(allCharucoCorners, allCharucoIds, board, frameSize, None, None)
        # newCameraMatrix, roi = cv2.getOptimalNewCameraMatrix(cameraMatrix, distCoeffs, frameSize, 1, frameSize)

        # make undistorted video if requested
        if makeVideo:
            print("Undistort video")
            self.calibrationVideoProcessed = '%s/%s_undistorted.mp4' % (self.dataPath, self.calibrationVideoRaw)
            vidOut = cv2.VideoWriter(self.calibrationVideoProcessed,
                                     cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), frameRate, frameSize)

            vidIn = cv2.VideoCapture('%s%s.mjpeg' % (self.dataPath, self.calibrationVideoRaw))
            fn = -1
            while 1:
                ret, frame = vidIn.read()
                fn = fn + 1

                if not ret:
                    break

                if fn >= starting_frame:
                    undistorted = cv2.undistort(frame, cameraMatrix, distCoeffs, None, newCameraMatrix)
                    if displayResults:
                        cv2.imshow('picture', undistorted)
                        cv2.waitKey(1)

                    vidOut.write(undistorted)

            cv2.destroyAllWindows()
            vidIn.release()
            vidOut.release()

        # Save calibration results
        self.calibrationMatrices = '%scalibrationMatrices.npy' % self.dataPath
        print('Saving calibration results as: %s' % self.calibrationMatrices)
        fid = open(self.calibrationMatrices, 'wb')
        np.save(fid, np.array(cameraMatrix))
        np.save(fid, np.array(distCoeffs))
        np.save(fid, np.array(newCameraMatrix))
        fid.close()

    def process_eye(self, force_reprocess=0):
        if (self.eyePositionFile != -1) and not force_reprocess:
            print('Eye already processed: {}\nCall process_eye with force_reprocess=1' % self.eyePositionFile)
            return
        if self.eyeVideoRaw == -1:
            raise ValueError('Provide an eye video file as eyeVideoRaw')

        vidIn = cv2.VideoCapture('%s%s.mjpeg' % (self.dataPath, self.eyeVideoRaw))
        triggersData = pd.read_csv('%s%s.txt' % (self.dataPath, self.eyeVideoRaw), sep=',',
                                   names=['frameTimes', 'trigger'], header=0, skiprows=0).values

        if not vidIn.isOpened():
            print('Failed to open video file: %s' % self.eyeVideoRaw)
            return

        # Get eye video parameters
        frameRate = 90
        if self.config.has_option('eye', 'frameRate'):
            frameRate = int(self.config.get('eye', 'frameRate'))
        frameCount = vidIn.get(cv2.CAP_PROP_FRAME_COUNT)
        frameWidth = int(vidIn.get(cv2.CAP_PROP_FRAME_WIDTH))
        frameHeight = int(vidIn.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frameSize = (frameWidth, frameHeight)
        print('Frames per second : ', frameRate, 'FPS')
        print('Frame size :', frameSize)
        print('Frame count : ', frameCount)

        # Illumination of the eye video is not homogenous, images are detrended to improve results
        x, y = np.meshgrid(range(-frameHeight // 2, frameHeight // 2),
                           range(-frameWidth // 2, frameWidth // 2), indexing='ij')
        regressors = np.vstack([np.ravel(x), np.ravel(y), np.sqrt(np.power(x, 2) + np.power(y, 2)).ravel()]).T

        # create 2D detector from pupil labs
        detector_2d = Detector2D()
        if self.config.has_option('eye', 'pupilSizeMin'):
            detector_2d.update_properties({'pupil_size_min': int(self.config.get('eye', 'pupilSizeMin'))})

        # This is the regular processed video
        displayResults = 0
        if self.config.has_option('eye', 'displayResults'):
            displayResults = int(self.config.get('eye', 'displayResults'))
        makeProcessedVideo = 0
        if self.config.has_option('eye', 'makeProcessedVideo'):
            makeProcessedVideo = int(self.config.get('eye', 'makeProcessedVideo'))
        makePupilVideo = 0
        if self.config.has_option('eye', 'makePupilVideo'):
            makePupilVideo = int(self.config.get('eye', 'makePupilVideo'))

        if makeProcessedVideo:
            vidOut = cv2.VideoWriter('%s%s_processed.mp4' % (self.dataPath, self.eyeVideoRaw),
                                     cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), frameRate, frameSize)
        if makePupilVideo:
            vidPupil = cv2.VideoWriter('%s%s_pupil.mp4' % (self.dataPath, self.eyeVideoRaw),
                                       cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), frameRate, frameSize, 1)

        # Panda frame with eye positions
        eyePosition = pd.DataFrame(data=triggersData)
        eyePosition = eyePosition.assign(eyeX=np.full(eyePosition.shape[0], np.nan))
        eyePosition = eyePosition.assign(eyeY=np.full(eyePosition.shape[0], np.nan))
        eyePosition = eyePosition.assign(eyeD=np.full(eyePosition.shape[0], np.nan))
        eyePosition = eyePosition.assign(eyeC=np.full(eyePosition.shape[0], np.nan))

        for frameNum in range(0, triggersData.shape[0]):
            print("Processing eye video ... %3.1f%%" % (100 * frameNum / triggersData.shape[0]))
            ret, frame = vidIn.read()

            if makeProcessedVideo:
                vidOut.write(frame)

            # Detrend, normalize and denoise the image
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            solution = la.lstsq(regressors, gray.ravel())
            grayDetrended = gray + np.reshape(np.dot(regressors, solution[0]), gray.shape)
            grayDetrended = grayDetrended - np.min(grayDetrended)
            grayDetrended = np.uint8(255 * np.divide(grayDetrended, np.max(grayDetrended)))
            grayDenoised = cv2.medianBlur(grayDetrended, 5)

            # Run the pupil_detector, add result to panda frame
            result2d = detector_2d.detect(grayDenoised)
            eyePosition['eyeX'].loc[frameNum] = result2d["ellipse"]['center'][0]
            eyePosition['eyeY'].loc[frameNum] = result2d["ellipse"]['center'][1]
            eyePosition['eyeD'].loc[frameNum] = result2d['diameter']
            eyePosition['eyeC'].loc[frameNum] = result2d['confidence']

            if displayResults or makePupilVideo:
                drawing = np.copy(cv2.cvtColor(grayDenoised, cv2.COLOR_GRAY2BGR))
                cv2.ellipse(drawing, np.array(result2d["ellipse"]['center'], dtype='int'),
                            (0.5 * np.array(result2d["ellipse"]['axes'])).astype('int'),
                            result2d["ellipse"]['angle'], 0, 360,
                            color=(0, 0, 255))
                if displayResults:
                    cv2.imshow("Pupil", drawing)
                    cv2.waitKey(1)
                if makePupilVideo:
                    vidPupil.write(drawing)

        cv2.destroyAllWindows()
        vidIn.release()
        if makeProcessedVideo:
            vidOut.release()
        if makePupilVideo:
            vidPupil.release()

        # Save the dataframe as a csv file
        self.eyePositionFile = '%s%s_eyePosition.csv' % (self.dataPath, self.eyeVideoRaw)
        eyePosition.to_csv(self.eyePositionFile)

    def process_scene(self, force_reprocess=0):
        if (self.sceneVideoProcessed != -1) and not force_reprocess:
            print('Scene already processed: {}\nCall process_scene with force_reprocess=1' % self.sceneVideoProcessed)
            return
        if self.sceneVideoRaw == -1:
            raise ValueError('Provide a scene video file as sceneVideoRaw')

        vidIn = cv2.VideoCapture('%s%s.mjpeg' % (self.dataPath, self.sceneVideoRaw))
        triggersData = pd.read_csv('%s%s.txt' % (self.dataPath, self.sceneVideoRaw), sep=',',
                                   names=['frameTimes', 'trigger'], header=0, skiprows=0).values

        if not vidIn.isOpened():
            print('Failed to open video file: %s' % self.sceneVideoRaw)
            return

        # Get scene video parameters
        frameRate = 30
        if self.config.has_option('scene', 'frameRate'):
            frameRate = int(self.config.get('scene', 'frameRate'))
        frameCount = vidIn.get(cv2.CAP_PROP_FRAME_COUNT)
        frameWidth = int(vidIn.get(cv2.CAP_PROP_FRAME_WIDTH))
        frameHeight = int(vidIn.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frameSize = (frameWidth, frameHeight)
        print('Frames per second : ', frameRate, 'FPS')
        print('Frame size :', frameSize)
        print('Frame count : ', frameCount)

        vidOut = cv2.VideoWriter('%s%s_processed.mp4' % (self.dataPath, self.sceneVideoRaw),
                                 cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), frameRate, frameSize)

        for frameNum in range(0, triggersData.shape[0]):
            print("Processing scene video ... %3.1f%%" % (100 * frameNum / triggersData.shape[0]))
            ret, frame = vidIn.read()
            vidOut.write(frame)

        vidIn.release()
        vidOut.release()

    def compute_scene_intrinsic(self):
        pass

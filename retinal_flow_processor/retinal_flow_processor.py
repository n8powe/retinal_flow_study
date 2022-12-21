
# session must be in format YYYY-mm-dd
#

import os
import configparser
import datetime
import cv2


class RetinalFlowProcessor:

    def __init__(self, session, profile='default'):

        # Load parameters
        self.config = configparser.ConfigParser()
        self.config.read('%s.ini' % profile)

        # Extract parameters
        self.dataPath = self.config.get('general', 'dataPath')

        # Find session files
        self.calibFile = -1
        self.eyeVideoRaw = -1
        self.eyeVideoProcessed = -1
        self.eyeVideoPupil = -1
        self.eyePosFile = -1
        self.sceneVideoRaw = -1
        self.sceneVideoProcessed = -1

        self.find_files(session)

    def find_files(self, session):
        sessionDate = datetime.datetime.strptime(session, '%Y-%m-%d').date()
        fileList = os.listdir(self.dataPath)
        for file in fileList:
            if file.__contains__('calib'):
                self.calibFile = file
            elif file.__contains__(datetime.datetime.strftime(sessionDate ,'eye_%YYYY-%mm-%dd')):
                if file.__contains__('.mjpeg'):
                    self.eyeVideoRaw = file
                elif file.__contains__('processed'):
                    self.eyeVideoProcessed = file
                elif file.__contains__('pupil'):
                    self.eyeVideoPupil = file
                elif file.__contains__('eyePos'):
                    self.eyePosFile = file
            elif file.__contains__(datetime.datetime.strftime(sessionDate ,'scene_%YYYY-%mm-%dd')):
                if file.__contains__('.mjpeg'):
                    self.sceneVideoRaw = file
                elif file.__contains__('processed'):
                    self.sceneVideoProcessed = file

    def do_calibration(self, force_reprocess=0):
        if (self.calibFile != -1) and not force_reprocess:
            print('Calibration file already exists: %s' % self.eyePosFile)
            return

        # open calibration video
        vidIn = cv2.VideoCapture('{0}/{1}.mjpeg'.format(self.dataPath, self.config.get('calib', 'videoName')))
        frameWidth = int(vidIn.get(cv2.CAP_PROP_FRAME_WIDTH))
        frameHeight = int(vidIn.get(cv2.CAP_PROP_FRAME_HEIGHT))

        frameSize = (frameWidth, frameHeight)
        if self.config.get('calib', 'makeVideo'):
            fps = int(vidIn.get(cv2.CAP_PROP_FPS))
            vidOut = cv2.VideoWriter('%s/%s_processed.mp4' % (self.dataPath, self.config.get('calib', 'videoName')),
                                     cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), fps, frameSize)

        # Generate the same charuco board used for calibration
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        board = cv2.aruco.CharucoBoard_create(int(self.config.get('calib', 'gridSizeWidth')),
                                              int(self.config.get('calib', 'gridSizeHeight')),
                                              int(self.config.get('calib', 'boxWidthPix')),
                                              0.75 * int(self.config.get('calib', 'boxWidthPix')),
                                              dictionary)

        # Extract frames from the 1st trigger where the charuco was displayed and detect it
        print("Detect charuco board")
        allCharucoCorners = []
        allCharucoIds = []
        while 1:
            ret, frame = vidIn.read()
            if not ret:
                break

            arucoCorners, arucoIds, arucoRejected = cv2.aruco.detectMarkers(frame, dictionary)
            cv2.aruco.drawDetectedMarkers(frame, arucoCorners, arucoIds, borderColor=(0, 0, 255))
            if bool(self.config.get('calib', 'makeVideo')):
                vidOut.write(frame)

            if len(arucoCorners) > 0:
                charucoNumber, charucoCorners, charucoIds = \
                    cv2.aruco.interpolateCornersCharuco(arucoCorners, arucoIds, frame, board)

                if charucoNumber > int(self.config.get('calib', 'cornerThreshold')):
                    allCharucoCorners.append(charucoCorners)
                    allCharucoIds.append(charucoIds)

            if bool(self.config.get('calib', 'displayResults')):
                cv2.imshow('picture', frame)
                cv2.waitKey(1)

        vidOut.release()
        cv2.destroyAllWindows()

        # Perform camera calibration from charuco board
        print("Perform camera calibration")
        retval, cameraMatrix, distCoeffs, rvecs, tvecs = \
            cv2.aruco.calibrateCameraCharuco(allCharucoCorners, allCharucoIds, board, frameSize, None, None)
        newCameraMatrix, roi = cv2.getOptimalNewCameraMatrix(cameraMatrix, distCoeffs, frameSize, 1, frameSize)

        # Show the undistortion
        if bool(self.config.get('calib', 'displayResults')) or bool(self.config.get('calib', 'makeVideo')):
            print("Undistort images")
            vidIn.set(cv2.CAP_PROP_POS_FRAMES, 0)
            while 1:
                ret, frame = vidIn.read()
                if not ret:
                    break

                undistorted = cv2.undistort(frame, cameraMatrix, distCoeffs, None, newCameraMatrix)
                if self.config.get('calib', 'displayResults'):
                    cv2.imshow('picture', undistorted)
                    cv2.waitKey(10)
            cv2.destroyAllWindows()

    def process_eye(self, force_reprocess=0):
        if self.eyePosFile != -1:
            print('Eye-position file already exists: %s' % self.eyePosFile)
            return

    def compute_scene_intrinsic(self):
        pass

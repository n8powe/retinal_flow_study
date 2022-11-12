#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  9 18:32:44 2022

@author: bremmerlab
"""

import os, io, time, serial, threading
import cv2
import PySpin


data_path = '/media/Data/headtracking/'
wait_time = 1

camera_fps = 30
tmax = 30
n_images = camera_fps*tmax
image_height = 1080
image_width = 1440
bin_size = 1

grab_timeout = int(1000*2/camera_fps)
stream_buffer_count = 200

master_camera = '21190983'
trigger_source_master = 'Line2'
trigger_source_slave = 'Line3'
exposure_time = int(2001) # microseconds
gain_value = 1 # in dB, 0-40;
gamma_value = 0.3 # 0.25-1

recording_time = time.strftime("%Y-%m-%d_%H-%M-%S")


print('Open Pyspin instance')
system = PySpin.System.GetInstance()
cameras = system.GetCameras()

# Thread frame writing
class ThreadWriteImage(threading.Thread):
    def __init__(self, image, dataFolder, cn, im):
        threading.Thread.__init__(self)
        self.image = image
        self.dataFolder = dataFolder
        self.cn = cn
        self.im = im
        
    def run(self):
        image_converted = self.image.Convert(PySpin.PixelFormat_RGB8, PySpin.HQ_LINEAR)
        filename = '%s/camera-%s_im%d.png' % (self.dataFolder, self.cn, self.im)
        image_converted.Save(filename)
        
class ThreadWrite(threading.Thread):
    def __init__(self, image, writer):
        threading.Thread.__init__(self)
        self.image = image
        self.writer = writer

    def run(self):
        self.writer.Append(self.image)

# Capturing is also threaded, to increase performance
class ThreadCapture(threading.Thread):
    def __init__(self,camera,cn,vid_handle,pts_handle):
        threading.Thread.__init__(self)
        self.camera = camera
        self.cn = cn
        self.vid_handle = vid_handle
        self.pts_handle = pts_handle

    def run(self):
        
        timestamps = list()
        t0 = -1

        for im in range(n_images):
            try:
                #  Get next frame
                image_result = self.camera.GetNextImage()

                if (t0==-1):
                    t0 = image_result.GetTimeStamp()
                    print('*** ACQUISITION STARTED ***')
                timestamps.append((image_result.GetTimeStamp()-t0)/1000000.0)
                self.pts_handle.write('%d,%f\n' % (im,timestamps[im]))
                tn = timestamps[im]/1000
                print('Camera %d, Frame %d, time %.2f' % (self.cn,im,tn))
                
                background = ThreadWriteImage(image_result, self.vid_handle, self.cn, im)
                background.start()
                
                
                image_result.Release()
                
                
            except PySpin.SpinnakerException as ex:
                print('Error (577): %s' % ex)
                return 1
            except KeyboardInterrupt:
                print('Interrupted by user')
                return 0
            except Exception as ex:
                print(ex)
                return 1
        
        self.camera.EndAcquisition()
        
def configure_cam(camera, master):    
    try:
        nodemap = camera.GetNodeMap()
        try:
            camera.EndAcquisition()
        except:
            pass
        
        camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        
        print('Requested bin size: %i' % bin_size)
        if PySpin.IsWritable(camera.BinningHorizontal):
            camera.BinningHorizontal.SetValue(bin_size)
        if PySpin.IsWritable(camera.BinningVertical):
            camera.BinningVertical.SetValue(bin_size)
        print('Bin size: %ix%i.' % (camera.BinningHorizontal.GetValue(),camera.BinningVertical.GetValue()))
        
        resolution = [int(camera.SensorWidth.GetValue()/bin_size),int(camera.SensorHeight.GetValue()/bin_size)]
        
        if PySpin.IsWritable(camera.Width):
            camera.Width.SetValue(resolution[0])
        if PySpin.IsWritable(camera.Height):
            camera.Height.SetValue(resolution[1])
        print('Resolution: %ix%i.' % (camera.Width.GetValue(),camera.Height.GetValue()))

        
        if master:
            camera.AcquisitionFrameRateEnable.SetValue(True)
            camera.AcquisitionFrameRate.SetValue(30)
            camera.TriggerMode.SetValue(PySpin.TriggerMode_Off)
            camera.LineSelector.SetValue(PySpin.LineSelector_Line2)
            camera.LineMode.SetValue(PySpin.LineMode_Output) 
            camera.LineSource.SetValue(PySpin.LineSource_ExposureActive)
        else:
            camera.AcquisitionFrameRateEnable.SetValue(False)
            camera.TriggerMode.SetValue(PySpin.TriggerMode_Off)
            camera.TriggerSource.SetValue(PySpin.TriggerSource_Line3)
            camera.TriggerOverlap.SetValue(PySpin.TriggerOverlap_ReadOut)
            camera.TriggerActivation.SetValue(PySpin.TriggerActivation_RisingEdge)
            camera.TriggerSelector.SetValue(PySpin.TriggerSelector_FrameStart)
            camera.TriggerMode.SetValue(PySpin.TriggerMode_On)
        
        
        # Retrieve Stream Parameters device nodemap
        camTLS = camera.GetTLStreamNodeMap()
        handling_mode = PySpin.CEnumerationPtr(camTLS.GetNode('StreamBufferHandlingMode'))
        handling_mode_entry = handling_mode.GetEntryByName('OldestFirst')
        handling_mode.SetIntValue(handling_mode_entry.GetValue())
        

        # Access trigger overlap info
        node_trigger_overlap = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerOverlap'))
        if not PySpin.IsAvailable(node_trigger_overlap) or not PySpin.IsWritable(node_trigger_overlap):
            print('Unable to set trigger overlap to "Read Out". Aborting...')
            return False

        # Retrieve enumeration for trigger overlap Read Out
        node_trigger_overlap_ro = node_trigger_overlap.GetEntryByName('ReadOut')
        
        if not PySpin.IsAvailable(node_trigger_overlap_ro) or not PySpin.IsReadable(
                node_trigger_overlap_ro):
            print('Unable to set trigger overlap (entry retrieval). Aborting...')
            return False

        # Retrieve integer value from enumeration
        trigger_overlap_ro = node_trigger_overlap_ro.GetValue()

        # Set trigger overlap using retrieved integer from enumeration
        node_trigger_overlap.SetIntValue(trigger_overlap_ro)

        # Access exposure auto info
        node_exposure_auto = PySpin.CEnumerationPtr(nodemap.GetNode('ExposureAuto'))
        if not PySpin.IsAvailable(node_exposure_auto) or not PySpin.IsWritable(node_exposure_auto):
            print('Unable to get exposure auto. Aborting...')
            return False

        # Retrieve enumeration for trigger overlap Read Out
        node_exposure_auto_off = node_exposure_auto.GetEntryByName('Off')
        if not PySpin.IsAvailable(node_exposure_auto_off) or not PySpin.IsReadable(
                node_exposure_auto_off):
            print('Unable to get exposure auto "Off" (entry retrieval). Aborting...')
            return False

        # Set exposure auto to off
        node_exposure_auto.SetIntValue(node_exposure_auto_off.GetValue())

        # Access exposure info
        node_exposure_time = PySpin.CFloatPtr(nodemap.GetNode('ExposureTime'))
        if not PySpin.IsAvailable(node_exposure_time) or not PySpin.IsWritable(node_exposure_time):
            print('Unable to get exposure time. Aborting...')
            return False

    except PySpin.SpinnakerException as ex:
        print('Error (237): %s' % ex)
        return False

    return True


def config_and_acquire(cam_list, data_folder):
    
    thread = []
    
    # First configure all cameras
    for cn,camera in enumerate(cam_list):
        
        camera.Init()
        print('Setting camera %s' % camera.DeviceSerialNumber())
        
        # Configure camera
        if camera.DeviceSerialNumber()==master_camera:
            configure_cam(camera,1)
        else:
            configure_cam(camera,0)
    
    print("Initiated all cameras")
    time.sleep(1)
    
    # Then start acquiring
    print("Start acquiring")
    for cn,camera in enumerate(cam_list):
        # Open video file
        vid_filename = data_path+'headtracking_%s_%s'%(recording_time,camera.DeviceSerialNumber())
        
        
        # Open timestamps file
        pts_filename = data_path+'headtracking_%s_%s.txt'%(recording_time,camera.DeviceSerialNumber())
        pts_handle = io.open(pts_filename, 'w')
        print('Opened file %s' % pts_filename)
        
        
        camera.BeginAcquisition()
        thread.append(ThreadCapture(camera,cn,data_folder,pts_handle))
        thread[cn].start()
        

    # # print('*** WAITING FOR FIRST TRIGGER... ***\n')
    # wait_time = 0.5
    # print('Wait %d seconds' % wait_time)
    # time.sleep(wait_time)
    # msg = 'S'
    # sid.write(msg.encode()) 
        
    for t in thread:
        t.join()

    print('*** ALL THREAD CLOSED... ***\n')

    # msg = 'Q'
    # sid.write(msg.encode())
    # wait_time = 0.5
    # print('Wait %d seconds' % wait_time)
    # time.sleep(wait_time)

    pts_handle.close()

    for cn, camera in enumerate(cam_list):
        camera.DeInit()
        # camera.EndAcquisition()

def main():

    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    num_cameras = cam_list.GetSize()
    print('Number of cameras detected: %d' % num_cameras)
    
    if num_cameras == 0:
        cam_list.Clear()
        system.ReleaseInstance()
        print('Not enough cameras! Goodbye :(')
        return False
    else:
        data_folder = time.strftime(data_path+"calibration_%Y-%m-%d_%H-%M-%S")
        os.mkdir(data_folder)
        config_and_acquire(cam_list,data_folder)
   
    print('*** CLOSING... ***\n')

    # Clear cameras and release system instance
    cam_list.Clear()
    system.ReleaseInstance()

    print('DONE')
    time.sleep(.5)
    print('Goodbye :)')
    
    return 0

if __name__ == '__main__':
    main()



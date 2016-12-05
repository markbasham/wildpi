import io
import random
import picamera
from PIL import Image
import numpy as np
import picamera
import picamera.array
from subprocess import call
import datetime


motion_detected = False

class DetectMotion(picamera.array.PiMotionAnalysis):

    def reset(self):
        self.motion_detected = False

    def check_motion(self):
        result = self.motion_detected
        self.reset()
        return result
        
    def analyze(self, a):
        a = np.sqrt(
            np.square(a['x'].astype(np.float)) +
            np.square(a['y'].astype(np.float))
            ).clip(0, 255).astype(np.uint8)
        # If there're more than 10 vectors with a magnitude greater
        # than 60, then say we've detected motion
        if (a > 60).sum() > 10:
            print('Motion detected! in the motion class')
            self.motion_detected = True
            

with picamera.PiCamera() as camera:
    with DetectMotion(camera) as output:
        output.reset()
        camera.resolution = (640, 480)  # (1280, 720)
        stream = picamera.PiCameraCircularIO(camera, seconds=10)
        camera.start_recording(stream, format='h264', motion_output=output)
        try:
            count = 0
            while count < 5:
                print("count is at %i" % (count))
                camera.wait_recording(1)
                if output.check_motion():
                    print('Motion detected!, capturing movies')
                    # As soon as we detect motion, split the recording to
                    # record the frames "after" motion
                    camera.split_recording('/tmp/after.h264')
                    # Write the 10 seconds "before" motion to disk as well
                    stream.copy_to('/tmp/before.h264', seconds=10)
                    stream.clear()
                    # Wait until motion is no longer detected, then split
                    # recording back to the in-memory circular buffer
                    while output.check_motion():
                        camera.wait_recording(10)
                    print('Motion stopped, ending recording!')
                    camera.split_recording(stream)
                    count+=1
                    call(["MP4Box",
                          "-cat",
                          "/tmp/before.h264",
                          "-cat",
                          "/tmp/after.h264",
                          "-new",
                          "/tmp/capture_%s.mp4" % (str(datetime.datetime.now()))])
                    # Need to add a call out here to build a compiled file
                    # MP4Box -cat before1.h264 -cat after1.h264 -new mergedFile.mp4
                    
        finally:
            camera.stop_recording()
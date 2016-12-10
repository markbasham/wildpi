import io
import random
import picamera
from PIL import Image
import numpy as np
import picamera
import picamera.array
from subprocess import call
import datetime

from pydrive.auth import GoogleAuth

gauth = GoogleAuth()

print("Authenticating")
if gauth.credentials is None:
    print("Authenticate if they're not there")
#    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    print("Refresh them if expired")
    gauth.Refresh()
else:
    print("Initialize the saved creds")
    gauth.Authorize()

print("Credentials sorted")

from pydrive.drive import GoogleDrive

drive = GoogleDrive(gauth)

# get the wildpi folder in google drive
folder_id = None
file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
for file1 in file_list:
    if file1['title'] == 'wildpi': 
        print('title: %s, id: %s' % (file1['title'], file1['id']))
        folder_id = file1['id']

print("File ID is %s" % folder_id)


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
        #print(a.shape, (a > 20).sum(), a.mean())
        if (a > 20).sum() > 10:
            print('Motion detected! in the motion class')
            self.motion_detected = True
            

with picamera.PiCamera() as camera:
    with DetectMotion(camera) as output:
        output.reset()
        #camera.resolution = (1920, 1080)
        #camera.resolution = (1280, 720)
        camera.resolution = (640, 480)  # (1280, 720)
        stream = picamera.PiCameraCircularIO(camera, seconds=10)
        camera.start_recording(stream, format='h264', motion_output=output)
        try:
            count = 0
            while True: #count < 3:
                print("count is at %i" % (count))
                camera.wait_recording(1)
                motion = output.check_motion()
                if motion:
                    print('Motion detected!, capturing movies')
                    # As soon as we detect motion, split the recording to
                    # record the frames "after" motion
                    camera.split_recording('/tmp/after.h264')
                    # Write the 10 seconds "before" motion to disk as well
                    stream.copy_to('/tmp/before.h264', seconds=10)
                    stream.clear()
                    # Wait until motion is no longer detected, then split
                    # recording back to the in-memory circular buffer
                    while motion:
                        camera.wait_recording(10)
                        motion = output.check_motion()
                    print('Motion stopped, ending recording!')
                    camera.split_recording(stream)
                    count+=1
                    timestampval = str(datetime.datetime.now())
                    file_name = "capture_%s.mp4" % (timestampval)
                    print('Composing movie')
                    call(["MP4Box",
                          "-cat",
                          "/tmp/before.h264",
                          "-cat",
                          "/tmp/after.h264",
                          "-new",
                          "/tmp/" + file_name])
                    # Need to add a call out here to build a compiled file
                    # MP4Box -cat before1.h264 -cat after1.h264 -new mergedFile.mp4

                    print('Uploading to google drive')
                    file1 = drive.CreateFile({'title': file_name, "parents": [{"kind": "drive#fileLink","id": folder_id}]})
                    #file1.SetContentString('Hello World!') # Set content of the file from given string.
                    file1.SetContentFile("/tmp/" + file_name)
                    file1.Upload()
                    # check again after the upload to avoid a bad collect.
                    motion = output.check_motion()

        finally:
            camera.stop_recording()

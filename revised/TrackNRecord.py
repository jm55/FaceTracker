'''
Face Tracking by Shubham Santosh (https://create.arduino.cc/projecthub/shubhamsantosh99/face-tracker-using-opencv-and-arduino-55412e)
AV Recording by JRodrigoF (https://github.com/JRodrigoF/AVrecordeR)
'''

#Tracking Libraries
import cv2
import serial #PLEASE UNCOMMENT THIS
import time

#Recording Libraries
import AVrecordeR
import subprocess

import math

def GetCamera():
    ctr = 0
    cams = []
    while True:
        cam = cv2.VideoCapture(ctr)
        try:
            if cam.getBackendName() == "MSMF":
                cams.append(ctr)
        except:
            break
        cam.release()
        ctr+=1
    return input("Enter cams (0 - " + str(ctr) + "): ")

print("Setting variables...")
print("Loading classifier...")
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
print("Loading camera...")



camera = 0 #SET CAMERA ACCORDINGLY
cap = cv2.VideoCapture(camera,cv2.CAP_DSHOW)
print("Setting output file...")
filename = time.ctime(time.time()).replace(':','').replace(' ','-')
audio_thread = None
video_out = None
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
fps = 15.0 #DON'T MODIFY
video_out = cv2.VideoWriter('temp_video'+'.avi',fourcc,fps,(640,480))
print("Setting timestamp...")
start_time = end_time = elapsed_time = recorded_fps = 0

def TrackNRecord():
    print("Output file to be saved as: " + filename + ".avi")
    #Arduino Connection
    print("Connecting to Arduino...")
    #ArduinoSerial=serial.Serial('com3',9600,timeout=0.1) #PLEASE UNCOMMENT THIS
    #UNCOMMENT THIS AREA
    #if ArduinoSerial.isOpen():
    #    print("Arduino Connected!\nStarting Recording...")
    #else:
    #    print("Arduino Not Connected!\nExiting...")
    #    exit(404)
    time.sleep(1)
    start_time = time.time()
    AVrecordeR.ready_audio_recording()
    AVrecordeR.audio_thread.start()
    framecount = 0
    while cap.isOpened():
        ret, frame = cap.read()
        frame = cv2.flip(frame,1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1,6)
        track = ""
        for x,y,w,h in faces:
            track = 'X{0:d}Y{1:d}'.format((x+w//2),(y+h//2))
            #ArduinoSerial.write(track.encode('utf-8')) #PLEASE UNCOMMENT THIS
            #Center of Face
            #cv2.circle(frame,(x+w//2,y+h//2),2,(0,255,0),2)
            #ROI
            #cv2.rectangle(frame,(x,y),(x+w,y+h),(0,0,255),3)
        #Squared Region
        #cv2.rectangle(frame,(640//2-30,480//2-30),(640//2+30,480//2+30),(255,255,255),3)

        #Text data on frame
        #Just comment out what you need and don't need
        #Reference: https://stackoverflow.com/a/34273603
        recorded_time = time.time()-start_time
        framecount = framecount + 1
        fps = round(framecount/recorded_time,2)
        cv2.putText(frame, 'Frame Count: ' + str(framecount) + " (" + str(fps) + "fps)", org=(20,380), fontFace=0, fontScale=0.6, color=(255,255,255), thickness=2) #Frame Count
        cv2.putText(frame, 'Arduino Track: ' + track, org=(20,420), fontFace=0, fontScale=0.6, color=(255,255,255), thickness=2) #Arduino Tracking Data
        cv2.putText(frame, 'Recorded Time: ' + time.strftime('%H:%M:%S', time.gmtime(recorded_time)), org=(20,440), fontFace=0, fontScale=0.6, color=(255,255,255), thickness=2) #Recorded Time
        cv2.putText(frame, time.ctime(time.time()), org=(20,460), fontFace=0, fontScale=0.6, color=(255,255,255), thickness=2) #Time Data
        if len(faces) == 0:
            cv2.putText(frame, 'Face Count: No Face Detected',org=(20,400), fontFace=0, fontScale=0.6,color=(255,255,255),thickness=2) #No Face Alert
        else:
            cv2.putText(frame, 'Face Count: ' + str(len(faces)), org=(20,400), fontFace=0, fontScale=0.6, color=(255,255,255), thickness=2) #Face Tracking Data
        #Camera Window
        window_title = "Face Tracker"
        cv2.imshow(window_title, frame)

        #Write output as video or image
        video_out.write(frame) #Video

        #Exit
        if cv2.waitKey(10)&0xFF== ord('q'):
            AVrecordeR.audio_thread.stop()
            audio_frames = len(AVrecordeR.audio_thread.audio_frames)
            cap.release()
            cv2.destroyAllWindows()
            while AVrecordeR.threading.active_count() > 1:
                time.sleep(1)
            end_time = time.time()
            elapsed_time = end_time - start_time
            recorded_fps = math.ceil(framecount / elapsed_time)
            break
    
    #Muxing
    #Timing offsets, int only. Negative to delay, positive to advance
    audio_offset = '0.0'
    video_offset = '0.0'
    start_trim = '00:00:00' #Don't Modify
    cmd = ''
    if abs(recorded_fps - 15) >= 0.01:
        print('FPS mismatch')
        reencode = 'ffmpeg -r ' + str(recorded_fps) + ' -i temp_video.avi -b:v 6M -q:v 2  -pix_fmt yuv420p -r 15 -y temp_video2.avi' #Re-encoding
        mux = "ffmpeg -ac 2 -channel_layout mono -i temp_audio.wav -i temp_video2.avi -b:v 6M -q:v 2  -pix_fmt yuv420p " + filename + ".avi" #Muxing
        subprocess.call(reencode, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(mux, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print('FPS match')
        cmd = "ffmpeg -ac 2 -channel_layout mono -itsoffset " + audio_offset + " -i temp_audio.wav -itsoffset " + video_offset + " -i temp_video.avi -ss " + start_trim + " -b:v 6M -q:v 2 -pix_fmt yuv420p -filter:v fps=15 " + filename + ".avi"
        subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return filename + ".avi"
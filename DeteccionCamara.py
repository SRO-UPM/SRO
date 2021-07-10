from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import numpy as np
import RPi.GPIO as IO
import paho.mqtt.client as paho


ACCESS_TOKEN='8snQi0MBHuG3tg6yTtbi'
broker="demo.thingsboard.io"
port=1883

IO.setmode(IO.BOARD)
IO.setup(32, IO.OUT)  # LED Amarilla

contorno=0


def on_publish(client,userdata,result):
   print("data published to thingsboard \n")
   pass
client1= paho.Client("control1")
client1.on_publish = on_publish
client1.username_pw_set(ACCESS_TOKEN)
client1.connect(broker,port,keepalive=60)
 
     
# initialize the camera and grab a reference to the raw camera capture 
camera = PiCamera()
#camera.resolution = (640, 480)
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(640, 480))
# allow the camera to warmup
time.sleep(0.1)
IO.output(32, True)
# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
          image = frame.array
          gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
          hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
          
          #lower_yellow = np.array([22,60,200])
          #upper_yellow = np.array([60,255,255]) amarillo
        
          #lower_yellow = np.array([110,50,50]) azul
          #upper_yellow = np.array([130,255,255])

          #lower_yellow = np.array([136,87,111]) 
          #upper_yellow = np.array([180,255,255]) #rojo
        
          lower_yellow= np.array([25,52,200]) #verde
          upper_yellow = np.array([102,255,255])
          
          mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
          res = cv2.bitwise_and(image,image, mask= mask)
        
          contours, hierarchy = cv2.findContours(mask,
                                           cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)[-2:]
          for pic, contour in enumerate(contours):
            
                 area = cv2.contourArea(contour)
                 contorno=0
                 if(area > 200):
                     contorno= contorno +1
                     x, y, w, h = cv2.boundingRect(contour)
                     image = cv2.rectangle(image, (x, y), 
                                       (x + w, y + h),
                                       (0, 255, 0), 2)
              
                     cv2.putText(image, "Green Colour", (x, y),
                             cv2.FONT_HERSHEY_SIMPLEX, 
                             1.0, (0, 255, 0))
                     
                  
          cv2.imshow("Frame", image)
          cv2.imshow('mask',mask)
          cv2.imshow('res',res)
          
          key = cv2.waitKey(1) & 0xFF
	  # clear the stream in preparation for the next frame
          rawCapture.truncate(0)
	  # if the `q` key was pressed, break from the loop
          if key == ord("q"):
               IO.output(32, False)
               break
   
          payload="{"
          payload+="\"Contorno\": %s"%contorno;
          payload+="}"
    
          ret= client1.publish("v1/devices/me/telemetry",payload)
    
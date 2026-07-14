#!/usr/bin/env python3
import cv2
import numpy as np
import glob
import os
import time
import subprocess
import signal
import sys
import datetime

# v1.02

# check for RAW files
Home_Files  = []
Home_Files.append(os.getlogin())
files = glob.glob('/home/' + Home_Files[0] + '/Pictures/*.raw')
valid = 0
if len(files) > 1:
    # load an image
    f = open(files[1],'rb')
    image = np.fromfile(f,dtype=np.uint16,count=-1)
    f.close()
    # check size
    if image.size == 12354560: #PiHQ 4056x3040 Pi5 or Pi4
        cols = 4064
        rows = 3040
        valid = 1
    elif image.size == 1601536: #PiGS 1456x1088 Pi5 or Pi4
        cols = 1472
        rows = 1088
        valid = 1
    else:
        valid = 0
        print("Failed to find suitable file ",image.size)
   
    # process if a valid size
    if valid > 0:
        C  = image.reshape(int(rows/2),int(cols*2))
        D  = np.split(C, 2, axis=1)
        # blue
        E  = D[0].reshape(int(image.size/2),1)
        F = E[0::2]
        Blue  = F.reshape(int(rows/2),int(cols/2))
        # green1
        #E  = D[0].reshape(int(image.size/2),1)
        #F = E[1::2]
        #g1  = F.reshape(int(rows/2),int(cols/2))
        # green0
        E  = D[1].reshape(int(image.size/2),1)
        F = E[0::2]
        Green  = F.reshape(int(rows/2),int(cols/2))
        # red
        E  = D[1].reshape(int(image.size/2),1)
        F = E[1::2]
        Red  = F.reshape(int(rows/2),int(cols/2))

        # combine B,G,R
        BGR=np.dstack((Blue,Green,Red)).astype(np.uint16)
        res = cv2.resize(BGR, dsize=(cols,rows), interpolation=cv2.INTER_CUBIC)
        res = res.astype(np.uint16)
                 
        # show R,G and B
        R2 = cv2.resize(Red, dsize=(640,480), interpolation=cv2.INTER_CUBIC)
        B2 = cv2.resize(Blue, dsize=(640,480), interpolation=cv2.INTER_CUBIC)
        G2 = cv2.resize(Green, dsize=(640,480), interpolation=cv2.INTER_CUBIC)
        RGB = cv2.resize(res, dsize=(640,480), interpolation=cv2.INTER_CUBIC)
        cv2.imshow('RED',R2)
        cv2.imshow('BLUE',B2)
        cv2.imshow('GREEN',G2)
        cv2.imshow('RGB', RGB)
            
        # save outputs as TIFs
        now = datetime.datetime.now()
        timestamp = now.strftime("%y%m%d%H%M%S")
        cv2.imwrite("RED_" + timestamp + ".tif", Red)
        cv2.imwrite("BLUE_" + timestamp + ".tif", Blue)
        cv2.imwrite("GREEN_" + timestamp + ".tif", Green)
            
        # show RGB result
        result = cv2.resize(res, dsize=(640,480), interpolation=cv2.INTER_CUBIC)
        cv2.imshow('Output',result)
        time.sleep(10)
        cv2.destroyAllWindows()
        sys.exit()

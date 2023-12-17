#!/usr/bin/env python3

"""Copyright (c) 2023
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

import time
import pygame
from pygame.locals import *
import os, sys
import datetime
import subprocess
import signal
import cv2
import glob
from datetime import timedelta
import numpy as np
import math
from gpiozero import Button
import random

version = 4.73

# Set displayed preview image size (must be less than screen size to allow for the menu!!)
# Recommended 640x480 (Pi 7" or other 800x480 screen), 720x540 (FOR SQUARE HYPERPIXEL DISPLAY),
# 800x600, 1280x960 or 1440x1080
# For a FULL HD screen (1920x1080) and FULLSCREEN ON set preview_width = 1440, preview_height = 1080
preview_width  = 800 
preview_height = 600
fullscreen     = 0   # set to 1 for FULLSCREEN
frame          = 1   # set to 0 for NO frame (i.e. if using Pi 7" touchscreen)
FUP            = 21  # Pi v3 camera Focus UP GPIO button
FDN            = 16  # Pi v3 camera Focus DN GPIO button

# if using Arducams version of libcamera set use_ard == 1
use_ard = 0

# set sq_dis = 1 for a square display, 0 for normal
sq_dis = 0

# set default values (see limits below)
rotate      = 0       # rotate preview ONLY, 0 = none, 1 = 90, 2 = 180, 3 = 270
camera      = 0       # choose camera to use, usually 0 unless using a Pi5 or multiswitcher
stream_port = 5000    # set video streaming port number
mode        = 1       # set camera mode ['manual','normal','sport'] 
speed       = 16      # position in shutters list (16 = 1/125th)
gain        = 0       # set gain 
brightness  = 0       # set camera brightness
contrast    = 70      # set camera contrast 
ev          = 0       # eV correction 
blue        = 12      # blue balance 
red         = 15      # red balance 
extn        = 0       # still file type  (0 = jpg)
vlen        = 10      # video length in seconds
fps         = 25      # video fps
vformat     = 10      # set video format (10 = 1920x1080)
codec       = 0       # set video codec  (0 = h264)
tinterval   = 60      # time between timelapse shots in seconds
tshots      = 10      # number of timelapse shots
saturation  = 10      # picture colour saturation
meter       = 2       # metering mode (2 = average)
awb         = 1       # auto white balance mode, off, auto etc (1 = auto)
sharpness   = 15      # set sharpness level
denoise     = 1       # set denoise level
quality     = 93      # set quality level
profile     = 0       # set h264 profile
level       = 0       # set h264 level
histogram   = 0       # OFF = 0
histarea    = 50      # set histogram size
v3_f_mode   = 0       # v3 focus mode
v3_f_range  = 0       # v3 focus range
v3_f_speed  = 0       # v3 focus speed
# NOTE if you change any of the above defaults you need to delete the con_file and restart.

# default directories and files
pic         = "Pictures"
vid         = "Videos"
con_file    = "PiLCConfig12.txt"

# setup directories
Home_Files  = []
Home_Files.append(os.getlogin())
pic_dir     = "/home/" + Home_Files[0]+ "/" + pic + "/"
vid_dir     = "/home/" + Home_Files[0]+ "/" + vid + "/"
config_file = "/home/" + Home_Files[0]+ "/" + con_file

# Camera max exposure (Note v1 is currently 1 second not the raspistill 6 seconds)
# whatever value set it MUST be in shutters list !!
max_v1      = 1
max_v2      = 11
max_v3      = 112
max_hq      = 650
max_16mp    = 200
max_64mp    = 435
max_gs      = 15

# inital parameters
focus       = 2000
foc_man     = 0
fcount      = 0
fstep       = 20
max_fcount  = 30
old_foc     = 0
ran         = 0
prev_fps    = 10 
focus_fps   = 25 
focus_mode  = 0
v3_focus    = 480
v3_hdr      = 0
vpreview    = 1
scientific  = 0
scientif    = 0
zx          = int(preview_width/2)
zy          = int(preview_height/2)
fxz         = 1
zoom        = 0
igw         = 2592
igh         = 1944
zwidth      = igw 
zheight     = igh
buttonFUP   = Button(FUP)
buttonFDN   = Button(FDN)
if tinterval > 0:
    tduration  = tshots * tinterval
else:
    tduration = 5
if sq_dis == 1:
    dis_height = preview_width
else:
    dis_height = preview_height

# set button sizes
bw = int(preview_width/8)
bh = int(preview_height/16)
ft = int(preview_width/55)
fv = int(preview_width/55)

# data
cameras      = ['Unknown','Pi v1','Pi v2','Pi v3','Pi HQ','Arducam 16MP','Arducam 64MP','Pi GS']
camids       = ['','ov5647','imx219','imx708','imx477','imx519','arduc','imx296']
max_gains    = [64,     255,      40,      64,      88,      64,      64,      64]
max_shutters = [0,   max_v1, max_v2,   max_v3,  max_hq,max_16mp,max_64mp,  max_gs]
mags         = [64,     255,      40,      64,      88,      64,      64,      64]
modes        = ['manual','normal','sport']
extns        = ['jpg','png','bmp','rgb','yuv420','raw']
extns2       = ['jpg','png','bmp','data','data','dng']
vwidths      = [640,720,800,1280,1280,1296,1332,1456,1536,1640,1920,2028,2028,2304,2592,3280,3840,4032,4056,4608,4656,9152]
vheights     = [480,540,600, 720, 960, 972, 990,1088, 864,1232,1080,1080,1520,1296,1944,2464,2160,3024,3040,2592,3496,6944]
v_max_fps    = [200,120, 40,  40,  40,  30,  30,  30,  30,  30,  30,  40,  40,  25,  20,  20,  20,  20,  10,  20,  20,  20]
v3_max_fps   = [200,120,125,  66,  50,  46,  30,  30,  47,  30,  30,  30,  25,  25,  20,  20,  20,  20,  20,  15,  20,  20]
zwidths      = [640,800,1280,2592,3280,4056,4656,9152]
zheights     = [480,600, 960,1944,2464,3040,3496,6944]
zws          = [864,1080,1728,2592,1093,1367,2187,3280,1536,1920,3072,4608,1352,1690,2704,4056,1552,1940,3104,4656,3050,3813,6101,9152]
zhs          = [648, 810,1296,1944, 821,1027,1643,2464, 864,1080,1728,2592,1013,1267,2027,3040,1165,1457,2331,3496,2288,2860,4576,6944]
shutters     = [-4000,-2000,-1600,-1250,-1000,-800,-640,-500,-400,-320,-288,-250,-240,-200,-160,-144,-125,-120,-100,-96,-80,-60,-50,-48,-40,-30,-25,-20,-15,-13,-10,-8,-6,-5,-4,-3,
                0.4,0.5,0.6,0.8,1,1.1,1.2,2,3,4,5,6,7,8,9,10,11,15,20,25,30,40,50,60,75,100,112,120,150,200,220,230,239,435,500,600,650,660,670]
codecs       = ['h264','mjpeg','yuv420','raw']
codecs2      = ['h264','mjpeg','data','raw']
h264profiles = ['baseline 4','baseline 4.1','baseline 4.2','main 4','main 4.1','main 4.2','high 4','high 4.1','high 4.2']
meters       = ['centre','spot','average']
awbs         = ['off','auto','incandescent','tungsten','fluorescent','indoor','daylight','cloudy']
denoises     = ['off','cdn_off','cdn_fast','cdn_hq']
v3_f_modes   = ['auto','manual','continuous']
v3_f_ranges  = ['normal','macro','full']
v3_f_speeds  = ['normal','fast']
histograms   = ["OFF","Red","Green","Blue","Lum","ALL"]
still_limits = ['mode',0,len(modes)-1,'speed',0,len(shutters)-1,'gain',0,30,'brightness',-100,100,'contrast',0,200,'ev',-10,10,'blue',1,80,'sharpness',0,30,
                'denoise',0,len(denoises)-1,'quality',0,100,'red',1,80,'extn',0,len(extns)-1,'saturation',0,20,'meter',0,len(meters)-1,'awb',0,len(awbs)-1,
                'histogram',0,len(histograms)-1,'v3_f_speed',0,len(v3_f_speeds)-1]
video_limits = ['vlen',0,3600,'fps',1,40,'focus',0,4096,'vformat',0,7,'0',0,0,'zoom',0,5,'Focus',0,1,'tduration',1,9999,'tinterval',0,999,'tshots',1,999,
                'flicker',0,3,'codec',0,len(codecs)-1,'profile',0,len(h264profiles)-1,'v3_focus',0,1023,'histarea',10,50,'v3_f_range',0,len(v3_f_ranges)-1]

# check config_file exists, if not then write default values
if not os.path.exists(config_file):
    points = [mode,speed,gain,brightness,contrast,frame,red,blue,ev,vlen,fps,vformat,codec,tinterval,tshots,extn,zx,zy,zoom,saturation,
              meter,awb,sharpness,denoise,quality,profile,level,histogram,histarea,v3_f_speed,v3_f_range,rotate]
    with open(config_file, 'w') as f:
        for item in points:
            f.write("%s\n" % item)

# read config_file
config = []
with open(config_file, "r") as file:
   line = file.readline()
   while line:
      config.append(line.strip())
      line = file.readline()
config = list(map(int,config))

mode        = config[0]
speed       = config[1]
gain        = config[2]
brightness  = config[3]
contrast    = config[4]
red         = config[6]
blue        = config[7]
ev          = config[8]
vlen        = config[9]
fps         = config[10]
vformat     = config[11]
codec       = config[12]
tinterval   = config[13]
tshots      = config[14]
extn        = config[15]
zx          = config[16]
zy          = config[17]
zoom        = 0
saturation  = config[19]
meter       = config[20]
awb         = config[21]
sharpness   = config[22]
denoise     = config[23]
quality     = config[24]
profile     = config[25]
level       = config[26]
histogram   = config[27]
histarea    = config[28]
v3_f_speed  = config[29]
v3_f_range  = config[30]
#rotate      = config[31]

#check Pi model.
Pi = 0
if os.path.exists ('/run/shm/md.txt'): 
    os.remove("/run/shm/md.txt")
os.system("cat /proc/cpuinfo >> /run/shm/md.txt")
with open("/run/shm/md.txt", "r") as file:
        line = file.readline()
        while line:
           line = file.readline()
           if line[0:5] == "Model":
               model = line
mod = model.split(" ")
if mod[3] == "5":
    Pi = 5
    
def Camera_Version():
  # Check for Pi Camera version
  global mode,mag,max_gain,max_shutter,Pi_Cam,max_camera,same_cams,cam0,cam1,cam2,cam3,max_gains,max_shutters,scientif,max_vformat,vformat,vwidth,vheight,vfps,sspeed,tduration,video_limits,speed,shutter,max_vf_7,max_vf_6,max_vf_5,max_vf_4,max_vf_3,max_vf_2,max_vf_1,max_vf_4a,max_vf_0
  # DETERMINE NUMBER OF CAMERAS (FOR ARDUCAM MULITPLEXER or Pi5)
  if os.path.exists('libcams.txt'):
   os.rename('libcams.txt', 'oldlibcams.txt')
  os.system("rpicam-vid --list-cameras >> libcams.txt")
  time.sleep(0.5)
  # read libcams.txt file
  camstxt = []
  with open("libcams.txt", "r") as file:
    line = file.readline()
    while line:
        camstxt.append(line.strip())
        line = file.readline()
  max_camera = 0
  same_cams  = 0
  cam0 = "0"
  cam1 = "1"
  cam2 = "2"
  cam3 = "3"
  for x in range(0,len(camstxt)):
    # Determine camera models
    if camstxt[x][0:4] == "0 : ":
        cam0 = camstxt[x][4:10]
    elif camstxt[x][0:4] == "1 : ":
        cam1 = camstxt[x][4:10]
    elif camstxt[x][0:4] == "2 : ":
        cam2 = camstxt[x][4:10]
    elif camstxt[x][0:4] == "3 : ":
        cam3 = camstxt[x][4:10]
    # Determine MAXIMUM number of cameras available 
    if camstxt[x][0:4] == "3 : " and max_camera < 3:
        max_camera = 3
    elif camstxt[x][0:4] == "2 : " and max_camera < 2:
        max_camera = 2
    elif camstxt[x][0:4] == "1 : " and max_camera < 1:
        max_camera = 1
    pic = 0
    Pi_Cam = -1
    for x in range(0,len(camids)):
        if camera == 0:
            if cam0 == camids[x]:
                Pi_Cam = x
                pic = 1
        elif camera == 1:
            if cam1 == camids[x]:
                Pi_Cam = x
                pic = 1
        elif camera == 2:
            if cam2 == camids[x]:
                Pi_Cam = x
                pic = 1
        elif camera == 3:
            if cam3 == camids[x]:
                Pi_Cam = x
                pic = 1
        if pic == 1:
            max_shutter = max_shutters[Pi_Cam]
            max_gain = max_gains[Pi_Cam]
            mag = int(max_gain/4)
            still_limits[8] = max_gain
            
  pygame.display.set_caption('RPiGUI - v' + str(version) + "  " + cameras[Pi_Cam] + " Camera" )
    
  if max_camera == 1 and cam0 == cam1:
    same_cams = 1
        

  if Pi_Cam == 5 or Pi_Cam == 6:
    # read /boot/config.txt file
    configtxt = []
    with open("/boot/config.txt", "r") as file:
        line = file.readline()
        while line:
            configtxt.append(line.strip())
            line = file.readline()
            
  # max video formats (not for h264)
  max_vf_7  = 7
  max_vf_6  = 20
  max_vf_5  = 14
  max_vf_4  = 18
  max_vf_3  = 19
  max_vf_2  = 15
  max_vf_1  = 14
  max_vf_4a = 12
  max_vf_0  = 10 # default if using h264

  if codec > 0 and (Pi_Cam == 5 or Pi_Cam == 6) and ("dtoverlay=vc4-kms-v3d,cma-512" in configtxt): # Arducam IMX519 16MP or 64MP
    max_vformat = max_vf_6
  elif codec > 0 and (Pi_Cam == 5 or Pi_Cam == 6): # Arducam IMX519 16MP or 64MP
    max_vformat = max_vf_5
  elif Pi_Cam == 7:               # Pi GS
    max_vformat = max_vf_7
  elif codec > 0 and Pi_Cam == 4: # Pi HQ
    max_vformat = max_vf_4
  elif codec > 0 and Pi_Cam == 3: # Pi V3
    max_vformat = max_vf_3
  elif codec > 0 and Pi_Cam == 2: # Pi V2
    max_vformat = max_vf_2
  elif codec > 0 and Pi_Cam == 1: # Pi V1
    max_vformat = max_vf_1
  elif Pi_Cam == 4:               # Pi HQ
    max_vformat = max_vf_4a
    if (os.path.exists('/usr/share/libcamera/ipa/rpi/vc4/imx477_scientific.json') or os.path.exists('/usr/share/libcamera/ipa/rpi/pisp/imx477_scientific.json')) and Pi_Cam == 4:
        scientif = 1
    else:
        scientif = 0
  else:
    max_vformat = max_vf_0
  if vformat > max_vformat:
    vformat = max_vformat
  vwidth    = vwidths[vformat]
  vheight   = vheights[vformat]
  vfps      = v_max_fps[vformat]

  video_limits[5] = vfps
  if tinterval > 0:
    tduration = tinterval * tshots
  else:
    tduration = 5

  shutter = shutters[speed]
  if shutter < 0:
    shutter = abs(1/shutter)
  sspeed = int(shutter * 1000000)
  if (shutter * 1000000) - int(shutter * 1000000) > 0.5:
    sspeed +=1
  # determine max speed for camera
  max_speed = 0
  while max_shutter > shutters[max_speed]:
    max_speed +=1
  if speed > max_speed:
    speed = max_speed
    shutter = shutters[speed]
    if shutter < 0:
        shutter = abs(1/shutter)
    sspeed = int(shutter * 1000000)
    if mode == 0:
        if shutters[speed] < 0:
            text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
        else:
            text(0,2,3,1,1,str(shutters[speed]),fv,10)
    else:
        if shutters[speed] < 0:
            text(0,2,0,1,1,"1/" + str(abs(shutters[speed])),fv,10)
        else:
            text(0,2,0,1,1,str(shutters[speed]),fv,10)
  if mode == 0:
    draw_bar(0,2,lgrnColor,'speed',speed)

Camera_Version()

pygame.init()
if frame == 1:
    if sq_dis == 0 and fullscreen == 1:
        windowSurfaceObj = pygame.display.set_mode((preview_width + (bw*2),dis_height),  pygame.FULLSCREEN, 24)
    elif sq_dis == 0 and fullscreen == 0:
        windowSurfaceObj = pygame.display.set_mode((preview_width + (bw*2),dis_height),  0, 24)
    else:
        windowSurfaceObj = pygame.display.set_mode((preview_width,dis_height), 0, 24)
else:
    if sq_dis == 0:
        windowSurfaceObj = pygame.display.set_mode((preview_width + (bw*2),dis_height), pygame.NOFRAME, 24)
    else:
        windowSurfaceObj = pygame.display.set_mode((preview_width,dis_height), pygame.NOFRAME, 24)
pygame.display.set_caption('RPiGUI - v' + str(version) + "  " + cameras[Pi_Cam] + " Camera" )

global greyColor, redColor, greenColor, blueColor, dgryColor, lgrnColor, blackColor, whiteColor, purpleColor, yellowColor,lpurColor,lyelColor
bredColor =   pygame.Color(255,   0,   0)
lgrnColor =   pygame.Color(162, 192, 162)
lpurColor =   pygame.Color(192, 162, 192)
lyelColor =   pygame.Color(192, 192, 162)
blackColor =  pygame.Color(  0,   0,   0)
whiteColor =  pygame.Color(200, 200, 200)
greyColor =   pygame.Color(128, 128, 128)
dgryColor =   pygame.Color( 64,  64,  64)
greenColor =  pygame.Color(  0, 255,   0)
purpleColor = pygame.Color(255,   0, 255)
yellowColor = pygame.Color(255, 255,   0)
blueColor =   pygame.Color(  0,   0, 255)
redColor =    pygame.Color(200,   0,   0)

def button(col,row, bkgnd_Color,border_Color):
    global preview_width,bw,bh,sq_dis
    colors = [greyColor, dgryColor,yellowColor,purpleColor,greenColor,whiteColor,lgrnColor,lpurColor,lyelColor,blueColor]
    Color = colors[bkgnd_Color]
    if sq_dis == 0:
        bx = preview_width + (col * bw)
        by = row * bh
    else:
        if col == 0:
            if row < 6:
                bx = row * bw
                by = preview_height
            else:
                bx = (row - 6) * bw
                by = preview_height + bh
        elif row < 7:
            bx = row * bw
            by = preview_height + (bh*2)
        else:
            bx = (row - 7) * bw
            by = preview_height + (bh*3)
    pygame.draw.rect(windowSurfaceObj,Color,Rect(bx,by,bw-1,bh))
    pygame.draw.line(windowSurfaceObj,colors[border_Color],(bx,by),(bx+bw,by))
    pygame.draw.line(windowSurfaceObj,greyColor,(bx+bw-1,by),(bx+bw-1,by+bh))
    pygame.draw.line(windowSurfaceObj,colors[border_Color],(bx,by),(bx,by+bh-1))
    pygame.draw.line(windowSurfaceObj,dgryColor,(bx,by+bh-1),(bx+bw-1,by+bh-1))
    pygame.display.update(bx, by, bw, bh)
    return

def text(col,row,fColor,top,upd,msg,fsize,bkgnd_Color):
    global bh,preview_width,fv,tduration
    colors =  [dgryColor, greenColor, yellowColor, redColor, purpleColor, blueColor, whiteColor, greyColor, blackColor, purpleColor,lgrnColor,lpurColor,lyelColor]
    Color  =  colors[fColor]
    bColor =  colors[bkgnd_Color]
    if sq_dis == 0:
        bx = preview_width + (col * bw)
        by = row * bh
    else:
        if col == 0:
            if row < 6:
                bx = row * bw
                by = preview_height
            else:
                bx = (row - 6) * bw
                by = preview_height + bh
        elif row < 7:
            bx = row * bw
            by = preview_height + (bh*2)
        else:
            bx = (row - 7) * bw
            by = preview_height + (bh*3)
    if os.path.exists ('/usr/share/fonts/truetype/freefont/FreeSerif.ttf'): 
        fontObj = pygame.font.Font('/usr/share/fonts/truetype/freefont/FreeSerif.ttf', int(fsize))
    else:
        fontObj = pygame.font.Font(None, int(fsize))
    msgSurfaceObj = fontObj.render(msg, False, Color)
    msgRectobj = msgSurfaceObj.get_rect()
    if top == 0:
        pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+1,by+int(bh/3),bw-2,int(bh/3)))
        msgRectobj.topleft = (bx + 5, by + int(bh/3)-int(preview_width/640))
    elif msg == "Config":
        pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+1,by+int(bh/1.5),int(bw/2),int(bh/3)-1))
        msgRectobj.topleft = (bx+5,  by + int(bh/1.5)-1)
    elif top == 1:
        pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+20,by+int(bh/1.5)-1,int(bw-21),int(bh/3)))
        msgRectobj.topleft = (bx + 20, by + int(bh/1.5)-int(preview_width/640)-1) 
    elif top == 2:
        if bkgnd_Color == 1:
            pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,row * fsize,preview_width,fv*2))
        msgRectobj.topleft = (0,row * fsize)
    windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
    if upd == 1 and top == 2:
        pygame.display.update(0,0,preview_width,fv*2)
    if upd == 1:
        pygame.display.update(bx, by, bw, bh)

def draw_bar(col,row,color,msg,value):
    global bw,bh,preview_width,still_limits,max_speed,v3_mag
    for f in range(0,len(still_limits)-1,3):
        if still_limits[f] == msg:
            pmin = still_limits[f+1]
            pmax = still_limits[f+2]
    if msg == "speed":
        pmax = max_speed
    if sq_dis == 0:
        pygame.draw.rect(windowSurfaceObj,color,Rect(preview_width + col*bw,row * bh,bw-1,int(bh/3)))
    else:
        if row < 6:
            pygame.draw.rect(windowSurfaceObj,color,Rect(row*bw,preview_height ,bw-1,int(bh/3)))
        else:
            pygame.draw.rect(windowSurfaceObj,color,Rect((row-6)*bw,preview_height + bh,bw-1,int(bh/3)))
    if pmin > -1: 
        j = value / (pmax - pmin)  * bw
        jag = mag / (pmax - pmin) * bw
    else:
        j = int(bw/2) + (value / (pmax - pmin)  * bw)
    j = min(j,bw-5)
    if sq_dis == 0:
        
        pygame.draw.rect(windowSurfaceObj,(0,200,0),Rect(int(preview_width + int(col*bw) + 2),int(row * bh),int(j+1),int(bh/3)))
        if msg == "gain" and value > mag:
           pygame.draw.rect(windowSurfaceObj,(200,200,0),Rect(int(preview_width + int(col*bw) + 2 + jag),int(row * bh),int(j+1 - jag),int(bh/3)))
        pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width + int(col*bw) + j ),int(row * bh),3,int(bh/3)))
    else:
        if row < 6:
            pygame.draw.rect(windowSurfaceObj,(150,120,150),Rect(int((row*bw) + 2),preview_height ,int(j+1),int(bh/3)))
            pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int((row*bw) + j) ,preview_height ,3,int(bh/3)))
        else:
            pygame.draw.rect(windowSurfaceObj,(150,120,150),Rect(int(((row-6)*bw) + 2),int(preview_height + bh),int(j+1),int(bh/3)))
            pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(((row-6)*bw) + j) ,int(preview_height +  bh),3,int(bh/3)))
    pygame.display.update()

def draw_Vbar(col,row,color,msg,value):
    global bw,bh,preview_width,video_limits
    for f in range(0,len(video_limits)-1,3):
        if video_limits[f] == msg:
            pmin = video_limits[f+1]
            pmax = video_limits[f+2]
    if msg == "vformat":
        pmax = max_vformat
    if sq_dis == 0:
        pygame.draw.rect(windowSurfaceObj,color,Rect(preview_width + col*bw,row * bh,bw-1,int(bh/3)))
    else:
        if row < 7:
            pygame.draw.rect(windowSurfaceObj,color,Rect(row*bw,preview_height + (bh*2),bw-1,int(bh/3)))
        else:
            pygame.draw.rect(windowSurfaceObj,color,Rect((row-7)*bw,preview_height + (bh*3),bw-1,int(bh/3)))
    if pmin > -1: 
        j = value / (pmax - pmin)  * bw
    else:
        j = int(bw/2) + (value / (pmax - pmin)  * bw)
    j = min(j,bw-5)
    if sq_dis == 0:
        pygame.draw.rect(windowSurfaceObj,(150,120,150),Rect(int(preview_width + (col*bw) + 2),int(row * bh),int(j+1),int(bh/3)))
        pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width + (col*bw) + j ),int(row * bh),3,int(bh/3)))
    else:
        if row < 7:
            pygame.draw.rect(windowSurfaceObj,(150,120,150),Rect(int((row*bw) + 2),int(preview_height + (bh*2)),int(j+1),int(bh/3)))
            pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int((row*bw) + j) ,int(preview_height + (bh*2)),3,int(bh/3)))
        else:
            pygame.draw.rect(windowSurfaceObj,(150,120,150),Rect(int(((row-7)*bw) + 2),int(preview_height +  + (bh*3)),int(j+1),int(bh/3)))
            pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(((row-7)*bw) + j) ,int(preview_height +  + (bh*3)),3,int(bh/3)))
    pygame.display.update()

def preview():
    global Pi,scientif,scientific,fxx,fxy,fxz,v3_focus,v3_hdr,v3_f_mode,v3_f_modes,prev_fps,focus_fps,focus_mode,restart,rpistr,count,p, brightness,contrast,modes,mode,red,blue,gain,sspeed,ev,preview_width,preview_height,zoom,igw,igh,zx,zy,awbs,awb,saturations,saturation,meters,meter,flickers,flicker,sharpnesss,sharpness,rotate
    files = glob.glob('/run/shm/*.jpg')
    for f in files:
        os.remove(f)
    speed2 = sspeed
    speed2 = min(speed2,2000000)
    rpistr = "rpicam-vid --camera " + str(camera) + " -n --codec mjpeg -t 0 --segment 1"
    if (Pi_Cam == 5 or Pi_Cam == 6) and (focus_mode == 1 or zoom > 0):
        rpistr += " --width 3280 --height 2464 -o /run/shm/test%d.jpg "
    elif Pi_Cam == 7 :
        rpistr += " --width 1456 --height 1088 -o /run/shm/test%d.jpg "
    elif Pi_Cam == 3 :
        rpistr += " --width 2304 --height 1296 -o /run/shm/test%d.jpg "
    elif (Pi_Cam == 5 or Pi_Cam == 6) or focus_mode == 1 :
        rpistr += " --width 1920 --height 1440 -o /run/shm/test%d.jpg "
    else:
        if preview_width == 600 and preview_height == 480:
            rpistr += " --width 720 --height 540 -o /run/shm/test%d.jpg "
        else:
            rpistr += " --width 1920 --height 1440 -o /run/shm/test%d.jpg "
    rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
    if mode == 0:
        rpistr += " --shutter " + str(speed2) 
    else:
        rpistr += " --exposure " + str(modes[mode]) 
    if zoom > 4 and (Pi_Cam < 5 or Pi_Cam == 7) and Pi_Cam != 3 and mode != 0:
        rpistr += " --framerate " + str(focus_fps)
    elif (zoom < 5 or Pi_Cam == 3) and mode != 0:
        rpistr += " --framerate " + str(prev_fps)
    elif mode == 0:
        speed3 = 1000000/speed2
        speed3 = min(speed3,25)
        rpistr += " --framerate " + str(speed3)
    if ev != 0:
        rpistr += " --ev " + str(ev)
    if sspeed > 5000000 and mode == 0:
        rpistr += " --gain 1 --awbgains " + str(red/10) + "," + str(blue/10)
    else:
        rpistr += " --gain " + str(gain)
        if awb == 0:
            rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
        else:
            rpistr += " --awb " + awbs[awb]
    rpistr += " --metering "   + meters[meter]
    rpistr += " --saturation " + str(saturation/10)
    rpistr += " --sharpness "  + str(sharpness/10)
    rpistr += " --denoise "    + denoises[denoise]
    rpistr += " --quality " + str(quality)
    if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and use_ard == 1:
        rpistr += " --autofocus "
    if (Pi_Cam == 3 and v3_f_mode > 0 and fxx == 0) or ((Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and use_ard == 0):
        rpistr += " --autofocus-mode " + v3_f_modes[v3_f_mode]
        if v3_f_mode == 1:
            rpistr += " --lens-position " + str(v3_focus/100)
    elif Pi_Cam == 3 and zoom == 0 and fxx != 0 and v3_f_mode != 1:
        rpistr += " --autofocus-window " + str(fxx) + "," + str(fxy) + "," + str(fxz) + "," + str(fxz)
    if Pi_Cam == 3 and v3_f_speed != 0:
        rpistr += " --autofocus-speed " + v3_f_speeds[v3_f_speed]
    if Pi_Cam == 3 and v3_f_range != 0:
        rpistr += " --autofocus-range " + v3_f_ranges[v3_f_range]
    if Pi_Cam == 3 and v3_hdr == 1:
        rpistr += " --hdr"
    if Pi_Cam == 4 and scientific == 1:
        if os.path.exists('/usr/share/libcamera/ipa/rpi/vc4/imx477_scientific.json'):
            rpistr += " --tuning-file /usr/share/libcamera/ipa/rpi/vc4/imx477_scientific.json"
        if os.path.exists('/usr/share/libcamera/ipa/rpi/pisp/imx477_scientific.json'):
            rpistr += " --tuning-file /usr/share/libcamera/ipa/rpi/pisp/imx477_scientific.json"
    if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 1 and Pi == 5:
        if os.path.exists('/usr/share/libcamera/ipa/rpi/pisp/imx519mf.json'):
            rpistr += " --tuning-file /usr/share/libcamera/ipa/rpi/pisp/imx519mf.json"
    if zoom > 1 and zoom < 5:
        zxo = ((1920-zwidths[4 - zoom])/2)/1920
        zyo = ((1440-zheights[4 - zoom])/2)/1440
        rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(zwidths[4 - zoom]/1920) + "," + str(zheights[4 - zoom]/1440)
    if zoom == 5:
        zxo = ((igw/2)-(preview_width/2))/igw
        zyo = ((igh/2)-(preview_height/2))/igh
        rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
    p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
    #print (rpistr)
    restart = 0
    time.sleep(0.2)
    if Pi_Cam == 3 and rotate == 0:
        pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,int(preview_height * .75),preview_width,int(preview_height *.24) ))

def v3_focus_manual():
    global focus_mode,v3_f_mode,foc_man,restart,v3_f_modes,v3_focus,v3_pmin,drgyColor,fv,video_limits,v3_pmax
    focus_mode = 1
    v3_f_mode = 1 # manual focus
    foc_man = 1 
    button(1,7,1,9)
    for f in range(0,len(video_limits)-1,3):
        if video_limits[f] == 'v3_focus':
            v3_pmin = video_limits[f+1]
            v3_pmax = video_limits[f+2]
    restart = 1 
    draw_Vbar(1,7,dgryColor,'v3_focus',v3_focus-v3_pmin)
    text(1,7,3,0,1,'<<< ' + str(int(v3_focus)) + ' >>>',fv,0)
    text(1,7,3,1,1,str(v3_f_modes[v3_f_mode]),fv,0)
    time.sleep(0.25)
        
# draw buttons
for d in range(1,13):
        button(0,d,6,4)
for d in range(1,7):
        button(1,d,7,3)
for d in range(10,13):
        button(1,d,8,2)
button(0,0,0,4)
button(1,0,0,3)
button(1,7,0,2)
button(1,9,0,2)
button(1,13,0,5)
button(1,14,0,5)
button(0,14,0,5)

def Menu():
  global Pi_Cam,scientif,mode,v3_hdr,scientific,tinterval,zoom,vwidth,vheight,preview_width,preview_height,ft,fv,focus,fxz
  if Pi_Cam == 6 and mode == 0:
    text(0,0,1,1,1,"STILL    2x2",ft,7)
  else:
    text(0,0,1,1,1,"Still ",ft,7)
  if Pi_Cam == 6 and mode == 0 and tinterval > 0:
    text(1,9,1,1,1,"T'lapse  2x2",ft,7)
  else:
    text(1,9,1,1,1,"Timelapse",ft,7)
  if (Pi_Cam == 5 or Pi_Cam == 6):
    text(1,7,3,1,1,"auto",fv,7)
    if foc_man == 1:
        text(1,7,3,1,1,"manual",fv,0)
   
  draw_Vbar(1,3,lpurColor,'vformat',vformat)
  if Pi_Cam == 3:
    button(0,15,0,5)
    button(1,15,0,5)
    button(0,13,6,4)
    text(0,15,2,0,1,"Focus Speed",ft,7)
    text(0,15,3,1,1,v3_f_speeds[v3_f_speed],fv,7)
    text(1,15,2,0,1,"Focus Range",ft,7)
    text(1,15,3,1,1,v3_f_ranges[v3_f_range],fv,7)
    text(1,7,3,1,1,str(v3_f_modes[v3_f_mode]),fv,7)
    text(0,13,5,0,1,"HDR",fv,10)
    if v3_hdr == 0:
        text(0,13,3,1,1,"Off",fv,10)
    else:
        text(0,13,3,1,1,"ON ",fv,10)
    if foc_man == 1:
        button(1,7,1,9)
        draw_Vbar(1,7,dgryColor,'v3_focus',v3_focus-pmin)
        text(1,7,3,0,1,'<<< ' + str(int(v3_focus)) + ' >>>',fv,0)
        text(1,7,3,1,1,str(v3_f_modes[v3_f_mode]),fv,0)
    draw_bar(0,15,greyColor,'v3_f_speed',v3_f_speed)
    draw_Vbar(1,15,greyColor,'v3_f_range',v3_f_range)
    if fxz != 1:
        text(1,7,3,1,1,"Spot",fv,7)
    
  else:
    button(0,15,0,5)
    button(1,15,0,5)
    button(0,13,0,5)
    button(1,7,0,9)
    text(1,7,5,0,1,"FOCUS",ft,7)
    if zoom == 0:
      button(1,8,0,9)
      text(1,8,5,0,1,"Zoom",ft,7)
      text(1,8,3,1,1,"",fv,7)
      text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
    elif zoom < 10:
      button(1,8,1,9)
      text(1,8,2,0,1,"ZOOMED",ft,0)
      text(1,8,3,1,1,str(zoom),fv,0)
      text(1,3,3,1,1,str(preview_width) + "x" + str(preview_height),fv,11)
      draw_Vbar(1,8,greyColor,'zoom',zoom)
      
  if Pi_Cam == 4 and scientif == 1:
    button(0,13,6,4)
    text(0,13,5,0,1,"Scientific",fv,10)
    if scientific == 0:
        text(0,13,3,1,1,"Off",fv,10)
    else:
        text(0,13,3,1,1,"ON ",fv,10)
  

    
Menu()

# write button texts
text(0,0,1,0,1,"CAPTURE",ft,7)
text(1,0,1,0,1,"CAPTURE",ft,7)
text(1,0,1,1,1,"Video",ft,7)
text(0,1,5,0,1,"Mode",ft,10)
text(0,1,3,1,1,modes[mode],fv,10)
if mode == 0:
    text(0,2,5,0,1,"Shutter S",ft,10)
    if shutters[speed] < 0:
        text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
    else:
        text(0,2,3,1,1,str(shutters[speed]),fv,10)
else:
    text(0,2,5,0,1,"eV",ft,10)
    text(0,2,3,1,1,str(ev),fv,10)
text(0,3,5,0,1,"Gain    A/D",ft,10)
if gain > 0:
    text(0,3,5,0,1,"Gain    A/D",ft,10)
    if gain <= mag:
        text(0,3,3,1,1,str(gain) + " :  " + str(gain) + "/1",fv,10)
    else:
        text(0,3,3,1,1,str(gain) + " :  " + str(int(mag)) + "/" + str(((gain/mag)*10)/10)[0:3],fv,10)
else:
    text(0,3,5,0,1,"Gain",ft,10)
    text(0,3,3,1,1,"Auto",fv,10)
text(0,4,5,0,1,"Brightness",ft,10)
text(0,4,3,1,1,str(brightness/100)[0:4],fv,10)
text(0,5,5,0,1,"Contrast",ft,10)
text(0,5,3,1,1,str(contrast/100)[0:4],fv,10)
if awb == 0:
    text(0,7,5,0,1,"Blue",ft,10)
    text(0,8,5,0,1,"Red",ft,10)
    text(0,8,3,1,1,str(red/10)[0:3],fv,10)
    text(0,7,3,1,1,str(blue/10)[0:3],fv,10)
else:
    text(0,7,5,0,1,"Denoise",fv,10)
    text(0,7,3,1,1,denoises[denoise],fv,10)
    text(0,8,5,0,1,"Sharpness",fv,10)
    text(0,8,3,1,1,str(sharpness/10),fv,10)
text(0,10,5,0,1,"Quality",ft,10)
text(0,10,3,1,1,str(quality)[0:3],fv,10)
text(0,9,5,0,1,"File Format",ft,10)
text(0,9,3,1,1,extns[extn],fv,10)
button(1,7,0,9)
text(1,7,5,0,1,"FOCUS",ft,7)
if zoom == 0:
    button(1,8,0,9)
    text(1,8,5,0,1,"Zoom",ft,7)
    text(1,8,3,1,1,"",fv,7)
    text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
elif zoom < 10:
    button(1,8,1,9)
    text(1,8,2,0,1,"ZOOMED",ft,0)
    text(1,8,3,1,1,str(zoom),fv,0)
    text(1,3,3,1,1,str(preview_width) + "x" + str(preview_height),fv,11)
text(0,6,5,0,1,"AWB",ft,10)
text(0,6,3,1,1,awbs[awb],fv,10)
text(0,11,5,0,1,"Saturation",fv,10)
text(0,11,3,1,1,str(saturation/10),fv,10)
text(0,12,5,0,1,"Metering",fv,10)
text(0,12,3,1,1,meters[meter],fv,10)
text(1,1,5,0,1,"V_Length",ft,11)
td = timedelta(seconds=vlen)
text(1,1,3,1,1,str(td),fv,11)
text(1,2,5,0,1,"V_FPS",ft,11)
text(1,2,3,1,1,str(fps),fv,11)
text(1,3,5,0,1,"V_Format",ft,11)
text(1,4,5,0,1,"V_Codec",ft,11)
text(1,4,3,1,1,codecs[codec],fv,11)
text(1,5,5,0,1,"h264 Profile",ft,11)
text(1,5,3,1,1,str(h264profiles[profile]),fv,11)
text(1,6,5,0,1,"V_Preview",ft,11)
text(1,6,3,1,1,"ON ",fv,11)
text(1,9,1,0,1,"CAPTURE",ft,7)
td = timedelta(seconds=tduration)
text(1,10,5,0,1,"Duration",ft,12)
text(1,10,3,1,1,str(td),fv,12)
td = timedelta(seconds=tinterval)
text(1,11,5,0,1,"Interval",ft,12)
text(1,11,3,1,1,str(td),fv,12)
text(1,12,5,0,1,"No. of Shots",ft,12)
if tinterval > 0:
    text(1,12,3,1,1,str(tshots),fv,12)
else:
    text(1,12,3,1,1," ",fv,12)
text(1,13,2,0,1,"Save      EXIT",fv,7)
text(1,13,2,1,1,"Config",fv,7)
text(0,14,2,0,1,"Histogram",ft,7)
text(0,14,3,1,1,histograms[histogram],fv,7)
text(1,14,2,0,1,"Hist Area",ft,7)
text(1,14,3,1,1,str(histarea),fv,7)

# draw sliders
draw_bar(0,1,lgrnColor,'mode',mode)
draw_bar(0,3,lgrnColor,'gain',gain)
draw_bar(0,4,lgrnColor,'brightness',brightness)
draw_bar(0,5,lgrnColor,'contrast',contrast)
if mode != 0:
    draw_bar(0,2,lgrnColor,'ev',ev)
if awb == 0:
    draw_bar(0,7,lgrnColor,'blue',blue)
    draw_bar(0,8,lgrnColor,'red',red)
else:
    draw_bar(0,7,lgrnColor,'denoise',denoise)
    draw_bar(0,8,lgrnColor,'sharpness',sharpness)
draw_bar(0,10,lgrnColor,'quality',quality)
draw_bar(0,9,lgrnColor,'extn',extn)
draw_bar(0,6,lgrnColor,'awb',awb)
draw_bar(0,11,lgrnColor,'saturation',saturation)
draw_bar(0,12,lgrnColor,'meter',meter)
if rotate == 0:
    draw_bar(0,14,greyColor,'histogram',histogram)

draw_Vbar(1,1,lpurColor,'vlen',vlen)
draw_Vbar(1,2,lpurColor,'fps',fps)
draw_Vbar(1,3,lpurColor,'vformat',vformat)
draw_Vbar(1,4,lpurColor,'codec',codec)
draw_Vbar(1,5,lpurColor,'profile',profile)
draw_Vbar(1,8,greyColor,'zoom',zoom)
draw_Vbar(1,10,lyelColor,'tduration',tduration)
draw_Vbar(1,11,lyelColor,'tinterval',tinterval)
draw_Vbar(1,12,lyelColor,'tshots',tshots)
if rotate == 0:
    draw_Vbar(1,14,greyColor,'histarea',histarea)

text(0,0,6,2,1,"Please Wait, checking camera",int(fv* 1.7),1)
text(0,0,6,2,1,"Found " + str(cameras[Pi_Cam]),int(fv*1.7),1)
time.sleep(1)
pygame.display.update()

# determine max speed for camera
max_speed = 0
while max_shutter > shutters[max_speed]:
    max_speed +=1
if speed > max_speed:
    speed = max_speed
    shutter = shutters[speed]
    if shutter < 0:
        shutter = abs(1/shutter)
    sspeed = int(shutter * 1000000)
    if mode == 0:
        if shutters[speed] < 0:
            text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
        else:
            text(0,2,3,1,1,str(shutters[speed]),fv,10)
    else:
        if shutters[speed] < 0:
            text(0,2,0,1,1,"1/" + str(abs(shutters[speed])),fv,10)
        else:
            text(0,2,0,1,1,str(shutters[speed]),fv,10)
if mode == 0:
    draw_bar(0,2,lgrnColor,'speed',speed)
pygame.display.update()
time.sleep(.25)

xx = int(preview_width/2)
xy = int(preview_height/2)

fxx = 0
fxy = 0
fxz = 1
fyz = 1
old_histarea = histarea

# start preview
if rotate == 0:
    text(0,0,6,2,1,"Please Wait for preview...",int(fv*1.7),1)
preview()

# determine /dev/v4l-subdevX for Pi v3 and Arducam 16/64MP cameras
foc_sub3 = -1
foc_sub5 = -1
for x in range(0,10):
    if os.path.exists("ctrls.txt"):
        os.remove("ctrls.txt")
    os.system("v4l2-ctl -d /dev/v4l-subdev" + str(x) + " --list-ctrls >> ctrls.txt")
    time.sleep(0.25)
    ctrlstxt = []
    with open("ctrls.txt", "r") as file:
        line = file.readline()
        while line:
            ctrlstxt.append(line.strip())
            line = file.readline()
    for a in range(0,len(ctrlstxt)):
        if ctrlstxt[a][0:51] == "focus_absolute 0x009a090a (int)    : min=0 max=4095":
            foc_sub5 = x
        if ctrlstxt[a][0:51] == "focus_absolute 0x009a090a (int)    : min=0 max=1023":
            foc_sub3 = x

# main loop
while True:
    time.sleep(0.1)
    # focus UP
    if Pi_Cam == 3:
      if buttonFUP.is_pressed:
        if v3_f_mode != 1:
            v3_focus_manual()
        v3_focus += 1
        v3_focus = min(v3_focus,v3_pmax)
        draw_Vbar(1,7,dgryColor,'focus',v3_focus * 4)
        os.system("v4l2-ctl -d /dev/v4l-subdev" + str(foc_sub3) + " -c focus_absolute=" + str(focus))
        text(1,7,3,0,1,'<<< ' + str(v3_focus) + ' >>>',fv,0)
        time.sleep(0.25)

    # Arducam FOCUS UP/DOWN
    if (Pi_Cam == 5 or Pi_Cam == 6) and (buttonFUP.is_pressed or buttonFDN.is_pressed):
        if foc_man == 0:
            for f in range(0,len(video_limits)-1,3):
                if video_limits[f] == 'focus':
                    pmin = video_limits[f+1]
                    pmax = video_limits[f+2]
            focus_mode = 1
            foc_man = 1 # manual focus
            zoom = 0
            button(1,7,1,9)
        if buttonFDN.is_pressed:
            focus -= 10
        if buttonFUP.is_pressed:
            focus += 10
        focus = max(pmin,focus)
        focus = min(pmax,focus)
        os.system("v4l2-ctl -d /dev/v4l-subdev" + str(foc_sub5) + " -c focus_absolute=" + str(focus))
        text(1,7,3,0,1,'<<< ' + str(focus) + ' >>>',fv,0)
        draw_Vbar(1,7,dgryColor,'focus',focus)
        text(1,7,3,1,1,"manual",fv,0)
        time.sleep(0.25)

    # focus DOWN
    if Pi_Cam == 3:
      if buttonFDN.is_pressed:
        if v3_f_mode != 1:
            v3_focus_manual()
        v3_focus -= 1
        v3_focus = max(v3_focus,v3_pmin)
        draw_Vbar(1,7,dgryColor,'focus',v3_focus * 4)
        os.system("v4l2-ctl -d /dev/v4l-subdev" + str(foc_sub3) + " -c focus_absolute=" + str(focus))
        text(1,7,3,0,1,'<<< ' + str(v3_focus) + ' >>>',fv,0)
        time.sleep(0.25)
        
    pics = glob.glob('/run/shm/*.jpg')
    if len(pics) > 1:
        try:
            image = pygame.image.load(pics[1])
            for tt in range(1,len(pics)):
                 os.remove(pics[tt])
        except pygame.error:
            pass
        if Pi_Cam == 3 and zoom < 5:
            if rotate == 0:
                image = pygame.transform.scale(image, (preview_width,int(preview_height * 0.75)))
            else:
                image = pygame.transform.rotate(image, int(rotate * 90))
                if rotate != 2:
                    igwr = image.get_width()
                    ighr = image.get_height()
                    image = pygame.transform.scale(image, (int(preview_height * (igwr/ighr)),preview_height))
                else:
                    image = pygame.transform.scale(image, (preview_width,preview_height))
        else:
            if rotate == 0:
                image = pygame.transform.scale(image, (preview_width,preview_height))
            else:
                image = pygame.transform.rotate(image, int(rotate * 90))
                if rotate != 2:
                    igwr = image.get_width()
                    ighr = image.get_height()
                    image = pygame.transform.scale(image, (int(preview_height * (igwr/ighr)),preview_height))
                else:
                    image = pygame.transform.scale(image, (preview_width,preview_height))
        if rotate == 1 or rotate == 3:
            windowSurfaceObj.blit(image, (int((preview_width/2) - ((preview_height * (igwr/ighr)))/2),0))
        else:
            windowSurfaceObj.blit(image, (0,0))
        if zoom > 0 or foc_man == 1:
            image2 = pygame.surfarray.pixels3d(image)
            crop2 = image2[xx-histarea:xx+histarea,xy-histarea:xy+histarea]
            gray = cv2.cvtColor(crop2,cv2.COLOR_RGB2GRAY)
            if zoom > 0 and histogram > 0:
                if (histogram == 1 or histogram == 5):
                    red1   = crop2[:,:,0]
                    red2   = red1.reshape(histarea * histarea * 4,1)
                    rede   = [0] * 256
                if (histogram == 2 or histogram == 5):
                    green1 = crop2[:,:,1]
                    green2 = green1.reshape(histarea * histarea * 4,1)
                    greene = [0] * 256
                if (histogram == 3 or histogram == 5):
                    blue1  = crop2[:,:,2]
                    blue2  = blue1.reshape(histarea * histarea * 4,1)
                    bluee  = [0] * 256

                gray2  = gray.reshape(histarea * histarea * 4,1)
                lume   = [0] * 256
                for q in range(0,len(gray2)):
                    if (histogram == 4 or histogram == 5):
                        lume[int(gray2[q])] +=1
                    if (histogram == 1 or histogram == 5):
                        rede[int(red2[q])] +=1
                    if (histogram == 2 or histogram == 5):
                        greene[int(green2[q])] +=1
                    if (histogram == 3 or histogram == 5):
                        bluee[int(blue2[q])] +=1
                for t in range(0,256):
                    if histogram == 4 or histogram == 5:
                        if lume[t] > 0:
                            lume[t] = int(25*math.log10(lume[t]))
                    if histogram == 1 or histogram == 5:
                        if rede[t] > 0:
                            rede[t] = int(25*math.log10(rede[t]))
                    if histogram == 2 or histogram == 5:
                        if greene[t] > 0:
                            greene[t] = int(25*math.log10(greene[t]))
                    if histogram == 3 or histogram == 5:
                        if bluee[t] > 0:
                            bluee[t] = int(25*math.log10(bluee[t]))
                output = np.zeros((256,100,3))
                old_lume   = 0
                old_rede   = 0
                old_greene = 0
                old_bluee  = 0
                for count in range(0,255):
                    if histogram == 4 or histogram == 5:
                      if lume[count] > 0:
                        if lume[count] > old_lume:
                            st = 1
                        else:
                            st = -1
                        for y in range(old_lume,lume[count],st):
                            output[count, y,0] = 255
                            output[count, y,1] = 255
                            output[count, y,2] = 255
                    if histogram == 1 or histogram == 5:
                      if rede[count] > 0:
                        if rede[count] > old_rede:
                            st = 1
                        else:
                            st = -1
                        for y in range(old_rede,rede[count],st):
                            output[count, y,0] = 255
                    if histogram == 2 or histogram == 5:
                      if greene[count] > 0:
                        if greene[count] > old_greene:
                            st = 1
                        else:
                            st = -1
                        for y in range(old_greene,greene[count],st):
                            output[count, y,1] = 255
                    if histogram == 3 or histogram == 5:
                      if bluee[count] > 0:
                        if bluee[count] > old_bluee:
                            st = 1
                        else:
                            st = -1
                        for y in range(old_bluee,bluee[count],st):
                            output[count, y,2] = 255
                    if histogram == 4 or histogram == 5:
                        old_lume   = lume[count]
                    if histogram == 1 or histogram == 5:
                        old_rede   = rede[count]
                    if histogram == 2 or histogram == 5:
                        old_greene = greene[count]
                    if histogram == 3 or histogram == 5:
                        old_bluee  = bluee[count]
                graph = pygame.surfarray.make_surface(output)
                graph = pygame.transform.flip(graph,0,1)
                graph.set_alpha(160)
                pygame.draw.rect(windowSurfaceObj,greyColor,Rect(9,preview_height-111,64,102),1)
                pygame.draw.rect(windowSurfaceObj,greyColor,Rect(73,preview_height-111,64,102),1)
                pygame.draw.rect(windowSurfaceObj,greyColor,Rect(137,preview_height-111,64,102),1)
                pygame.draw.rect(windowSurfaceObj,greyColor,Rect(201,preview_height-111,66,102),1)
                windowSurfaceObj.blit(graph, (10,preview_height-110))
            if rotate != 0:
                pygame.draw.rect(windowSurfaceObj,blackColor,Rect(0,0,int(preview_width/4.5),int(preview_height/8)),0)
            foc = cv2.Laplacian(gray, cv2.CV_64F).var()
            text(20,0,3,2,0,"Focus: " + str(int(foc)),fv* 2,0)
            pygame.draw.rect(windowSurfaceObj,redColor,Rect(xx-histarea,xy-histarea,histarea*2,histarea*2),1)
            pygame.draw.line(windowSurfaceObj,(255,255,255),(xx-int(histarea/2),xy),(xx+int(histarea/2),xy),1)
            pygame.draw.line(windowSurfaceObj,(255,255,255),(xx,xy-int(histarea/2)),(xx,xy+int(histarea/2)),1)
        else:
            if rotate != 0:
                pygame.draw.rect(windowSurfaceObj,blackColor,Rect(0,0,int(preview_width/4.5),int(preview_height/8)),0)
            text(0,0,6,2,0,"Preview",fv* 2,0)
            zxp = (zx -((preview_width/2) / (igw/preview_width)))
            zyp = (zy -((preview_height/2) / (igh/preview_height)))
            zxq = (zx - zxp) * 2
            zyq = (zy - zyp) * 2
            if zxp + zxq > preview_width:
                zx = preview_width - int(zxq/2)
                zxp = (zx -((preview_width/2) / (igw/preview_width)))
                zxq = (zx - zxp) * 2
            if zyp + zyq > preview_height:
                zy = preview_height - int(zyq/2)
                zyp = (zy -((preview_height/2) / (igh/preview_height)))
                zyq = (zy - zyp) * 2
            if zxp < 0:
                zx = int(zxq/2) + 1
                zxp = 0
                zxq = (zx - zxp) * 2
            if zyp < 0:
                zy = int(zyq/2) + 1
                zyp = 0
                zyq = (zy - zyp) * 2
            if preview_width < 800:
                gw = 2
            else:
                gw = 1
            if Pi_Cam == 3 and fxz != 1 and zoom == 0 and rotate == 0:
                pygame.draw.rect(windowSurfaceObj,(200,0,0),Rect(int(fxx*preview_width),int(fxy*preview_height*.75),int(fxz*preview_width),int(fyz*preview_height)),1)
            if (Pi_Cam == 5 or Pi_Cam == 6) and (rotate == 0 or rotate == 2):
                if vwidth == 1280 and vheight == 960:
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width * 0.20),int(preview_height * 0.22),int(preview_width * 0.62),int(preview_height * 0.57)),gw)
                elif vwidth == 1280 and vheight == 720:
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width * 0.22),int(preview_height * 0.30),int(preview_width * 0.56),int(preview_height * 0.41)),gw)
                elif (vwidth == 1296 and vheight == 972) or (vwidth == 2592 and vheight == 1944):
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width * 0.19),int(preview_height * 0.16),int(preview_width * 0.62),int(preview_height * 0.64)),gw)
                elif vwidth == 800 and vheight == 600:
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width * 0.30),int(preview_height * 0.30),int(preview_width * 0.41),int(preview_height * 0.41)),gw)
                elif vwidth == 640 and vheight == 480:
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width * 0.30),int(preview_height * 0.30),int(preview_width * 0.41),int(preview_height * 0.41)),gw)
                elif (vwidth == 1920 and vheight == 1080) or (vwidth == 3840 and vheight == 2160):
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width * 0.09),int(preview_height * 0.20),int(preview_width * 0.82),int(preview_height * 0.62)),gw)
            elif rotate == 0 or rotate == 2:
                if Pi_Cam == 1 and ((vwidth == 1920 and vheight == 1080) or (vwidth == 1280 and vheight == 720) or (vwidth == 1536 and vheight == 864)):
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width * 0.13),int(preview_height * 0.22),int(preview_width * 0.74),int(preview_height * 0.57)),gw)
                elif Pi_Cam == 2 and ((vwidth == 1920 and vheight == 1080) or (vwidth == 1280 and vheight == 720) or (vwidth == 1536 and vheight == 864)):
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width * 0.2),int(preview_height * 0.28),int(preview_width * 0.60),int(preview_height * 0.45)),gw)
                elif Pi_Cam == 2 and ((vwidth == 640 and vheight == 480) or (vwidth == 720 and vheight == 540)):
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width * 0.30),int(preview_height * 0.30),int(preview_width * 0.41),int(preview_height * 0.41)),gw)
                elif Pi_Cam == 3 and ((vwidth == 640 and vheight == 480) or (vwidth == 1296 and vheight == 972) or (vwidth == 1280 and vheight == 960)):
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width * 0.25),int(preview_height * 0.17),int(preview_width * 0.50),int(preview_height * 0.46)),gw)
                elif Pi_Cam == 3 and ((vwidth == 800 and vheight == 600) or (vwidth == 720 and vheight == 540)):
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width * 0.25),int(preview_height * 0.17),int(preview_width * 0.50),int(preview_height * 0.46)),gw)
                elif Pi_Cam == 3 and ((vwidth == 1280 and vheight == 720) or (vwidth == 1536 and vheight == 864)):
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width * 0.175),int(preview_height * 0.15),int(preview_width * 0.66),int(preview_height * 0.48)),gw)
                elif Pi_Cam == 3 and vwidth == 1640 and vheight == 1232:
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width * 0.12),0,int(preview_width * 0.75),int(preview_height * 0.75)),gw)
                elif Pi_Cam == 3 and vwidth == 1456 and vheight == 1088:
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_width * 0.12),0,int(preview_width * 0.75),int(preview_height * 0.75)),gw)
                elif Pi_Cam == 7 and ((vwidth == 1920 and vheight == 1080) or (vwidth == 1280 and vheight == 720)):
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(0,int(preview_height * 0.12),int(preview_width),int(preview_height * 0.75)),gw)
                elif Pi_Cam == 4  and ((vwidth == 1920 and vheight == 1080) or (vwidth == 1536 and vheight == 864) or (vwidth == 1280 and vheight == 720)):
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(0,int(preview_height * 0.15),int(preview_width),int(preview_height * 0.75)),gw)
            elif rotate == 1 or rotate == 3:
                if Pi_Cam == 2 and ((vwidth == 1920 and vheight == 1080) or (vwidth == 1280 and vheight == 720) or (vwidth == 1536 and vheight == 864)):
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_height * 0.51),int(preview_width * 0.15),int(preview_height * 0.33),int(preview_width * 0.45)),gw)
                elif Pi_Cam == 2 and ((vwidth == 640 and vheight == 480) or (vwidth == 720 and vheight == 540)):
                    pygame.draw.rect(windowSurfaceObj,(155,0,150),Rect(int(preview_height * 0.50),int(preview_width * 0.22),int(preview_height * 0.33),int(preview_width * 0.31)),gw)

        # ARDUCAM AF
        if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and fcount < max_fcount and Pi != 5:
                image2 = pygame.surfarray.pixels3d(image)
                crop2 = image2[xx-histarea:xx+histarea,xy-histarea:xy+histarea]
                pygame.draw.rect(windowSurfaceObj,redColor,Rect(xx-histarea,xy-histarea,histarea*2,histarea*2),1)
                gray = cv2.cvtColor(crop2,cv2.COLOR_RGB2GRAY)
                foc = cv2.Laplacian(gray, cv2.CV_64F).var()
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'focus':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if foc >= 50:
                    ran = 0
                else:
                    focus = random.randint(pmin + 100,pmax - 100)
                    fcount = 1
                    ran = 1
                    old_foc = foc
                if (int(foc) >= int(old_foc) or fcount == 0) and ran == 0:
                    if fcount == 0:
                        if focus < int(pmax/2):
                            focus  += fstep
                        else:
                            focus  -= fstep
                    else:        
                        focus  += fstep
                elif ran == 0:
                    fstep = -fstep
                    focus += fstep
                old_foc = foc
                focus = max(pmin,focus)
                focus = min(pmax,focus)
                if focus < pmin + 100 or focus > pmax - 100:
                    focus = int(pmax/2)
                    fcount = 0
                os.system("v4l2-ctl -d /dev/v4l-subdev" + str(foc_sub5) + " -c focus_absolute=" + str(focus))
                text(20,1,3,2,0,"Ctrl  : " + str(int(focus)),fv* 2,0)
                text(20,2,3,2,0,"Focus : " + str(int(foc)),fv* 2,0)
                time.sleep(.5)
                fcount += 1

        pygame.display.update()
    
    # continuously read mouse buttons
    buttonx = pygame.mouse.get_pressed()
    if buttonx[0] != 0 :
        pos = pygame.mouse.get_pos()
        mousex = pos[0]
        mousey = pos[1]
        # determine button pressed
        if mousex > preview_width or (sq_dis == 1 and mousey > preview_height):
          # normal layout(buttons on right)
          if mousex > preview_width:
              button_column = int((mousex-preview_width)/bw) + 1
              button_row = int((mousey)/bh) + 1
              if mousex > preview_width + bw:
                  if mousex > preview_width + bw + (bw/2):
                      button_pos = 3
                  else:
                      button_pos = 2
              elif mousex > preview_width + (bw/2):
                  button_pos = 1
              else:
                  button_pos = 0
          # square layout(buttons below)    
          else:
              if mousey - preview_height < bh:
                  button_column = 1
                  button_row = int(mousex / bw) + 1
                  if mousex > ((button_row -1) * bw) + (bw/2):
                      button_pos = 1
                  else:
                      button_pos = 0
              elif mousey - preview_height < bh * 2:
                  button_column = 1
                  button_row = int(mousex / bw) + 7
                  if mousex > ((button_row - 7) * bw) + (bw/2):
                      button_pos = 1
                  else:
                      button_pos = 0
              elif mousey - preview_height < bh * 3:
                  button_column = 2
                  button_row = int(mousex / bw) + 1
                  if mousex > ((button_row -1) * bw) + (bw/2):
                      button_pos = 1
                  else:
                      button_pos = 0
              elif mousey - preview_height < bh * 4:
                  button_column = 2
                  button_row = int(mousex / bw) + 8
                  if mousex > ((button_row - 8) * bw) + (bw/2):
                      button_pos = 1
                  else:
                      button_pos = 0
  
          if button_column == 1:
            if button_row == 2:
                # MODE
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'mode':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    mode = int(((mousex-preview_width) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height  and mousey < preview_height + int(bh/3)):
                    mode = int(((mousex-((button_row - 1)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        mode -=1
                        mode  = max(mode ,pmin)
                    else:
                        mode  +=1
                        mode = min(mode ,pmax)
                if mode == 0:
                    text(0,2,5,0,1,"Shutter S",ft,10)
                    draw_bar(0,2,lgrnColor,'speed',speed)
                    if shutters[speed] < 0:
                        text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
                    else:
                        text(0,2,3,1,1,str(shutters[speed]),fv,10)
                    if gain == 0:
                        gain = 1
                        text(0,3,5,0,1,"Gain    A/D",ft,10)
                        if gain <= mag:
                            text(0,3,3,1,1,str(gain) + " :  " + str(gain) + "/1",fv,10)
                        else:
                            text(0,3,3,1,1,str(gain) + " :  " + str(int(mag)) + "/" + str(((gain/mag)*10)/10)[0:3],fv,10)
                        draw_bar(0,3,lgrnColor,'gain',gain)
                else:
                    text(0,2,5,0,1,"eV",ft,10)
                    text(0,2,3,1,1,str(ev),fv,10)
                    draw_bar(0,2,lgrnColor,'ev',ev)
                    gain = 0
                    text(0,3,5,0,1,"Gain ",ft,10)
                    text(0,3,3,1,1,"Auto",fv,10)
                    draw_bar(0,3,lgrnColor,'gain',gain)
                if Pi_Cam == 6 and mode == 0:
                    text(0,0,1,1,1,"STILL    2x2",ft,7)
                else:
                    text(0,0,1,1,1,"Still ",ft,7)
                if Pi_Cam == 6 and mode == 0 and tinterval > 0:
                    text(1,9,1,1,1,"T'lapse  2x2",ft,7)
                else:
                    text(1,9,1,1,1,"Timelapse",ft,7)
                text(0,1,3,1,1,modes[mode],fv,10)
                draw_bar(0,1,lgrnColor,'mode',mode)
                td = timedelta(seconds=tinterval)
                text(1,11,3,1,1,str(td),fv,12)
                draw_Vbar(1,10,lyelColor,'tinterval',tinterval)
                if tinterval > 0:
                    tduration = tinterval * tshots
                if mode == 0 and tinterval == 0 :
                    speed = 15
                    shutter = shutters[speed]
                    if shutter < 0:
                        shutter = abs(1/shutter)
                    sspeed = int(shutter * 1000000)
                    if (shutter * 1000000) - int(shutter * 1000000) > 0.5:
                        sspeed +=1
                    if shutters[speed] < 0:
                        text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
                    else:
                        text(0,2,3,1,1,str(shutters[speed]),fv,10)
                    draw_bar(0,2,lgrnColor,'speed',speed)

                time.sleep(.25)
                restart = 1

            elif button_row == 3:
                # SHUTTER SPEED or EV (dependent on MODE set)
                if mode == 0 :
                    for f in range(0,len(still_limits)-1,3):
                        if still_limits[f] == 'speed':
                            pmin = still_limits[f+1]
                            pmax = max_speed
                    if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                        speed = int(((mousex-preview_width) / bw) * (pmax+1-pmin))
                    elif (mousey > preview_height  and mousey < preview_height + int(bh/3)):
                        speed = int(((mousex-((button_row - 1)*bw)) / bw) * (pmax+1-pmin))
                    else:
                        if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                            speed -=1
                            speed  = max(speed ,pmin)
                        else:
                            speed  +=1
                            speed = min(speed ,pmax)
                    shutter = shutters[speed]
                    if shutter < 0:
                        shutter = abs(1/shutter)
                    sspeed = int(shutter * 1000000)
                    if (shutter * 1000000) - int(shutter * 1000000) > 0.5:
                        sspeed +=1
                    if shutters[speed] < 0:
                        text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
                    else:
                        text(0,2,3,1,1,str(shutters[speed]),fv,10)
                    draw_bar(0,2,lgrnColor,'speed',speed)
                    if tinterval > 0:
                        tinterval = int(sspeed/1000000)
                        tinterval = max(tinterval,1)
                        td = timedelta(seconds=tinterval)
                        text(1,11,3,1,1,str(td),fv,12)
                        draw_Vbar(1,11,lyelColor,'tinterval',tinterval)
                        tduration = tinterval * tshots
                        td = timedelta(seconds=tduration)
                        text(1,10,3,1,1,str(td),fv,12)
                        draw_Vbar(1,10,lyelColor,'tduration',tduration)
                        
                    time.sleep(.25)
                    restart = 1
                else:
                    # EV
                    for f in range(0,len(still_limits)-1,3):
                        if still_limits[f] == 'ev':
                            pmin = still_limits[f+1]
                            pmax = still_limits[f+2]
                    if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                        ev = int(((mousex-preview_width) / bw) * (pmax+1-pmin)) + pmin 
                    elif (mousey > preview_height + bh  and mousey < preview_height + bh + int(bh/3)):
                        ev = int(((mousex-((button_row - 7)*bw)) / bw) * (pmax+1-pmin)) + pmin 
                    else:
                        if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                            ev -=1
                            ev  = max(ev ,pmin)
                        else:
                            ev  +=1
                            ev = min(ev ,pmax)
                    text(0,2,3,1,1,str(ev),fv,10)
                    draw_bar(0,2,lgrnColor,'ev',ev)
                    time.sleep(0.25)
                    restart = 1
                    
            elif button_row == 4:
                # GAIN
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'gain':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    gain = int(((mousex-preview_width) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height  and mousey < preview_height + int(bh/3)):
                    gain = int(((mousex-((button_row - 1)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        gain -=1
                        gain  = max(gain ,pmin)
                    else:
                        gain  +=1
                        gain = min(gain ,pmax)
                if gain > 0:
                    text(0,3,5,0,1,"Gain    A/D",ft,10)
                    if gain <= mag:
                        text(0,3,3,1,1,str(gain) + " :  " + str(gain) + "/1",fv,10)
                    else:
                        text(0,3,3,1,1,str(gain) + " :  " + str(int(mag)) + "/" + str(((gain/mag)*10)/10)[0:3],fv,10)
                else:
                    if gain == 0:
                        text(0,3,5,0,1,"Gain ",ft,10)
                    else:
                        text(0,3,5,0,1,"Gain    A/D",ft,10)
                    text(0,3,3,1,1,"Auto",fv,10)
                time.sleep(.25)
                draw_bar(0,3,lgrnColor,'gain',gain)
                restart = 1
                
            elif button_row == 5:
                # BRIGHTNESS
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'brightness':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    brightness = int(((mousex-preview_width) / bw) * (pmax+1-pmin)) + pmin 
                elif (mousey > preview_height  and mousey < preview_height + int(bh/3)):
                    brightness = int(((mousex-((button_row - 1)*bw)) / bw) * (pmax+1-pmin)) + pmin 
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        brightness -=1
                        brightness  = max(brightness ,pmin)
                    else:
                        brightness  +=1
                        brightness = min(brightness ,pmax)
                text(0,4,3,1,1,str(brightness/100),fv,10)
                draw_bar(0,4,lgrnColor,'brightness',brightness)
                time.sleep(0.025)
                restart = 1
                
            elif button_row == 6:
                # CONTRAST
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'contrast':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    contrast = int(((mousex-preview_width) / bw) * (pmax+1-pmin)) 
                elif (mousey > preview_height  and mousey < preview_height + int(bh/3)):
                    contrast = int(((mousex-((button_row - 1)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        contrast -=1
                        contrast  = max(contrast ,pmin)
                    else:
                        contrast  +=1
                        contrast = min(contrast ,pmax)
                text(0,5,3,1,1,str(contrast/100)[0:4],fv,10)
                draw_bar(0,5,lgrnColor,'contrast',contrast)
                time.sleep(0.025)
                restart = 1
                
                
            elif button_row == 8 and awb == 0:
                # BLUE
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'blue':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    blue = int(((mousex-preview_width) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + bh  and mousey < preview_height + bh + int(bh/3)):
                    blue = int(((mousex-((button_row - 7)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        blue -=1
                        blue  = max(blue ,pmin)
                    else:
                        blue  +=1
                        blue = min(blue ,pmax)
                text(0,7,3,1,1,str(blue/10)[0:3],fv,10)
                draw_bar(0,7,lgrnColor,'blue',blue)
                time.sleep(.25)
                restart = 1

            elif button_row == 11:
                # QUALITY
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'quality':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    quality = int(((mousex-preview_width) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + bh  and mousey < preview_height + bh + int(bh/3)):
                    quality = int(((mousex-((button_row - 7)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        quality -=1
                        quality  = max(quality ,pmin)
                    else:
                        quality  +=1
                        quality = min(quality ,pmax)
                text(0,10,3,1,1,str(quality)[0:3],fv,10)
                draw_bar(0,10,lgrnColor,'quality',quality)
                time.sleep(.25)
                restart = 1

            elif button_row == 9 and awb == 0 :
                # RED
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'red':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    red = int(((mousex-preview_width) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + bh  and mousey < preview_height + bh + int(bh/3)):
                    red = int(((mousex-((button_row - 7)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        red -=1
                        red  = max(red ,pmin)
                    else:
                        red  +=1
                        red = min(red ,pmax)
                text(0,8,3,1,1,str(red/10)[0:3],fv,10)
                draw_bar(0,8,lgrnColor,'red',red)
                time.sleep(.25)
                restart = 1

            elif button_row == 8 and awb != 0:
                # DENOISE
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'denoise':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    denoise = int(((mousex-preview_width) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + (bh)  and mousey < preview_height + (bh) + int(bh/3)):
                    denoise = int(((mousex-((button_row -7)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        denoise -=1
                        denoise = max(denoise,pmin)
                    else:
                        denoise +=1
                        denoise = min(denoise,pmax)
                text(0,7,3,1,1,denoises[denoise],fv,10)
                draw_bar(0,7,lgrnColor,'denoise',denoise)
                time.sleep(.25)
                restart = 1

            elif button_row == 9 and awb != 0:
                # SHARPNESS
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'sharpness':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    sharpness = int(((mousex-preview_width) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + (bh)  and mousey < preview_height + (bh) + int(bh/3)):
                    sharpness = int(((mousex-((button_row -7)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        sharpness -=1
                        sharpness = max(sharpness,pmin)
                    else:
                        sharpness +=1
                        sharpness = min(sharpness,pmax)
                        
                text(0,8,3,1,1,str(sharpness/10),fv,10)
                draw_bar(0,8,lgrnColor,'sharpness',sharpness)
                time.sleep(.25)
                restart = 1
                
            elif button_row == 10:
                # EXTENSION
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'extn':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    extn = int(((mousex-preview_width) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + bh  and mousey < preview_height + bh + int(bh/3)):
                    extn = int(((mousex-((button_row - 7)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        extn -=1
                        extn  = max(extn ,pmin)
                    else:
                        extn  +=1
                        extn = min(extn ,pmax) 
                text(0,9,3,1,1,extns[extn],fv,10)
                draw_bar(0,9,lgrnColor,'extn',extn)
                time.sleep(.25)
                
            elif button_row == 7:
                # AWB
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'awb':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    awb = int(((mousex-preview_width) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + bh  and mousey < preview_height + bh + int(bh/3)):
                    awb = int(((mousex-((button_row - 7)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        awb -=1
                        awb  = max(awb ,pmin)
                    else:
                        awb  +=1
                        awb = min(awb ,pmax)
                text(0,6,3,1,1,awbs[awb],fv,10)
                draw_bar(0,6,lgrnColor,'awb',awb)
                if awb == 0:
                    text(0,7,5,0,1,"Blue",ft,10)
                    text(0,8,5,0,1,"Red",ft,10)
                    text(0,8,3,1,1,str(red/10)[0:3],fv,10)
                    text(0,7,3,1,1,str(blue/10)[0:3],fv,10)
                    draw_bar(0,7,lgrnColor,'blue',blue)
                    draw_bar(0,8,lgrnColor,'red',red)
                else:
                    text(0,7,5,0,1,"Denoise",fv,10)
                    text(0,7,3,1,1,denoises[denoise],fv,10)
                    text(0,8,5,0,1,"Sharpness",fv,10)
                    text(0,8,3,1,1,str(sharpness/10),fv,10)
                    draw_bar(0,7,lgrnColor,'denoise',denoise)
                    draw_bar(0,8,lgrnColor,'sharpness',sharpness)
                time.sleep(.25)
                restart = 1
                
            elif button_row == 12:
                # SATURATION
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'saturation':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    saturation = int(((mousex-preview_width) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + bh  and mousey < preview_height + bh + int(bh/3)):
                    saturation = int(((mousex-((button_row - 7)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        saturation -=1
                        saturation  = max(saturation ,pmin)
                    else:
                        saturation  +=1
                        saturation = min(saturation ,pmax)
                text(0,11,3,1,1,str(saturation/10),fv,10)
                draw_bar(0,11,lgrnColor,'saturation',saturation)
                time.sleep(.25)
                restart = 1
                
            elif button_row == 13:
                # METER
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'meter':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    meter = int(((mousex-preview_width) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + bh  and mousey < preview_height + bh + int(bh/3)):
                    meter = int(((mousex-((button_row - 7)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        meter -=1
                        meter  = max(meter ,pmin)
                    else:
                        meter  +=1
                        meter = min(meter ,pmax)
                text(0,12,3,1,1,meters[meter],fv,10)
                draw_bar(0,12,lgrnColor,'meter',meter)
                time.sleep(.25)
                restart = 1

            elif button_row == 14 and Pi_Cam == 3:
                # PI V3 CAMERA HDR
                if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                    v3_hdr -=1
                    v3_hdr  = max(v3_hdr ,0)
                else:
                    v3_hdr  +=1
                    v3_hdr = min(v3_hdr ,1)

                text(0,13,5,0,1,"HDR",fv,10)
                if v3_hdr == 0:
                    text(0,13,3,1,1,"Off",fv,10)
                else:
                    text(0,13,3,1,1,"ON ",fv,10)
                time.sleep(0.25)
                restart = 1

            elif button_row == 14 and Pi_Cam == 4 and scientif == 1:
                # v4 (HQ) CAMERA Scientific.json
                if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                    scientific -=1
                    scientific = max(scientific ,0)
                else:
                    scientific  +=1
                    scientific = min(scientific ,1)

                text(0,13,5,0,1,"Scientific",fv,10)
                if scientific == 0:
                    text(0,13,3,1,1,"Off",fv,10)
                else:
                    text(0,13,3,1,1,"ON ",fv,10)
                time.sleep(0.25)
                restart = 1

            elif button_row == 15:
                # HISTOGRAM 
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'histogram':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    histogram = int(((mousex-preview_width) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + bh  and mousey < preview_height + bh + int(bh/3)):
                    histogram = int(((mousex-((button_row - 7)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        histogram -=1
                        histogram = max(histogram,pmin)
                    else:
                        histogram +=1
                        histogram = min(histogram,pmax)
                text(0,14,3,1,1,histograms[histogram],fv,7)
                draw_bar(0,14,greyColor,'histogram',histogram)
                time.sleep(.25)

            elif button_row == 16 and Pi_Cam == 3:
                # V3 FOCUS SPEED 
                for f in range(0,len(still_limits)-1,3):
                    if still_limits[f] == 'v3_f_speed':
                        pmin = still_limits[f+1]
                        pmax = still_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    v3_f_speed = int(((mousex-preview_width) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + bh  and mousey < preview_height + bh + int(bh/3)):
                    v3_f_speed = int(((mousex-((button_row - 7)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        v3_f_speed-=1
                        v3_f_speed = max(v3_f_speed,pmin)
                    else:
                        v3_f_speed +=1
                        v3_f_speed = min(v3_f_speed,pmax)
                text(0,15,3,1,1,v3_f_speeds[v3_f_speed],fv,7)
                draw_bar(0,15,greyColor,'v3_f_speed',v3_f_speed)
                restart = 1
                time.sleep(.25)
               
          elif button_column == 2:
            if button_row == 2:
                # VIDEO LENGTH
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'vlen':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    vlen = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height  + (bh*2) and mousey < preview_height + (bh*2) + int(bh/3)):
                    vlen = int(((mousex-((button_row - 1)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + bw + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        vlen -=1
                        vlen  = max(vlen ,pmin)
                    else:
                        vlen  +=1
                        vlen = min(vlen ,pmax)
                td = timedelta(seconds=vlen)
                text(1,1,3,1,1,str(td),fv,11)
                draw_Vbar(1,1,lpurColor,'vlen',vlen)
                time.sleep(.25)
 
            elif button_row == 3:
                # FPS
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'fps':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    fps = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                    fps = min(fps,vfps)
                    fps = max(fps,pmin)
                elif (mousey > preview_height  + (bh*2) and mousey < preview_height + (bh*2) + int(bh/3)):
                    fps = int(((mousex-((button_row - 1)*bw)) / bw) * (pmax+1-pmin))
                    fps = min(fps,vfps)
                    fps = max(fps,pmin)
                else:
                    if (sq_dis == 0 and mousex < preview_width + bw + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        fps -=1
                        fps  = max(fps ,pmin)
                    else:
                        fps  +=1
                        fps = min(fps ,pmax)
                
                text(1,2,3,1,1,str(fps),fv,11)
                draw_Vbar(1,2,lpurColor,'fps',fps)
                time.sleep(.25)
                restart = 1
                   
            elif button_row == 4:
                # VFORMAT
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'vformat':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    if codec > 0 and (Pi_Cam == 5 or Pi_Cam == 6) and ("dtoverlay=vc4-kms-v3d,cma-512" in configtxt): # Arducam IMX519 16MP OR 64MP
                        max_vformat = max_vf_6
                    elif codec > 0 and (Pi_Cam == 5 or Pi_Cam == 6): # Arducam IMX519 16MP or 64MP
                        max_vformat = max_vf_5
                    elif Pi_Cam == 7: # PI GS
                        max_vformat = max_vf_7
                    elif codec > 0 and Pi_Cam == 4:
                        max_vformat = max_vf_4
                    elif codec > 0 and Pi_Cam == 3:
                        max_vformat = max_vf_3
                    elif codec > 0 and Pi_Cam == 2:
                        max_vformat = max_vf_2
                    elif codec > 0 and Pi_Cam == 1:
                        max_vformat = max_vf_1
                    elif Pi_Cam == 4:
                        max_vformat = max_vf_4a
                    else:
                        max_vformat = max_vf_0
                    pmax = max_vformat
                    vformat = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height  + (bh*2) and mousey < preview_height + (bh*2) + int(bh/3)):
                    if codec > 0 and (Pi_Cam == 5 or Pi_Cam == 6) and ("dtoverlay=vc4-kms-v3d,cma-512" in configtxt): # Arducam IMX519 16MP OR 64MP
                        max_vformat = max_vf_6
                    elif codec > 0 and (Pi_Cam == 5 or Pi_Cam == 6): # Arducam IMX519 16MP or 64MP
                        max_vformat = max_vf_5
                    elif Pi_Cam == 7: # PI GS
                        max_vformat = max_vf_7
                    elif codec > 0 and Pi_Cam == 4:
                        max_vformat = max_vf_4
                    elif codec > 0 and Pi_Cam == 3:
                        max_vformat = max_vf_3
                    elif codec > 0 and Pi_Cam == 2:
                        max_vformat = max_vf_2
                    elif codec > 0 and Pi_Cam == 1:
                        max_vformat = max_vf_1
                    elif Pi_Cam == 4:
                        max_vformat = max_vf_4a
                    else:
                        max_vformat = max_vf_0
                    pmax = max_vformat
                    vformat = int(((mousex-((button_row - 1)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + bw + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        vformat -=1
                        if codec > 0 and (Pi_Cam == 5 or Pi_Cam == 6) and ("dtoverlay=vc4-kms-v3d,cma-512" in configtxt): # Arducam IMX519 16MP OR 64MP
                            max_vformat = max_vf_6
                        elif codec > 0 and (Pi_Cam == 5 or Pi_Cam == 6): # Arducam IMX519 16MP or 64MP
                            max_vformat = max_vf_5
                        elif Pi_Cam == 7: # PI GS
                            max_vformat = max_vf_7
                        elif codec > 0 and Pi_Cam == 4:
                            max_vformat = max_vf_4
                        elif codec > 0 and Pi_Cam == 3:
                            max_vformat = max_vf_3
                        elif codec > 0 and Pi_Cam == 2:
                            max_vformat = max_vf_2
                        elif codec > 0 and Pi_Cam == 1:
                            max_vformat = max_vf_1
                        elif Pi_Cam == 4:
                            max_vformat = max_vf_4a
                        else:
                            max_vformat = max_vf_0
                        vformat = min(vformat,max_vformat)
                        vformat = max(vformat,pmin)
                    else:
                        vformat +=1
                        if codec > 0 and (Pi_Cam == 5 or Pi_Cam == 6) and ("dtoverlay=vc4-kms-v3d,cma-512" in configtxt): # Arducam IMX519 16MP OR 64MP
                            max_vformat = max_vf_6
                        elif codec > 0 and (Pi_Cam == 5 or Pi_Cam == 6): # Arducam IMX519 16MP or 64MP
                            max_vformat = max_vf_5
                        elif Pi_Cam == 7: # PI GS
                            max_vformat = max_vf_7
                        elif codec > 0 and Pi_Cam == 4:
                            max_vformat = max_vf_4
                        elif codec > 0 and Pi_Cam == 3:
                            max_vformat = max_vf_3
                        elif codec > 0 and Pi_Cam == 2:
                            max_vformat = max_vf_2
                        elif codec > 0 and Pi_Cam == 1:
                            max_vformat = max_vf_1
                        elif Pi_Cam == 4:
                            max_vformat = max_vf_4a
                        else:
                            max_vformat = max_vf_0
                        vformat = min(vformat,max_vformat)
                draw_Vbar(1,3,lpurColor,'vformat',vformat)
                vwidth  = vwidths[vformat]
                vheight = vheights[vformat]
                if Pi_Cam == 3:
                    vfps = v3_max_fps[vformat]
                    if vwidth == 1920 and codec == 0:
                        prof = h264profiles[profile].split(" ")
                        if str(prof[1]) == "4.2":
                            if vpreview == 1:
                                vfps = 45
                            else:
                                vfps = 60
                    elif vwidth == 1536 and codec == 0:
                        prof = h264profiles[profile].split(" ")
                        if str(prof[1]) == "4.2":
                            if vpreview == 1:
                                vfps = 60
                            else:
                                vfps = 90
                else:
                    vfps = v_max_fps[vformat]
                fps = min(fps,vfps)
                video_limits[5] = vfps
                text(1,2,3,1,1,str(fps),fv,11)
                draw_Vbar(1,2,lpurColor,'fps',fps)
                text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
                time.sleep(.25)

            elif button_row == 5:
                # CODEC
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'codec':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    codec = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + (bh*2) and mousey < preview_height + (bh*2) + int(bh/3)):
                    codec = int(((mousex-((button_row - 1)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + bw + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        codec -=1
                        codec  = max(codec ,pmin)
                    else:
                        codec  +=1
                        codec = min(codec ,pmax)
                if codec > 0 and (Pi_Cam == 5 or Pi_Cam == 6) and ("dtoverlay=vc4-kms-v3d,cma-512" in configtxt): # Arducam IMX519 16MP OR 64MP
                    max_vformat = max_vf_6
                elif codec > 0 and (Pi_Cam == 5 or Pi_Cam == 6): # Arducam IMX519 16MP or 64MP
                    max_vformat = max_vf_5
                elif Pi_Cam == 7: # PI GS
                    max_vformat = max_vf_7
                elif codec > 0 and Pi_Cam == 4: # PI HQ
                    max_vformat = max_vf_4
                elif codec > 0 and Pi_Cam == 3: # PI V3
                    max_vformat = max_vf_3
                elif codec > 0 and Pi_Cam == 2: # PI V2
                    max_vformat = max_vf_2
                elif codec > 0 and Pi_Cam == 1: # PI V1
                    max_vformat = max_vf_1
                elif Pi_Cam == 4:
                    max_vformat = max_vf_4a
                else:
                    max_vformat = max_vf_0
                vformat = min(vformat,max_vformat)
                text(1,4,3,1,1,codecs[codec],fv,11)
                draw_Vbar(1,4,lpurColor,'codec',codec)
                draw_Vbar(1,3,lpurColor,'vformat',vformat)
                vwidth  = vwidths[vformat]
                vheight = vheights[vformat]
                if Pi_Cam == 3:
                    vfps = v3_max_fps[vformat]
                    if vwidth == 1920 and codec == 0:
                        prof = h264profiles[profile].split(" ")
                        if str(prof[1]) == "4.2":
                            if vpreview == 1:
                                vfps = 45
                            else:
                                vfps = 60
                    elif vwidth == 1536 and codec == 0:
                        prof = h264profiles[profile].split(" ")
                        if str(prof[1]) == "4.2":
                            if vpreview == 1:
                                vfps = 60
                            else:
                                vfps = 90
                else:
                    vfps = v_max_fps[vformat]
                fps = min(fps,vfps)
                video_limits[5] = vfps
                text(1,2,3,1,1,str(fps),fv,11)
                draw_Vbar(1,2,lpurColor,'fps',fps)
                text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
                time.sleep(.25)

            elif button_row == 6:
                # H264 PROFILE
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'profile':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    profile = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + (bh*2) and mousey < preview_height + (bh*2) + int(bh/3)):
                    profile = int(((mousex-((button_row - 1)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + bw + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        profile -=1
                        profile  = max(profile ,pmin)
                    else:
                        profile  +=1
                        profile = min(profile ,pmax)
                text(1,5,3,1,1,h264profiles[profile],fv,11)
                draw_Vbar(1,5,lpurColor,'profile',profile)
                vwidth  = vwidths[vformat]
                vheight = vheights[vformat]
                if Pi_Cam == 3:
                    vfps = v3_max_fps[vformat]
                    if vwidth == 1920 and codec == 0:
                        prof = h264profiles[profile].split(" ")
                        if str(prof[1]) == "4.2":
                            if vpreview == 1:
                                vfps = 45
                            else:
                                vfps = 60
                    elif vwidth == 1536 and codec == 0:
                        prof = h264profiles[profile].split(" ")
                        if str(prof[1]) == "4.2":
                            if vpreview == 1:
                                vfps = 60
                            else:
                                vfps = 90
                else:
                    vfps = v_max_fps[vformat]
                fps = min(fps,vfps)
                video_limits[5] = vfps
                text(1,2,3,1,1,str(fps),fv,11)
                draw_Vbar(1,2,lpurColor,'fps',fps)
                time.sleep(.25)

            elif button_row == 7:
                # V_PREVIEW
                if (sq_dis == 0 and mousex > preview_width + bw + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                    vpreview +=1
                    vpreview  = min(vpreview ,1)
                else:
                    vpreview  -=1
                    vpreview = max(vpreview ,0)

                if vpreview == 0:
                    text(1,6,3,1,1,"Off",fv,11)
                else:
                    text(1,6,3,1,1,"ON ",fv,11)
                vwidth  = vwidths[vformat]
                vheight = vheights[vformat]
                if Pi_Cam == 3:
                    vfps = v3_max_fps[vformat]
                    if vwidth == 1920 and codec == 0:
                        prof = h264profiles[profile].split(" ")
                        if str(prof[1]) == "4.2":
                            if vpreview == 1:
                                vfps = 45
                            else:
                                vfps = 60
                    elif vwidth == 1536 and codec == 0:
                        prof = h264profiles[profile].split(" ")
                        if str(prof[1]) == "4.2":
                            if vpreview == 1:
                                vfps = 60
                            else:
                                vfps = 90
                else:
                    vfps = v_max_fps[vformat]
                fps = min(fps,vfps)
                video_limits[5] = vfps
                text(1,2,3,1,1,str(fps),fv,11)
                draw_Vbar(1,2,lpurColor,'fps',fps)
                time.sleep(0.25)

            elif button_row == 8:
                # FOCUS
                if Pi_Cam == 3:
                    for f in range(0,len(video_limits)-1,3):
                        if video_limits[f] == 'v3_focus':
                            pmin = video_limits[f+1]
                            pmax = video_limits[f+2]
                if Pi_Cam == 5 or Pi_Cam == 6:
                    for f in range(0,len(video_limits)-1,3):
                        if video_limits[f] == 'focus':
                            pmin = video_limits[f+1]
                            pmax = video_limits[f+2]
                if (mousex > preview_width + bw and mousey < ((button_row-1)*bh) + (bh/3)) and (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 1:
                    focus = int(((mousex-preview_width-bw) / bw) * pmax)
                    draw_Vbar(1,7,dgryColor,'focus',focus)
                    os.system("v4l2-ctl -d /dev/v4l-subdev" + str(foc_sub5) + " -c focus_absolute=" + str(focus))
                    text(1,7,3,0,1,'<<< ' + str(focus) + ' >>>',fv,0)
                elif mousex > preview_width + bw and mousey > ((button_row-1)*bh) + (bh/3) and mousey < ((button_row-1)*bh) + (bh/1.5) and (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 1:
                    if button_pos == 2:
                        focus -= 10
                    elif button_pos == 3:
                        focus += 10
                    draw_Vbar(1,7,dgryColor,'focus',focus)
                    os.system("v4l2-ctl -d /dev/v4l-subdev" + str(foc_sub5) + " -c focus_absolute=" + str(focus))
                    text(1,7,3,0,1,'<<< ' + str(focus) + ' >>>',fv,0)

                elif (mousey > preview_height + (bh*3) and mousey < preview_height + (bh*3) + (bh/3)) and (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 1:
                    focus = int(((mousex-((button_row - 8)*bw)) / bw)* pmax)
                    draw_Vbar(1,7,dgryColor,'focus',focus)
                    os.system("v4l2-ctl -d /dev/v4l-subdev" + str(foc_sub5) + " -c focus_absolute=" + str(focus))
                    text(1,7,3,0,1,'<<< ' + str(focus) + ' >>>',fv,0)
                elif mousey > preview_height + (bh*3) and mousey > preview_height + (bh*3) + (bh/3) and mousey < preview_height + (bh*3) + (bh/1.5) and (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 1:
                    if button_pos == 0:
                        focus -= 10
                    elif button_pos == 1:
                        focus += 10
                    draw_Vbar(1,7,dgryColor,'focus',focus)
                    if cam0 == "imx519" and camera == 0:
                        os.system("v4l2-ctl -d /dev/v4l-subdev1 -c focus_absolute=" + str(focus))
                    if cam1 == "imx519" and camera == 1:
                        os.system("v4l2-ctl -d /dev/v4l-subdev6 -c focus_absolute=" + str(focus))
                    text(1,7,3,0,1,'<<< ' + str(focus) + ' >>>',fv,0)
                # new v3
                elif (mousex > preview_width + bw and mousey < ((button_row-1)*bh) + (bh/3)) and Pi_Cam == 3 and foc_man == 1:
                    v3_focus = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin)) + pmin
                    draw_Vbar(1,7,dgryColor,'v3_focus',v3_focus-pmin)
                    text(1,7,3,0,1,'<<< ' + str(int(v3_focus)) + ' >>>',fv,0)
                    restart = 1
                elif mousex > preview_width + bw and mousey > ((button_row-1)*bh) + (bh/3) and mousey < ((button_row-1)*bh) + (bh/1.5) and Pi_Cam == 3  and foc_man == 1:
                    if button_pos == 2:
                        v3_focus -= 1
                        v3_focus = max(v3_focus,pmin)
                    elif button_pos == 3:
                        v3_focus += 1
                        v3_focus = min(v3_focus,pmax)
                    draw_Vbar(1,7,dgryColor,'v3_focus',v3_focus-pmin)
                    text(1,7,3,0,1,'<<< ' + str(int(v3_focus)) + ' >>>',fv,0)
                    restart = 1
                elif (mousey > preview_height + (bh*3) and mousey < preview_height + (bh*3) + (bh/3)) and Pi_Cam == 3 and foc_man == 1:
                    v3_focus = int(((mousex-((button_row - 8)*bw)) / bw)* pmax)
                    draw_Vbar(1,7,dgryColor,'v3_focus',v3_focus-pmin)
                    text(1,7,3,0,1,'<<< ' + str(int(v3_focus)) + ' >>>',fv,0)
                    restart = 1
                elif mousey > preview_height + (bh*3) and mousey > preview_height + (bh*3) + (bh/3) and mousey < preview_height + (bh*3) + (bh/1.5) and Pi_Cam == 3 and foc_man == 1:
                    if button_pos == 0:
                        v3_focus -= 1
                        v3_focus = max(v3_focus,0.0)
                    elif button_pos == 1:
                        v3_focus += 1
                    draw_Vbar(1,7,dgryColor,'v3_focus',v3_focus-pmin)
                    text(1,7,3,0,1,'<<< ' + str(int(v3_focus)) + ' >>>',fv,0)
                    restart = 1
                    
                elif ((sq_dis == 0 and button_pos > 1) or (sq_dis == 1 and button_pos == 0)):
                    if (Pi_Cam < 3 or Pi_Cam == 4 or Pi_Cam == 7) and focus_mode == 0:
                        zoom = 4
                        focus_mode = 1
                        button(1,7,1,9)
                        text(1,7,3,0,1,"FOCUS",ft,0)
                        text(1,3,3,1,1,str(preview_width) + "x" + str(preview_height),fv,11)
                        button(1,8,1,9)
                        text(1,8,2,0,1,"ZOOMED",ft,0)
                        text(1,8,3,1,1,str(zoom),fv,0)
                        draw_Vbar(1,8,dgryColor,'zoom',zoom)
                        time.sleep(0.25)
                        restart = 1
                    elif (Pi_Cam < 3 or Pi_Cam == 4 or Pi_Cam == 7) and focus_mode == 1:
                        zoom = 0
                        focus_mode = 0
                        button(1,7,0,9)
                        text(1,7,5,0,1,"FOCUS",ft,7)
                        text(1,7,3,1,1,"",fv,7)
                        text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
                        button(1,8,0,9)
                        text(1,8,5,0,1,"Zoom",ft,7)
                        text(1,8,3,1,1,"",fv,7)
                        draw_Vbar(1,8,greyColor,'zoom',zoom)
                        restart = 1
                    elif Pi_Cam == 3 and v3_f_mode == 0:
                        focus_mode = 1
                        v3_f_mode = 1 # manual focus
                        foc_man = 1 
                        button(1,7,1,9)
                        restart = 1
                        time.sleep(0.25)
                        restart = 1 
                        draw_Vbar(1,7,dgryColor,'v3_focus',v3_focus-pmin)
                        text(1,7,3,0,1,'<<< ' + str(int(v3_focus)) + ' >>>',fv,0)
                        text(1,7,3,1,1,str(v3_f_modes[v3_f_mode]),fv,0)
                        time.sleep(0.25)
                    elif (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0:
                        focus_mode = 1
                        foc_man = 1 # manual focus
                        button(1,7,1,9)
                        if os.path.exists("ctrls.txt"):
                            os.remove("ctrls.txt")
                        os.system("v4l2-ctl -d /dev/v4l-subdev" + str(foc_sub5) + " --list-ctrls >> ctrls.txt")
                        restart = 1
                        time.sleep(0.25)
                        ctrlstxt = []
                        with open("ctrls.txt", "r") as file:
                            line = file.readline()
                            while line:
                                ctrlstxt.append(line.strip())
                                line = file.readline()
                        foc_ctrl = ctrlstxt[3].split('value=')
                        focus = int(foc_ctrl[1])
                        os.system("v4l2-ctl -d /dev/v4l-subdev" + str(foc_sub5) + " -c focus_absolute=" + str(focus))
                        text(1,7,3,0,1,'<<< ' + str(focus) + ' >>>',fv,0)
                        draw_Vbar(1,7,dgryColor,'focus',focus)
                        text(1,7,3,1,1,"manual",fv,0)
                        time.sleep(0.25)
                    elif (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 1:
                        focus_mode = 0
                        foc_man = 0
                        fcount = 0
                        zoom = 0
                        button(1,7,0,9)
                        text(1,7,5,0,1,"FOCUS",ft,7)
                        text(1,7,3,1,1,"auto",fv,7)
                        button(1,8,0,9)
                        text(1,8,5,0,1,"Zoom",ft,7)
                        text(1,8,3,1,1,"",fv,7)
                        text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
                        time.sleep(0.25)
                        restart = 1
                    elif Pi_Cam == 3 and v3_f_mode == 1:
                        focus_mode = 0
                        v3_f_mode = 2
                        foc_man = 0
                        zoom = 0
                        fxx = 0
                        fxy = 0
                        fxz = 1
                        fyz = 0.75
                        pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,0,preview_width,preview_height))
                        button(1,7,0,9)
                        text(1,7,5,0,1,"FOCUS",ft,7)
                        text(1,7,3,1,1,str(v3_f_modes[v3_f_mode]),fv,7)
                        button(1,8,0,9)
                        text(1,8,5,0,1,"Zoom",ft,7)
                        text(1,8,3,1,1,"",fv,7)
                        text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
                        time.sleep(0.25)
                        restart = 1
                    elif Pi_Cam == 3 and v3_f_mode == 2:
                        focus_mode = 0
                        v3_f_mode = 0
                        foc_man = 0
                        zoom = 0
                        fxx = 0
                        fxy = 0
                        fxz = 1
                        fyz = 0.75
                        pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,0,preview_width,preview_height))
                        button(1,7,0,9)
                        text(1,7,5,0,1,"FOCUS",ft,7)
                        text(1,7,3,1,1,str(v3_f_modes[v3_f_mode]),fv,7)
                        button(1,8,0,9)
                        text(1,8,5,0,1,"Zoom",ft,7)
                        text(1,8,3,1,1,"",fv,7)
                        text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
                        time.sleep(0.25)
                        restart = 1
                time.sleep(.25)
                
            elif button_row == 9:
                # ZOOM
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'zoom':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    zoom = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                    if zoom != 5 and Pi_Cam == 3:
                        pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,int(preview_height * .75),preview_width,preview_height))
                elif (mousey > preview_height + (bh*3)  and mousey < preview_height + (bh*3) + int(bh/3)):
                    zoom = int(((mousex-((button_row -8)*bw)) / bw) * (pmax+1-pmin))
                    if zoom != 5 and Pi_Cam == 3:
                        pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,int(preview_height * .75),preview_width,preview_height))
                elif ((sq_dis == 0 and mousex > preview_width + bw + (bw/2)) or (sq_dis == 1 and button_pos == 1)) and zoom != 5:
                    zoom +=1
                    zoom = min(zoom,pmax)
                elif ((sq_dis == 0 and mousex < preview_width + bw + (bw/2)) or (sq_dis == 1 and button_pos == 0)) and zoom > 0:
                    zoom -=1
                    if zoom != 5 and Pi_Cam == 3:
                        pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,int(preview_height * .75),preview_width,preview_height))
                if zoom == 0:
                    button(1,8,0,9)
                    text(1,8,5,0,1,"Zoom",ft,7)
                    text(1,8,3,1,1,"",fv,7)
                    text(1,3,3,1,1,str(vwidth) + "x" + str(vheight),fv,11)
                    draw_Vbar(1,8,greyColor,'zoom',zoom)
                else:
                    button(1,8,1,9)
                    text(1,8,2,0,1,"ZOOMED",ft,0)
                    text(1,8,3,1,1,str(zoom),fv,0)
                    text(1,3,3,1,1,str(preview_width) + "x" + str(preview_height),fv,11)
                    draw_Vbar(1,8,dgryColor,'zoom',zoom)
                if zoom > 0:
                    fxx = 0
                    fxy = 0
                    fxz = 1
                    fyz = 1
                    #fcount = 0
                    if Pi_Cam == 3 and v3_f_mode == 0:
                        text(1,7,3,1,1,str(v3_f_modes[v3_f_mode]),fv,7)
                restart = 1
                time.sleep(.2)

            elif button_row == 11:
                # TIMELAPSE DURATION
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'tduration':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    tduration = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + (bh*3)  and mousey < preview_height + (bh*3) + int(bh/3)):
                    tduration = int(((mousex-((button_row - 8)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + bw + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        tduration -=1
                        tduration = max(tduration,pmin)
                    else:
                        tduration +=1
                        tduration = min(tduration,pmax)
                td = timedelta(seconds=tduration)
                text(1,10,3,1,1,str(td),fv,12)
                draw_Vbar(1,10,lyelColor,'tduration',tduration)
                if tinterval > 0:
                    tshots = int(tduration / tinterval)
                    text(1,12,3,1,1,str(tshots),fv,12)
                else:
                    text(1,12,3,1,1," ",fv,12)
                draw_Vbar(1,12,lyelColor,'tshots',tshots)
                time.sleep(.25)

            elif button_row == 12:
                # TIMELAPSE INTERVAL
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'tinterval':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    tinterval = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + (bh*3)  and mousey < preview_height + (bh*3) + int(bh/3)):
                    tinterval = int(((mousex-((button_row -8)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + bw + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        tinterval -=1
                        tinterval = max(tinterval,pmin)
                    else:
                        tinterval +=1
                        tinterval = min(tinterval,pmax)
                if Pi_Cam == 6 and mode == 0 and tinterval > 0:
                    text(1,9,1,1,1,"T'lapse  2x2",ft,7)
                else:
                    text(1,9,1,1,1,"Timelapse",ft,7)
                td = timedelta(seconds=tinterval)
                text(1,11,3,1,1,str(td),fv,12)
                draw_Vbar(1,11,lyelColor,'tinterval',tinterval)
                if tinterval != 0:
                    tduration = tinterval * tshots
                    td = timedelta(seconds=tduration)
                    text(1,10,3,1,1,str(td),fv,12)
                    draw_Vbar(1,10,lyelColor,'tduration',tduration)
                if tinterval == 0:
                    text(1,12,3,1,1," ",fv,12)
                    if mode == 0:
                        speed = 15
                        shutter = shutters[speed]
                        if shutter < 0:
                            shutter = abs(1/shutter)
                        sspeed = int(shutter * 1000000)
                        if (shutter * 1000000) - int(shutter * 1000000) > 0.5:
                            sspeed +=1
                        if shutters[speed] < 0:
                            text(0,2,3,1,1,"1/" + str(abs(shutters[speed])),fv,10)
                        else:
                            text(0,2,3,1,1,str(shutters[speed]),fv,10)
                        draw_bar(0,2,lgrnColor,'speed',speed)
                        restart = 1
                else:
                    text(1,12,3,1,1,str(tshots),fv,12)
                time.sleep(.25)
                
            elif button_row == 13 and tinterval > 0:
                # TIMELAPSE SHOTS
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'tshots':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    tshots = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + (bh*3)  and mousey < preview_height + (bh*3) + int(bh/3)):
                    tshots = int(((mousex-((button_row -8)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + bw + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        tshots -=1
                        tshots = max(tshots,pmin)
                    else:
                        tshots +=1
                        tshots = min(tshots,pmax)
                text(1,12,3,1,1,str(tshots),fv,12)
                draw_Vbar(1,12,lyelColor,'tshots',tshots)
                if tduration > 0:
                    tduration = tinterval * tshots
                if tduration == 0:
                    tduration = 1
                td = timedelta(seconds=tduration)
                text(1,10,3,1,1,str(td),fv,12)
                draw_Vbar(1,10,lyelColor,'tduration',tduration)
                time.sleep(.25)

            elif button_row == 15:
                # HISTOGRAM SIZE
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'histarea':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    histarea = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                    histarea = max(histarea,pmin)
                elif (mousey > preview_height + (bh*3)  and mousey < preview_height + (bh*3) + int(bh/3)):
                    histarea = int(((mousex-((button_row -8)*bw)) / bw) * (pmax+1-pmin))
                    histarea = max(histarea,pmin)
                else:
                    if (sq_dis == 0 and mousex < preview_width + bw + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        histarea -=1
                        histarea = max(histarea,pmin)
                                               
                    else:
                        histarea +=1
                        histarea = min(histarea,pmax)
                if xx - histarea < 0 or xy - histarea < 0:
                    histarea = old_histarea
                if xy + histarea > preview_height or xx + histarea > preview_width:
                    histarea = old_histarea
                if Pi_Cam == 3 and (xy + histarea > preview_height * 0.75 or xx + histarea > preview_width):
                    histarea = old_histarea
                text(1,14,3,1,1,str(histarea),fv,7)
                draw_Vbar(1,14,greyColor,'histarea',histarea)
                old_histarea = histarea
                time.sleep(.25)

            elif button_row == 16 and Pi_Cam == 3:
                # V3 FOCUS RANGE 
                for f in range(0,len(video_limits)-1,3):
                    if video_limits[f] == 'v3_f_range':
                        pmin = video_limits[f+1]
                        pmax = video_limits[f+2]
                if (mousex > preview_width and mousey < ((button_row-1)*bh) + int(bh/3)):
                    v3_f_range = int(((mousex-preview_width-bw) / bw) * (pmax+1-pmin))
                elif (mousey > preview_height + bh  and mousey < preview_height + (bh*3) + int(bh/3)):
                    v3_f_range = int(((mousex-((button_row - 8)*bw)) / bw) * (pmax+1-pmin))
                else:
                    if (sq_dis == 0 and mousex < preview_width + bw + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                        v3_f_range-=1
                        v3_f_range = max(v3_f_range,pmin)
                    else:
                        v3_f_range +=1
                        v3_f_range = min(v3_f_range,pmax)
                text(1,15,3,1,1,v3_f_ranges[v3_f_range],fv,7)
                draw_Vbar(1,15,greyColor,'v3_f_range',v3_f_range)
                restart = 1
                time.sleep(.25)

               
            elif button_row == 14:
                if (sq_dis == 0 and mousex < preview_width + bw + (bw/2)) or (sq_dis == 1 and button_pos == 0):
                   # SAVE CONFIG
                   text(1,13,3,1,1,"Config",fv,7)
                   config[0] = mode
                   config[1] = speed
                   config[2] = gain
                   config[3] = int(brightness)
                   config[4] = int(contrast)
                   config[5] = frame
                   config[6] = int(red)
                   config[7] = int(blue)
                   config[8] = ev
                   config[9] = vlen
                   config[10] = fps
                   config[11] = vformat
                   config[12] = codec
                   config[13] = tinterval
                   config[14] = tshots
                   config[15] = extn
                   config[16] = zx
                   config[17] = zy
                   config[18] = zoom
                   config[19] = int(saturation)
                   config[20] = meter
                   config[21] = awb
                   config[22] = sharpness
                   config[23] = int(denoise)
                   config[24] = quality
                   config[25] = profile
                   config[26] = level
                   config[27] = histogram
                   config[28] = histarea
                   config[29] = v3_f_speed
                   config[30] = v3_f_range
                   config[31] = rotate
                   with open(config_file, 'w') as f:
                       for item in config:
                           f.write("%s\n" % item)
                   time.sleep(1)
                   text(1,13,2,1,1,"Config",fv,7)
                else:
                   os.killpg(p.pid, signal.SIGTERM)
                   pygame.display.quit()
                   sys.exit()
    # RESTART         
    if restart > 0 and buttonx[0] == 0:
        os.killpg(p.pid, signal.SIGTERM)
        time.sleep(0.25)
        text(0,0,6,2,1,"Waiting for preview ...",int(fv*1.7),1)
        preview()
        
    #check for any mouse button presses
    for event in pygame.event.get():
        if event.type == QUIT:
            os.killpg(p.pid, signal.SIGTERM)
            pygame.quit()
        elif (event.type == MOUSEBUTTONUP):
            mousex, mousey = event.pos
            if mousex < preview_width and mousey < preview_height and rotate == 0 and event.button != 3:
                xx = mousex
                xx = min(xx,preview_width - histarea)
                xx = max(xx,histarea)
                xy = mousey
                if Pi_Cam == 3 and zoom < 5:
                    xy = min(xy,int(preview_height * .75) - histarea)
                else:
                    xy = min(xy,preview_height - histarea)
                xy = max(xy,histarea)
                if Pi_Cam == 3 and mousex < preview_width and mousey < preview_height *.75 and zoom == 0 and (v3_f_mode == 0 or v3_f_mode == 2):
                    fxx = (xx - 25)/preview_width
                    xy  = min(xy,int((preview_height - 25) * .75))
                    fxy = ((xy - 20) * 1.3333)/preview_height
                    fxz = 50/preview_width
                    fyz = fxz
                    if fxz != 1:
                        text(1,7,3,1,1,"Spot",fv,7)
                elif Pi_Cam == 3 and zoom == 0:
                    fxx = 0
                    fxy = 0
                    fxz = 1
                    fzy = 1
                    if (v3_f_mode == 0 or v3_f_mode == 2):
                        text(1,7,3,1,1,str(v3_f_modes[v3_f_mode]),fv,7)
                if Pi_Cam == 3 and zoom == 0:
                    restart = 1
                    
            # SWITCH CAMERA
            if mousex < preview_width and mousey < preview_height and event.button == 3:
                camera += 1
                if camera > max_camera:
                    camera = 0
                poll = p.poll()
                if poll == None:
                    os.killpg(p.pid, signal.SIGTERM)
                if same_cams == 0:
                    Camera_Version()
                    Menu()
                restart = 1
                
            if (sq_dis == 0 and mousex > preview_width) or (sq_dis == 1 and mousey > preview_height):
                if sq_dis == 0:
                    button_column = int((mousex-preview_width)/bw) + 1
                    button_row = int((mousey)/bh) + 1
                    if mousex > preview_width + bw + (bw/2):
                        button_pos = 2
                    elif mousex > preview_width + (bw/2):
                        button_pos = 1
                    else:
                        button_pos = 0
                else:
                    if mousey - preview_height < bh:
                        button_column = 1
                        button_row = int(mousex / bw) + 1
                        if mousex > ((button_row -1) * bw) + (bw/2):
                            button_pos = 1
                        else:
                            button_pos = 0
                    elif mousey - preview_height < bh * 2:
                        button_column = 1
                        button_row = int(mousex / bw) + 7
                        if mousex > ((button_row - 7) * bw) + (bw/2):
                            button_pos = 1
                        else:
                            button_pos = 0
                    elif mousey - preview_height < bh * 3:
                        button_column = 2
                        button_row = int(mousex / bw) + 1
                        if mousex > ((button_row -1) * bw) + (bw/2):
                            button_pos = 1
                        else:
                            button_pos = 0
                    elif mousey - preview_height < bh * 4:
                        button_column = 2
                        button_row = int(mousex / bw) + 8
                        if mousex > ((button_row - 8) * bw) + (bw/2):
                            button_pos = 1
                        else:
                            button_pos = 0
                y = button_row-1
                
                if button_column == 1:    
                    if button_row == 1 :
                        # TAKE STILL
                        os.killpg(p.pid, signal.SIGTERM)
                        button(0,0,1,4)
                        if os.path.exists("PiLibtext.txt"):
                             os.remove("PiLibtext.txt")
                        text(0,0,2,0,1,"CAPTURING",ft,0)
                        if Pi_Cam == 6 and mode == 0 and button_pos == 1:
                            text(0,0,2,1,1,"STILL    2x2",ft,0)
                        else:
                            text(0,0,2,1,1,"STILL",ft,0)
                        text(1,0,0,0,1,"CAPTURE",ft,7)
                        text(1,0,0,1,1,"Video",ft,7)
                        text(1,9,0,0,1,"CAPTURE",ft,7)
                        if Pi_Cam == 6 and mode == 0 and tinterval > 0:
                            text(1,9,0,1,1,"T'lapse  2x2",ft,7)
                        else:
                            text(1,9,0,1,1,"Timelapse",ft,7)
                        text(0,0,6,2,1,"Please Wait, taking still ...",int(fv*1.7),1)
                        now = datetime.datetime.now()
                        timestamp = now.strftime("%y%m%d%H%M%S")
                        if extns[extn] != 'raw':
                            fname =  pic_dir + str(timestamp) + '.' + extns2[extn]
                            rpistr = "rpicam-still --camera " + str(camera) + " -e " + extns[extn] + " -n -t 5000 -o " + fname
                        else:
                            fname =  pic_dir + str(timestamp) + '.' + extns2[extn]
                            rpistr = "rpicam-still --camera " + str(camera) + " -r -n -t 5000 -o " + fname
                            if preview_width == 640 and preview_height == 480 and zoom == 4:
                                rpistr += " --rawfull"
                        rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
                        if extns[extn] == "jpg" and preview_width == 640 and preview_height == 480 and zoom == 4:
                            rpistr += " -r --rawfull"
                        if mode == 0:
                            rpistr += " --shutter " + str(sspeed)
                        else:
                            rpistr += " --exposure " + str(modes[mode])
                        if ev != 0:
                            rpistr += " --ev " + str(ev)
                        if sspeed > 1000000 and mode == 0 and (Pi_Cam < 5 or Pi_Cam == 7):
                            rpistr += " --gain " + str(gain) + " --immediate --awbgains " + str(red/10) + "," + str(blue/10)
                        else:    
                            rpistr += " --gain " + str(gain)
                            if awb == 0:
                                rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
                            else:
                                rpistr += " --awb " + awbs[awb]
                        rpistr += " --metering " + meters[meter]
                        rpistr += " --saturation " + str(saturation/10)
                        rpistr += " --sharpness " + str(sharpness/10)
                        rpistr += " --quality " + str(quality)
                        rpistr += " --denoise " + denoises[denoise] # + " --width 2304 --height 1296"
                        if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and use_ard == 1:
                            rpistr += " --autofocus "
                        if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 1 and Pi == 5 and use_ard == 0:
                            if os.path.exists('/usr/share/libcamera/ipa/rpi/pisp/imx519mf.json'):
                                 rpistr += " --tuning-file /usr/share/libcamera/ipa/rpi/pisp/imx519mf.json"
                        if (Pi_Cam == 3 and v3_f_mode > 0 and fxx == 0) or ((Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and use_ard == 0):
                            rpistr += " --autofocus-mode " + v3_f_modes[v3_f_mode]
                            if v3_f_mode == 1:
                                rpistr += " --lens-position " + str(v3_focus/100)
                        elif Pi_Cam == 3 and v3_f_mode == 0 and fxz == 1:
                            rpistr += " --autofocus-mode " + v3_f_modes[v3_f_mode] + " --autofocus-on-capture"
                        elif Pi_Cam == 3 and zoom == 0:
                            rpistr += " --autofocus-window " + str(fxx) + "," + str(fxy) + "," + str(fxz) + "," + str(fxz)
                        if  v3_hdr == 1:
                            rpistr += " --hdr"
                        if Pi_Cam == 6 and mode == 0 and button_pos == 1:
                            rpistr += " --width 4624 --height 3472 " # 16MP superpixel mode for higher light sensitivity
                        elif Pi_Cam == 6:
                            rpistr += " --width 9152 --height 6944"
                        if zoom > 0 and zoom < 5:
                            zxo = ((igw-zws[(4-zoom) + ((Pi_Cam-1)* 4)])/2)/igw
                            zyo = ((igh-zhs[(4-zoom) + ((Pi_Cam-1)* 4)])/2)/igh
                            rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(zws[(4-zoom) + ((Pi_Cam-1)* 4)]/igw) + "," + str(zhs[(4-zoom) + ((Pi_Cam-1)* 4)]/igh)
                        if zoom == 5:
                            zxo = ((igw/2)-(preview_width/2))/igw
                            zyo = ((igh/2)-(preview_height/2))/igh
                            rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
                        rpistr += " --metadata - --metadata-format txt >> PiLibtext.txt"
                        #print(rpistr)
                        os.system(rpistr)

                        while not os.path.exists(fname):
                            pass
                        if extns2[extn] == 'jpg' or extns2[extn] == 'bmp' or extns2[extn] == 'png':
                            image = pygame.image.load(fname)
                            if rotate != 0:
                                image = pygame.transform.rotate(image, int(rotate * 90))
                                pygame.image.save(image,fname[:-4]+"r." + extns2[extn])
                            if Pi_Cam == 3 and zoom < 5:
                                if rotate == 0:
                                    image = pygame.transform.scale(image, (preview_width,int(preview_height * 0.75)))
                                else:
                                    if rotate != 2:
                                        igwr = image.get_width()
                                        ighr = image.get_height()
                                        image = pygame.transform.scale(image, (int(preview_height * (igwr/ighr)),preview_height))
                                    else:
                                        image = pygame.transform.scale(image, (preview_width,preview_height))
                            else:
                                if rotate == 0 or rotate == 2:
                                    image = pygame.transform.scale(image, (preview_width,preview_height))
                                else:
                                    if rotate != 2:
                                        igwr = image.get_width()
                                        ighr = image.get_height()
                                        image = pygame.transform.scale(image, (int(preview_height * (igwr/ighr)),preview_height))
                                    else:
                                        image = pygame.transform.scale(image, (preview_width,preview_height))
                            if rotate == 1 or rotate == 3:
                                windowSurfaceObj.blit(image, (int((preview_width/2) - ((preview_height * (igwr/ighr)))/2),0))
                            else:
                                windowSurfaceObj.blit(image, (0,0))
                        dgain = 0
                        again = 0
                        etime = 0
                        if os.path.exists("PiLibtext.txt"):
                          with open("PiLibtext.txt", "r") as file:
                            line = file.readline()
                            check = line.split("=")
                            if check[0] == "DigitalGain":
                                dgain = check[1][:-1]
                            if check[0] == "AnalogueGain":
                                again = check[1][:-1]
                            if check[0] == "ExposureTime":
                                etime = check[1][:-1]
                            while line:
                                line = file.readline()
                                check = line.split("=")
                                if check[0] == "DigitalGain":
                                    dgain = check[1][:-1]
                                if check[0] == "AnalogueGain":
                                    again = check[1][:-1]
                                if check[0] == "ExposureTime":
                                    etime = check[1][:-1]
                          text(0,25,6,2,1,"Ana Gain: " + str(again) + " Dig Gain: " + str(dgain) + " Exp Time: " + str(etime) +"uS",int(fv*1.5),1)
                        text(0,0,6,2,1,fname,int(fv*1.5),1)
                        pygame.display.update()
                        time.sleep(2)
                        if rotate != 0:
                            pygame.draw.rect(windowSurfaceObj,blackColor,Rect(0,0,preview_width,preview_height),0)
                        button(0,0,0,4)
                        text(0,0,1,0,1,"CAPTURE",ft,7)
                        text(1,0,1,0,1,"CAPTURE",ft,7)
                        text(1,0,1,1,1,"Video",ft,7)
                        if Pi_Cam == 6 and mode == 0:
                            text(0,0,1,1,1,"STILL    2x2",ft,7)
                        else:
                            text(0,0,1,1,1,"Still ",ft,7)
                        text(1,9,1,0,1,"CAPTURE",ft,7)
                        if Pi_Cam == 6 and mode == 0 and tinterval > 0:
                            text(1,9,1,1,1,"T'lapse  2x2",ft,7)
                        else:
                            text(1,9,1,1,1,"Timelapse",ft,7)
                        restart = 2
                        
                if button_column == 2:                       
                    if button_row == 1 and event.button != 3:
                        # TAKE VIDEO
                        os.killpg(p.pid, signal.SIGTERM)
                        button(1,0,1,3)
                        text(1,0,3,0,1,"STOP ",ft,0)
                        text(1,0,3,1,1,"Record",ft,0)
                        text(0,0,0,0,1,"CAPTURE",ft,7)
                        if Pi_Cam == 6 and mode == 0 and tinterval > 0:
                            text(0,0,0,1,1,"STILL    2x2",ft,7)
                        else:
                            text(0,0,0,1,1,"Still ",ft,7)
                        text(1,9,0,0,1,"CAPTURE",ft,7)
                        if Pi_Cam == 6 and mode == 0 and tinterval > 0:
                            text(1,9,0,1,1,"T'lapse  2x2",ft,7)
                        else:
                            text(1,9,0,1,1,"Timelapse",ft,7)
                        text(0,0,6,2,1,"Please Wait, taking video ...",int(fv*1.7),1)
                        now = datetime.datetime.now()
                        timestamp = now.strftime("%y%m%d%H%M%S")
                        vname =  vid_dir + str(timestamp) + "." + codecs2[codec]
                        if codecs2[codec] != 'raw':
                            rpistr = "rpicam-vid --camera " + str(camera) + " -t " + str(vlen * 1000) + " -o " + vname
                            if mode != 0:
                                rpistr += " --framerate " + str(fps)
                            else:
                                speed7 = sspeed
                                speed7 = max(speed7,int((1/fps)*1000000))
                                rpistr += " --framerate " + str(int((1/speed7)*1000000))
                            if codecs[codec] != 'h264' and codecs[codec] != 'mp4':
                                rpistr += " --codec " + codecs[codec]
                            else:
                                prof = h264profiles[profile].split(" ")
                                #rpistr += " --profile " + str(prof[0]) + " --level " + str(prof[1])
                                rpistr += " --level " + str(prof[1])
                        else:
                            rpistr = "rpicam-raw --camera " + str(camera) + " -t " + str(vlen * 1000) + " -o " + vname + " --framerate " + str(fps)
                        if vpreview == 0:
                            rpistr += " -n "
                        rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
                        if zoom > 0:
                            rpistr += " --width " + str(preview_width) + " --height " + str(preview_height)
                        elif Pi_Cam == 4 and vwidth == 2028:
                            rpistr += " --mode 2028:1520:12"
                        elif Pi_Cam == 3 and vwidth == 2304 and codec == 0:
                            rpistr += " --mode 2304:1296:10 --width 2304 --height 1296"
                        elif Pi_Cam == 3 and vwidth == 2028 and codec == 0:
                            rpistr += " --mode 2028:1520:10 --width 2028 --height 1520"
                        else:
                            rpistr += " --width " + str(vwidth) + " --height " + str(vheight)
                        if mode == 0:
                            rpistr += " --shutter " + str(sspeed)
                        else:
                            rpistr += " --exposure " + modes[mode]
                        rpistr += " --gain " + str(gain)
                        if ev != 0:
                            rpistr += " --ev " + str(ev)
                        if awb == 0:
                            rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
                        else:
                            rpistr += " --awb " + awbs[awb]
                        rpistr += " --metering " + meters[meter]
                        rpistr += " --saturation " + str(saturation/10)
                        rpistr += " --sharpness " + str(sharpness/10)
                        rpistr += " --denoise "    + denoises[denoise]

                        if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and use_ard == 1:
                            rpistr += " --autofocus "
                        if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 1 and Pi == 5 and use_ard == 0:
                            if os.path.exists('/usr/share/libcamera/ipa/rpi/pisp/imx519mf.json'):
                                rpistr += " --tuning-file /usr/share/libcamera/ipa/rpi/pisp/imx519mf.json"
                        if (Pi_Cam == 3 and v3_f_mode > 0 and fxx == 0) or ((Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and use_ard == 0):
                            rpistr += " --autofocus-mode " + v3_f_modes[v3_f_mode]
                            if v3_f_mode == 1:
                                rpistr += " --lens-position " + str(v3_focus/100)
                        elif Pi_Cam == 3 and zoom == 0 and fxx != 0 and v3_f_mode != 1:
                            rpistr += " --autofocus-window " + str(fxx) + "," + str(fxy) + "," + str(fxz) + "," + str(fxz)
                        if Pi_Cam == 3 and v3_f_speed != 0:
                            rpistr += " --autofocus-speed " + v3_f_speeds[v3_f_speed]
                        if Pi_Cam == 3 and v3_f_range != 0:
                            rpistr += " --autofocus-range " + v3_f_ranges[v3_f_range]
                        if Pi_Cam == 3 and v3_hdr == 1:
                            rpistr += " --hdr"
                        rpistr += " -p 0,0," + str(preview_width) + "," + str(preview_height)
                        if zoom > 0 and zoom < 5:
                            zxo = ((1920-zwidths[4 - zoom])/2)/1920
                            zyo = ((1440-zheights[4 - zoom])/2)/1440
                            rpistr += " --mode 1920:1440:10  --roi " + str(zxo) + "," + str(zyo) + "," + str(zwidths[4 - zoom]/1920) + "," + str(zheights[4 - zoom]/1440)
                        if zoom == 5:
                            zxo = ((igw/2)-(preview_width/2))/igw
                            zyo = ((igh/2)-(preview_height/2))/igh
                            rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)                            
                        #print (rpistr)
                        p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
                        start_video = time.monotonic()
                        stop = 0
                        while (time.monotonic() - start_video < vlen or vlen == 0) and stop == 0:
                            if vlen != 0:
                                vlength = int(vlen - (time.monotonic()-start_video))
                            else:
                                vlength = int(time.monotonic()-start_video)
                            td = timedelta(seconds=vlength)
                            text(1,1,1,1,1,str(td),fv,11)
                            for event in pygame.event.get():
                                if (event.type == MOUSEBUTTONUP):
                                    mousex, mousey = event.pos
                                    # stop video recording
                                    if mousex > preview_width:
                                        button_column = int((mousex-preview_width)/bw) + 1
                                        button_row = int((mousey)/bh) + 1
                                        if mousex > preview_width + bw + (bw/2):
                                            button_pos = 1
                                        else:
                                            button_pos = 0
                                    else:
                                        if mousey - preview_height < bh:
                                            button_column = 1
                                            button_row = int(mousex / bw) + 1
                                        elif mousey - preview_height < bh * 2:
                                            button_column = 1
                                            button_row = int(mousex / bw) + 7
                                        elif mousey - preview_height < bh * 3:
                                            button_column = 2
                                            button_row = int(mousex / bw) + 1
                                        elif mousey - preview_height < bh * 4:
                                            button_column = 2
                                            button_row = int(mousex / bw) + 7
                                    if button_column == 2 and button_row == 1:
                                       os.killpg(p.pid, signal.SIGTERM)
                                       stop = 1
                        text(0,0,6,2,1,vname,int(fv*1.5),1)
                        time.sleep(1)
                        td = timedelta(seconds=vlen)
                        if rotate != 0:
                            pygame.draw.rect(windowSurfaceObj,blackColor,Rect(0,0,preview_width,preview_height),0)
                        text(1,1,3,1,1,str(td),fv,11)
                        button(1,0,0,3)
                        text(0,0,1,0,1,"CAPTURE",ft,7)
                        if Pi_Cam == 5 and mode == 0:
                            text(0,0,1,1,1,"STILL    2x2",ft,7)
                        else:
                            text(0,0,1,1,1,"Still ",ft,7)
                        text(1,0,1,0,1,"CAPTURE",ft,7)
                        text(1,0,1,1,1,"Video",ft,7)
                        text(1,9,1,0,1,"CAPTURE",ft,7)
                        if Pi_Cam == 5 and mode == 0 and tinterval > 0:
                            text(1,9,1,1,1,"T'lapse  2x2",ft,7)
                        else:
                            text(1,9,1,1,1,"Timelapse",ft,7)
                        restart = 2
                                       
                    elif button_row == 1 and event.button == 3:
                        # STREAM VIDEO
                        os.killpg(p.pid, signal.SIGTERM)
                        button(1,0,1,3)
                        text(1,0,3,0,1,"STOP ",ft,0)
                        text(1,0,3,1,1,"STREAM",ft,0)
                        text(0,0,0,0,1,"CAPTURE",ft,7)
                        if Pi_Cam == 6 and mode == 0 and tinterval > 0:
                            text(0,0,0,1,1,"STILL    2x2",ft,7)
                        else:
                            text(0,0,0,1,1,"Still ",ft,7)
                        text(1,9,0,0,1,"CAPTURE",ft,7)
                        if Pi_Cam == 6 and mode == 0 and tinterval > 0:
                            text(1,9,0,1,1,"T'lapse  2x2",ft,7)
                        else:
                            text(1,9,0,1,1,"Timelapse",ft,7)
                        text(0,0,6,2,1,"Streaming Video ...",int(fv*1.7),1)
                        now = datetime.datetime.now()
                        timestamp = now.strftime("%y%m%d%H%M%S")
                        vname =  vid_dir + str(timestamp) + "." + codecs2[codec]
                        rpistr = "rpicam-vid --camera " + str(camera) + " -t " + str(vlen * 1000) + " --inline --listen -o tcp://0.0.0.0:" + str(stream_port)
                        if mode != 0:
                            rpistr += " --framerate " + str(fps)
                        else:
                            speed7 = sspeed
                            speed7 = max(speed7,int((1/fps)*1000000))
                            rpistr += " --framerate " + str(int((1/speed7)*1000000))
                        prof = h264profiles[profile].split(" ")
                        #rpistr += " --profile " + str(prof[0]) + " --level " + str(prof[1])
                        rpistr += " --level " + str(prof[1])
                        if vpreview == 0:
                            rpistr += " -n "
                        rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
                        if zoom > 0:
                            rpistr += " --width " + str(preview_width) + " --height " + str(preview_height)
                        elif Pi_Cam == 4 and vwidth == 2028:
                            rpistr += " --mode 2028:1520:12"
                        elif Pi_Cam == 3 and vwidth == 2304 and codec == 0:
                            rpistr += " --mode 2304:1296:10 --width 2304 --height 1296"
                        elif Pi_Cam == 3 and vwidth == 2028 and codec == 0:
                            rpistr += " --mode 2028:1520:10 --width 2028 --height 1520"
                        else:
                            rpistr += " --width " + str(vwidth) + " --height " + str(vheight)
                        if mode == 0:
                            rpistr += " --shutter " + str(sspeed)
                        else:
                            rpistr += " --exposure " + modes[mode]
                        rpistr += " --gain " + str(gain)
                        if ev != 0:
                            rpistr += " --ev " + str(ev)
                        if awb == 0:
                            rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
                        else:
                            rpistr += " --awb " + awbs[awb]
                        rpistr += " --metering " + meters[meter]
                        rpistr += " --saturation " + str(saturation/10)
                        rpistr += " --sharpness " + str(sharpness/10)
                        rpistr += " --denoise "    + denoises[denoise]
                        if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and use_ard == 1:
                            rpistr += " --autofocus "
                        if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 1 and Pi == 5 and use_ard == 0:
                            if os.path.exists('/usr/share/libcamera/ipa/rpi/pisp/imx519mf.json'):
                                rpistr += " --tuning-file /usr/share/libcamera/ipa/rpi/pisp/imx519mf.json"
                        if (Pi_Cam == 3 and v3_f_mode > 0 and fxx == 0) or ((Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and use_ard == 0):
                            rpistr += " --autofocus-mode " + v3_f_modes[v3_f_mode]
                            if v3_f_mode == 1:
                                rpistr += " --lens-position " + str(v3_focus/100)
                        elif Pi_Cam == 3 and zoom == 0 and fxx != 0 and v3_f_mode != 1:
                            rpistr += " --autofocus-window " + str(fxx) + "," + str(fxy) + "," + str(fxz) + "," + str(fxz)
                        if Pi_Cam == 3 and v3_f_speed != 0:
                            rpistr += " --autofocus-speed " + v3_f_speeds[v3_f_speed]
                        if Pi_Cam == 3 and v3_f_range != 0:
                            rpistr += " --autofocus-range " + v3_f_ranges[v3_f_range]
                        if Pi_Cam == 3 and v3_hdr == 1:
                            rpistr += " --hdr"
                        rpistr += " -p 0,0," + str(preview_width) + "," + str(preview_height)
                        if zoom > 0 and zoom < 5:
                            zxo = ((1920-zwidths[4 - zoom])/2)/1920
                            zyo = ((1440-zheights[4 - zoom])/2)/1440
                            rpistr += " --mode 1920:1440:10  --roi " + str(zxo) + "," + str(zyo) + "," + str(zwidths[4 - zoom]/1920) + "," + str(zheights[4 - zoom]/1440)
                        if zoom == 5:
                            zxo = ((igw/2)-(preview_width/2))/igw
                            zyo = ((igh/2)-(preview_height/2))/igh
                            rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)                            
                        #print (rpistr)
                        p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
                        start_video = time.monotonic()
                        stop = 0
                        while (time.monotonic() - start_video < vlen or vlen == 0) and stop == 0:
                            if vlen != 0:
                                vlength = int(vlen - (time.monotonic()-start_video))
                            else:
                                vlength = int(time.monotonic()-start_video)
                            td = timedelta(seconds=vlength)
                            text(1,1,1,1,1,str(td),fv,11)
                            for event in pygame.event.get():
                                if (event.type == MOUSEBUTTONUP):
                                    mousex, mousey = event.pos
                                    # stop video streaming
                                    if mousex > preview_width:
                                        button_column = int((mousex-preview_width)/bw) + 1
                                        button_row = int((mousey)/bh) + 1
                                        if mousex > preview_width + bw + (bw/2):
                                            button_pos = 1
                                        else:
                                            button_pos = 0
                                    else:
                                        if mousey - preview_height < bh:
                                            button_column = 1
                                            button_row = int(mousex / bw) + 1
                                        elif mousey - preview_height < bh * 2:
                                            button_column = 1
                                            button_row = int(mousex / bw) + 7
                                        elif mousey - preview_height < bh * 3:
                                            button_column = 2
                                            button_row = int(mousex / bw) + 1
                                        elif mousey - preview_height < bh * 4:
                                            button_column = 2
                                            button_row = int(mousex / bw) + 7
                                    if button_column == 2 and button_row == 1:
                                       os.killpg(p.pid, signal.SIGTERM)
                                       stop = 1
                        td = timedelta(seconds=vlen)
                        if rotate != 0:
                            pygame.draw.rect(windowSurfaceObj,blackColor,Rect(0,0,preview_width,preview_height),0)
                        text(1,1,3,1,1,str(td),fv,11)
                        button(1,0,0,3)
                        text(0,0,1,0,1,"CAPTURE",ft,7)
                        if Pi_Cam == 5 and mode == 0:
                            text(0,0,1,1,1,"STILL    2x2",ft,7)
                        else:
                            text(0,0,1,1,1,"Still ",ft,7)
                        text(1,0,1,0,1,"CAPTURE",ft,7)
                        text(1,0,1,1,1,"Video",ft,7)
                        text(1,9,1,0,1,"CAPTURE",ft,7)
                        if Pi_Cam == 5 and mode == 0 and tinterval > 0:
                            text(1,9,1,1,1,"T'lapse  2x2",ft,7)
                        else:
                            text(1,9,1,1,1,"Timelapse",ft,7)
                        restart = 2
                        
                    elif button_row == 10:
                        # TAKE TIMELAPSE
                        os.killpg(p.pid, signal.SIGTERM)
                        button(1,9,1,2)
                        text(1,9,3,0,1,"STOP",ft,0)
                        text(1,9,3,1,1,"Timelapse",ft,0)
                        text(0,0,0,0,1,"CAPTURE",ft,7)
                        text(1,0,0,0,1,"CAPTURE",ft,7)
                        text(1,0,0,1,1,"Video",ft,7)
                        if Pi_Cam == 5 and mode == 0:
                            text(0,0,0,1,1,"STILL    2x2",ft,7)
                        else:
                            text(0,0,0,1,1,"Still ",ft,7)
                        tcount = 0
                        
                        if tinterval > 0 and mode != 0:
                            text(1,9,3,0,1,"STOP",ft,0)
                            text(1,9,3,1,1,"Timelapse",ft,0)
                            text(0,0,6,2,1,"Please Wait, taking Timelapse ...",int(fv*1.7),1)
                            now = datetime.datetime.now()
                            timestamp = now.strftime("%y%m%d%H%M%S")
                            count = 0
                            fname =  pic_dir + str(timestamp) + '_%04d.' + extns2[extn]
                            if extns[extn] != 'raw':
                                rpistr = "rpicam-still --camera " + str(camera) + " -e " + extns[extn] + " -s -n -t 0 -o " + fname
                            else:
                                rpistr = "rpicam-still --camera " + str(camera) + " -r -s -n -t 0 -o " + fname 
                                if preview_width == 640 and preview_height == 480 and zoom >= 4:
                                    rpistr += " --rawfull"
                            rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
                            if extns[extn] == "jpg" and preview_width == 640 and preview_height == 480 and zoom >= 4:
                                rpistr += " -r --rawfull"
                            if mode == 0:
                                rpistr += " --shutter " + str(sspeed)
                            else:
                                rpistr += " --exposure " + modes[mode]
                            if ev != 0:
                                rpistr += " --ev " + str(ev)
                            if sspeed > 1000000 and mode == 0 and (Pi_Cam < 5 or Pi_Cam == 7):
                                rpistr += " --gain " + str(gain) + " --immediate --awbgains " + str(red/10) + "," + str(blue/10)
                            else:
                                rpistr += " --gain " + str(gain)
                                if awb == 0:
                                    rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
                                else:
                                    rpistr += " --awb " + awbs[awb]
                            rpistr += " --metering " + meters[meter]
                            rpistr += " --saturation " + str(saturation/10)
                            rpistr += " --sharpness " + str(sharpness/10)
                            rpistr += " --quality " + str(quality)
                            rpistr += " --denoise "    + denoises[denoise]
                            if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and use_ard == 1:
                                rpistr += " --autofocus "
                            if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 1 and Pi == 5 and use_ard == 0:
                                if os.path.exists('/usr/share/libcamera/ipa/rpi/pisp/imx519mf.json'):
                                    rpistr += " --tuning-file /usr/share/libcamera/ipa/rpi/pisp/imx519mf.json"
                            if (Pi_Cam == 3 and v3_f_mode > 0 and fxx == 0) or ((Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and use_ard == 0):
                                rpistr += " --autofocus-mode " + v3_f_modes[v3_f_mode]
                                if v3_f_mode == 1:
                                    rpistr += " --lens-position " + str(v3_focus/100)
                            elif Pi_Cam == 3 and v3_f_mode == 0 and fxz == 1:
                                rpistr += " --autofocus-mode " + v3_f_modes[v3_f_mode] + " --autofocus-on-capture"
                            elif Pi_Cam == 3 and zoom == 0:
                                rpistr += " --autofocus-window " + str(fxx) + "," + str(fxy) + "," + str(fxz) + "," + str(fxz)
                            if  v3_hdr == 1:
                                rpistr += " --hdr"
                            if Pi_Cam == 6 and mode == 0 and button_pos == 2:
                                rpistr += " --width 4624 --height 3472 " # 16MP superpixel mode for higher light sensitivity
                            elif Pi_Cam == 6:
                                rpistr += " --width 9152 --height 6944"
                            if zoom > 0 and zoom < 5:
                                zxo = ((igw-zws[(4-zoom) + ((Pi_Cam-1)* 4)])/2)/igw
                                zyo = ((igh-zhs[(4-zoom) + ((Pi_Cam-1)* 4)])/2)/igh
                                rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(zws[(4-zoom) + ((Pi_Cam-1)* 4)]/igw) + "," + str(zhs[(4-zoom) + ((Pi_Cam-1)* 4)]/igh)
                            if zoom == 5:
                                zxo = ((igw/2)-(preview_width/2))/igw
                                zyo = ((igh/2)-(preview_height/2))/igh
                                rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
                            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
                            #print (rpistr)
                            start_timelapse = time.monotonic()
                            start2 = time.monotonic()
                            stop = 0
                            pics3 = []
                            count = 0
                            old_count = 0
                            while count < tshots and stop == 0:
                                if time.monotonic() - start2 >= tinterval:
                                    os.system('pkill -SIGUSR1 rpicam-still')
                                    start2 = time.monotonic()
                                    text(0,0,6,2,1,"Please Wait, taking Timelapse ..."  + " " + str(count+1),int(fv*1.7),1)
                                    show = 0
                                    while count == old_count:
                                        time.sleep(0.1)
                                        pics3 = glob.glob(pic_dir + "*.*")
                                        counts = []
                                        for xu in range(0,len(pics3)):
                                            ww = pics3[xu].split("/")
                                            if ww[4][0:12] == timestamp:
                                                counts.append(pics3[xu])
                                        count = len(counts)
                                        counts.sort()
                                        for event in pygame.event.get():
                                            if (event.type == MOUSEBUTTONUP):
                                                mousex, mousey = event.pos
                                                # stop timelapse
                                                if mousex > preview_width:
                                                    button_column = int((mousex-preview_width)/bw) + 1
                                                    button_row = int((mousey)/bh) + 1
                                                else:
                                                    if mousey - preview_height < bh:
                                                        button_column = 1
                                                        button_row = int(mousex / bw) + 1
                                                    elif mousey - preview_height < bh * 2:
                                                        button_column = 1
                                                        button_row = int(mousex / bw) + 7
                                                    elif mousey - preview_height < bh * 3:
                                                        button_column = 2
                                                        button_row = int(mousex / bw) + 1
                                                    elif mousey - preview_height < bh * 4:
                                                        button_column = 2
                                                        button_row = int(mousex / bw) + 8
                                                if button_column == 2 and button_row == 10:
                                                    os.killpg(p.pid, signal.SIGTERM)
                                                    text(1,12,3,1,1,str(tshots),fv,12)
                                                    stop = 1
                                                    count = tshots
                                        
                                    old_count = count
                                    text(1,12,1,1,1,str(tshots - count),fv,12)
                                    tdur = tinterval * (tshots - count)
                                    td = timedelta(seconds=tdur)
                                    text(1,10,1,1,1,str(td),fv,12)
                                time.sleep(0.1)
                                for event in pygame.event.get():
                                    if (event.type == MOUSEBUTTONUP):
                                        mousex, mousey = event.pos
                                        # stop timelapse
                                        if mousex > preview_width:
                                            button_column = int((mousex-preview_width)/bw) + 1
                                            button_row = int((mousey)/bh) + 1
                                        else:
                                            if mousey - preview_height < bh:
                                                button_column = 1
                                                button_row = int(mousex / bw) + 1
                                            elif mousey - preview_height < bh * 2:
                                                button_column = 1
                                                button_row = int(mousex / bw) + 7
                                            elif mousey - preview_height < bh * 3:
                                                button_column = 2
                                                button_row = int(mousex / bw) + 1
                                            elif mousey - preview_height < bh * 4:
                                                button_column = 2
                                                button_row = int(mousex / bw) + 8
                                        if button_column == 2 and button_row == 10:
                                            os.killpg(p.pid, signal.SIGTERM)
                                            text(1,12,3,1,1,str(tshots),fv,12)
                                            stop = 1
                                            count = tshots

                        elif tinterval > 0 and mode == 0:
                            text(1,9,3,0,1,"STOP",ft,0)
                            text(1,9,3,1,1,"Timelapse",ft,0)
                            text(0,0,6,2,1,"Please Wait, taking Timelapse ...",int(fv*1.7),1)
                            now = datetime.datetime.now()
                            timestamp = now.strftime("%y%m%d%H%M%S")
                            start2 = time.monotonic()
                            stop = 0
                            pics3 = []
                            count = 0
                            old_count = 0
                            while count < tshots and stop == 0:
                                if time.monotonic() - start2 > tinterval:
                                    start2 = time.monotonic()
                                    poll = p.poll()
                                    while poll == None:
                                        poll = p.poll()
                                        time.sleep(0.1)
                                    fname =  pic_dir + str(timestamp) + "_" + str(count) + "." + extns2[extn]
                                    if extns[extn] != 'raw':
                                        rpistr = "rpicam-still --camera " + str(camera) + " -e " + extns[extn] + " -n -t 1000 -o " + fname
                                    else:
                                        rpistr = "rpicam-still --camera " + str(camera) + " -r -n -t 1000 -o " + fname 
                                        if preview_width == 640 and preview_height == 480 and zoom >= 4:
                                            rpistr += " --rawfull"
                                    rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
                                    if extns[extn] == "jpg" and preview_width == 640 and preview_height == 480 and zoom >= 4:
                                        rpistr += " -r --rawfull"
                                    rpistr += " --shutter " + str(sspeed)
                                    if ev != 0:
                                        rpistr += " --ev " + str(ev)
                                    if sspeed > 1000000 and mode == 0 and (Pi_Cam < 5 or Pi_Cam == 7):
                                        rpistr += " --gain " + str(gain) + " --immediate --awbgains " + str(red/10) + "," + str(blue/10)
                                    else:
                                        rpistr += " --gain " + str(gain)
                                        if awb == 0:
                                            rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
                                        else:
                                            rpistr += " --awb " + awbs[awb]
                                    rpistr += " --metering " + meters[meter]
                                    rpistr += " --saturation " + str(saturation/10)
                                    rpistr += " --sharpness " + str(sharpness/10)
                                    rpistr += " --quality " + str(quality)
                                    rpistr += " --denoise "    + denoises[denoise]
                                    if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and use_ard == 1:
                                        rpistr += " --autofocus "
                                    if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 1 and Pi == 5 and use_ard == 0:
                                        if os.path.exists('/usr/share/libcamera/ipa/rpi/pisp/imx519mf.json'):
                                            rpistr += " --tuning-file /usr/share/libcamera/ipa/rpi/pisp/imx519mf.json"
                                    if (Pi_Cam == 3 and v3_f_mode > 0 and fxx == 0) or ((Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and use_ard == 0):
                                        rpistr += " --autofocus-mode " + v3_f_modes[v3_f_mode]
                                        if v3_f_mode == 1:
                                            rpistr += " --lens-position " + str(v3_focus/100)
                                    elif Pi_Cam == 3 and v3_f_mode == 0 and fxz == 1:
                                        rpistr += " --autofocus-mode " + v3_f_modes[v3_f_mode] + " --autofocus-on-capture"
                                    elif Pi_Cam == 3 and zoom == 0:
                                        rpistr += " --autofocus-window " + str(fxx) + "," + str(fxy) + "," + str(fxz) + "," + str(fxz)
                                    if  v3_hdr == 1:
                                        rpistr += " --hdr"
                                    if Pi_Cam == 6 and mode == 0 and button_pos == 2:
                                        rpistr += " --width 4624 --height 3472 " # 16MP superpixel mode for higher light sensitivity
                                    elif Pi_Cam == 6:
                                        rpistr += " --width 9152 --height 6944"
                                    if zoom > 0 and zoom < 5:
                                        zxo = ((igw-zws[(4-zoom) + ((Pi_Cam-1)* 4)])/2)/igw
                                        zyo = ((igh-zhs[(4-zoom) + ((Pi_Cam-1)* 4)])/2)/igh
                                        rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(zws[(4-zoom) + ((Pi_Cam-1)* 4)]/igw) + "," + str(zhs[(4-zoom) + ((Pi_Cam-1)* 4)]/igh)
                                    if zoom == 5:
                                        zxo = ((igw/2)-(preview_width/2))/igw
                                        zyo = ((igh/2)-(preview_height/2))/igh
                                        rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
                                    #print(rpistr)
                                    p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
                                    text(0,0,6,2,1,"Please Wait, taking Timelapse ..."  + " " + str(count+1),int(fv*1.7),1)
                                    show = 0
                                    while count == old_count:
                                        time.sleep(0.1)
                                        pics3 = glob.glob(pic_dir + "*.*")
                                        counts = []
                                        for xu in range(0,len(pics3)):
                                            ww = pics3[xu].split("/")
                                            if ww[4][0:12] == timestamp:
                                                counts.append(pics3[xu])
                                        count = len(counts)
                                        counts.sort()
                                        if (extns2[extn] == 'jpg' or extns2[extn] == 'bmp' or extns2[extn] == 'png') and count > 0 and show == 0:
                                            image = pygame.image.load(counts[count-1])
                                            if (Pi_Cam != 3) or (Pi_Cam == 3 and zoom == 5):
                                                catSurfacesmall = pygame.transform.scale(image, (preview_width,preview_height))
                                            else:
                                                catSurfacesmall = pygame.transform.scale(image, (preview_width,int(preview_height * 0.75)))
                                            windowSurfaceObj.blit(catSurfacesmall, (0, 0))
                                            text(0,0,6,2,1,counts[count-1],int(fv*1.5),1)
                                            pygame.display.update()
                                            show == 1
                                        for event in pygame.event.get():
                                            if (event.type == MOUSEBUTTONUP):
                                                mousex, mousey = event.pos
                                                # stop timelapse
                                                if mousex > preview_width:
                                                    button_column = int((mousex-preview_width)/bw) + 1
                                                    button_row = int((mousey)/bh) + 1
                                                else:
                                                    if mousey - preview_height < bh:
                                                        button_column = 1
                                                        button_row = int(mousex / bw) + 1
                                                    elif mousey - preview_height < bh * 2:
                                                        button_column = 1
                                                        button_row = int(mousex / bw) + 7
                                                    elif mousey - preview_height < bh * 3:
                                                        button_column = 2
                                                        button_row = int(mousex / bw) + 1
                                                    elif mousey - preview_height < bh * 4:
                                                        button_column = 2
                                                        button_row = int(mousex / bw) + 8
                                                if button_column == 2 and button_row == 10:
                                                    os.killpg(p.pid, signal.SIGTERM)
                                                    text(1,12,3,1,1,str(tshots),fv,12)
                                                    stop = 1
                                                    count = tshots
                                        
                                    old_count = count
                                    text(1,12,1,1,1,str(tshots - count),fv,12)
                                    tdur = tinterval * (tshots - count)
                                    td = timedelta(seconds=tdur)
                                    text(1,10,1,1,1,str(td),fv,12)
                                time.sleep(0.1)
                                for event in pygame.event.get():
                                    if (event.type == MOUSEBUTTONUP):
                                        mousex, mousey = event.pos
                                        # stop timelapse
                                        if mousex > preview_width:
                                            button_column = int((mousex-preview_width)/bw) + 1
                                            button_row = int((mousey)/bh) + 1
                                        else:
                                            if mousey - preview_height < bh:
                                                button_column = 1
                                                button_row = int(mousex / bw) + 1
                                            elif mousey - preview_height < bh * 2:
                                                button_column = 1
                                                button_row = int(mousex / bw) + 7
                                            elif mousey - preview_height < bh * 3:
                                                button_column = 2
                                                button_row = int(mousex / bw) + 1
                                            elif mousey - preview_height < bh * 4:
                                                button_column = 2
                                                button_row = int(mousex / bw) + 8
                                        if button_column == 2 and button_row == 10:
                                            os.killpg(p.pid, signal.SIGTERM)
                                            text(1,12,3,1,1,str(tshots),fv,12)
                                            stop = 1
                                            count = tshots


                        elif tinterval == 0:
                            if tduration == 0:
                                tduration = 1
                            text(0,0,6,2,1,"Please Wait, taking Timelapse ...",int(fv*1.7),1)
                            now = datetime.datetime.now()
                            timestamp = now.strftime("%y%m%d%H%M%S")
                            fname =  pic_dir + str(timestamp) + '_%04d.' + extns2[extn]
                            if codecs2[codec] != 'raw':
                                rpistr = "rpicam-vid --camera " + str(camera) + " -n --codec mjpeg -t " + str(tduration*1000) + " --segment 1 -o " + fname
                            else:
                                fname =  pic_dir + str(timestamp) + '_%04d.' + codecs2[codec]
                                rpistr = "rpicam-raw --camera " + str(camera) + " -n -t " + str(tduration*1000) + " --segment 1 -o " + fname  
                            if zoom > 0:
                                rpistr += " --width " + str(preview_width) + " --height " + str(preview_height)
                            else:
                                rpistr += " --width " + str(vwidth) + " --height " + str(vheight)
                            rpistr += " --brightness " + str(brightness/100) + " --contrast " + str(contrast/100)
                            if mode == 0:
                                rpistr += " --shutter " + str(sspeed) + " --framerate " + str(1000000/sspeed)
                            else:
                                rpistr += " --exposure " + str(modes[mode]) + " --framerate " + str(fps)
                            if ev != 0:
                                rpistr += " --ev " + str(ev)
                            if sspeed > 5000000 and mode == 0 and (Pi_Cam < 5 or Pi_Cam == 7):
                                rpistr += " --gain 1 --immediate --awbgains " + str(red/10) + "," + str(blue/10)
                            else:
                                rpistr += " --gain " + str(gain)
                                if awb == 0:
                                    rpistr += " --awbgains " + str(red/10) + "," + str(blue/10)
                                else:
                                    rpistr += " --awb " + awbs[awb]
                            rpistr += " --metering "   + meters[meter]
                            rpistr += " --saturation " + str(saturation/10)
                            rpistr += " --sharpness "  + str(sharpness/10)
                            rpistr += " --denoise "    + denoises[denoise]
                            if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and use_ard == 1:
                                rpistr += " --autofocus " 
                            if (Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 1 and Pi == 5 and use_ard == 0:
                                if os.path.exists('/usr/share/libcamera/ipa/rpi/pisp/imx519mf.json'):
                                    rpistr += " --tuning-file /usr/share/libcamera/ipa/rpi/pisp/imx519mf.json"
                            if (Pi_Cam == 3 and v3_f_mode > 0 and fxx == 0) or ((Pi_Cam == 5 or Pi_Cam == 6) and foc_man == 0 and use_ard == 0):
                                rpistr += " --autofocus-mode " + v3_f_modes[v3_f_mode]
                                if v3_f_mode == 1:
                                    rpistr += " --lens-position " + str(v3_focus/100)
                            elif Pi_Cam == 3 and zoom == 0:
                                rpistr += " --autofocus-window " + str(fxx) + "," + str(fxy) + "," + str(fxz) + "," + str(fxz)
                            if Pi_Cam == 3 and v3_hdr == 1:
                                rpistr += " --hdr"
                            if zoom > 0 and zoom < 5 :
                                zxo = ((igw-zws[(4-zoom) + ((Pi_Cam-1)* 4)])/2)/igw
                                zyo = ((igh-zhs[(4-zoom) + ((Pi_Cam-1)* 4)])/2)/igh
                                rpistr += " --mode 1920:1440:10 --roi " + str(zxo) + "," + str(zyo) + "," + str(zws[(4-zoom) + ((Pi_Cam-1)* 4)]/igw) + "," + str(zhs[(4-zoom) + ((Pi_Cam-1)* 4)]/igh)
                            if zoom == 5:
                                zxo = ((igw/2)-(preview_width/2))/igw
                                zyo = ((igh/2)-(preview_height/2))/igh
                                rpistr += " --roi " + str(zxo) + "," + str(zyo) + "," + str(preview_width/igw) + "," + str(preview_height/igh)
                            #print (rpistr)
                            p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
                            start_timelapse = time.monotonic()
                            stop = 0
                            while time.monotonic() - start_timelapse < tduration+1 and stop == 0:
                                tdur = int(tduration - (time.monotonic() - start_timelapse))
                                td = timedelta(seconds=tdur)
                                text(1,10,1,1,1,str(td),fv,12)
                                for event in pygame.event.get():
                                    if (event.type == MOUSEBUTTONUP):
                                        mousex, mousey = event.pos
                                        # stop timelapse
                                        if mousex > preview_width:
                                            button_column = int((mousex-preview_width)/bw) + 1
                                            button_row = int((mousey)/bh) + 1
                                        else:
                                            if mousey - preview_height < bh:
                                                button_column = 1
                                                button_row = int(mousex / bw) + 1
                                            elif mousey - preview_height < bh * 2:
                                                button_column = 1
                                                button_row = int(mousex / bw) + 7
                                            elif mousey - preview_height < bh * 3:
                                                button_column = 2
                                                button_row = int(mousex / bw) + 1
                                            elif mousey - preview_height < bh * 4:
                                                button_column = 2
                                                button_row = int(mousex / bw) + 7
                                        if button_column == 2 and button_row == 10:
                                            os.killpg(p.pid, signal.SIGTERM)
                                            stop = 1
                        button(1,9,0,2)
                        if tinterval != 0:
                            text(1,12,3,1,1,str(tshots),fv,12)
                        if rotate != 0:
                            pygame.draw.rect(windowSurfaceObj,blackColor,Rect(0,0,preview_width,preview_height),0)
                        td = timedelta(seconds=tduration)
                        text(1,10,3,1,1,str(td),fv,12)
                        text(0,0,1,0,1,"CAPTURE",ft,7)
                        text(1,0,1,0,1,"CAPTURE",ft,7)
                        text(1,0,1,1,1,"Video",ft,7)
                        if Pi_Cam == 6 and mode == 0:
                            text(0,0,1,1,1,"STILL    2x2",ft,7)
                        else:
                            text(0,0,1,1,1,"Still ",ft,7)
                        text(1,9,1,0,1,"CAPTURE",ft,7)
                        if Pi_Cam == 6 and mode == 0 and tinterval > 0:
                            text(1,9,1,1,1,"T'lapse  2x2",ft,7)
                        else:
                            text(1,9,1,1,1,"Timelapse",ft,7)
                        restart = 2
        # RESTART
        if restart > 0:
            poll = p.poll()
            if poll == None:
                os.killpg(p.pid, signal.SIGTERM)
            if rotate == 0:
                text(0,0,6,2,1,"Waiting for preview ...",int(fv*1.7),1)
            preview()






                      


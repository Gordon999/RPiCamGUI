# RPiCamGUI

To work with RaspiOS based on BULLSEYE / BOOKWORM, using libcamera (NOT raspistill/raspivid).

preview uses rpicam-vid (so may not be as sharp as captured stills), stills rpicam-still, videos rpicam-vid, timelapses depends on timings and settings, rpicam-still, -vid or -raw. Note preview has a maximum shutter setting of 1 second.

At your own risk !!. Ensure you have any required software backed up.

Script to allow control of a Pi Camera. Will work with all Pi camera models, v1, v2, v3, HQ and GS. Also Arducam 16MP and 64MP Autofocus. 

(Note You can use an Arducam 16/64MP camera with the default Pi Rpicam-apps... remember to add dtoverlay=imx519 to /boot/config.txt (see below for a Pi5))

(To make an Arducam 16/64MP work on a Pi5...make a copy of usr/share/libcamera/ipa/rpi/pisp/imx219.json and rename it usr/share/libcamera/ipa/rpi/pisp/imx519.json
in /boot/firmware/config.txt #camera_auto_detect=1, and add dtoverlay=imx519,cam0 or dtoverlay=imx519,cam1 as appropriate. If you have a 2nd camera add a dtoverlay for that as well.)

It will work with different models of cameras.

## Screenshot

![screenshot](screenshot.jpg)

With Pi V3 or Arducam 16/64MP Click on FOCUS button to focus. This will show manual which gives Manual Focusing, then click on 'slider' or the middle of the button, left <<< or right >>> for fine adjustment, to adjust Manual Focus. Click on the image where you want to focus and it will show a value for focus in the top left corner, adjust for a maximum. Click on lower part of the button to goto continuous , and again to go back to auto focus.

With the Pi V3 camera you can add 2 focus buttons to the Pi,up and down, GPIOs 21 & 26, to switch to gnd, to manually focus.

Spot focussing (focus point) in Auto Focus - ONLY with Pi v3 camera - with Zoom not in use and Focussing not in manual click on the point in the preview image you want the camera to focus on (see image below). A red box will appear to show where it's focussing. To return to normal either click below the preview image or switch to manual FOCUS and back to auto.

If not using a v3 camera in Manual or spot focus stills will use autofocus-at-capture

HDR option for Pi v3 camera

Gain shows analog and digital gain. Green shows analog gain, when increased beyond a level will show yellow when applying digital gain.
eg 153 : 64/2.4 means gain set to 153, analog gain is 64, digital gain is 2.4
When a still is captured will show Analogue Gain, Digital Gain and Exposure time.

When using Zoom it will show a focus value, and an option of a histogram showing RGB and/or L, all based on the area shown, the area can be moved by clicking on the image, and changed using the Hist Area button.

2x2 binning option for 64MP camera, Click on right hand side of the Capture Still or Capture Timelapse buttons. 

For use with Hyperpixel square display set preview_width  = 720, preview_height = 540, sq_dis = 1 

If you want a fullscreen display set fullscreen = 1 in the script. if using a full HD screen (1920×1080) then set preview-width to 1440 and preview-height to 1080, fullscreen = 1

lf you want to use HQ imx477_scientific.json the file needs to be in /usr/share/libcamera/ipa/raspberrypi/imx477_scientific.json, see https://forums.raspberrypi.com/viewtopic.php?t=343449#p2068315

Pi4B recommended.

Shows a reduced preview but saves stills at camera full resolution, and videos at user set resolution.

Can also save timelapses. If you want to capture high resolution images as fast as possible using Timelapse set Interval to 0, set Duration to required seconds, set V_FPS to max, set V_Coder to mjpeg or raw , set V_Format to maximum value, click on CAPTURE Timelapse to start. The images will be in /home/.username./Pictures. If using Arducam 16MP or 64MP AF camera you will need more memory allocated to achieve full resolution if using Timelapse. In /boot/config.txt set dtoverlay=vc4-kms-v3d,cma-512 and then reboot. Note for fastest timelapse it uses libcamera-vid so not the highest quality images or libcamera-raw if v_codec set to raw.

To convert RAWs to TIF from a Pi v1,v2,v3 or HQ camera try https://github.com/Gordon999/PiRAW2TIF

With a Pi HQ Camera will allow exposures upto 650 seconds. (Note Pi v1 limited to approx 1.1 seconds, and v3 to approx 1.7 seconds ( at present) due to libcamera), Arducam 16 and 64mp cameras upto 200 and 435 seconds.

Click mouse on the left of a button to decrease, right to increase or use the appropriate slider

 # Always use the EXIT button to EXIT
 ( or you will need to reboot your pi)
 
lf using a Pi HQ camera for astrophotography it might be worth a try adding "imx477.dpc_enable=0" in /boot/cmdline.txt this will disable depleted pixel correction. 

# To install(manual):

Install latest RaspiOS based on Bullseye (tested with FULL 32bit and 64bit versions)
```bash
sudo apt install python3 -y
for BUSTER & BULLSEYE but NOT BOOKWORM - python3 -m pip install -U pygame --user
sudo apt install python3-opencv -y

(You may not need the following line if using RaspiOS 64bit)
sudo apt install libsdl-gfx1.2-5 libsdl-image1.2 libsdl-kitchensink1 libsdl-mixer1.2 libsdl-sound1.2 libsdl-ttf2.0-0 libsdl1.2debian libsdl2-2.0-0 libsdl2-gfx-1.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 -y

```
Let's download **RPiCamGUI.py** to our home directory

```bash
curl -fsSL https://raw.githubusercontent.com/Gordon999/RPiCamGUI/main/RPiCamGUI.py -o ~/RPiCamGUI.py
```

Use the following commands to run it.
  
```bash
python3 ~/PiLibCameraGUI.py
```

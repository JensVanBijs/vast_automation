from controllers.Usb2Comm import Usb2Comm
from controllers.LED_Control import LedCtrl, LedSettings
from controllers.Motor_Control import Motor
from controllers.LEICA_control import MicroscopeManager
from camera_stream import setup_camera, Handler, turn_on_led
from enum import Enum
import time
import threading
import os
import datetime

from vimba import Vimba, Camera, VimbaFeatureError, Frame, FrameStatus, PixelFormat
import cv2
from PIL import Image
import numpy as np



def create_img_directory(date_time: str, control: bool = False, zoom: str = None, fluorescence: str = None):
    if not os.path.exists("Results"):
        os.makedirs("Results")
    
    dir_string = "Results/" + date_time
    if control:
        dir_string += "/Control"
    else:
        dir_string += f'/{zoom}/{fluorescence}'
    os.makedirs(dir_string)
    return dir_string

def destroy_empty_img_dir(dir):
    import os
    if not os.listdir(dir):
        os.rmdir(dir)

def get_control_images(motor, led, date_time):
    camera: Camera
    with Vimba.get_instance() as vimba:
        cameras = vimba.get_all_cameras()
        with cameras[0] as camera:
            setup_camera(camera)
            try: 
                camera.get_feature_by_name('Height').set(250)   
                camera.get_feature_by_name('Width').set(1024)
            except (AttributeError, VimbaFeatureError) as e:
                print("Failed to set camera position")
                print(e)
                pass
            motor.IniMotor(True)
            led.LedOnOff(1, True, 1)
            dir = create_img_directory(date_time, control = True)
            try:
                for i in range(500):
                    img = camera.get_frame()
                    img_array = img.as_opencv_image()
                    cv2.imwrite(f"{dir}/img_{i}.tiff", img_array)
                    motor.RotateToPos(1, 10, 300, 20)
                    time.sleep(0.2)
            except Exception as e:
                print(e)
            finally:
                destroy_empty_img_dir(dir)
                cv2.destroyAllWindows()
                led.LedOnOff(1, False, 1)

def get_leica_images(motor, led, zoom: list, fluorescence: list, microscope: MicroscopeManager, date_time: str):
    motor.IniMotor(True)
    led.LedOnOff(1, False, 1)
    for z in zoom:
        for f in fluorescence:
            dir = create_img_directory(date_time=date_time, control=False, zoom=z, fluorescence=f)
            microscope.switch_filter(f)
            microscope.wait()
            microscope.switch_objective(z)
            microscope.wait()
            microscope.light = 1
            snap_images(motor, microscope, dir)

def snap_images(motor: Motor, microscope: MicroscopeManager, dir: str):
    try:
        for i in range(500):
            img = microscope.snap_picture()
            microscope.wait()
            cv2.imwrite(f"{dir}/img_{i}.tiff", img)
            motor.RotateToPos(1, 10, 300, 20)
            time.sleep(0.2)
    except Exception as e:
        print(e)
    finally:
        destroy_empty_img_dir(dir)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    usb = Usb2Comm().usb
    motor = Motor(usb)
    ledcnt = LedCtrl(usb)
    ledcnt.InitDac(LedSettings())
    ledcnt.SetCurrent(1, 0.5)
    handler = Handler()
    microscope = MicroscopeManager()
    now = datetime.datetime.now()
    date_time = now.strftime("%Y-%m-%d %H-%M-%S")
    get_control_images(motor, ledcnt, date_time)
    get_leica_images(motor=motor, 
                     led=ledcnt, 
                     zoom=['2.5x'], 
                     fluorescence=['White'], 
                     microscope=microscope,
                     date_time=date_time)
    
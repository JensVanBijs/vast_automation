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

from vimba import Vimba, Camera, Frame, FrameStatus, PixelFormat
import cv2
from PIL import Image
import numpy as np

usb = Usb2Comm().usb
motor = Motor(usb)
microscope = MicroscopeManager()
led = turn_on_led(usb)
handler = Handler()

def create_img_directory():
    if not os.path.exists("Results"):
        os.makedirs("Results")
    now = datetime.datetime.now()
    date_time = now.strftime("%Y-%m-%d %H-%M-%S")
    os.makedirs("Results/" + date_time)
    return "Results/" + date_time

def destroy_empty_img_dir(dir):
    import os
    if not os.listdir(dir):
        os.rmdir(dir)

def get_control_images(motor, led):
    camera: Camera
    with Vimba.get_instance() as vimba:
        cameras = vimba.get_all_cameras()
        with cameras[0] as camera:
            setup_camera(camera)
            motor.IniMotor(True)
            dir = create_img_directory()
            try:
                for i in range(500):
                    img = camera.get_frame()
                    img_array = img.as_opencv_image()
                    cv2.imwrite(f"{dir}/img_{i}.png", img_array)
                    motor.RotateToPos(1, 10, 300, 20)
                    time.sleep(0.2)
            except Exception as e:
                print(e)
            finally:
                destroy_empty_img_dir(dir)
                cv2.destroyAllWindows()
                led.LedOnOff(1, False, 1)

def get_leica_images(motor, led, zoom: list, fluorescence: list, microscope: MicroscopeManager):
    motor.IniMotor(True)
    led.LedOnOff(1, False, 1)
    dir = create_img_directory()
    for z in zoom:
        for f in fluorescence:
            microscope.switch_objective(z)
            microscope.switch_filter(f)
            snap_images(motor, microscope, dir)
    snap_images(motor, microscope, dir)

def snap_images(motor, microscope, dir):
    try:
        for i in range(500):
            img = microscope.snap_picture()
            cv2.imwrite(f"{dir}/img_{i}.png", img)
            motor.RotateToPos(1, 10, 300, 20)
            time.sleep(0.2)
    except Exception as e:
        print(e)
    finally:
        destroy_empty_img_dir(dir)
        cv2.destroyAllWindows()

microscope.light = 1
microscope.switch_objective("2.5x")
microscope.switch_filter("Blue")

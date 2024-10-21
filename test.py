from controllers.Usb2Comm import Usb2Comm
from controllers.LED_Control import LedCtrl, LedSettings
from controllers.Motor_Control import Motor
from controllers.LEICA_control import MicroscopeManager
from camera_stream import setup_camera, Handler, turn_on_led
from enum import Enum
import time
import threading

from vimba import Vimba, Camera, Frame, FrameStatus, intersect_pixel_formats, OPENCV_PIXEL_FORMATS, VimbaFeatureError
import cv2

usb = Usb2Comm().usb
motor = Motor(usb)
microscope = MicroscopeManager()
led = turn_on_led(usb)
handler = Handler()

def get_camera() -> Camera:
    with Vimba.get_instance() as vimba:
        camera = vimba.get_all_cameras()[0]
        camera.open()
        return camera
    
# start video stream on separate thread
def start_video_stream(camera: Camera):
    setup_camera(camera)
    camera.start_streaming(handler=handler, buffer_count=10)
    while not handler.shutdown.is_set():
        pass
    camera.stop_streaming()

stream_thread = threading.Thread(target=start_video_stream, args=(get_camera(),))


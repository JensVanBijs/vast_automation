from controllers.led_control import LedCtrl, LedSettings
from controllers.Usb2Comm import Usb2Comm
from vimba import Vimba, Camera, Frame, FrameStatus, intersect_pixel_formats, OPENCV_PIXEL_FORMATS, VimbaFeatureError
import cv2
import threading

def turn_on_led(usb, current: float) -> LedCtrl:
    if type(current) is not float:
        raise ValueError("Current must be a float")
    ledsttgs = LedSettings()
    ledctrl = LedCtrl(usb)
    ledctrl.InitDac(ledsttgs)
    ledctrl.SetCurrent(1, current)
    ledctrl.LedOnOff(1, True, 1)
    return ledctrl

def setup_camera(camera: Camera):
    with camera:
        try: 
            camera.get_feature_by_name('Height').set(720)   
            camera.get_feature_by_name('Width').set(1280)
        except (AttributeError, VimbaFeatureError):
            pass

        try:
            camera.ExposureAuto.set('Continuous')
            camera.BalanceWhiteAuto.set('Continuous')
            camera.GVSPAdjustPacketSize.run()

            while not camera.GVSPAdjustPacketSize.is_done():
                pass

        except (AttributeError, VimbaFeatureError):
            pass

        fmts = camera.get_pixel_formats()
        fmts = intersect_pixel_formats(fmts, OPENCV_PIXEL_FORMATS)
        if fmts:
            camera.set_pixel_format(fmts[0])
        else:
            raise Exception("No matching pixel format available")

class Handler:
    def __init__(self):
        self.shutdown = threading.Event()

    def __call__(self, camera: Camera, frame: Frame):
        ENTER_KEY_CODE = 13
        key = cv2.waitKey(1)
        if key == ENTER_KEY_CODE:
            self.shutdown.set()
            return
        
        if frame.get_status() == FrameStatus.Complete:
            cv2.imshow(f'Camera {camera.get_name()}', frame.as_opencv_image())
        
        camera.queue_frame(frame)

def main():
    usb = Usb2Comm().usb
    ledctrl = turn_on_led(usb, 1.0)
    with Vimba.get_instance() as vimba:
        cameras = vimba.get_all_cameras()
        if not cameras:
            raise Exception("No cameras available")
    
        camera: Camera
        with cameras[0] as camera:
            setup_camera(camera)
            handler = Handler()
        
            try:
                camera.start_streaming(handler=handler, buffer_count=10)
                handler.shutdown.wait()

            finally:
                camera.stop_streaming()
                ledctrl.LedOnOff(1, False, 1)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
from controllers.led_control import LedCtrl, LedSettings
from controllers.Usb2Comm import Usb2Comm
from vimba import Vimba, Camera, Frame, FrameStatus, intersect_pixel_formats, OPENCV_PIXEL_FORMATS, VimbaFeatureError
import cv2
import threading

class CameraControl():
    def __init__(self):
        pass

    def turn_on_led(self, usb, current: float) -> LedCtrl:
        if type(current) is not float:
            raise ValueError("Current must be a float")
        ledsttgs = LedSettings()
        ledctrl = LedCtrl(usb)
        ledctrl.InitDac(ledsttgs)
        ledctrl.SetCurrent(1, current)
        ledctrl.LedOnOff(1, True, 1)
        return ledctrl

    def setup_camera(self, camera: Camera, height = 720, width = 1280):
        with camera:
            try: 
                camera.get_feature_by_name('Height').set(height)   
                camera.get_feature_by_name('Width').set(width)
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
    
    def main(self):
        usb = Usb2Comm().usb
        ledctrl = self.turn_on_led(usb, 0.5)
        with Vimba.get_instance() as vimba:
            cameras = vimba.get_all_cameras()
            if not cameras:
                raise Exception("No cameras available")
        
            camera: Camera
            with cameras[0] as camera:
                self.setup_camera(camera)
                handler = Handler()
            
                try:
                    camera.start_streaming(handler=handler, buffer_count=10)
                    handler.shutdown.wait()

                finally:
                    camera.stop_streaming()
                    ledctrl.LedOnOff(1, False, 1)

    cv2.destroyAllWindows()

    def capture_image(self, usb: Usb2Comm, height: int, width: int):
        led_control = self.turn_on_led(usb, 0.5)
        with Vimba.get_instance() as vimba:
            cameras = vimba.get_all_cameras()
            if not cameras:
                raise Exception("No cameras available")
            
            camera: Camera
            img = None
            with cameras[0] as camera:
                self.setup_camera(camera, height, width)
                img = camera.get_frame()

            return img

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




if __name__ == "__main__":
    pass
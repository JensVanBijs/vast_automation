import numpy as np
from controllers.led_control import LedCtrl, LedSettings
from controllers.Usb2Comm import Usb2Comm
from vimba import Vimba, Camera, Frame, FrameStatus, intersect_pixel_formats, BAYER_PIXEL_FORMATS, VimbaFeatureError, PixelFormat, PersistType, OPENCV_PIXEL_FORMATS
import cv2
import threading
import os

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

    def setup_camera(self, camera: Camera, height = 200, width = 1024):
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
                print(fmts)
                # camera.set_pixel_format(fmts[0])
            else:
                raise Exception("No matching pixel format available")
            cwd = os.getcwd()
            print(f"Current working directory: {cwd}")
            settings_path = os.path.join(cwd, 'controllers', 'vast_settings', 'vast_camera_settings.xml')
            camera.load_settings(settings_path, PersistType.All)

    def main(self):
        usb = Usb2Comm().usb
        ledctrl = self.turn_on_led(usb, 0.5)
        with Vimba.get_instance() as vimba:
            cameras = vimba.get_all_cameras()
            if not cameras:
                raise Exception("No cameras available")
        
            camera: Camera
            with cameras[0] as camera:
                print('setting up camera')
                self.setup_camera(camera)
                print('camera setup complete')
                handler = Handler()
            
                try:
                    print('starting camera stream')
                    camera.start_streaming(handler=handler, buffer_count=10)
                    handler.shutdown.wait()

                finally:
                    camera.stop_streaming()
                    ledctrl.LedOnOff(1, False, 1)

        cv2.destroyAllWindows()

    def capture_image(self, usb: Usb2Comm, height: int = 720, width: int = 1280, led_brightness: float = 0.25):
        led_control = self.turn_on_led(usb, led_brightness)
        with Vimba.get_instance() as vimba:
            cameras = vimba.get_all_cameras()
            if not cameras:
                raise Exception("No cameras available")
            
            camera: Camera
            img: Frame
            with cameras[0] as camera:
                self.setup_camera(camera)
                img = camera.get_frame()
                img.convert_pixel_format(PixelFormat.Bgr8)
                img = img.as_numpy_ndarray()
                led_control.LedOnOff(1, False, 1)

            assert isinstance(img, np.ndarray), "Captured image is not a numpy array"

        return img.copy()

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
            frame.convert_pixel_format(PixelFormat.Bgr8)
            cv2.imshow(f'Camera {camera.get_name()}', frame.as_opencv_image())

        camera.queue_frame(frame)




if __name__ == "__main__":
    ctr = CameraControl()
    ctr.main()
    

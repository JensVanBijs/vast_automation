import numpy as np
from controllers.led_control import LedCtrl, LedSettings
from controllers.Usb2Comm import Usb2Comm
from vimba import Vimba, Camera, Frame, FrameStatus, intersect_pixel_formats, BAYER_PIXEL_FORMATS, VimbaFeatureError, PixelFormat, PersistType, OPENCV_PIXEL_FORMATS
import cv2
import threading
import os
import time

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
        try: 
            camera.get_feature_by_name('Height').set(height)   
            camera.get_feature_by_name('Width').set(width)
        except (AttributeError, VimbaFeatureError):
            pass

        try:
            # Stop any existing acquisition first
            try:
                camera.get_feature_by_name('AcquisitionStop').run()
                time.sleep(0.1)
            except:
                pass
            
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
        
        # Give camera time to initialize properly
        print("Waiting for camera to initialize...")
        time.sleep(2)
        
        # Ensure acquisition is properly started
        try:
            camera.get_feature_by_name('AcquisitionStart').run()
            time.sleep(0.5)
        except Exception as e:
            print(f"Warning: Could not start acquisition: {e}")

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
                
                # Add timeout and retry logic for frame capture
                max_retries = 3
                timeout_ms = 10000  # Increased to 10 seconds timeout
                
                for attempt in range(max_retries):
                    try:
                        print(f"Attempting to capture frame (attempt {attempt + 1}/{max_retries})")
                        
                        # Ensure acquisition is running before each frame
                        try:
                            acq_status = camera.get_feature_by_name('AcquisitionStatus').get()
                            if acq_status != 'Running':
                                camera.get_feature_by_name('AcquisitionStart').run()
                                time.sleep(0.2)
                        except:
                            pass
                        
                        img = camera.get_frame(timeout_ms=timeout_ms)
                        break  # Success, exit retry loop
                    except Exception as e:
                        print(f"Frame capture attempt {attempt + 1} failed: {e}")
                        if attempt == max_retries - 1:
                            led_control.LedOnOff(1, False, 1)
                            raise Exception(f"Failed to capture frame after {max_retries} attempts: {e}")
                        
                        # Try to reset acquisition between attempts
                        try:
                            camera.get_feature_by_name('AcquisitionStop').run()
                            time.sleep(0.5)
                            camera.get_feature_by_name('AcquisitionStart').run()
                            time.sleep(0.5)
                        except:
                            pass
                
                # Process the captured frame
                try:
                    img.convert_pixel_format(PixelFormat.Bgr8)
                    img_array = img.as_numpy_ndarray()
                    
                    # Apply brightness enhancement for very dark images
                    # Increase contrast and brightness significantly
                    alpha = 4.0  # DOUBLED: Even higher contrast multiplier for maximum brightness
                    beta = 150   # DOUBLED: Much higher brightness addition for whiter appearance
                    img_array = cv2.convertScaleAbs(img_array, alpha=alpha, beta=beta)
                    
                    # Reduce green tint by adjusting color channels
                    # Split into BGR channels
                    b, g, r = cv2.split(img_array)
                    
                    # Reduce green channel intensity and boost red/blue for whiter appearance
                    g = cv2.multiply(g, 0.65)  # Reduce green more: 25% reduction instead of 15%
                    r = cv2.multiply(r, 1.20)  # Boost red slightly more: 20% instead of 15%
                    b = cv2.multiply(b, 1.15)  # Boost blue slightly more: 15% instead of 10%
                    
                    # Merge channels back
                    img_array = cv2.merge([b, g, r])
                    
                    # Apply gamma correction for additional brightness
                    gamma = 0.6  # Even lower gamma for more brightness
                    inv_gamma = 1.0 / gamma
                    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
                    img_array = cv2.LUT(img_array, table)
                    
                except Exception as e:
                    print(f"Error converting frame: {e}")
                    led_control.LedOnOff(1, False, 1)
                    raise Exception(f"Failed to convert frame: {e}")
                
                led_control.LedOnOff(1, False, 1)

            assert isinstance(img_array, np.ndarray), "Captured image is not a numpy array"

        return img_array.copy()

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
    

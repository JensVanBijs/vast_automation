import datetime
from controllers.Usb2Comm import Usb2Comm
from controllers.led_control import LedCtrl, LedSettings
from controllers.motor_control import Motor
from controllers.LEICA_control import MicroscopeManager
from controllers.vast_camera_control import CameraControl, Handler
from enum import Enum
import time
import os
from vimba import Vimba, Camera, VimbaFeatureError, Frame, FrameStatus, PixelFormat
import cv2
from PIL import Image
import numpy as np

class AutoImager():
    def __init__(self):
        """
        Initializes the main components of the system.
        This function sets up the following components:
        - USB communication
        - Rotational motor
        - Z positional motor
        - LED controller
        - Microscope manager
        Returns:
            tuple: A tuple containing the initialized components in the following order:
                - self.usb (Usb2Comm): The USB communication object.
                - rotational_motor (Motor): The motor responsible for rotational movement.
                - z_positional_motor (Motor): The motor responsible for Z-axis positional movement.
                - led (LedCtrl): The LED controller.
                - microscope (MicroscopeManager): The microscope manager.
        """
        self.usb = Usb2Comm().usb
        self.rotational_motor = Motor(self.usb)
        self.z_positional_motor = Motor(self.usb, 2)
        self.led = LedCtrl(self.usb)
        self.led.InitDac(LedSettings())
        self.microscope = MicroscopeManager()

    def snap_images(self, dir: str):
        """
        Captures a series of images using a microscope and saves them to a specified directory.
        Args:
            motor (Motor): The motor object used to rotate the sample.
            microscope (MicroscopeManager): The microscope manager object used to capture images.
            dir (str): The directory where the images will be saved.
        Raises:
            Exception: If an error occurs during image capture or motor rotation.
        Notes:
            - Captures 500 images in total.
            - Each image is saved in TIFF format with a filename pattern 'img_<index>.tiff'.
            - The motor is rotated to a specific position after each image capture.
            - Waits for a short period between each capture to ensure stability.
            - Cleans up the directory and closes all OpenCV windows upon completion or error.
        """
        try:
            for i in range(500):
                img = self.microscope.snap_picture()
                self.microscope.wait()
                cv2.imwrite(f"{dir}/img_{i}.tiff", img)
                self.rotational_motor.RotateToPos(1, 10, 300, 20)
                time.sleep(0.2)
        except Exception as e:
            print(e)
        finally:
            self.destroy_empty_img_dir(dir)
            cv2.destroyAllWindows()

    def get_leica_images(self, zoom: list, fluorescence: list, date_time: str):
        """
        Captures images using a Leica microscope setup with specified zoom levels and fluorescence filters.
        Args:
            motor: The motor controller object to control the microscope stage.
            led: The LED controller object to manage the illumination.
            zoom (list): A list of zoom levels to capture images at.
            fluorescence (list): A list of fluorescence filter settings to use.
            microscope (MicroscopeManager): The microscope manager object to control the microscope.
            date_time (str): The date and time string to use for naming directories and files.
        Returns:
            None
        """
        self.rotational_motor.IniMotor(True)
        self.led.LedOnOff(1, False, 1)
        for z in zoom:
            for f in fluorescence:
                dir = self.create_img_directory(date_time=date_time, control=False, zoom=z, fluorescence=f)
                self.microscope.switch_filter(f)
                self.microscope.wait()
                self.microscope.switch_objective(z)
                self.microscope.wait()
                self.snap_images(dir)

    def get_control_images(self, motor, led, date_time):
        """
        Captures control images using a camera, motor, and LED setup.
        Parameters:
        motor (Motor): The motor object used to control the camera's position.
        led (LED): The LED object used to control the lighting.
        date_time (str): The date and time string used to create the image directory.
        Returns:
        None
        The function performs the following steps:
        1. Initializes the camera using the Vimba API.
        2. Sets up the camera with specific height and width settings.
        3. Initializes the motor and turns on the LED.
        4. Creates a directory to store the captured images.
        5. Captures 500 images, saving each one to the directory and rotating the motor between captures.
        6. Handles any exceptions that occur during the image capture process.
        7. Cleans up by destroying the image directory if empty, closing all OpenCV windows, and turning off the LED.
        """
        camera: Camera
        cam_ctrl = CameraControl()
        with Vimba.get_instance() as vimba:
            cameras = vimba.get_all_cameras()
            with cameras[0] as camera:
                cam_ctrl.setup_camera(camera)
                try: 
                    camera.get_feature_by_name('Height').set(250)   
                    camera.get_feature_by_name('Width').set(1024)
                except (AttributeError, VimbaFeatureError) as e:
                    print("Failed to set camera position")
                    print(e)
                    pass
                motor.IniMotor(True)
                led.LedOnOff(1, True, 1)
                dir = self.create_img_directory(date_time, control = True)
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
                    self.destroy_empty_img_dir(dir)
                    cv2.destroyAllWindows()
                    led.LedOnOff(1, False, 1)

    def destroy_empty_img_dir(self, dir):
        import os
        if not os.listdir(dir):
            os.rmdir(dir)

    def create_img_directory(self, date_time: str, control: bool = False, zoom: str = None, fluorescence: str = None):
        if not os.path.exists("Results"):
            os.makedirs("Results")
        
        dir_string = "Results/" + date_time
        if control:
            dir_string += "/Control"
        else:
            dir_string += f'/{zoom}/{fluorescence}'
        os.makedirs(dir_string)
        return dir_string
    
if __name__ == "__main__":
    imager = AutoImager()
    now = datetime.datetime.now()
    date_time = now.strftime("%Y-%m-%d %H-%M-%S")
    imager.get_leica_images(['2.5x'], ['White'], date_time)
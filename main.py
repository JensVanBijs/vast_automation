import datetime
import shutil
from controllers.Usb2Comm import Usb2Comm
from controllers.led_control import LedCtrl, LedSettings
from controllers.Motor_Control import Motor
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
        self.led.SetCurrent(1, 1)
        self.microscope = MicroscopeManager()

    def snap_images(self, dir: str, progress_callback=None, current_image_offset=0):
        """
        Captures a series of images using a microscope and saves them to a specified directory.
        Args:
            motor (Motor): The motor object used to rotate the sample.
            microscope (MicroscopeManager): The microscope manager object used to capture images.
            dir (str): The directory where the images will be saved.
            progress_callback (callable): Optional callback function to report progress
            current_image_offset (int): Offset for image numbering in progress updates
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
                self.microscope.save_picture(img, f"{dir}/img_{i}.tiff")
                self.rotational_motor.RotateToPos(1, 10, 300, 20)
                time.sleep(0.2)
                
                # Report progress if callback provided
                if progress_callback:
                    progress_callback(current_image_offset + i + 1)
                    
        except Exception as e:
            print(e)
        finally:
            self.destroy_empty_img_dir(dir)
            cv2.destroyAllWindows()
        return

    def get_leica_images(self, zoom: list, fluorescence: list, sample_id: str, progress_callback=None):
        """
        Captures images using a Leica microscope setup with specified zoom levels and fluorescence filters.
        Args:
            motor: The motor controller object to control the microscope stage.
            led: The LED controller object to manage the illumination.
            zoom (list): A list of zoom levels to capture images at.
            fluorescence (list): A list of fluorescence filter settings to use.
            microscope (MicroscopeManager): The microscope manager object to control the microscope.
            date_time (str): The date and time string to use for naming directories and files.
            progress_callback (callable): Optional callback function to report progress
        Returns:
            None
        """
        self.rotational_motor.IniMotor(True)
        self.led.LedOnOff(1, False, 1)
        
        current_image_count = 0
        
        for z in zoom:
            for f in fluorescence:
                dir = self.create_img_directory(sample_id, control=False, zoom=z, fluorescence=f)
                self.microscope.switch_objective(z)
                self.microscope.wait()
                self.microscope.switch_filter(f)
                self.microscope.wait()
                
                # Pass progress callback with current offset
                self.snap_images(dir, progress_callback, current_image_count)
                current_image_count += 500  # Each snap_images captures 500 images
                
        self.microscope.switch_filter("White")
        self.microscope.wait()
        return

    def test_image(self, test_name, fluorescence, zoom):
        """
        Captures a test image using the microscope and saves it to a specified directory.
        Args:
            test_name (str): The name of the test, used to create a directory for saving images.
        Returns:
            None
        """
        try:
            dir = self.create_img_directory(test_name, False, zoom, fluorescence)
            self.led.LedOnOff(1, False, 1)
            self.microscope.switch_objective(zoom)
            self.microscope.wait()
            self.microscope.switch_filter(fluorescence)
            self.microscope.wait()
            img = self.microscope.snap_picture()
            self.microscope.wait()
            self.microscope.save_picture(img, f"{dir}/test_image.tiff")
        except Exception as e:
            print(f"Error during test image capture: {e}")
            self.destroy_empty_img_dir(dir)
        return

    def get_control_images(self, sample_id, brightness: float = 1.0, progress_callback=None):
        """
        Captures control images using a camera, motor, and LED setup.
        Parameters:
        motor (Motor): The motor object used to control the camera's position.
        led (LED): The LED object used to control the lighting.
        date_time (str): The date and time string used to create the image directory.
        brightness (float): LED brightness level (0.0 to 1.0)
        progress_callback (callable): Optional callback function to report progress
        Returns:
        None
        The function performs the following steps:
        1. Initializes the camera using the Vimba API.
        2. Sets up the camera with specific height and width settings.
        3. Initializes the motor and turns on the LED.
        4. Creates a directory to store the captured images.
        5. Captures 20 images, saving each one to the directory and rotating the motor between captures.
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
                self.rotational_motor.IniMotor(True)
                self.led.SetCurrent(1, brightness)
                self.led.LedOnOff(1, True, 1)
                dir = self.create_img_directory(sample_id, control = True)
                try:
                # Get the camera's pixel format
                    cam_pixel_format = camera.get_feature_by_name('PixelFormat').get()
                    print(f"Camera pixel format: {cam_pixel_format}")
                    
                    # Ensure acquisition is started
                    try:
                        camera.get_feature_by_name('AcquisitionStart').run()
                        time.sleep(0.5)
                    except:
                        pass
                    
                    for i in range(20):
                        frame: Frame
                        
                        # Add timeout and retry logic for frame capture
                        max_retries = 3
                        timeout_ms = 10000  # Increased to 10 seconds timeout
                        
                        for attempt in range(max_retries):
                            try:
                                print(f"Capturing frame {i+1}/20 (attempt {attempt + 1}/{max_retries})")
                                
                                # Check acquisition status before each frame
                                try:
                                    acq_status = camera.get_feature_by_name('AcquisitionStatus').get()
                                    if acq_status != 'Running':
                                        camera.get_feature_by_name('AcquisitionStart').run()
                                        time.sleep(0.2)
                                except:
                                    pass
                                
                                frame = camera.get_frame(timeout_ms=timeout_ms)
                                break  # Success, exit retry loop
                            except Exception as e:
                                print(f"Frame capture attempt {attempt + 1} failed: {e}")
                                if attempt == max_retries - 1:
                                    raise Exception(f"Failed to capture frame {i+1} after {max_retries} attempts: {e}")
                                
                                # Try to reset acquisition between attempts
                                try:
                                    camera.get_feature_by_name('AcquisitionStop').run()
                                    time.sleep(0.5)
                                    camera.get_feature_by_name('AcquisitionStart').run()
                                    time.sleep(0.5)
                                except:
                                    pass
                        
                        # Handle Bayer formats by converting to a compatible format
                        if 'Bayer' in str(cam_pixel_format):
                            # Convert Bayer to BGR format that OpenCV can handle
                            frame.convert_pixel_format(PixelFormat.Bgr8)
                        # img_array = frame.as_opencv_image()
                        # cv2.imwrite(f"{dir}/img_{i}.tiff", img_array)
                        img = Image.fromarray(frame.as_numpy_ndarray())
                        img.save(f"{dir}/img_{i}.tiff")
                        self.rotational_motor.RotateToPos(1, 10, 300, 20)
                        time.sleep(0.2)
                        
                        # Report progress if callback provided
                        if progress_callback:
                            progress_callback(i + 1)
                            
                except Exception as e:
                    print(f"Error during image capture: {e}")
                finally:
                    self.destroy_empty_img_dir(dir)
                    cv2.destroyAllWindows()
                    self.led.LedOnOff(1, False, 1)

    def destroy_empty_img_dir(self, dir):
        import os
        if not os.listdir(dir):
            os.rmdir(dir)

    def create_img_directory(self, date_time: str, control: bool = False, zoom: str = None, fluorescence: str = None):
        if not os.path.exists("Results"):
            os.makedirs("Results")

        # Create the main directory for this session
        main_dir = "Results/" + date_time
        if not os.path.exists(main_dir):
            os.makedirs(main_dir)
            
            # Save microscope configuration file only once per session at the main directory level
            config_source = "controllers/microscope_settings/microscope_configuration.json"
            config_dest = os.path.join(main_dir, "microscope_configuration.json")

            if os.path.exists(config_source):
                shutil.copy(config_source, config_dest)
                print(f"Microscope configuration saved to {config_dest}")
            else:
                print(f"Configuration file {config_source} does not exist. Skipping copy.")
        
        # Create the specific subdirectory for images
        if control:
            dir_string = main_dir + "/Control/structure_images"
        else:
            dir_string = main_dir + f'/{zoom}/{fluorescence}/structure_images'
        os.makedirs(dir_string)

        return dir_string
    
if __name__ == "__main__":
    imager = AutoImager()
    now = datetime.datetime.now()
    date_time = now.strftime("%Y-%m-%d %H-%M-%S")
    # imager.get_control_images(date_time)
    # Uncomment the following lines to capture images with specific zoom and fluorescence settings
    imager.test_image('test', "Blue", "4x")
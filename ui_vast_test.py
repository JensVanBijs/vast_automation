from itertools import tee
import time
import customtkinter as ctk
from main import AutoImager
from PIL import Image, ImageTk
from PIL.Image import Resampling
import numpy as np
from controllers.vast_camera_control import CameraControl
from PIL import Image
from controllers.motor_control import Motor
import cv2
from datetime import datetime
from main import AutoImager
from controllers.LEICA_control import MicroscopeManager
import os
import xml.etree.ElementTree as ET
from controllers.led_control import LedCtrl, LedSettings

class VAST360CaptureApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.auto_imager = AutoImager()
        self.running = False
        self.streaming = False

        try:
            self.microscope = MicroscopeManager()
        except Exception as e:
            self.microscope = None
            print(f"Error initializing microscope: {e}")

        self.pos_var = ctk.IntVar(value=10)   
        self.rot_var = ctk.IntVar(value=10)

        self.exposure_var = ctk.DoubleVar(value=200.0)

        # initialieze LED settings and control
        self.led_settings = LedSettings()
        self.led_ctrl = LedCtrl(self.auto_imager.usb)
        
        # Try to initialize the LED DAC
        try:
            self.led_ctrl.InitDac(self.led_settings)
            print("LED control initialized successfully")
        except Exception as e:
            print(f"Error initializing LED control: {e}")
        
        # Add variables for LED brightness (0.0-1.0 range)
        self.led1_brightness = ctk.DoubleVar(value=1.0)

        # initialize motors
        self.pos_motor = self.auto_imager.z_positional_motor
        self.rot_motor = self.auto_imager.rotational_motor

        self.init_motors()

        # Configure window
        self.title("Automatic VAST 360 Capture")
        self.geometry("1200x800")

        # sample ID
        self.status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_frame.pack(fill="x", pady=(0, 5))

        self.sample_info_frame = ctk.CTkFrame(self.status_frame, fg_color="#444")
        self.sample_info_frame.pack(side="left", padx=10, fill="y")
        
        self.sample_id_label = ctk.CTkLabel(self.sample_info_frame, text="Sample ID: ", width=100)
        self.sample_id_label.pack(side="left", padx=5)
        
        self.sample_id_entry = ctk.CTkEntry(self.sample_info_frame, width=150)
        self.sample_id_entry.pack(side="left", padx=5)
        self.sample_id_entry.insert(0, f"EXP-{time.strftime('%Y%m%d')}-001")

        # Tabs 
        self.tab_view = ctk.CTkTabview(self, corner_radius=10)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs 
        self.capture_tab = self.tab_view.add("Capture")
        self.motor_tab = self.tab_view.add("Motor")

        # Capture tab 
        self.create_capture_tab()

        # Motor tab
        self.create_motor_tab()

    def init_motors(self):
        try:
            self.pos_motor = Motor(self.auto_imager.usb, motIdx=2)
            self.pos_motor.IniMotor(True)
            time.sleep(1)

            self.rot_motor = Motor(self.auto_imager.usb, motIdx=1)
            self.rot_motor.IniMotor(True)
            time.sleep(1)

            self.update_status("Motors initialized succesfully")
            
            print(self.pos_motor, self.rot_motor)
        except Exception as e:
            self.update_status(f"Error initializing motors: {e}")
           
    def create_capture_tab(self):
        """ Create the Capture tab UI """
        # Left section: Fluorescence & Magnification
        left_frame = ctk.CTkFrame(self.capture_tab, fg_color="#7C7C7C", corner_radius=10)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Fluorescence section
        fluorescence_label = ctk.CTkLabel(left_frame, text="Fluorescence", font=("Arial", 14, "bold"))
        fluorescence_label.pack(padx=10, pady=(10, 5), anchor="w")

        channel_label = ctk.CTkLabel(left_frame, text="Channel Selection", font=("Arial", 12))
        channel_label.pack(padx=10, pady=(5, 5), anchor="w")

        fluorescence_options = ["White (brightfield)", "Green (340 nm, CH1)", "Blue (430 nm, CH2)"]
        self.fluorescence_vars = {}
    
        for option in fluorescence_options:
            var = ctk.StringVar(value="off")
            checkbox = ctk.CTkCheckBox(left_frame, text=option, variable=var, onvalue="on", offvalue="off")
            checkbox.pack(anchor="w", padx=10)
            spacer = ctk.CTkFrame(left_frame, height=10, fg_color='transparent') 
            spacer.pack()
            self.fluorescence_vars[option] = var

                # LED Controls
        led_control_label = ctk.CTkLabel(left_frame, text="LED Controls to Change Brightness", font=("Arial", 14, "bold"))
        led_control_label.pack(padx=10, pady=(15, 5), anchor="w")

        # LED brightness slider
        led1_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        led1_frame.pack(fill="x", padx=10, pady=5)

        led1_label = ctk.CTkLabel(led1_frame, text="LED:")
        led1_label.pack(side="left")

        led1_slider = ctk.CTkSlider(led1_frame, from_=0.0, to=1.0, variable=self.led1_brightness)
        led1_slider.pack(side="left", padx=5, fill="x", expand=True)

        led1_value = ctk.CTkLabel(led1_frame, text="100%", width=50)
        led1_value.pack(side="left")

        # Update value labels when sliders change
        def update_led1_label(*args):
            led1_value.configure(text=f"{int(self.led1_brightness.get() * 100)}%")
        self.led1_brightness.trace_add("write", update_led1_label)

        # Button to apply LED settings
        led_apply_btn = ctk.CTkButton(left_frame, text="Apply LED Setting", 
                                    fg_color="orange", hover_color="darkorange", 
                                    command=self.apply_led_settings)
        led_apply_btn.pack(pady=(5, 10), anchor="w", padx=10)

        # exposure settings 
        exposure_label = ctk.CTkLabel(left_frame, text="Exposure Settings", font=("Arial", 14, "bold"))
        exposure_label.pack(padx=10, pady=(15, 5), anchor="w")
        
        exposure_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        exposure_frame.pack(fill="x", padx=10, pady=5)
        
        exposure_value_label = ctk.CTkLabel(exposure_frame, text="Exposure:")
        exposure_value_label.pack(side="left")
        
        exposure_entry = ctk.CTkEntry(exposure_frame, width=60, textvariable=self.exposure_var)
        exposure_entry.pack(side="left", padx=5)
        
        exposure_unit = ctk.CTkLabel(exposure_frame, text="ms")
        exposure_unit.pack(side="left")

        exposure_apply_btn = ctk.CTkButton(left_frame, text="Apply", width=60, fg_color="orange", hover_color="darkorange", command=self.apply_exposure)
        exposure_apply_btn.pack(pady=(5, 10), anchor="w", padx=10)


        # Magnification section
        magnification_label = ctk.CTkLabel(left_frame, text="Magnification", font=("Arial", 14, "bold"))
        magnification_label.pack(padx=10, pady=(10, 5), anchor="w")

        magnification_options = ["2.5x", "4x", "10x"]
        self.magnification_vars = {}
        for option in magnification_options:
            var = ctk.StringVar(value="off")
            checkbox = ctk.CTkCheckBox(left_frame, text=option, variable=var, onvalue="on", offvalue="off")
            checkbox.pack(anchor="w", padx=10)
            spacer = ctk.CTkFrame(left_frame, height=10, fg_color='transparent')  # Adjust height for spacing
            spacer.pack()
            self.magnification_vars[option] = var

        # Right section: Stream/Test Capture
        right_frame = ctk.CTkFrame(self.capture_tab, fg_color="#7C7C7C", corner_radius=10)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Display area
        self.capture_display = ctk.CTkFrame(right_frame, height=300, width=400, fg_color="black")
        self.capture_display.pack(padx=10, pady=10, expand=True, fill="both")

        label = ctk.CTkLabel(self.capture_display, text="Test capture", text_color="white")
        label.place(relx=0.5, rely=0.5, anchor="center")

        # Buttons
        button_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)

        self.test_capture_btn = ctk.CTkButton(button_frame,
                                              text="Test capture", 
                                              fg_color="blue", 
                                              hover_color="darkblue", 
                                              command=self.on_test_capture)
        self.test_capture_btn.pack(side="left", padx=5, expand=True, fill="x")

        self.run_btn = ctk.CTkButton(button_frame, text="Run", fg_color="green", hover_color="darkgreen", command=self.on_run)
        self.run_btn.pack(side="left", padx=5, expand=True, fill="x")

        # Grid configuration
        self.capture_tab.grid_columnconfigure(0, weight=1)
        self.capture_tab.grid_columnconfigure(1, weight=3)
        self.capture_tab.grid_rowconfigure(0, weight=1)

    def create_motor_tab(self):
        """ Create the Motor tab UI """
        # Left section: Motor controls
        motor_frame = ctk.CTkFrame(self.motor_tab, fg_color="gray30")
        motor_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Positional Motor Controls
        pos_label = ctk.CTkLabel(motor_frame, text="Positional motor (from left to right)", font=("Arial", 14, "bold"))
        pos_label.pack(pady=(10, 5), anchor="center")

        preset_frame = ctk.CTkFrame(motor_frame, fg_color="transparent")
        preset_frame.pack(pady=5)

        preset_label = ctk.CTkLabel(preset_frame, text="Step size:")
        preset_label.pack(side="left", padx=5)

        for preset in [1, 5, 10, 25]:
            preset_btn = ctk.CTkButton(preset_frame, text=str(preset), width=30, command=lambda p=preset: self.pos_var.set(p))
            preset_btn.pack(side="left", padx=5)

        pos_control = ctk.CTkEntry(motor_frame, textvariable=self.pos_var, width=50)
        pos_control.pack(pady=5)

        # Create a frame for positional motor buttons
        pos_button_frame = ctk.CTkFrame(motor_frame, fg_color="transparent")
        pos_button_frame.pack(pady=5)

        self.pos_btn_left = ctk.CTkButton(pos_button_frame, text="←", width=40, command=self.move_pos_motor_left)
        self.pos_btn_left.pack(side="left", padx=5)

        self.pos_btn_right = ctk.CTkButton(pos_button_frame, text="→", width=40, command=self.move_pos_motor_right)
        self.pos_btn_right.pack(side="left", padx=5)

        # self.pos_reset_btn = ctk.CTkButton(pos_button_frame, text="Reset", width=40, command=self.reset_pos_motor)
        # self.pos_reset_btn.pack(padx=5)

        separator = ctk.CTkFrame(motor_frame, height=2, width=200, fg_color="gray")
        separator.pack(pady=10, fill="x")

        # Rotational Motor Controls
        rot_label = ctk.CTkLabel(motor_frame, text="Rotational motor (clockwise)", font=("Arial", 14, "bold"))
        rot_label.pack(pady=(10, 5), anchor="center")

        rot_preset_frame = ctk.CTkFrame(motor_frame, fg_color="transparent")
        rot_preset_frame.pack(pady=5)

        rot_preset_label = ctk.CTkLabel(rot_preset_frame, text="Degree:")
        rot_preset_label.pack(side="left", padx=5)

        for preset in [5, 10, 45, 90]:
            rot_preset_btn = ctk.CTkButton(rot_preset_frame, text=str(preset), width=30, command=lambda p=preset: self.rot_var.set(p))
            rot_preset_btn.pack(side="left", padx=2)

        rot_control = ctk.CTkEntry(motor_frame, textvariable=self.rot_var, width=50)
        rot_control.pack(pady=5)

        # Create a frame for rotational motor buttons
        rot_button_frame = ctk.CTkFrame(motor_frame, fg_color="transparent")
        rot_button_frame.pack(pady=5)

        self.rot_btn_left = ctk.CTkButton(rot_button_frame, text="⟲", width=40, command=self.rotate_motor_ccw)
        self.rot_btn_left.pack(side="left", padx=5)

        self.rot_btn_right = ctk.CTkButton(rot_button_frame, text="⟳", width=40, command=self.rotate_motor_cw)
        self.rot_btn_right.pack(side="left", padx=5)

        # self.rot_preset_btn = ctk.CTkButton(rot_button_frame, text="Reset", width=40, command=self.reset_rot_motor)
        # self.rot_preset_btn.pack(padx=5)

        separator2 = ctk.CTkFrame(motor_frame, height=2, width=200, fg_color="gray")
        separator2.pack(pady=10, fill="x")

        # self.full_reset_btn = ctk.CTkButton(motor_frame, text="Full Reset", width=100, fg_color="orange", hover_color="darkorange", command=self.full_reset_motors)
        # self.full_reset_btn.pack(pady=5)

        # Right section: Test capture
        right_frame = ctk.CTkFrame(self.motor_tab, fg_color="gray30")
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.motor_test_capture_display = ctk.CTkFrame(right_frame, height=300, width=400, fg_color="black")
        self.motor_test_capture_display.pack(padx=10, pady=10, expand=True, fill="both")

        stream_label = ctk.CTkLabel(self.motor_test_capture_display, text="Stream", text_color="white")
        stream_label.place(relx=0.5, rely=0.5, anchor="center")

        self.motor_test_capture_btn = ctk.CTkButton(right_frame, text="Test capture", fg_color="green", hover_color="darkgreen", command=self.test_capture_motor)
        self.motor_test_capture_btn.pack(pady=10)

        # Grid configuration
        self.motor_tab.grid_columnconfigure(0, weight=1)
        self.motor_tab.grid_columnconfigure(1, weight=3)
        self.motor_tab.grid_rowconfigure(0, weight=1)

    def apply_exposure(self):    
        try:
            if not hasattr(self, 'microscope') or self.microscope is None:
                self.update_status("Microscope not initialized")
                return
            exposure_value = self.exposure_var.get()
            if exposure_value <= 0:
                self.update_status("Exposure time must be positive")
                return
            self.microscope.core.setExposure(exposure_value)
            self.update_status(f"Exposure time set to {exposure_value} ms")
        except Exception as e:
            self.update_status(f"Error applying exposure: {e}")

    def move_pos_motor_left(self):
        try:
            if self.pos_motor:
                distance = self.pos_var.get()
                print(f"Moving positional motor left by {distance} steps")
                self.pos_motor.SelectMotor()
                self.pos_motor.move_z_motor(distance, "left")
                self.update_status(f"Moved positional motor left by {distance} steps")
            else:
                self.update_status("Positional motor not initialized")
        except Exception as e:
            self.update_status(f"Error moving positional motor: {e}")
        
    def move_pos_motor_right(self):
        try:
            if self.pos_motor:
                distance = self.pos_var.get()
                try:
                    distance = int(distance)
                except ValueError:
                    self.update_status("Invalid distance value")
                    return  
                print(f"Moving positional motor right by {distance} steps")
                self.pos_motor.SelectMotor()
                self.pos_motor.move_z_motor(distance, "right")
                self.update_status(f"Moved positional motor right by {distance} steps")
            else:
                self.update_status("Positional motor not initialized")
        except Exception as e:
            self.update_status(f"Error moving positional motor: {e}")

    def rotate_motor_ccw(self):
        try:
            if self.rot_motor:
                degree = self.rot_var.get()
                try:
                    degree = int(degree)
                except ValueError:
                    self.update_status("Invalid degree value")
                    return
                print(f"Rotating motor counterclockwise by {degree} degrees")
                self.rot_motor.SelectMotor()
                self.rot_motor.RotateToPos(degree, 5, 500000, 0.1)
                self.update_status(f"Rotated motor counterclockwise by {degree} degrees")
            else:
                self.update_status("Rotational motor not initialized")
        except Exception as e:
            self.update_status(f"Error rotating motor: {e}")

    def rotate_motor_cw(self):
        try:
            if self.rot_motor:
                degree = self.rot_var.get()
                print(f"Rotating motor clockwise by {degree} degrees")
                self.rot_motor.SelectMotor()
                self.rot_motor.RotateToPos(-degree, 5, 500000, 0)
                self.update_status(f"Rotated motor clockwise by {degree} degrees")
            else:
                self.update_status("Rotational motor not initialized")
        except Exception as e:
            self.update_status(f"Error rotating motor: {e}")

    # def reset_pos_motor(self):
    #     try:
    #         if self.pos_motor:
    #             self.pos_motor.SelectMotor()
    #             self.pos_motor.ResetPos()
    #             self.update_status("Positional motor reset")
    #         else:
    #             self.update_status("Positional motor not initialized")
    #     except Exception as e:
    #         self.update_status(f"Error resetting positional motor: {e}")

    # def reset_rot_motor(self):
    #     try:
    #         if self.rot_motor:
    #             self.rot_motor.SelectMotor()
    #             self.rot_motor.ResetPos()
    #             self.update_status("Rotational motor reset")
    #         else:
    #             self.update_status("Rotational motor not initialized")
    #     except Exception as e:
    #         self.update_status(f"Error resetting rotational motor: {e}")

    # def full_reset_motors(self):
    #     self.reset_pos_motor()
    #     time.sleep(1)
    #     self.reset_rot_motor()  
    
    def on_test_capture(self):
        try:
            self.running = True
            self.disable_buttons()
            exposure_value = self.exposure_var.get()
            if exposure_value <= 0:
                self.update_status("Exposure time must be positive")
                self.running = False
                self.enable_buttons()
                return
            
            camera_control = CameraControl()
            capture_display = self.capture_tab.children['!ctkframe2'].children['!ctkframe']
            display_height = capture_display.winfo_height()
            display_width = capture_display.winfo_width()
            current_brightness = self.led1_brightness.get()
            image = camera_control.capture_image(self.auto_imager.usb, display_height, display_width, led_brightness=current_brightness, exposure_ms=exposure_value)
            self.display_image(image, capture_display)
        except Exception as e:
            self.update_status(f"Error during test capture: {e}")
        finally:
            self.running = False
            self.enable_buttons()

    def test_capture_motor(self):
        self.running = True
        self.disable_buttons()
        camera_control = CameraControl()
        capture_display = self.motor_tab.children['!ctkframe2'].children['!ctkframe']
        display_height = self.motor_test_capture_display.winfo_height()
        display_width = self.motor_test_capture_display.winfo_width()
        current_brightness = self.led1_brightness.get()
        image = camera_control.capture_image(self.auto_imager.usb, display_height, display_width, led_brightness=current_brightness)
        self.display_image(image, capture_display)
        self.running = False
        self.enable_buttons()

    def on_run(self):
        magnification_options, lighting_options = self.get_magnification_and_lighting_options()
        self.running = True
        self.disable_buttons()
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.auto_imager.get_control_images(now)
        self.auto_imager.microscope.wait()
        self.auto_imager.get_leica_images(magnification_options, lighting_options, now)
        self.auto_imager.microscope.wait()
        self.running = False
        self.enable_buttons()

        # magnification_options, lighting_options = self.get_magnification_and_lighting_options()
        # self.running = True
        # self.disable_buttons()

        # try:
        #     sample_id = self.sample_id_entry.get().strip()
        #     timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        #     folder_name = sample_id or f"Sample_{timestamp_str.replace(':', '_')}"
        #     save_dir = os.path.join("captured_data", folder_name)
        #     os.makedirs(save_dir, exist_ok=True)

        #     self.auto_imager.get_control_images(timestamp_str)
        #     self.auto_imager.microscope.wait()
        #     self.auto_imager.get_leica_images(magnification_options, lighting_options, timestamp_str)
        #     self.auto_imager.microscope.wait()

        #     root = ET.Element("experiment")
        #     ET.SubElement(root, "sample_id").text = sample_id
        #     ET.SubElement(root, "timestamp").text = timestamp_str

        #     lighting_elem = ET.SubElement(root, "lighting")
        #     for light in lighting_options:
        #         ET.SubElement(lighting_elem, "channel").text = light

        #     mag_elem = ET.SubElement(root, "magnification")
        #     for mag in magnification_options:
        #         ET.SubElement(mag_elem, "objective").text = mag

        #     ET.SubElement(root, "Exposuretime").text = str(self.exposure_var.get())
        #     ET.SubElement(root, "Rotationsteps").text = str(self.rot_var.get())
        #     ET.SubElement(root, "ImageDirectory").text = save_dir

        #     xml_path = os.path.join(save_dir, f"{sample_id}_metadata.xml")
        #     tree = ET.ElementTree(root)
        #     tree.write(xml_path)
        #     self.update_status(f"Metadata saved to {xml_path}")
        # except Exception as e:
        #     self.update_status(f"Error during run: {e}")

        # self.running = False
        # self.enable_buttons()

    def get_magnification_and_lighting_options(self):
        checkboxes = [ c for c in self.capture_tab.children['!ctkframe'].children.values() if isinstance(c, ctk.CTkCheckBox) ]
        filter_map = {
            "White (brightfield)": "White", 
            "Green (340 nm, CH1)": "Green",
            "Blue (430 nm, CH2)": "Blue"
        }
        objective_map = {
        "2.5x": "2.5x",  
        "4x": "4x",
        "10x": "10x"
        }
        lighting_options = []
        for c in checkboxes[:3]:
            if c.get() == "on":
                checkbox_text = c.cget("text")
                if checkbox_text in filter_map:
                    lighting_options.append(filter_map[checkbox_text])
                else:
                    print(f"Warning: No mapping found for '{checkbox_text}'")
        magnification_options = []
        for c in checkboxes[3:]:
            if c.get() == "on":
                checkbox_text = c.cget("text")
                if checkbox_text in objective_map:
                    magnification_options.append(objective_map[checkbox_text])
                else:
                    print(f"Warning: No mapping found for magnification option '{checkbox_text}'")

        return magnification_options, lighting_options
    
    def apply_led_settings(self):
        try:
            if not hasattr(self, 'led_ctrl') or self.led_ctrl is None or self.led_ctrl._usbComm is None:
                self.update_status("LED control not initialized")
                return
            self.led_settings._curr[0] = self.led1_brightness.get()
            self.led_ctrl.SetLed(49406, self.led_settings, True)
            self.update_status("LED settings applied")
        except Exception as e:
            self.update_status(f"Error applying LED settings: {e}")
    
    def disable_buttons(self):
        if not self.running:
            return
        if self.streaming:
            self.test_capture_btn.configure(require_redraw=True, state="disabled", fg_color='gray', hover_color='gray')
            self.run_btn.configure(require_redraw=True, state="disabled", fg_color='gray', hover_color='gray')
        else:
            self.test_capture_btn.configure(require_redraw=True, state="disabled")
            self.run_btn.configure(require_redraw=True, state="disabled")

    def enable_buttons(self):
        self.test_capture_btn.configure(require_redraw=True, state="normal", fg_color='blue')
        self.run_btn.configure(require_redraw=True, state="normal", fg_color='green')
    
    def display_image(self, image, capture_display):
        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
        display_width = capture_display.winfo_width() or 400
        display_height = capture_display.winfo_height() or 300
        img = cv2.resize(img, (capture_display.winfo_width(), capture_display.winfo_height()))

        pil_image = Image.fromarray(img)
        
        photo = ctk.CTkImage(dark_image=pil_image, size=(display_width, display_height))
        label = ctk.CTkLabel(capture_display, image=photo, text='')
        label.place(relx=0.5, rely=0.5, anchor="center")

    def update_status(self, message):
        print(message)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = VAST360CaptureApp()
    app.mainloop()
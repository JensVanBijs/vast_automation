from itertools import tee
import time
import customtkinter as ctk
from main import AutoImager
from PIL import Image, ImageTk
from PIL.Image import Resampling
import numpy as np
from controllers.vast_camera_control import CameraControl
from PIL import Image
from controllers.Motor_Control import Motor
import cv2
from datetime import datetime
from main import AutoImager
from controllers.LEICA_control import MicroscopeManager
import os
import xml.etree.ElementTree as ET
from controllers.led_control import LedCtrl, LedSettings
import json
from pathlib import Path

CONFIG_Path = Path(__file__).parent / "controllers" / "microscope_settings" / "microscope_configuration.json"

try:
    with open(CONFIG_Path, 'r', encoding='utf-8') as f:
        IMAGING_CONFIG = json.load(f)
except Exception as e:
    raise RuntimeError(f"Failed to load microscope configuration from {CONFIG_Path}: {e}")

class VAST360CaptureApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.imaging_config = IMAGING_CONFIG

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
        # self.pos_motor = self.auto_imager.z_positional_motor
        # self.rot_motor = self.auto_imager.rotational_motor

        self.init_motors()

        # Configure window
        self.title("Automatic VAST 360 Capture")
        self.geometry("1400x800")

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
        self.manual_loading_tab = self.tab_view.add("Manual Loading")
        self.capture_tab = self.tab_view.add("Capture")
        self.motor_tab = self.tab_view.add("Motor")

        # Manual loading tab
        self.create_manual_loading_tab()

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
        except Exception as e:
            self.update_status(f"Error initializing motors: {e}")


    def create_manual_loading_tab(self):
        """ Create the Manual Loading tab UI """
        # Main container frame
        main_frame = ctk.CTkFrame(self.manual_loading_tab, fg_color="#7C7C7C", corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="Step-by-Step Guide for Manually Loading Zebrafish", 
                                font=("Arial", 16, "bold"))
        title_label.pack(pady=(20, 10))
        
        # Steps container with scrollable frame
        steps_frame = ctk.CTkScrollableFrame(main_frame, fg_color="#6B6B6B", corner_radius=10)
        steps_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Define the steps
        steps = [
            "Open the VAST software",
            "Flush the system with PRIME",
            "Load the zebrafish into the tube and pump into the capillary with its manual pomping controls",
            "Press LOAD to initialize loading",
            "Once first image is visible, press Abort Operation",
            "Exit VAST software and position your zebrafish from within the Capture and Motor tab",
            "Select magnification and fluorescence options",
            "Enter sample ID and press RUN"
        ]
        
        # Create step widgets
        self.step_widgets = []
        for i, step_text in enumerate(steps, 1):
            # Step container
            step_container = ctk.CTkFrame(steps_frame, fg_color="#5A5A5A", corner_radius=8)
            step_container.pack(fill="x", pady=5, padx=10)
            
            # Step content frame
            step_content = ctk.CTkFrame(step_container, fg_color="transparent")
            step_content.pack(fill="x", padx=15, pady=10)
            
            # Step number circle
            step_number = ctk.CTkLabel(step_content, text=str(i), 
                                    font=("Arial", 12, "bold"),
                                    fg_color="#2196F3", 
                                    corner_radius=15,
                                    width=30, height=30)
            step_number.pack(side="left", padx=(0, 15))
            
            # Step text
            step_label = ctk.CTkLabel(step_content, text=step_text, 
                                    font=("Arial", 12),
                                    anchor="w",
                                    justify="left")
            step_label.pack(side="left", fill="x", expand=True)
            
            # Store reference for potential future use
            self.step_widgets.append({
                'container': step_container,
                'number': step_number,
                'label': step_label,
                'completed': False
            })
        
        # Tips button in bottom right corner
        tips_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        tips_frame.pack(side="bottom", anchor="se", padx=40, pady=30)
        
        self.tips_button = ctk.CTkButton(tips_frame, 
                                        text="💡 Click here for more tips",
                                        font=("Arial", 14),
                                        fg_color="#FFA500",
                                        hover_color="#FF8C00",
                                        corner_radius=20,
                                        command=self.show_tips_popup)
        self.tips_button.pack()

        # Optional: Add functionality to mark steps as complete
        self.add_step_completion_functionality()

    def add_step_completion_functionality(self):
        """ Add click functionality to mark steps as complete """
        for i, step_widget in enumerate(self.step_widgets):
            def make_click_handler(index):
                def on_step_click(event=None):
                    self.toggle_step_completion(index)
                return on_step_click
            
            # Make the step clickable
            click_handler = make_click_handler(i)
            step_widget['container'].bind("<Button-1>", click_handler)
            step_widget['number'].bind("<Button-1>", click_handler)
            step_widget['label'].bind("<Button-1>", click_handler)

    
    def show_tips_popup(self):
        """ Show tips popup window """
        # Create popup window
        tips_window = ctk.CTkToplevel(self)
        tips_window.title("Loading and Imaging Tips")
        tips_window.geometry("800x600")
        tips_window.resizable(True, True)
        
        # Make window modal
        tips_window.transient(self)
        tips_window.grab_set()
        
        # Center the window
        tips_window.after(100, lambda: tips_window.lift())
        
        # Main container
        main_container = ctk.CTkFrame(tips_window, fg_color="#7C7C7C", corner_radius=10)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(main_container, text="💡 Helpful Tips for Loading and Imaging", 
                            font=("Arial", 18, "bold"))
        title.pack(pady=(15, 10))
        
        # Tips container with scrollable frame
        tips_container = ctk.CTkScrollableFrame(main_container, fg_color="#6B6B6B", corner_radius=10)
        tips_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Define tips with categories
        tips_data = [
            {
                "category": "🐟 Sample Preparation",
                "tips": [
                    "Put some soap in your petri dish, to ensure that the zebrafish travels smoothly through the tube",
                    "Make sure that the container is filled up with enough water"
                ]
            },
            {
                "category": "🔧 Loading Process",
                "tips": [
                    "Prime the system thoroughly to remove all air bubbles before loading",
                    "Load fish head-first for consistent orientation across samples",
                    "If fish gets stuck, reverse the pump briefly and try again with less pressure"
                ]
            },
            {
                "category": "📷 Imaging Optimization",
                "tips": [
                    "For fluorescence imaging, minimize ambient light in the room", 
                    "Adjust the microscropic camera such that it is properly focused on the zebrafish",
                    "To adjust exposure time or brightness of the microscopic camera, change it in controllers/microscope_settings/microscope_configuration.json"
                ]
            },
            {
                "category": "⚡ Troubleshooting",
                "tips": [
                    "Motor movement issues? Check that motors are properly initialized before use",
                    "If software becomes unresponsive, restart the application and re-initialize all components",
                    "No view from microscopic camera? Make sure that the pin is properly extended"
                ]
            }
        ]
        
        # Create tip sections
        for section in tips_data:
            # Category header
            category_frame = ctk.CTkFrame(tips_container, fg_color="#5A5A5A", corner_radius=8)
            category_frame.pack(fill="x", pady=(10, 5), padx=10)
            
            category_label = ctk.CTkLabel(category_frame, text=section["category"], 
                                        font=("Arial", 14, "bold"),
                                        anchor="w")
            category_label.pack(anchor="w", padx=15, pady=10)
            
            # Tips for this category
            for tip in section["tips"]:
                tip_frame = ctk.CTkFrame(tips_container, fg_color="#4A4A4A", corner_radius=6)
                tip_frame.pack(fill="x", pady=2, padx=20)
                
                tip_label = ctk.CTkLabel(tip_frame, text=f"• {tip}", 
                                        font=("Arial", 13),
                                        anchor="w",
                                        justify="left",
                                        wraplength=500)
                tip_label.pack(anchor="w", padx=15, pady=8, fill="x")
        
        # Close button
        close_button = ctk.CTkButton(main_container, text="Close", 
                                    command=tips_window.destroy,
                                    fg_color="#2196F3",
                                    hover_color="#1976D2",
                                    width=100)
        close_button.pack(pady=(0, 15))


    def toggle_step_completion(self, step_index):
        """ Toggle completion status of a step """
        step_widget = self.step_widgets[step_index]
        
        if step_widget['completed']:
            # Mark as incomplete
            step_widget['number'].configure(fg_color="#2196F3")
            step_widget['container'].configure(fg_color="#5A5A5A")
            step_widget['completed'] = False
        else:
            # Mark as complete
            step_widget['number'].configure(fg_color="#4CAF50")
            step_widget['container'].configure(fg_color="#4A4A4A")
            step_widget['completed'] = True
            
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

        fluorescence_options = ["White (brightfield)", "Green (visualizes red fluorescence)", "Blue (visualizes green fluorescence)"]
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
        self.capture_display = ctk.CTkFrame(right_frame, height=300, width=1024, fg_color="black")
        self.capture_display.pack(padx=10, pady=10, expand=True, fill="both")

        label = ctk.CTkLabel(self.capture_display, text="Test capture", text_color="white")
        label.place(relx=0.5, rely=0.5, anchor="center")

        # Progress section
        progress_frame = ctk.CTkFrame(right_frame, fg_color="#6B6B6B", corner_radius=10)
        progress_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Time estimation display
        self.time_info_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        self.time_info_frame.pack(fill="x", padx=10, pady=5)

        self.time_estimate_label = ctk.CTkLabel(self.time_info_frame, text="Estimated time: --", 
                                            font=("Arial", 12, "bold"))
        self.time_estimate_label.pack(anchor="w")

        self.time_remaining_label = ctk.CTkLabel(self.time_info_frame, text="Time remaining: --", 
                                            font=("Arial", 11))
        self.time_remaining_label.pack(anchor="w")

        # Progress bar container
        progress_container = ctk.CTkFrame(progress_frame, fg_color="transparent")
        progress_container.pack(pady=10)

        # Create circular progress bar canvas
        self.progress_canvas = ctk.CTkCanvas(progress_container, width=120, height=120, 
                                    bg="#6B6B6B", highlightthickness=0)
        self.progress_canvas.pack()

        # Progress text labels
        self.progress_text_label = ctk.CTkLabel(progress_frame, text="0 / 0 images", 
                                            font=("Arial", 11))
        self.progress_text_label.pack()

        self.progress_percentage_label = ctk.CTkLabel(progress_frame, text="0%", 
                                                    font=("Arial", 14, "bold"))
        self.progress_percentage_label.pack()

        # Update time estimation when checkboxes change
        self.bind_checkbox_updates()

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

        # initialize progress bar 
        self.draw_progress_circle(0)
        self.update_time_estimation()

        # Grid configuration
        self.capture_tab.grid_columnconfigure(0, weight=1)
        self.capture_tab.grid_columnconfigure(1, weight=3)
        self.capture_tab.grid_rowconfigure(0, weight=1)

    def bind_checkbox_updates(self):
        """ Bind checkbox changes to update time estimation """
        # This needs to be called after checkboxes are created
        def update_estimation(*args):
            self.after(100, self.update_time_estimation)  # Small delay to ensure checkbox state is updated
        
        # Bind to all fluorescence and magnification checkboxes
        for var in self.fluorescence_vars.values():
            var.trace_add("write", update_estimation)
        
        for var in self.magnification_vars.values():
            var.trace_add("write", update_estimation)

    def calculate_imaging_time(self):
        """ Calculate total imaging time based on selected options """
        magnification_options, lighting_options = self.get_magnification_and_lighting_options()
        
        if not magnification_options or not lighting_options:
            return 0, 0
        
        total_time_ms = 0
        total_images = 0
        images_per_channel = 500
        
        for mag in magnification_options:
            for channel in lighting_options:
                if mag in self.imaging_config["objectives"] and channel in self.imaging_config["filters"]:
                    exposure_time = self.imaging_config["filters"][channel]["exposure"]
                    channel_time = images_per_channel * exposure_time
                    total_time_ms += channel_time
                    total_images += images_per_channel
        
        return total_time_ms, total_images

    def format_time(self, milliseconds):
        """ Format time from milliseconds to readable format """
        if milliseconds == 0:
            return "--"
        
        seconds = milliseconds / 1000
        
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    def update_time_estimation(self):
        """ Update the time estimation display """
        total_time_ms, total_images = self.calculate_imaging_time()
        
        self.total_images = total_images
        self.estimated_time = total_time_ms
        
        formatted_time = self.format_time(total_time_ms)
        self.time_estimate_label.configure(text=f"Estimated time: {formatted_time}")
        
        if total_images > 0:
            self.progress_text_label.configure(text=f"0 / {total_images} images")
        else:
            self.progress_text_label.configure(text="0 / 0 images")

    def draw_progress_circle(self, percentage):
        """ Draw circular progress bar """
        self.progress_canvas.delete("all")
        
        # Canvas dimensions
        width = 120
        height = 120
        center_x = width // 2
        center_y = height // 2
        radius = 45
        
        # Background circle
        self.progress_canvas.create_oval(center_x - radius, center_y - radius,
                                    center_x + radius, center_y + radius,
                                    outline="#404040", width=8, fill="")
        
        # Progress arc
        if percentage > 0:
            # Calculate angle (tkinter uses degrees, starting from 3 o'clock, going clockwise)
            # We want to start from 12 o'clock, so we subtract 90 degrees
            start_angle = 90  # Start from top
            extent_angle = -(percentage / 100) * 360  # Negative for clockwise
            
            self.progress_canvas.create_arc(center_x - radius, center_y - radius,
                                        center_x + radius, center_y + radius,
                                        start=start_angle, extent=extent_angle,
                                        outline="#4CAF50", width=8, style="arc")
        
        # Center text showing percentage
        self.progress_canvas.create_text(center_x, center_y, text=f"{percentage:.1f}%",
                                    fill="white", font=("Arial", 14, "bold"))

    def update_progress(self, current_image):
        """ Update progress bar and labels """
        self.current_image = current_image
        
        if self.total_images > 0:
            percentage = (current_image / self.total_images) * 100
            self.draw_progress_circle(percentage)
            self.progress_text_label.configure(text=f"{current_image} / {self.total_images} images")
            self.progress_percentage_label.configure(text=f"{percentage:.1f}%")
            
            # Calculate remaining time
            if self.start_time and current_image > 0:
                elapsed_time = time.time() - self.start_time
                avg_time_per_image = elapsed_time / current_image
                remaining_images = self.total_images - current_image
                remaining_time_seconds = remaining_images * avg_time_per_image
                
                remaining_time_formatted = self.format_time(remaining_time_seconds * 1000)
                self.time_remaining_label.configure(text=f"Time remaining: {remaining_time_formatted}")

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

        separator2 = ctk.CTkFrame(motor_frame, height=2, width=200, fg_color="gray")
        separator2.pack(pady=10, fill="x")

        # Right section: Test capture
        right_frame = ctk.CTkFrame(self.motor_tab, fg_color="gray30")
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.motor_test_capture_display = ctk.CTkFrame(right_frame, height=300, width=1024, fg_color="black")
        self.motor_test_capture_display.pack(padx=10, pady=10)

        stream_label = ctk.CTkLabel(self.motor_test_capture_display, text="Test Capture", text_color="white")
        stream_label.place(relx=0.5, rely=0.5, anchor="center")

        self.motor_test_capture_btn = ctk.CTkButton(right_frame, text="Test capture", fg_color="green", hover_color="darkgreen", command=self.test_capture_motor)
        self.motor_test_capture_btn.pack(pady=10)

        # Grid configuration
        self.motor_tab.grid_columnconfigure(0, weight=1)
        self.motor_tab.grid_columnconfigure(1, weight=3)
        self.motor_tab.grid_rowconfigure(0, weight=1)

    def move_pos_motor_left(self):
        try:
            if self.pos_motor:
                distance = self.pos_var.get()
                print(f"Moving positional motor left by {distance} steps")
                self.pos_motor.SelectMotor()
                print(self.pos_motor)
                self.pos_motor.move_z_motor(distance, "left")
                print(self.pos_motor.move_z_motor(distance, "left"))

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
    
    def on_test_capture(self):
        try:
            self.running = True
            self.disable_buttons()
            camera_control = CameraControl()
            capture_display = self.capture_tab.children['!ctkframe2'].children['!ctkframe']
            display_height = capture_display.winfo_height()
            display_width = capture_display.winfo_width()
            current_brightness = self.led1_brightness.get()
            image = camera_control.capture_image(self.auto_imager.usb, display_height, display_width, led_brightness=current_brightness)
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
        self.start_time = time.time()
        self.current_image = 0
        self.update_progress(0)
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        sample_id = self.sample_id_entry.get()
        if not sample_id:
            sample_id = now
        current_brightness = self.led1_brightness.get()
        self.auto_imager.get_control_images(sample_id, current_brightness)
        self.auto_imager.microscope.wait()
        self.auto_imager.get_leica_images(magnification_options, lighting_options, sample_id, progress_callback=self.update_progress)
        self.auto_imager.microscope.wait()
        self.update_progress(self.total_images)
        self.time_remaining_label.configure(text="Completed!")
        self.running = False
        self.enable_buttons()
    
    def get_magnification_and_lighting_options(self):
        checkboxes = [ c for c in self.capture_tab.children['!ctkframe'].children.values() if isinstance(c, ctk.CTkCheckBox) ]
        filter_map = {
            "White (brightfield)": "White", 
            "Green (visualizes red fluorescence)": "Green",
            "Blue (visualizes green fluorescence)": "Blue"
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
        display_width = capture_display.winfo_width() or 400
        display_height = capture_display.winfo_height() or 300
        aspect_ratio = image.shape[1] / image.shape[0]

        pil_image = Image.fromarray(image)
        
        if display_width / aspect_ratio <= display_height:
            new_width = display_width
            new_height = int(display_width / aspect_ratio)
        else:
            new_height = display_height
            new_width = int(display_height * aspect_ratio)

        pil_image = pil_image.resize((new_width, new_height))

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
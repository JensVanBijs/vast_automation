import time
import customtkinter as ctk
# from main import AutoImager
from PIL import Image, ImageTk
from PIL.Image import Resampling
import numpy as np
# from controllers.vast_camera_control import CameraControl

class VAST360CaptureApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # self.auto_imager = AutoImager()
        self.running = False
        self.streaming = False

        self.pos_var = ctk.IntVar(value=1)   # Define pos_var
        self.rot_var = ctk.IntVar(value=10)

        # Configure window
        self.title("Automatic VAST 360 Capture")
        self.geometry("900x600")

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

    def create_capture_tab(self):
        """ Create the Capture tab UI """
        # Left section: Fluorescence & Magnification
        left_frame = ctk.CTkFrame(self.capture_tab, fg_color="#7C7C7C", corner_radius=10)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Fluorescence section
        fluorescence_label = ctk.CTkLabel(left_frame, text="Fluorescence", font=("Arial", 14, "bold"))
        fluorescence_label.pack(padx=10, pady=(10, 5), anchor="w")

        fluorescence_options = ["White", "Green", "Blue"]
        self.fluorescence_vars = {}
        for option in fluorescence_options:
            var = ctk.StringVar(value="on")
            checkbox = ctk.CTkCheckBox(left_frame, text=option, variable=var, onvalue="on", offvalue="off")
            checkbox.pack(anchor="w", padx=10)

            spacer = ctk.CTkFrame(left_frame, height=10, fg_color='transparent') 
            spacer.pack()

            self.fluorescence_vars[option] = var

        # Magnification section
        magnification_label = ctk.CTkLabel(left_frame, text="Magnification", font=("Arial", 14, "bold"))
        magnification_label.pack(padx=10, pady=(10, 5), anchor="w")

        magnification_options = ["2.5x", "4x", "10x"]
        self.magnification_vars = {}
        for option in magnification_options:
            var = ctk.StringVar(value="on")
            checkbox = ctk.CTkCheckBox(left_frame, text=option, variable=var, onvalue="on", offvalue="off")
            checkbox.pack(anchor="w", padx=10)
            spacer = ctk.CTkFrame(left_frame, height=10, fg_color='transparent')  # Adjust height for spacing
            spacer.pack()
            self.magnification_vars[option] = var

        # Right section: Stream/Test Capture
        right_frame = ctk.CTkFrame(self.capture_tab, fg_color="#7C7C7C", corner_radius=10)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Display area
        capture_display = ctk.CTkFrame(right_frame, height=300, width=400, fg_color="black")
        capture_display.pack(padx=10, pady=10, expand=True, fill="both")

        label = ctk.CTkLabel(capture_display, text="Stream / Test capture", text_color="white")
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

        self.stream_btn = ctk.CTkButton(button_frame, 
                                        text="Stream", 
                                        fg_color="green", 
                                        hover_color="darkgreen", 
                                        command=self.toggle_stream)
        self.stream_btn.pack(side="left", padx=5, expand=True, fill="x")


        self.run_btn = ctk.CTkButton(button_frame, text="Run", fg_color="green", hover_color="darkgreen")
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
        pos_label = ctk.CTkLabel(motor_frame, text="Positional motor", font=("Arial", 14, "bold"))
        pos_label.pack(pady=(10, 5), anchor="center")

        pos_control = ctk.CTkEntry(motor_frame, textvariable=self.pos_var, width=50)
        pos_control.pack(pady=5)

        # Create a frame for positional motor buttons
        pos_button_frame = ctk.CTkFrame(motor_frame, fg_color="transparent")
        pos_button_frame.pack(pady=5)

        self.pos_btn_left = ctk.CTkButton(pos_button_frame, text="←", width=40)
        self.pos_btn_left.pack(side="left", padx=5)

        self.pos_btn_right = ctk.CTkButton(pos_button_frame, text="→", width=40)
        self.pos_btn_right.pack(side="left", padx=5)

        # Rotational Motor Controls
        rot_label = ctk.CTkLabel(motor_frame, text="Rotational motor", font=("Arial", 14, "bold"))
        rot_label.pack(pady=(10, 5), anchor="center")

        rot_control = ctk.CTkEntry(motor_frame, textvariable=self.rot_var, width=50)
        rot_control.pack(pady=5)

        # Create a frame for rotational motor buttons
        rot_button_frame = ctk.CTkFrame(motor_frame, fg_color="transparent")
        rot_button_frame.pack(pady=5)

        self.rot_btn_left = ctk.CTkButton(rot_button_frame, text="⟲", width=40)
        self.rot_btn_left.pack(side="left", padx=5)

        self.rot_btn_right = ctk.CTkButton(rot_button_frame, text="⟳", width=40)
        self.rot_btn_right.pack(side="left", padx=5)


        # Right section: Streaming
        right_frame = ctk.CTkFrame(self.motor_tab, fg_color="gray30")
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        stream_display = ctk.CTkFrame(right_frame, height=300, width=400, fg_color="black")
        stream_display.pack(padx=10, pady=10, expand=True, fill="both")

        stream_label = ctk.CTkLabel(stream_display, text="Stream", text_color="white")
        stream_label.place(relx=0.5, rely=0.5, anchor="center")

        self.stream_btn = ctk.CTkButton(right_frame, text="Stream", fg_color="green", hover_color="darkgreen")
        self.stream_btn.pack(pady=10)

        # Grid configuration
        self.motor_tab.grid_columnconfigure(0, weight=1)
        self.motor_tab.grid_columnconfigure(1, weight=3)
        self.motor_tab.grid_rowconfigure(0, weight=1)
    
    def on_test_capture(self):
        # self.running = True
        # self.disable_buttons()
        # camera_control = CameraControl()
        # display_height = self.capture_tab.children[1].children[0].winfo_height()
        # display_width = self.capture_tab.children[1].children[0].winfo_width()
        # image = camera_control.capture_image(self.auto_imager.usb, display_height, display_width)
        # self.display_image(image)
        # self.running = False
        # self.enable_buttons()

        # Load image from downloads
        image_path = "/Users/coenwerre/Downloads/Domme foto.JPG"
        image = Image.open(image_path)

        # Convert image to numpy array
        image_array = np.array(image)
        self.display_image(image_array)
        
    def toggle_stream(self):
        pass

    def on_run(self):
        pass

    def disable_buttons(self):
        if not self.running:
            return
        
        if self.streaming:
             # If streaming, only keep stream button enabled
            self.test_capture_btn.configure(require_redraw=True, state="disabled", fg_color='gray', hover_color='gray')
            self.run_btn.configure(require_redraw=True, state="disabled", fg_color='gray', hover_color='gray')
        else:
            # If not streaming, disable all buttons except the current active one
            self.test_capture_btn.configure(require_redraw=True, state="disabled")
            self.stream_btn.configure(require_redraw=True, state="disabled")
            self.run_btn.configure(require_redraw=True, state="disabled")

    def enable_buttons(self):
        self.test_capture_btn.configure(require_redraw=True, state="normal", fg_color='blue')
        self.stream_btn.configure(require_redraw=True, state="normal")
        self.run_btn.configure(require_redraw=True, state="normal", fg_color='green')
    
    def display_image(self, image):
        capture_display = self.capture_tab.children['!ctkframe2'].children['!ctkframe']
        pil_image = Image.fromarray(image)
        
        # Get current display size
        display_width = capture_display.winfo_width() or 400
        display_height = capture_display.winfo_height() or 300
        
        # Resize image
        pil_image.thumbnail((display_width, display_height), Resampling.LANCZOS)
        
        # Convert to PhotoImage
        photo = ctk.CTkImage(dark_image=pil_image, size=(display_width, display_height))
        label = ctk.CTkLabel(capture_display, image=photo, text='')
        label.place(relx=0.5, rely=0.5, anchor="center")
        
        # # Update the label
        # capture_display.configure(label=label)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = VAST360CaptureApp()
    app.mainloop()
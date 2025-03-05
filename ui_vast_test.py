import customtkinter as ctk

class VAST360CaptureApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Automatic VAST 360 Capture")
        self.geometry("600x400")
        
        # Tabs 
        tab_view = ctk.CTkTabview(self)
        tab_view.pack(fill="both", expand=True, padx=10, pady=10)

        # Left side - Capture and Magnification sections
        left_frame = ctk.CTkFrame(main_frame, fg_color="gray30")
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Fluorescence section
        fluorescence_label = ctk.CTkLabel(left_frame, text="Fluorescence", font=("Arial", 14, "bold"))
        fluorescence_label.pack(pady=(10, 5), anchor="w")

        fluorescence_options = ["Brightfield", "Green", "Blue"]
        self.fluorescence_vars = {}
        for option in fluorescence_options:
            var = ctk.StringVar(value="on")
            checkbox = ctk.CTkCheckBox(left_frame, text=option, variable=var, 
                                       onvalue="on", offvalue="off")
            checkbox.pack(anchor="w", padx=10)
            self.fluorescence_vars[option] = var

        # Magnification section
        magnification_label = ctk.CTkLabel(left_frame, text="Magnification", font=("Arial", 14, "bold"))
        magnification_label.pack(pady=(10, 5), anchor="w")

        magnification_options = ["2.5x", "4x", "10x"]
        self.magnification_vars = {}
        for option in magnification_options:
            var = ctk.StringVar(value="on")
            checkbox = ctk.CTkCheckBox(left_frame, text=option, variable=var, 
                                       onvalue="on", offvalue="off")
            checkbox.pack(anchor="w", padx=10)
            self.magnification_vars[option] = var

        # Right side - Stream/Test Capture and Buttons
        right_frame = ctk.CTkFrame(main_frame, fg_color="gray30")
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Stream/Test Capture display
        capture_display = ctk.CTkFrame(right_frame, height=300, width=400, fg_color="black")
        capture_display.pack(padx=10, pady=10, expand=True, fill="both")

        label = ctk.CTkLabel(capture_display, text="Stream / Test capture", text_color="white")
        label.place(relx=0.5, rely=0.5, anchor="center")

        # Buttons
        button_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)

        test_capture_btn = ctk.CTkButton(button_frame, text="Test capture", fg_color="blue", hover_color="darkblue")
        test_capture_btn.pack(side="left", padx=5, expand=True, fill="x")

        stream_btn = ctk.CTkButton(button_frame, text="Stream", fg_color="green", hover_color="darkgreen")
        stream_btn.pack(side="left", padx=5, expand=True, fill="x")

        run_btn = ctk.CTkButton(button_frame, text="Run", fg_color="gray", hover_color="darkgray")
        run_btn.pack(side="left", padx=5, expand=True, fill="x")

        # Configure grid weights
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=3)
        main_frame.grid_rowconfigure(0, weight=1)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = VAST360CaptureApp()
    app.mainloop()
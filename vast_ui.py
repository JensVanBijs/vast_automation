import customtkinter as ctk

class VastUI(ctk.CTk):
    def __init__(self): 
        super().__init__()
        self.title("Vast UI")
        self.geometry("720x480")
        self.resizable(False, False)
        self.create_widgets()
        self.mainloop()
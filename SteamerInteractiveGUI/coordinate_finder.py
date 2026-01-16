import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageOps
import os
import sys

class CoordinateFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("Coordinate Finder - High Res Recalibration")
        self.root.geometry("1600x900") # Large window

        # Try to load the Render image for recalibration
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.image_path = os.path.join(base_dir, "Renders", "alloff.jpg")
            
            print(f"Loading: {self.image_path}")
            # Load basic RGB
            raw_img = Image.open(self.image_path).convert("RGB")

            # NO INVERSION for Renders - they are photos
            
            self.pil_image = raw_img
            print(f"Loaded Image Size: {self.pil_image.size}")

            # --- AUTO-SCALE FOR DISPLAY ---
            self.scale_factor = 1.0
            display_img = self.pil_image
            
            # Target display area (approx window size minus pads)
            target_w, target_h = 1500, 800
            w, h = self.pil_image.size
            
            if w > target_w or h > target_h:
                ratio = min(target_w/w, target_h/h)
                new_size = (int(w * ratio), int(h * ratio))
                display_img = self.pil_image.resize(new_size, Image.Resampling.LANCZOS)
                self.scale_factor = ratio
                print(f"Display Scale Factor: {self.scale_factor:.4f} (Display Size: {new_size})")
                
            self.tk_image = ImageTk.PhotoImage(display_img)

        except Exception as e:
            print(f"Error loading default image: {e}")
            self.image_path = filedialog.askopenfilename(title="Select your Steamer Image")
            if not self.image_path:
                return
            self.pil_image = Image.open(self.image_path)
            self.scale_factor = 1.0
            self.tk_image = ImageTk.PhotoImage(self.pil_image)

        # -----------------
        # Scrollable Canvas
        # -----------------
        self.container = tk.Frame(root)
        self.container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.container, bg="#202020", highlightthickness=0)
        
        self.v_scroll = tk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.h_scroll = tk.Scrollbar(self.container, orient="horizontal", command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
        
        # Configure scrolling region to DISPLAY size
        self.canvas.config(scrollregion=(0, 0, self.tk_image.width(), self.tk_image.height()))

        # Output box (Bottom)
        self.text_output = tk.Text(root, height=8, bg="#333", fg="white", font=("Consolas", 10))
        self.text_output.pack(side="bottom", fill="x")
        self.text_output.insert("1.0", "INSTRUCTIONS:\n1. Click CENTER of each button.\n2. Screen is scaled down, but output coordinates are FULL RESOLUTION.\n\n")

        # Click event - bind to canvas
        self.canvas.bind("<Button-1>", self.on_click)

    def on_click(self, event):
        # Account for scrolling offset
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Calculate Original Coordinates
        orig_x = int(canvas_x / self.scale_factor)
        orig_y = int(canvas_y / self.scale_factor)
        
        # Visual Marker (on display size)
        x, y = canvas_x, canvas_y
        r = 10
        self.canvas.create_oval(x-r, y-r, x+r, y+r, outline="#00ff00", width=2)
        self.canvas.create_line(x-r, y, x+r, y, fill="#00ff00")
        self.canvas.create_line(x, y-r, x, y+r, fill="#00ff00")
        
        # Log
        msg = f'"{orig_x}, {orig_y}",\n'
        print(f"Point: {orig_x}, {orig_y}")
        self.text_output.insert("end", msg)
        self.text_output.see("end")

if __name__ == "__main__":
    root = tk.Tk()
    app = CoordinateFinder(root)
    root.mainloop()

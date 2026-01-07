import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

class CoordinateFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("Coordinate Finder")
        
        # Load the image
        # Assuming the image is in the same directory, but using filedialog to be safe or flexible
        try:
            self.image_path = "test drawing 2.JPG" 
            self.pil_image = Image.open(self.image_path)
            self.tk_image = ImageTk.PhotoImage(self.pil_image)
        except Exception as e:
            print(f"Error loading default image: {e}")
            self.image_path = filedialog.askopenfilename(title="Select your Steamer Image")
            if not self.image_path:
                return
            self.pil_image = Image.open(self.image_path)
            self.tk_image = ImageTk.PhotoImage(self.pil_image)

        # Canvas for the image
        self.canvas = tk.Canvas(root, width=self.tk_image.width(), height=self.tk_image.height())
        self.canvas.pack()
        
        # Place image on canvas
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        
        # Output box
        self.text_output = tk.Text(root, height=10, width=50)
        self.text_output.pack(pady=10)
        self.text_output.insert("1.0", "Click on the center of each button (Power, Boost, Hold) to get coordinates.\n")
        
        # Click event
        self.canvas.bind("<Button-1>", self.on_click)

    def on_click(self, event):
        x, y = event.x, event.y
        # Draw a small temporary circle (standard circle marker)
        r = 5
        self.canvas.create_oval(x-r, y-r, x+r, y+r, outline="red", width=2)
        
        # Log coordinates
        msg = f"Clicked at: ({x}, {y})\n"
        print(msg.strip())
        self.text_output.insert("end", msg)
        self.text_output.see("end")

if __name__ == "__main__":
    root = tk.Tk()
    app = CoordinateFinder(root)
    root.mainloop()

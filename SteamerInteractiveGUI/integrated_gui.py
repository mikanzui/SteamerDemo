import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk, ImageDraw, ImageChops, ImageFilter
import math
import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

class SteamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Steamer Interactive GUI")
        
        # -----------------
        # Window Setup
        # -----------------
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.85)
        
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        # -----------------
        # Configuration
        # -----------------
        self.original_points = {
            "Power": (365, 292),
            "Boost": (366, 337),
            "Hold": (777, 364),
            "Steam": (1385, 173),
            "Power_Side": (1051, 291),
            "Boost_Side": (1051, 341)
        }
        self.original_radius = 25 
        
        self.light_colors = {
            "Power": (0, 255, 0),    # Green 
            "Boost": (255, 165, 0),  # Orange 
            "Hold": (0, 255, 255),   # Cyan
            "Steam": (0, 150, 255),  # Visual Blue for steam visibility
            "Power_Side": (0, 255, 0),
            "Boost_Side": (255, 165, 0)
        }
        
        self.current_scale = 1.0
        
        # State
        self.power_on = False
        self.mode = 1 
        self.hold_active = False 

        # Styles
        self.configure_styles()
        
        # -----------------
        # UI Layout Structure
        # -----------------
        # 1. Top Controls
        self.controls_frame = tk.Frame(root, padx=20, pady=15, bg="#2b2b2b", relief="ridge", borderwidth=0)
        self.controls_frame.pack(side="top", fill="x")
        self.setup_controls()

        # 2. Main Content Area (Split into Left Image, Right Info)
        self.main_content = tk.Frame(root, bg="#1e1e1e")
        self.main_content.pack(side="bottom", fill="both", expand=True)

        # 2a. Right Info Panel (Fixed width)
        self.info_panel = tk.Frame(self.main_content, width=300, bg="#252526", relief="flat")
        self.info_panel.pack(side="right", fill="y", padx=1, pady=1)
        self.info_panel.pack_propagate(False) # Force width
        self.setup_info_panel()

        # 2b. Left Image Area (Expands)
        self.image_frame = tk.Frame(self.main_content, bg="#e6e6e6")
        self.image_frame.pack(side="left", fill="both", expand=True)

        # Guide Label
        self.guide_label = tk.Label(self.image_frame, text="INTERACTIVE MODE: Click the buttons on the product image (Main or Side view) to operate.", 
                              bg="#e6e6e6", fg="#333333", font=("Segoe UI", 10, "bold"))
        self.guide_label.pack(side="bottom", pady=5)

        # -----------------
        # Load Image
        # -----------------
        try:
            self.image_path = resource_path("test drawing 2.png")
            self.base_image_original = Image.open(self.image_path).convert("RGBA")
            self.current_processed_image = self.base_image_original.copy()
            self.orig_w, self.orig_h = self.base_image_original.size
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image.\nError: {e}")
            root.destroy()
            return

        # Canvas
        self.canvas = tk.Canvas(self.image_frame, bg="#e6e6e6", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.image_id = self.canvas.create_image(0, 0, anchor="center")
        
        # Bind events
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Initial Draw
        self.refresh_ui()

    def configure_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam') 
        self.style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=6, background="#333333")
        self.style.map('TButton', background=[('active', '#555555'), ('pressed', '#777777')], foreground=[('!disabled', 'white')])

    def setup_controls(self):
        container = tk.Frame(self.controls_frame, bg="#2b2b2b")
        container.pack(anchor="center")
        
        self.create_control_group(container, "MAIN POWER", "Power", self.toggle_power, "POWER")
        tk.Frame(container, width=2, bg="#555555", height=40).pack(side="left", padx=20, fill="y")
        self.create_control_group(container, "INTENSITY", "Boost", self.toggle_boost, "BOOST")
        tk.Frame(container, width=2, bg="#555555", height=40).pack(side="left", padx=20, fill="y")
        self.create_control_group(container, "OPERATION", "Hold", None, "HOLD FOR STEAM", is_hold_btn=True, btn_width=20)

    def create_control_group(self, parent, label_text, key_name, command, btn_text, is_hold_btn=False, btn_width=14):
        frame = tk.Frame(parent, bg="#2b2b2b")
        frame.pack(side="left")
        tk.Label(frame, text=label_text, bg="#2b2b2b", fg="#aaaaaa", font=("Segoe UI", 8)).pack(side="top", pady=(0,5))
        row_frame = tk.Frame(frame, bg="#2b2b2b")
        row_frame.pack(side="top")
        btn = ttk.Button(row_frame, text=btn_text, width=btn_width, command=command)
        btn.pack(side="left", padx=5)
        
        if is_hold_btn:
            btn.bind("<ButtonPress-1>", lambda e: self.start_hold())
            btn.bind("<ButtonRelease-1>", lambda e: self.stop_hold())
            self.steam_indicator = tk.Label(row_frame, text="STANDBY", font=('Segoe UI', 9, 'bold'), width=12, bg="#2b2b2b", fg="#555555", relief="flat")
            self.steam_indicator.pack(side="left", padx=5)
        else:
            canvas_light = tk.Canvas(row_frame, width=16, height=16, bg="#2b2b2b", highlightthickness=0)
            canvas_light.pack(side="left", padx=5)
            canvas_light.create_oval(2, 2, 14, 14, fill="#404040", outline="#555555", tags="led")
            setattr(self, f"{key_name.lower()}_led", canvas_light)

    def refresh_ui(self):
        self.process_light_layer()
        self.display_current_image()
        self.update_info_panel()
        self.update_flowchart_hightlight()

    def update_info_panel(self):
        # Update LEDs
        # Power LED simple on/off (Green)
        self.power_led.itemconfig("led", fill="#00ff00" if self.power_on else "#404040")
        
        # Boost LED logic (Orange)
        boost_active = self.power_on and (self.mode == 2)
        self.boost_led.itemconfig("led", fill="#d18c02" if boost_active else "#404040")

        # Text Status
        if self.power_on:
            if self.hold_active:
                txt = "STEAMING"
                col = "#00aaaa" # Cyan
            else:
                txt = "READY"
                col = "#00ff00" # Green
        else:
            txt = "STANDBY"
            col = "#555555"
            
        self.steam_indicator.config(text=txt, fg=col)

    def setup_info_panel(self):
        # Header
        header = tk.Label(self.info_panel, text="State Overview", bg="#252526", fg="white", font=("Segoe UI", 12, "bold"))
        header.pack(pady=(20, 10), padx=10, anchor="w")
        
        description = tk.Label(self.info_panel, text="Logic Decision Tree:", bg="#252526", fg="#aaaaaa", font=("Segoe UI", 9))
        description.pack(pady=(0, 10), padx=10, anchor="w")

        # Flow Diagram Canvas
        self.flow_canvas = tk.Canvas(self.info_panel, bg="#252526", highlightthickness=0, height=450)
        self.flow_canvas.pack(fill="x", padx=10)
        
        self.draw_flowchart()

    def draw_flowchart(self):
        self.flow_canvas.delete("all")
        
        # --- Config ---
        cx = 150 # Center of canvas (approx width 300)
        
        # Styles
        box_style = {"fill": "#333333", "outline": "#555555", "width": 1}
        text_style = {"fill": "#aaaaaa", "font": ("Segoe UI", 8, "bold"), "justify": "center"}
        arrow_opts = {"fill": "#666666", "width": 1, "arrow": tk.LAST}

        def draw_box(x, y, w, h, text, tag):
            x1, y1 = x - w/2, y - h/2
            x2, y2 = x + w/2, y + h/2
            
            # Rect
            self.flow_canvas.create_rectangle(x1, y1, x2, y2, **box_style, tags=("box", f"box_{tag}"))
            # Text
            self.flow_canvas.create_text(x, y, text=text, **text_style, tags=("text", f"text_{tag}"))
            
            return x1, y1, x2, y2, x, y # Return geometry for lines

        def draw_line(x1, y1, x2, y2):
            self.flow_canvas.create_line(x1, y1, x2, y2, **arrow_opts)

        # Labels for transitions
        def label_line(x, y, txt):
            self.flow_canvas.create_text(x, y, text=txt, fill="#888888", font=("Segoe UI", 7, "italic"))

        # --- Nodes ---
        
        # Level 1: OFF
        _, _, _, b_off_y2, off_x, off_y = draw_box(cx, 40, 80, 30, "OFF", "off")
        
        # Level 2: ON (Split into Normal and Boost columns)
        # Left Column (Normal): x = 80
        # Right Column (Boost): x = 220
        norm_x = 80
        boost_x = 220
        l2_y = 130
        
        _, b_norm_y1, _, b_norm_y2, _, _ = draw_box(norm_x, l2_y, 90, 40, "ON\n(Normal)", "normal")
        _, b_boost_y1, _, b_boost_y2, _, _ = draw_box(boost_x, l2_y, 90, 40, "ON\n(Boost)", "boost")

        # Level 3: Hold / Steam
        l3_y = 250
        draw_box(norm_x, l3_y, 90, 40, "STEAM\n(Normal)", "steam_norm")
        draw_box(boost_x, l3_y, 90, 40, "STEAM\n(Boost)", "steam_boost")

        # --- Connections ---
        
        # Power ON (Off -> Normal)
        draw_line(off_x, b_off_y2, norm_x, b_norm_y1)
        label_line((off_x+norm_x)/2, (b_off_y2+b_norm_y1)/2, "Power")

        # Boost Toggle (Normal <-> Boost)
        # Draw double arrow line between them
        boost_arrow_opts = arrow_opts.copy()
        boost_arrow_opts['arrow'] = tk.BOTH
        self.flow_canvas.create_line(norm_x+45, l2_y, boost_x-45, l2_y, **boost_arrow_opts)
        label_line(cx, l2_y-10, "Boost")

        # Hold Steam (Normal -> Steam Norm)
        draw_line(norm_x, b_norm_y2, norm_x, l3_y-20) # manual offset for top of box
        label_line(norm_x+5, (b_norm_y2+l3_y-20)/2, "Hold")

        # Hold Steam (Boost -> Steam Boost)
        draw_line(boost_x, b_boost_y2, boost_x, l3_y-20)
        label_line(boost_x+5, (b_boost_y2+l3_y-20)/2, "Hold")


    # -----------------
    # State Logic
    # -----------------
    def toggle_power(self):
        self.power_on = not self.power_on
        if self.power_on: self.mode = 1
        else: self.mode = 1; self.hold_active = False
        self.refresh_ui()

    def toggle_boost(self):
        if not self.power_on: return
        self.mode = 2 if self.mode == 1 else 1
        self.refresh_ui()

    def start_hold(self):
        if not self.power_on: return
        self.hold_active = True
        self.refresh_ui()

    def stop_hold(self):
        self.hold_active = False
        self.refresh_ui()

    def update_flowchart_hightlight(self):
        # Reset All Boxes
        self.flow_canvas.itemconfig("box", fill="#333333", outline="#555555", width=1)
        self.flow_canvas.itemconfig("text", fill="#aaaaaa")
        
        # Determine Active Tag
        tag = "off"
        color = "#555555"
        text_col = "white"

        if self.power_on:
            if not self.hold_active:
                if self.mode == 1:
                    tag = "normal"
                    color = "#00aa00" # Green
                else:
                    tag = "boost"
                    color = "#d18c02" # Orange
                text_col = "black"
            else:
                # Steaming
                if self.mode == 1:
                    tag = "steam_norm"
                    color = "#00aaaa" # Cyan-ish
                else:
                    tag = "steam_boost"
                    color = "#00aaaa"
                text_col = "black" # Black text on bright fill

        # Highlight Active
        self.flow_canvas.itemconfig(f"box_{tag}", fill=color, outline="#ffffff", width=2)
        self.flow_canvas.itemconfig(f"text_{tag}", fill=text_col)


    def process_light_layer(self):
        working = self.base_image_original.copy()
        
        has_effects = False
        layer = Image.new("RGBA", working.size, (255, 255, 255, 255))
        draw = ImageDraw.Draw(layer)

        # Removed Guide Rings as per request

        if self.power_on:
            # 1. Standard Lights
            active_lights = [
                ("Power", self.light_colors["Power"]),
                ("Power_Side", self.light_colors["Power_Side"])
            ]
            
            if self.mode == 2: 
                active_lights.append(("Boost", self.light_colors["Boost"]))
                active_lights.append(("Boost_Side", self.light_colors["Boost_Side"]))
                
            # NOTE: Hold button light removed as per request
            # if self.hold_active: active_lights.append(("Hold", self.light_colors["Hold"]))

            for name, col in active_lights:
                if name in self.original_points:
                    x, y = self.original_points[name]
                    r = self.original_radius
                    # Draw light glow
                    draw.ellipse((x-r, y-r, x+r, y+r), fill=col + (255,))
                    has_effects = True

            # 2. Steam Lines (if holding)
            if self.hold_active:
                sx, sy = self.original_points.get("Steam", (0,0))
                # Only draw if we have valid coordinates (assuming 0,0 is default/invalid)
                if sx != 0 or sy != 0:
                    col = self.light_colors["Steam"] + (255,) # Blue
                    
                    # Boost logic
                    is_boost = (self.mode == 2)
                    width = 180 if is_boost else 120
                    line_w = 10 if is_boost else 6
                    scale = 1.4 if is_boost else 1.0

                    # Draw a cloud/steam background
                    draw.ellipse((sx - 60*scale, sy - 30*scale, sx + 60*scale, sy + 30*scale), fill=col)
                    draw.ellipse((sx - 40*scale, sy - 40*scale, sx + 20*scale, sy + 20*scale), fill=col)
                    draw.ellipse((sx + 10*scale, sy - 35*scale, sx + 70*scale, sy + 15*scale), fill=col)
                    
                    if is_boost:
                        # Extra steam patches
                        draw.ellipse((sx - 70, sy - 60, sx + 10, sy + 10), fill=col)
                        draw.ellipse((sx - 20, sy - 70, sx + 80, sy + 0), fill=col)

                    # Draw lines
                    draw.line((sx - width//2, sy, sx + width//2, sy), fill=col, width=line_w)
                    draw.line((sx - width//2 + 10, sy - 15, sx + width//2 - 10, sy - 15), fill=col, width=line_w)
                    draw.line((sx - width//2 + 10, sy + 15, sx + width//2 - 10, sy + 15), fill=col, width=line_w)
                    
                    if is_boost:
                        # Additional top/bottom lines
                        draw.line((sx - width//2 + 30, sy - 30, sx + width//2 - 30, sy - 30), fill=col, width=line_w)
                        draw.line((sx - width//2 + 30, sy + 30, sx + width//2 - 30, sy + 30), fill=col, width=line_w)

                    has_effects = True

        if has_effects:
            layer = layer.filter(ImageFilter.GaussianBlur(radius=5))
            self.current_processed_image = ImageChops.multiply(working.convert("RGB"), layer.convert("RGB"))
        else:
            self.current_processed_image = working.convert("RGB")

    def display_current_image(self):
        if not hasattr(self, 'current_processed_image'): return
        new_w = int(self.orig_w * self.current_scale)
        new_h = int(self.orig_h * self.current_scale)
        if new_w <= 0 or new_h <= 0: return

        resized = self.current_processed_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized)
        
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        self.canvas.config(width=cw, height=ch)
        self.canvas.itemconfigure(self.image_id, image=self.tk_image)
        self.canvas.coords(self.image_id, cw//2, ch//2)

    def on_resize(self, event):
        # Avoid excessive updates
        if event.widget == self.canvas:
            w, h = event.width, event.height
            if w > 10 and h > 10:
                scale_w = w / self.orig_w
                scale_h = h / self.orig_h
                self.current_scale = min(scale_w, scale_h) * 0.9
                self.display_current_image()

    def on_canvas_click(self, event):
        x = event.x
        y = event.y
        # Convert to original coordinates to check hit zones
        # Center of canvas is (cw/2, ch/2), image is centered there
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        
        img_w = int(self.orig_w * self.current_scale)
        img_h = int(self.orig_h * self.current_scale)
        
        # Top-left of the image on canvas
        img_x0 = (cw - img_w) // 2
        img_y0 = (ch - img_h) // 2
        
        # Click relative to image
        rel_x = (x - img_x0) / self.current_scale
        rel_y = (y - img_y0) / self.current_scale
        
        btn_name = self.get_clicked_button_name(rel_x, rel_y)
        if btn_name == "Power" or btn_name == "Power_Side":
            self.toggle_power()
        elif btn_name == "Boost" or btn_name == "Boost_Side":
            self.toggle_boost()
        elif btn_name == "Hold":
            self.start_hold()

    def on_canvas_release(self, event):
        self.stop_hold()

    def get_clicked_button_name(self, x, y):
        radius = self.original_radius * 1.5 # slightly larger hit area
        for name, (bx, by) in self.original_points.items():
            dist = ((x - bx)**2 + (y - by)**2)**0.5
            if dist <= radius:
                return name
        return None

if __name__ == "__main__":
    root = tk.Tk()
    app = SteamerGUI(root)
    root.mainloop()

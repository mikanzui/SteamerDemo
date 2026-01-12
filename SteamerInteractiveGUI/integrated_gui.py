import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk, ImageDraw, ImageChops, ImageFilter, ImageOps
import math
import sys
import os
import time

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
        # Coordinates for LINE DRAWING mode (Recalibrated for 4000x2110px)
        self.line_points = {
            "Power": (597, 669),
            "Boost": (597, 800),
            "Hold": (1776, 877), # Middle/Front View Trigger
            "Steam": (1776, 350), # Estimated Nozzle (Top of Front View)
            "Power_Side": (2634, 674),
            "Boost_Side": (2637, 797),
            "Hold_Side": (2914, 872)
        }
        
        # Coordinates for RENDER mode (Photo Realistic)
        # Recalibrated to 3840x2158
        self.render_points = {
            "Power": (898, 833),
            "Boost": (898, 944),
            "Hold": (1931, 1008),
            "Power_Side": (2638, 809),
            "Boost_Side": (2638, 925),
            "Hold_Side": (2883, 987)
        }
        
        # Default to line points initially
        self.original_points = self.line_points.copy()
        
        # Radius config
        self.line_radius = 50 # Increased for 4k resolution
        self.render_radius = 40 
        self.current_base_radius = self.line_radius # Active radius setting 
        
        # New White/Monochrome styling
        self.light_colors = {
            "Power": (255, 255, 255),    # White
            "Boost": (255, 255, 255),    # White 
            "Hold": (255, 255, 255),     
            "Steam": (255, 255, 255),    # Pure White for steam
            "Power_Side": (255, 255, 255),
            "Boost_Side": (255, 255, 255)
        }
        
        self.current_scale = 1.0
        
        # State
        self.power_on = False
        self.mode = 1 
        self.hold_active = False 
        self.is_heating = False
        self.pulse_intensity = 0.0 # 0.0 to 1.0 multiplier
        self.pulse_phase = 0.0

        # Toggle for Render Mode
        self.use_renders = False
        self.render_images = {} # Original loaded images
        self.scaled_renders = {} # Resized for display

        # Pre-cache graphics
        self.cache_assets()

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
        self.main_content = tk.Frame(root, bg="#000000")
        self.main_content.pack(side="bottom", fill="both", expand=True)

        # 2a. Right Info Panel (Fixed width)
        self.info_panel = tk.Frame(self.main_content, width=380, bg="#1a1a1a", relief="flat")
        self.info_panel.pack(side="right", fill="y", padx=1, pady=1)
        self.info_panel.pack_propagate(False) # Force width
        self.setup_info_panel()

        # 2b. Left Image Area (Expands)
        self.image_frame = tk.Frame(self.main_content, bg="#000000") # Darker background
        self.image_frame.pack(side="left", fill="both", expand=True)

        # Guide Label
        self.guide_label = tk.Label(self.image_frame, text="INTERACTIVE MODE: Click the buttons on the product image (Main or Side view) to operate.", 
                              bg="#000000", fg="#666666", font=("Segoe UI", 10, "bold"))
        self.guide_label.pack(side="bottom", pady=5)

        # -----------------
        # Load Image
        # -----------------
        try:
            self.image_path = resource_path("steamer.png")
            # Load High-Res Image
            raw_img = Image.open(self.image_path).convert("RGBA")
            
            # Processing: Invert colors to match Web Version (White Lines on Black BG)
            # This replicates the "Process" used in the web app
            if raw_img.mode == 'RGBA':
                r, g, b, a = raw_img.split()
                rgb_img = Image.merge('RGB', (r, g, b))
                inverted_rgb = ImageOps.invert(rgb_img)
                r2, g2, b2 = inverted_rgb.split()
                self.base_image_original = Image.merge('RGBA', (r2, g2, b2, a))
            else:
                self.base_image_original = ImageOps.invert(raw_img.convert('RGB')).convert('RGBA')
            
            # COORDINATE SCALING Logic
            # 1. Adapt to new image resolution (Reference: 4000x2110)
            self.orig_w, self.orig_h = self.base_image_original.size
            xref = 4000.0
            
            if self.orig_w != xref:
                scale_factor = self.orig_w / xref
                # Scale LINE points to match the loaded image resolution
                for k in self.line_points:
                    px, py = self.line_points[k]
                    self.line_points[k] = (px * scale_factor, py * scale_factor)
            
            # 2. Optimization: Downscale if too large for display (Max 1600px)
            max_dim = 1600
            w, h = self.base_image_original.size
            if w > max_dim or h > max_dim:
                ratio = min(max_dim/w, max_dim/h)
                new_size = (int(w*ratio), int(h*ratio))
                self.base_image_original = self.base_image_original.resize(new_size, Image.Resampling.LANCZOS)
                
                # Apply downscale ratio to LINE points
                for k in self.line_points:
                    px, py = self.line_points[k]
                    self.line_points[k] = (px * ratio, py * ratio)
                
                # Apply Separate Scaling for Render Points (Reference: 3840x2158)
                # We need to map 3840x2158 space -> new_size (which matches Line Drawing aspect)
                # This accounts for the slight stretch/squash applied to renders
                xref_render = 3840.0
                yref_render = 2158.0
                
                ratio_rx = new_size[0] / xref_render
                ratio_ry = new_size[1] / yref_render
                
                for k in self.render_points:
                    px, py = self.render_points[k]
                    self.render_points[k] = (px * ratio_rx, py * ratio_ry)

                self.line_radius *= ratio 
                self.render_radius *= ratio_rx # Scale radius by Width ratio roughly
                self.current_base_radius = self.line_radius
            
            # Set Active Points
            self.original_points = self.line_points.copy()
            
            self.current_processed_image = self.base_image_original.copy()
            self.orig_w, self.orig_h = self.base_image_original.size
            
            # Load additional renders now that we have the base path
            self.load_renders()
            self.cache_assets() # Re-cache with renders
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image.\nError: {e}")
            root.destroy()
            return

        # Canvas
        self.canvas = tk.Canvas(self.image_frame, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.image_id = self.canvas.create_image(0, 0, anchor="center")
        
        # Bind events
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Initial Draw
        self.refresh_ui()

    def load_renders(self):
        """Load the pre-rendered images for the realistic view mode"""
        files = {
            "alloff": "alloff.jpg",
            "on": "on.jpg",
            "onwithsteam": "onwithsteam.jpg",
            "onwithboost": "onwithboost.jpg",
            "onboostwithsteam": "onboostwithsteam.jpg"
        }
        
        try:
            render_dir = os.path.join(os.path.dirname(self.image_path), "Renders")
            if not os.path.exists(render_dir):
                # Fallback if running from a different context
                render_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Renders")

            for key, filename in files.items():
                path = os.path.join(render_dir, filename)
                if os.path.exists(path):
                    img = Image.open(path).convert("RGBA")
                    # Initial scale to match base image if needed, or keep original?
                    # The line drawing logic resizes the base image if it's too big. 
                    # We should probably match the render size to the base image size for consistent coordinates.
                    if hasattr(self, 'base_image_original'):
                        target_size = self.base_image_original.size
                        if img.size != target_size:
                            img = img.resize(target_size, Image.Resampling.LANCZOS)
                    
                    self.render_images[key] = img
                else:
                    print(f"Warning: Render file not found: {path}")
                    # Create a placeholder if missing
                    self.render_images[key] = Image.new("RGBA", (100, 100), (50, 50, 50))
                    
        except Exception as e:
            print(f"Error loading renders: {e}")

    def cache_assets(self):
        """Pre-render glfx to avoid doing it every frame"""
        # 1. Circular Glow
        r = self.line_radius # Use line radius for glow generation
        size = int(r * 6)
        self.glow_sprite = Image.new("RGBA", (size, size), (0,0,0,0))
        draw = ImageDraw.Draw(self.glow_sprite)
        
        cx, cy = size // 2, size // 2
        col = (255, 255, 255) # Base white
        
        # Draw light glow - Layered for Intensity
        # 1. Wide diffused outer glow
        draw.ellipse((cx-r*2.5, cy-r*2.5, cx+r*2.5, cy+r*2.5), fill=col + (50,))
        # 2. Medium glow
        draw.ellipse((cx-r*1.6, cy-r*1.6, cx+r*1.6, cy+r*1.6), fill=col + (100,))
        # 3. Bright Core
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=col + (255,))
        self.glow_sprite = self.glow_sprite.filter(ImageFilter.GaussianBlur(radius=8))

        # 2. Steam Sprites (Normal & Boost)
        self.steam_sprites = {}
        
        for kind in ["normal", "boost"]:
            sw, sh = 600, 500 # Doubled canvas size (was 300, 250)
            sprite = Image.new("RGBA", (sw, sh), (0,0,0,0))
            draw_s = ImageDraw.Draw(sprite)
            sx, sy = sw//2, sh//2
            col = (255, 255, 255)
            
            is_boost = (kind == "boost")
            base_s = 2.0 # Scale Factor
            scale = (1.4 if is_boost else 1.0) * base_s
            width = int((180 if is_boost else 120) * base_s)
            line_w = int((10 if is_boost else 6) * base_s)
            
            # Blobs
            draw_s.ellipse((sx - 60*scale, sy - 30*scale, sx + 60*scale, sy + 30*scale), fill=col + (255,))
            draw_s.ellipse((sx - 40*scale, sy - 40*scale, sx + 20*scale, sy + 20*scale), fill=col + (255,))
            draw_s.ellipse((sx + 10*scale, sy - 35*scale, sx + 70*scale, sy + 15*scale), fill=col + (255,))
            if is_boost:
                draw_s.ellipse((sx - 70*base_s, sy - 60*base_s, sx + 10*base_s, sy + 10*base_s), fill=col + (255,))
                draw_s.ellipse((sx - 20*base_s, sy - 70*base_s, sx + 80*base_s, sy + 0), fill=col + (255,))
            
            # Lines
            draw_s.line((sx - width//2, sy, sx + width//2, sy), fill=col + (255,), width=line_w)
            draw_s.line((sx - width//2 + 10*base_s, sy - 15*base_s, sx + width//2 - 10*base_s, sy - 15*base_s), fill=col + (255,), width=line_w)
            draw_s.line((sx - width//2 + 10*base_s, sy + 15*base_s, sx + width//2 - 10*base_s, sy + 15*base_s), fill=col + (255,), width=line_w)
            if is_boost:
                draw_s.line((sx - width//2 + 30*base_s, sy - 30*base_s, sx + width//2 - 30*base_s, sy - 30*base_s), fill=col + (255,), width=line_w)
                draw_s.line((sx - width//2 + 30*base_s, sy + 30*base_s, sx + width//2 - 30*base_s, sy + 30*base_s), fill=col + (255,), width=line_w)
            
            self.steam_sprites[kind] = sprite.filter(ImageFilter.GaussianBlur(radius=8*base_s))

    def configure_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam') 
        # Modern Dark Theme Button
        self.style.configure('TButton', 
                             font=('Segoe UI', 9, 'bold'), 
                             padding=(15, 8), 
                             background="#3a3a3a", 
                             foreground="#e0e0e0", 
                             borderwidth=0, 
                             focuscolor="none")
        self.style.map('TButton', 
                       background=[('active', '#505050'), ('pressed', '#606060')],
                       foreground=[('disabled', '#777777')])

    def setup_controls(self):
        # Slightly darker background for contrast
        container = tk.Frame(self.controls_frame, bg="#2b2b2b")
        container.pack(anchor="center", pady=5)
        
        # Increased spacing (padx) for cleaner layout
        self.create_control_group(container, "MAIN POWER", "Power", self.toggle_power, "POWER")
        
        # Thinner, subtler separators
        tk.Frame(container, width=1, bg="#444444", height=30).pack(side="left", padx=30, fill="y")
        
        self.create_control_group(container, "INTENSITY", "Boost", self.toggle_boost, "BOOST")
        
        tk.Frame(container, width=1, bg="#444444", height=30).pack(side="left", padx=30, fill="y")
        
        # Center the Hold button better
        self.create_control_group(container, "OPERATION", "Hold", None, "HOLD TO STEAM", is_hold_btn=True, btn_width=18)
        
        tk.Frame(container, width=1, bg="#444444", height=30).pack(side="left", padx=30, fill="y")
        
        # View Toggle
        view_frame = tk.Frame(container, bg="#2b2b2b")
        view_frame.pack(side="left")
        tk.Label(view_frame, text="VIEW MODE", bg="#2b2b2b", fg="#888888", font=("Segoe UI", 7, "bold")).pack(side="top", pady=(0,8))
        self.btn_view = ttk.Button(view_frame, text="SWITCH TO\nRENDERS", width=14, command=self.toggle_view_mode)
        self.btn_view.pack(side="top")

    def toggle_view_mode(self):
        self.use_renders = not self.use_renders
        if self.use_renders:
            self.btn_view.configure(text="SWITCH TO\nLINES")
            self.canvas.configure(bg="#000000") # Ensure black background
            # Clean switch to render points
            self.original_points = self.render_points.copy()
            self.current_base_radius = self.render_radius
        else:
            self.btn_view.configure(text="SWITCH TO\nRENDERS")
            # Switch back to line points
            self.original_points = self.line_points.copy()
            self.current_base_radius = self.line_radius
        
        # Ensure styles are correct
        self.refresh_ui()

    def create_control_group(self, parent, label_text, key_name, command, btn_text, is_hold_btn=False, btn_width=14):
        frame = tk.Frame(parent, bg="#2b2b2b")
        frame.pack(side="left")
        # Subtler label text
        tk.Label(frame, text=label_text, bg="#2b2b2b", fg="#888888", font=("Segoe UI", 7, "bold")).pack(side="top", pady=(0,8))
        row_frame = tk.Frame(frame, bg="#2b2b2b")
        row_frame.pack(side="top")
        
        btn = ttk.Button(row_frame, text=btn_text, width=btn_width, command=command)
        btn.pack(side="left", padx=5)
        
        if is_hold_btn:
            btn.bind("<ButtonPress-1>", lambda e: self.start_hold())
            btn.bind("<ButtonRelease-1>", lambda e: self.stop_hold())
            # Status indicator (READY / STEAMING)
            self.steam_indicator = tk.Label(row_frame, text="READY", font=('Segoe UI', 8, 'bold'), width=10, bg="#2b2b2b", fg="#555555", relief="flat")
            self.steam_indicator.pack(side="left", padx=5)
        else:
            # LED Indicator - slightly smaller and flatter
            canvas_light = tk.Canvas(row_frame, width=12, height=12, bg="#2b2b2b", highlightthickness=0)
            canvas_light.pack(side="left", padx=5)
            # Centered circle
            canvas_light.create_oval(1, 1, 11, 11, fill="#3a3a3a", outline="#505050", tags="led")
            setattr(self, f"{key_name.lower()}_led", canvas_light)

    def refresh_ui(self):
        if self.use_renders:
            # Render Mode: Select pre-rendered image based on state
            tag = "alloff"
            if self.power_on:
                if self.mode == 2: # Boost
                    if self.is_heating:
                        # FLASHING LOGIC (Render Mode)
                        # Alternate between Boost frame and Normal frame based on pulse
                        # Threshold > 0.6 creates a blinking effect
                        if self.pulse_intensity > 0.6:
                            tag = "onwithboost"
                        else:
                            tag = "on"
                    elif self.hold_active:
                        tag = "onboostwithsteam"
                    else:
                        tag = "onwithboost" # Covers active boost
                else: # Normal
                    if self.hold_active:
                        tag = "onwithsteam"
                    else:
                        tag = "on"
            
            # Get the scaled render
            # Default to alloff if something is missing
            img = self.scaled_renders.get(tag, self.scaled_renders.get("alloff"))
            # Fallback to base line drawing if even 'alloff' is missing (e.g. load failed)
            if img:
                 self.current_processed_image = img
            else:
                 # Last resort fallback
                 self.process_light_layer()
        else:
            # Line Drawing Mode: Use dynamic lighting
            self.process_light_layer()
            
        self.display_current_image()
        self.update_info_panel()
        self.update_flowchart_hightlight()

    def update_info_panel(self):
        # Update LEDs
        # Power LED
        self.power_led.itemconfig("led", fill="#ffffff" if self.power_on else "#333333")
        
        # Boost LED logic
        if self.power_on and self.mode == 2:
            if self.is_heating:
                # Pulse (using pulse_intensity)
                # Map 0.0-1.0 to hex color #000000-#ffffff
                val = int(self.pulse_intensity * 255)
                val = max(0, min(255, val))
                hex_val = f"{val:02x}"
                col = f"#{hex_val}{hex_val}{hex_val}"
            else:
                col = "#ffffff" # Solid White
        else:
            col = "#333333"
            
        self.boost_led.itemconfig("led", fill=col)

        # Text Status
        if self.power_on:
            if self.hold_active:
                txt = "STEAMING"
                col = "#ffffff" # White
            elif self.is_heating:
                txt = "HEATING..."
                col = "#aaaaaa"
            else:
                txt = "READY"
                col = "#ffffff" # White
        else:
            txt = "STANDBY"
            col = "#666666"
            
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
        cx = 190 # Center of canvas (panel width 380)
        
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
        norm_x = 90
        heat_x = 190 # Middle
        boost_x = 290
        l2_y = 130
        
        _, b_norm_y1, _, b_norm_y2, _, _ = draw_box(norm_x, l2_y, 80, 40, "ON\n(Normal)", "normal")
        # Heating Box
        _, b_heat_y1, _, b_heat_y2, _, _ = draw_box(heat_x, l2_y, 60, 30, "Heating\n(5s)", "heating")
        _, b_boost_y1, _, b_boost_y2, _, _ = draw_box(boost_x, l2_y, 80, 40, "ON\n(Boost)", "boost")

        # Level 3: Hold / Steam
        l3_y = 250
        draw_box(norm_x, l3_y, 80, 40, "STEAM\n(Normal)", "steam_norm")
        draw_box(boost_x, l3_y, 80, 40, "STEAM\n(Boost)", "steam_boost")

        # --- Connections ---
        
        # Power ON (Off -> Normal)
        draw_line(off_x, b_off_y2, norm_x, b_norm_y1)
        label_line((off_x+norm_x)/2, (b_off_y2+b_norm_y1)/2, "Power")

        # Boost Toggle (Normal <-> Heating <-> Boost)
        # Normal -> Heating
        draw_line(norm_x+40, l2_y, heat_x-30, l2_y)
        # Heating -> Boost
        draw_line(heat_x+30, l2_y, boost_x-40, l2_y)
        # Back from Boost to Normal
        self.flow_canvas.create_line(boost_x-40, l2_y+20, norm_x+40, l2_y+20, **arrow_opts)
        
        # Label
        label_line(heat_x, l2_y-25, "Boost Btn")

        # Hold Steam (Normal -> Steam Norm)
        draw_line(norm_x, b_norm_y2, norm_x, l3_y-20) 
        label_line(norm_x+5, (b_norm_y2+l3_y-20)/2, "Hold")

        # Hold Steam (Boost -> Steam Boost)
        draw_line(boost_x, b_boost_y2, boost_x, l3_y-20)
        label_line(boost_x+5, (b_boost_y2+l3_y-20)/2, "Hold")


    # -----------------
    # State Logic
    # -----------------
    def toggle_power(self):
        self.power_on = not self.power_on
        if self.power_on: 
            self.mode = 1
        else: 
            self.mode = 1
            self.hold_active = False
            self.cancel_heating()
        self.refresh_ui()

    def toggle_boost(self):
        if not self.power_on: return
        
        if self.mode == 1:
            # Switching TO Boost -> Start Heating
            self.mode = 2
            self.start_heating()
        else:
            # Switching TO Normal
            self.mode = 1
            self.cancel_heating()
            self.refresh_ui()

    def start_heating(self):
        self.is_heating = True
        
        # Duration params
        self.real_duration = 1.0 # 1s (seconds)
        self.sim_duration = 5.0  # 5s
        
        # Use Time-Delta to prevent drift/lag
        self.heating_start_time = time.time()
        self.last_frame_time = self.heating_start_time
        
        # Reduce target framerate to 30FPS for stability
        self.target_fps = 30
        self.step_delay = int(1000 / self.target_fps)
        
        self.pulse_intensity = 1.0
        self.process_heating_step()

    def process_heating_step(self):
        if not self.is_heating or not self.power_on or self.mode != 2:
            self.cancel_heating()
            return
            
        now = time.time()
        elapsed = now - self.heating_start_time
        
        # Calculate progress (0.0 to 1.0)
        self.heating_progress = min(1.0, elapsed / self.real_duration)
        
        # 1. Update Overlay
        self.update_heating_overlay()
        
        # 2. Pulse Calculation (Sine Wave)
        # Pulse based on absolute time. 
        # Slower frequency to avoid "jumping" on low-FPS systems.
        # 1 Hz = 1 full cycle per second.
        self.pulse_phase = elapsed * (math.pi * 2)
        
        # Sin varies -1 to 1. Map to 0.1 to 1.0
        self.pulse_intensity = (math.sin(self.pulse_phase) + 1) / 2 # 0 to 1
        self.pulse_intensity = 0.2 + (self.pulse_intensity * 0.8) # 0.2 to 1.0
        
        self.refresh_ui() # Redraws using new pulse intensity

        # 3. Check Finish
        if self.heating_progress >= 1.0:
            self.finish_heating()
        else:
            # Schedule next frame
            # Account for processing time? No, just keep simple loop
            self.root.after(self.step_delay, self.process_heating_step)

    def cancel_heating(self):
        self.is_heating = False
        self.canvas.delete("overlay") # Clear overlay

    def finish_heating(self):
        self.is_heating = False
        self.canvas.delete("overlay") # Clear overlay
        self.refresh_ui() # Ensures LED goes solid white

    def update_heating_overlay(self):
        self.canvas.delete("overlay")
        # If holding steam, hide the heating overlay so we can see the steam
        if self.hold_active: return
        if not self.is_heating: return
        
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        cx = cw // 2
        
        # Position at Top Center
        y_top = 40
        
        # Dimensions
        w, h = 300, 100
        x1, y1 = cx - w//2, y_top
        x2, y2 = cx + w//2, y_top + h
        
        # Background Box - Dark Grey with White Border
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="#2b2b2b", outline="#ffffff", width=2, tags="overlay")
        
        # Text "HEATING UP" - White
        self.canvas.create_text(cx, y1 + 25, text="HEATING UP...", fill="#ffffff", font=("Segoe UI", 16, "bold"), tags="overlay")
        
        # Bar vars
        # Display simulated time based on progress
        remaining = max(0.0, 5.0 * (1.0 - self.heating_progress))
        
        bar_w = 250
        bar_h = 12
        bx1 = cx - bar_w//2
        by1 = y1 + 55 # Shifted relative to box top
        bx2 = cx + bar_w//2
        by2 = by1 + bar_h
        
        # Bar Background - Darker
        self.canvas.create_rectangle(bx1, by1, bx2, by2, fill="#444444", outline="", tags="overlay")
        
        # Bar Fill - White
        fill_w = bar_w * self.heating_progress
        if fill_w > 0:
            self.canvas.create_rectangle(bx1, by1, bx1 + fill_w, by2, fill="#ffffff", outline="", tags="overlay")
        
        # Time Text - Grey
        self.canvas.create_text(cx, by2 + 20, text=f"{remaining:.1f}s", fill="#aaaaaa", font=("Segoe UI", 12), tags="overlay")

    def start_hold(self):
        if not self.power_on: return
        self.hold_active = True
        self.refresh_ui()

    def stop_hold(self):
        self.hold_active = False
        self.refresh_ui()

    def update_flowchart_hightlight(self):
        # Reset All Boxes
        self.flow_canvas.itemconfig("box", fill="#2b2b2b", outline="#444444", width=1)
        self.flow_canvas.itemconfig("text", fill="#666666")
        
        # Determine Active Tag
        tag = "off"
        color = "#2b2b2b" 
        outline = "#666666"

        if self.power_on:
            if not self.hold_active:
                if self.is_heating:
                    tag = "heating"
                    color = "#444444"
                    outline = "#ffffff"
                elif self.mode == 1:
                    tag = "normal"
                    color = "#444444"
                    outline = "#ffffff"
                else:
                    tag = "boost"
                    color = "#444444"
                    outline = "#ffffff"
            else:
                # Steaming
                if self.mode == 1:
                    tag = "steam_norm"
                    color = "#ffffff"
                    outline = "#ffffff"
                else:
                    tag = "steam_boost"
                    color = "#ffffff"
                    outline = "#ffffff"
        
        # OFF State
        if tag == "off":
             color = "#444444" if not self.power_on else "#2b2b2b"
             outline = "#ffffff" if not self.power_on else "#444444"

        # Highlight Active
        self.flow_canvas.itemconfig(f"box_{tag}", fill=color, outline=outline, width=2)
        # Check contrast for text
        text_col = "black" if color == "#ffffff" else "white"
        self.flow_canvas.itemconfig(f"text_{tag}", fill=text_col)


    def process_light_layer(self):
        if not hasattr(self, 'resized_base'): return
        
        # Work on the resized buffer directly
        working = self.resized_base.copy()
        img_w, img_h = working.size
        
        # OPTIMIZATION: Removed full-screen accumulator. 
        # Modifying 'working' image directly is faster.

        if self.power_on:
            # 1. Standard Lights
            active_lights = [
                ("Power", 1.0),
                ("Power_Side", 1.0)
            ]
            
            if self.mode == 2: 
                # Boost lights logic
                intensity = self.pulse_intensity if self.is_heating else 1.0
                active_lights.append(("Boost", intensity))
                active_lights.append(("Boost_Side", intensity))
                
            for name, intensity in active_lights:
                if intensity < 0.05: continue

                if name in self.original_points:
                    # Get SCALED coordinates
                    rx, ry = self.original_points[name]
                    x = int(rx * self.current_scale)
                    y = int(ry * self.current_scale)
                    
                    # Use SCALED sprite
                    sprite = self.scaled_glow
                    sprite_w, sprite_h = sprite.size
                    
                    px = x - sprite_w // 2
                    py = y - sprite_h // 2
                    
                    # Optimization: Only process intersection
                    x1 = max(0, px)
                    y1 = max(0, py)
                    x2 = min(img_w, px + sprite_w)
                    y2 = min(img_h, py + sprite_h)
                    
                    if x2 <= x1 or y2 <= y1: continue
                    
                    # Crop sprite
                    spr_x = x1 - px
                    spr_y = y1 - py
                    visible_sprite = sprite.crop((spr_x, spr_y, spr_x + (x2 - x1), spr_y + (y2 - y1)))
                    
                    # Dimming
                    if intensity < 0.99:
                        r, g, b, a = visible_sprite.split()
                        a = a.point(lambda p: int(p * intensity))
                        visible_sprite = Image.merge("RGBA", (r, g, b, a))

                    # Blend Local Region
                    dest_region = working.crop((x1, y1, x2, y2))
                    # Use screen blend for lights
                    blended = ImageChops.screen(dest_region, visible_sprite)
                    working.paste(blended, (x1, y1))

            # 2. Steam Lines (Cached & Optimized)
            if self.hold_active:
                rx, ry = self.original_points.get("Steam", (0,0))
                # Ensure integer coordinates
                sx = int(rx * self.current_scale)
                sy = int(ry * self.current_scale)
                
                if sx != 0 or sy != 0:
                    # Select Sprite
                    kind = "boost" if self.mode == 2 else "normal"
                    sprite = self.scaled_steam_sprites[kind]
                    
                    sprite_w, sprite_h = sprite.size
                    px = sx - sprite_w // 2
                    py = sy - sprite_h // 2
                    
                    x1 = max(0, px)
                    y1 = max(0, py)
                    x2 = min(img_w, px + sprite_w)
                    y2 = min(img_h, py + sprite_h)

                    if x2 > x1 and y2 > y1:
                        spr_x = x1 - px
                        spr_y = y1 - py
                        visible_steam = sprite.crop((spr_x, spr_y, spr_x + (x2 - x1), spr_y + (y2 - y1)))
                        
                        dest_region = working.crop((x1, y1, x2, y2))
                        # Use screen blend (lighter) to add light to the base
                        blended = ImageChops.screen(dest_region, visible_steam)
                        working.paste(blended, (x1, y1))

        # No final composite needed - 'working' is updated directly
        self.current_processed_image = working

    def on_resize(self, event):
        # Avoid excessive updates
        if event.widget == self.canvas:
            w, h = event.width, event.height
            if w > 10 and h > 10:
                scale_w = w / self.orig_w
                scale_h = h / self.orig_h
                new_scale = min(scale_w, scale_h) * 0.9
                
                # Check if scale changed significantly (optimization)
                if abs(new_scale - self.current_scale) > 0.01 or not hasattr(self, 'resized_base'):
                    self.current_scale = new_scale
                    self.cache_scaled_assets()
                    self.refresh_ui()

    def cache_scaled_assets(self):
        # 1. Base Image
        new_w = int(self.orig_w * self.current_scale)
        new_h = int(self.orig_h * self.current_scale)
        if new_w <= 0 or new_h <= 0: return
        self.resized_base = self.base_image_original.resize((new_w, new_h), Image.Resampling.BILINEAR)
        
        # 2. Glow Sprite
        gw, gh = self.glow_sprite.size
        self.scaled_glow = self.glow_sprite.resize((int(gw * self.current_scale), int(gh * self.current_scale)), Image.Resampling.BILINEAR)
        
        # 3. Steam Sprites
        self.scaled_steam_sprites = {}
        for k, v in self.steam_sprites.items():
            sw, sh = v.size
            self.scaled_steam_sprites[k] = v.resize((int(sw * self.current_scale), int(sh * self.current_scale)), Image.Resampling.BILINEAR)

        # 4. Renders
        self.scaled_renders = {}
        for k, v in self.render_images.items():
             new_w = int(v.width * self.current_scale)
             new_h = int(v.height * self.current_scale)
             self.scaled_renders[k] = v.resize((new_w, new_h), Image.Resampling.BILINEAR)

    def display_current_image(self):
        # Just display the pre-rendered image (no resizing here)
        if not hasattr(self, 'current_processed_image'): return
        
        self.tk_image = ImageTk.PhotoImage(self.current_processed_image)
        
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        #self.canvas.config(width=cw, height=ch) # Don't reconfig - loop danger
        self.canvas.itemconfigure(self.image_id, image=self.tk_image)
        self.canvas.coords(self.image_id, cw//2, ch//2)
        
        # Ensure overlay is on top after image update
        self.update_heating_overlay()

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
        elif btn_name == "Hold" or btn_name == "Hold_Side":
            self.start_hold()

    def on_canvas_release(self, event):
        self.stop_hold()

    def get_clicked_button_name(self, x, y):
        radius = self.current_base_radius * 1.5 # slightly larger hit area
        for name, (bx, by) in self.original_points.items():
            dist = ((x - bx)**2 + (y - by)**2)**0.5
            if dist <= radius:
                return name
        return None

if __name__ == "__main__":
    root = tk.Tk()
    app = SteamerGUI(root)
    root.mainloop()

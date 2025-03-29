# TallyPrimeConnect/ui/sidebar.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os

try:
    from utils.helpers import BASE_DIR
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
ICONS_DIR = os.path.join(ASSETS_DIR, 'icons')

SIDEBAR_BG = "#f0f0f0"
ACTIVE_BG = "#d0e0f0"
HOVER_BG = "#e0e0e0"

class Sidebar(tk.Frame):
    def __init__(self, parent, command_callback=None, *args, **kwargs):
        super().__init__(parent, bg=SIDEBAR_BG, width=200, *args, **kwargs)
        self.pack_propagate(False)
        self.buttons = {}
        self.icon_cache = {}
        self.command_callback = command_callback
        self._create_widgets()

    def _load_icon(self, icon_name, size=(20, 20)):
        if icon_name in self.icon_cache:
            return self.icon_cache[icon_name]
        icon_path = os.path.join(ICONS_DIR, icon_name)
        try:
            if os.path.exists(icon_path):
                img = Image.open(icon_path).resize(size, Image.Resampling.LANCZOS)
            else:
                print(f"Warning: Icon not found at {icon_path}")
                img = Image.new('RGBA', size, (0,0,0,0)) # Placeholder
        except Exception as e:
            print(f"Error loading icon {icon_name}: {e}")
            img = Image.new('RGBA', size, (0, 0, 0, 0)) # Placeholder on error
        photo_img = ImageTk.PhotoImage(img)
        self.icon_cache[icon_name] = photo_img
        return photo_img

    def _create_widgets(self):
        items = [
            ("My Companies", "company.png", "MyCompanies"),
            ("Add Company", "add_company.png", "AddCompany"),
            ("Settings", "settings.png", "Settings"),
            ("Profile", "profile.png", "Profile"),
            ("System Info", "system_info.png", "SystemInfo"),
            ("Tutorial", "tutorial.png", "Tutorial"),
            ("Support", "support.png", "Support"),
        ]

        for text, icon_file, identifier in items:
            icon = self._load_icon(icon_file)
            is_active = (identifier == "Settings") # Default active

            btn_command = None
            if self.command_callback:
                 btn_command = lambda id=identifier: self.command_callback(id)

            btn = tk.Button(
                self, text=f"  {text}", image=icon, compound=tk.LEFT, anchor="w",
                relief=tk.FLAT, bg=ACTIVE_BG if is_active else SIDEBAR_BG,
                fg="#333333", activebackground=HOVER_BG, activeforeground="#000000",
                padx=15, pady=10, font=("Arial", 10), command=btn_command
            )
            btn.pack(fill=tk.X, pady=1)
            self.buttons[identifier] = btn # Use identifier

            def make_hover_handler(widget, hover_color, leave_color, active_color):
                def on_enter(event):
                    if widget.cget('bg') != active_color: widget.config(bg=hover_color)
                def on_leave(event):
                    if widget.cget('bg') != active_color: widget.config(bg=leave_color)
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
            make_hover_handler(btn, HOVER_BG, SIDEBAR_BG, ACTIVE_BG)

    def set_active(self, identifier):
        active_found = False
        for id, button in self.buttons.items():
            is_active = (id == identifier)
            if is_active: active_found = True
            button.config(bg=ACTIVE_BG if is_active else SIDEBAR_BG)

            # Re-apply hover handler (important!)
            def make_hover_handler(widget, hover_color, leave_color, active_color):
                def on_enter(event):
                    if widget.cget('bg') != active_color: widget.config(bg=hover_color)
                def on_leave(event):
                    if widget.cget('bg') != active_color: widget.config(bg=leave_color)
                widget.unbind("<Enter>") # Prevent duplicates
                widget.unbind("<Leave>")
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
            make_hover_handler(button, HOVER_BG, SIDEBAR_BG, ACTIVE_BG)

        if not active_found:
             print(f"Warning: Sidebar identifier '{identifier}' not found for highlighting.")
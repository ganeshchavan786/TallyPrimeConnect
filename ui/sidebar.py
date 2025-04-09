# TallyPrimeConnect/ui/sidebar.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import logging

logger = logging.getLogger(__name__)

# --- Constants ---
try: BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError: BASE_DIR = os.path.dirname(os.getcwd())
ASSETS_DIR = os.path.join(BASE_DIR, 'assets'); ICONS_DIR = os.path.join(ASSETS_DIR, 'icons')
SIDEBAR_BG="#f0f0f0"; ACTIVE_BG="#d0e0f0"; HOVER_BG="#e0e0e0"; TEXT_COLOR="#333333"
ACTIVE_TEXT_COLOR="#000000"; BUTTON_FONT = ("Arial", 10); ICON_SIZE = (20, 20)

class Sidebar(tk.Frame):
    """Left navigation sidebar with icons and clickable buttons."""
    def __init__(self, parent, command_callback=None, *args, **kwargs):
        """Initializes the sidebar."""
        super().__init__(parent, bg=SIDEBAR_BG, width=200, *args, **kwargs)
        self.pack_propagate(False)
        self.buttons = {}
        self.icon_cache = {}
        self.command_callback = command_callback # Store the callback function from app.py
        self._create_widgets()
        logger.debug("Sidebar initialized.")

    def _load_icon(self, icon_name: str, size: tuple = ICON_SIZE) -> ImageTk.PhotoImage | None:
        """Loads and caches an icon PhotoImage."""
        if icon_name in self.icon_cache: return self.icon_cache[icon_name]
        icon_path = os.path.join(ICONS_DIR, icon_name); photo_img = None
        try:
            # Use placeholder if file doesn't exist
            img = Image.open(icon_path).resize(size, Image.Resampling.LANCZOS) if os.path.exists(icon_path) else Image.new('RGBA', size, (200,200,200,255)) # Gray placeholder
            photo_img = ImageTk.PhotoImage(img); self.icon_cache[icon_name] = photo_img
        except Exception as e: logger.exception(f"Error loading icon {icon_name}: {e}")
        return photo_img

    def _create_widgets(self):
        """Creates the sidebar buttons and assigns the callback command."""
        logger.debug("Creating sidebar widgets.")
        items = [ # (Display Text, Icon Filename, Unique Identifier)
            ("My Companies", "company.png", "MyCompanies"),
            ("Add Company", "add_company.png", "AddCompany"),
            ("Settings", "settings.png", "Settings"),
            ("License Info", "system_info.png", "LicenseInfo"), # Using system_info icon
            ("Profile", "profile.png", "Profile"),
            ("System Info", "system_info.png", "SystemInfo"), # Original System Info
            ("Tutorial", "tutorial.png", "Tutorial"),
            ("Support", "support.png", "Support"),
        ]
        for text, icon_file, identifier in items:
            icon = self._load_icon(icon_file)
            is_active_default = (identifier == "Settings") # Default active item
            bg_color = ACTIVE_BG if is_active_default else SIDEBAR_BG

            # Create command lambda that passes the unique identifier to the app's callback
            cmd = (lambda id=identifier: self._handle_click(id)) if self.command_callback else None

            button = tk.Button(self, text=f"  {text}", image=icon, compound=tk.LEFT, anchor="w", relief=tk.FLAT,
                            bg=bg_color, fg=TEXT_COLOR, activebackground=HOVER_BG, activeforeground=ACTIVE_TEXT_COLOR,
                            padx=15, pady=10, font=BUTTON_FONT, command=cmd) # Assign command here
            button.pack(fill=tk.X, pady=1); self.buttons[identifier] = button
            self._bind_hover(button, HOVER_BG, SIDEBAR_BG, ACTIVE_BG) # Apply hover effect

    def _handle_click(self, identifier: str):
        """Internal handler to call the main application callback."""
        logger.info(f"Sidebar item clicked: {identifier}")
        if self.command_callback:
            try:
                self.command_callback(identifier) # Execute the function passed from app.py
            except Exception as e:
                logger.exception(f"Error executing sidebar command callback for '{identifier}': {e}")

    def _bind_hover(self, widget: tk.Button, hover_color: str, leave_color: str, active_color: str):
        """Applies mouse enter/leave hover effects to a button."""
        def on_enter(event):
            try:
                 if widget.winfo_exists() and widget.cget('bg') != active_color: widget.config(bg=hover_color)
            except tk.TclError: pass
        def on_leave(event):
            try:
                 if widget.winfo_exists() and widget.cget('bg') != active_color: widget.config(bg=leave_color)
            except tk.TclError: pass
        widget.bind("<Enter>", on_enter, add='+'); widget.bind("<Leave>", on_leave, add='+')

    def set_active(self, identifier: str):
        """Highlights the specified button and de-highlights others."""
        logger.debug(f"Setting active sidebar item: {identifier}")
        active_found = False
        for id, button in self.buttons.items():
            try:
                 if not button.winfo_exists(): continue
                 is_active = (id == identifier);
                 if is_active: active_found = True
                 button.config(bg=ACTIVE_BG if is_active else SIDEBAR_BG)
                 button.unbind("<Enter>"); button.unbind("<Leave>") # Unbind old hover handlers
                 self._bind_hover(button, HOVER_BG, SIDEBAR_BG, ACTIVE_BG) # Re-bind hover effects
            except tk.TclError: logger.warning(f"Error setting active state for {id}")
            except Exception as e: logger.exception(f"Unexpected error setting active {id}: {e}")
        if not active_found: logger.warning(f"Sidebar identifier '{identifier}' not found.")
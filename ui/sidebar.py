# TallyPrimeConnect/ui/sidebar.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import logging

# --- Setup Logger ---
logger = logging.getLogger(__name__)

# --- Constants ---
try:
    # Determine BASE_DIR robustly relative to this file
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    # Fallback if __file__ is not defined
    BASE_DIR = os.path.dirname(os.getcwd())

ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
ICONS_DIR = os.path.join(ASSETS_DIR, 'icons')

# UI Style Constants
SIDEBAR_BG = "#f0f0f0"        # Light gray background
ACTIVE_BG = "#d0e0f0"         # Light blue for active button
HOVER_BG = "#e0e0e0"          # Slightly darker gray for hover
TEXT_COLOR = "#333333"       # Standard text color
ACTIVE_TEXT_COLOR = "#000000" # Text color when button is hovered/active
BUTTON_FONT = ("Arial", 10)
ICON_SIZE = (20, 20)


class Sidebar(tk.Frame):
    """
    Left navigation sidebar panel with icons and clickable buttons.
    Uses a callback function to notify the main application of selection changes.
    """
    def __init__(self, parent, command_callback=None, *args, **kwargs):
        """
        Initializes the Sidebar frame.

        Args:
            parent: The parent tkinter widget.
            command_callback: A function to call when a sidebar button is clicked.
                              It receives the unique identifier of the clicked button as an argument.
        """
        super().__init__(parent, bg=SIDEBAR_BG, width=200, *args, **kwargs)
        self.pack_propagate(False) # Prevent frame from resizing to fit content
        self.buttons = {}          # Dictionary to store button widgets: {identifier: button_widget}
        self.icon_cache = {}       # Cache for loaded PhotoImage objects to prevent garbage collection
        self.command_callback = command_callback # Store the callback function

        self._create_widgets()     # Build the UI elements
        logger.debug("Sidebar initialized.")

    def _load_icon(self, icon_name: str, size: tuple = ICON_SIZE) -> ImageTk.PhotoImage | None:
        """
        Loads an icon image file, resizes it, creates a PhotoImage, and caches it.
        Returns a placeholder if the icon cannot be loaded.

        Args:
            icon_name: The filename of the icon (e.g., "company.png").
            size: A tuple (width, height) for resizing the icon.

        Returns:
            A PhotoImage object or None if loading fails critically.
        """
        if icon_name in self.icon_cache:
            return self.icon_cache[icon_name]

        icon_path = os.path.join(ICONS_DIR, icon_name)
        photo_img = None
        try:
            if os.path.exists(icon_path):
                # Open, resize using LANCZOS for better quality, create PhotoImage
                img = Image.open(icon_path).resize(size, Image.Resampling.LANCZOS)
            else:
                # Log warning and create a transparent placeholder
                logger.warning(f"Icon file not found: {icon_path}")
                img = Image.new('RGBA', size, (0, 0, 0, 0)) # Transparent placeholder
            photo_img = ImageTk.PhotoImage(img)
            self.icon_cache[icon_name] = photo_img # Store in cache
        except Exception as e:
            # Log error and create placeholder on any exception during load/resize
            logger.exception(f"Error loading icon '{icon_name}': {e}")
            try:
                 # Attempt placeholder creation even after error
                 img = Image.new('RGBA', size, (0, 0, 0, 0))
                 photo_img = ImageTk.PhotoImage(img)
                 self.icon_cache[icon_name] = photo_img # Cache placeholder too
            except Exception as pe:
                 logger.error(f"Failed even to create placeholder icon for {icon_name}: {pe}")
                 photo_img = None # Return None if placeholder fails too
        return photo_img

    def _create_widgets(self):
        """Creates and packs the sidebar buttons based on the items list."""
        logger.debug("Creating sidebar widgets.")
        # Define items: (Display Text, Icon Filename, Unique Identifier)
        items = [
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
            # Determine initial background color (Active BG for 'Settings')
            is_active_default = (identifier == "Settings")
            bg_color = ACTIVE_BG if is_active_default else SIDEBAR_BG

            # Create command lambda that passes the unique identifier
            cmd = (lambda id=identifier: self.command_callback(id)) if self.command_callback else None

            # Create the button widget
            button = tk.Button(
                self,
                text=f"  {text}",               # Add space for icon visual separation
                image=icon,                    # Set the loaded icon
                compound=tk.LEFT,              # Icon appears to the left of text
                anchor="w",                    # Align content (icon + text) to the west (left)
                relief=tk.FLAT,                # No 3D border
                bg=bg_color,                   # Initial background color
                fg=TEXT_COLOR,                 # Standard text color
                activebackground=HOVER_BG,     # Background when mouse button is pressed
                activeforeground=ACTIVE_TEXT_COLOR, # Text color when mouse button is pressed
                padx=15,                       # Horizontal padding inside the button
                pady=10,                       # Vertical padding inside the button
                font=BUTTON_FONT,              # Set the button font
                command=cmd                    # Assign the callback command
            )
            # Pack button to fill horizontally, add small vertical space between buttons
            button.pack(fill=tk.X, pady=1)
            # Store button widget using its identifier as the key
            self.buttons[identifier] = button
            # Bind hover effects (enter/leave)
            self._bind_hover(button, HOVER_BG, SIDEBAR_BG, ACTIVE_BG)

    def _bind_hover(self, widget: tk.Button, hover_color: str, leave_color: str, active_color: str):
        """
        Applies mouse enter/leave hover background color changes to a widget,
        avoiding changes if the widget is the currently active one.
        """
        def on_enter(event):
            # Check if widget exists before trying to access properties/methods
            try:
                 if widget.winfo_exists() and widget.cget('bg') != active_color:
                     widget.config(bg=hover_color)
            except tk.TclError: pass # Ignore if widget destroyed between event and check

        def on_leave(event):
            try:
                 if widget.winfo_exists() and widget.cget('bg') != active_color:
                     widget.config(bg=leave_color)
            except tk.TclError: pass

        # Bind events, use add='+' to prevent overwriting other potential bindings
        widget.bind("<Enter>", on_enter, add='+')
        widget.bind("<Leave>", on_leave, add='+')

    def set_active(self, identifier: str):
        """
        Highlights the specified sidebar button and de-highlights all others.
        Re-applies hover bindings after changing background colors.

        Args:
            identifier: The unique identifier string of the button to activate.
        """
        logger.debug(f"Setting active sidebar item: {identifier}")
        active_found = False
        # Iterate through all stored button widgets
        for id, button in self.buttons.items():
            try:
                 # Ensure the button widget hasn't been destroyed
                 if not button.winfo_exists():
                     logger.warning(f"Button '{id}' widget destroyed, skipping in set_active.")
                     continue

                 # Check if the current button's ID matches the target identifier
                 is_active = (id == identifier)
                 if is_active:
                     active_found = True

                 # Update the button's background color
                 button.config(bg=ACTIVE_BG if is_active else SIDEBAR_BG)

                 # --- Crucial: Re-apply hover bindings ---
                 # Unbind previous hover events first to avoid multiple bindings firing
                 button.unbind("<Enter>")
                 button.unbind("<Leave>")
                 # Re-bind using the helper method, passing the correct active color context
                 self._bind_hover(button, HOVER_BG, SIDEBAR_BG, ACTIVE_BG)

            except tk.TclError:
                 # Log gracefully if configuring a destroyed widget
                 logger.warning(f"Error setting active state for sidebar button '{id}' (widget destroyed?)")
            except Exception as e:
                 # Catch other unexpected errors during config/bind
                 logger.exception(f"Unexpected error setting active state for sidebar button '{id}': {e}")

        # Log a warning if the provided identifier didn't match any known button
        if not active_found:
             logger.warning(f"Sidebar identifier '{identifier}' not found for highlighting.")
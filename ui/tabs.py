# TallyPrimeConnect/ui/tabs.py
import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)

# --- Constants ---
TAB_BG = "#ffffff"
TAB_HEIGHT = 50
ACTIVE_COLOR = "#0078d4" # Blue
INACTIVE_COLOR = "#555555" # Gray
FONT_FAMILY = "Arial"
FONT_SIZE = 10
FONT_WEIGHT = "bold"

class Tabs(tk.Frame):
    """Top navigation tab bar."""
    def __init__(self, parent, command_callback=None, *args, **kwargs):
        """Initializes the tab bar."""
        super().__init__(parent, bg=TAB_BG, height=TAB_HEIGHT, *args, **kwargs)
        self.pack_propagate(False)
        self.tab_buttons = {} # Stores {"name": {"button": btn, "underline": frame}}
        self.active_tab = "TALLY" # Default active tab
        self.command_callback = command_callback # Optional callback on tab change
        self._create_widgets()
        self.update_tabs() # Set initial visual state
        logger.debug("Tabs initialized.")

    def _create_widgets(self):
        """Creates the individual tab buttons and underlines."""
        tab_names = ["TALLY", "SYNC", "ADDITIONAL"]
        container = tk.Frame(self, bg=TAB_BG)
        # Use padding to position tabs within the main Tabs frame
        container.pack(side=tk.LEFT, padx=20, pady=(10, 0))

        for name in tab_names:
            # Frame holds button + underline for better alignment control
            frame = tk.Frame(container, bg=TAB_BG)
            frame.pack(side=tk.LEFT, padx=15) # Spacing between tabs

            btn = tk.Button(
                frame, text=name, relief=tk.FLAT, bg=TAB_BG, fg=INACTIVE_COLOR,
                activebackground=TAB_BG, activeforeground=ACTIVE_COLOR, # Click color
                font=(FONT_FAMILY, FONT_SIZE, FONT_WEIGHT), cursor="hand2",
                command=lambda n=name: self.set_active_tab(n)
            )
            btn.pack(side=tk.TOP)

            # Underline indicator (initially hidden by matching background)
            underline = tk.Frame(frame, height=2, bg=TAB_BG)
            underline.pack(fill=tk.X, pady=(2, 0)) # Fill horizontally below button

            self.tab_buttons[name] = {"button": btn, "underline": underline}

    def set_active_tab(self, tab_name: str):
        """Sets the currently active tab and updates visuals."""
        if tab_name in self.tab_buttons:
            logger.info(f"Tab selected: {tab_name}")
            self.active_tab = tab_name
            self.update_tabs()
            if self.command_callback:
                 try: self.command_callback(self.active_tab)
                 except Exception as e: logger.exception(f"Error in tab command callback: {e}")
        else:
            logger.warning(f"Attempted to set unknown active tab: '{tab_name}'")

    def update_tabs(self):
        """Updates button colors and underlines based on the active tab."""
        logger.debug(f"Updating tab visuals, active: {self.active_tab}")
        for name, widgets in self.tab_buttons.items():
            is_active = (name == self.active_tab)
            try:
                 if widgets["button"].winfo_exists():
                     widgets["button"].config(fg=ACTIVE_COLOR if is_active else INACTIVE_COLOR)
                 if widgets["underline"].winfo_exists():
                     widgets["underline"].config(bg=ACTIVE_COLOR if is_active else TAB_BG)
            except tk.TclError: logger.warning(f"Error updating tab '{name}' (widget destroyed?)")

    def show(self):
        """Makes the tab bar visible using pack."""
        # This method might not be strictly needed if app.py handles packing/forgetting
        logger.debug("Showing Tabs widget.")
        if not self.winfo_ismapped():
            self.pack(fill=tk.X, side=tk.TOP) # Use standard packing

    def hide(self):
        """Hides the tab bar using pack_forget."""
        logger.debug("Hiding Tabs widget.")
        if self.winfo_ismapped():
            self.pack_forget()
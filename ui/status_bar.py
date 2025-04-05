# TallyPrimeConnect/ui/status_bar.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import logging

logger = logging.getLogger(__name__)

# --- Constants ---
try: BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError: BASE_DIR = os.path.dirname(os.getcwd())
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
ICONS_DIR = os.path.join(ASSETS_DIR, 'icons')

STATUS_BAR_BG = "#f0f0f0"
STATUS_BAR_HEIGHT = 30
TEXT_COLOR = "#333333"
MUTED_COLOR = "#6c757d"
STATUS_FONT = ("Arial", 9)
INDICATOR_FONT = ("Arial", 12)

# Status Colors
STATUS_CONNECTED_COLOR = "#2ecc71" # Green
STATUS_DISCONNECTED_COLOR = "#e74c3c" # Red
STATUS_CHECKING_COLOR = "#f39c12" # Orange

class StatusBar(tk.Frame):
    """Bottom status bar displaying connection, version, and progress."""
    def __init__(self, parent, *args, **kwargs):
        """Initializes the status bar."""
        super().__init__(parent, bg=STATUS_BAR_BG, height=STATUS_BAR_HEIGHT, bd=1, relief=tk.SUNKEN, *args, **kwargs)
        self.pack_propagate(False) # Prevent resizing by content height
        self.icon_cache = {}
        self._create_widgets()
        self.update_tally_status(connected=None) # Set initial state
        logger.debug("StatusBar initialized.")

    def _load_icon(self, icon_name: str, size=(16, 16)) -> ImageTk.PhotoImage | None:
        """Loads and caches an icon PhotoImage."""
        # ... (Implementation remains the same) ...
        if icon_name in self.icon_cache: return self.icon_cache[icon_name]
        icon_path = os.path.join(ICONS_DIR, icon_name); photo_img = None
        try:
            img = Image.open(icon_path).resize(size, Image.Resampling.LANCZOS) if os.path.exists(icon_path) else Image.new('RGBA', size, (0,0,0,0))
            photo_img = ImageTk.PhotoImage(img); self.icon_cache[icon_name] = photo_img
        except Exception as e: logger.exception(f"Err load status icon {icon_name}: {e}")
        return photo_img

    def _create_widgets(self):
        """Creates the static widgets within the status bar."""
        logger.debug("Creating status bar widgets.")
        pad_x = 10; pad_y = (STATUS_BAR_HEIGHT - 18) // 2 # Auto vertical padding

        # --- Left Side: Tally Status ---
        tally_frame = tk.Frame(self, bg=self["bg"]); tally_frame.pack(side=tk.LEFT, padx=(pad_x, 5), pady=pad_y)
        self.tally_indicator_label = tk.Label(tally_frame, text="●", bg=self["bg"], font=INDICATOR_FONT); self.tally_indicator_label.pack(side=tk.LEFT, padx=(0, 5))
        self.tally_status_label = tk.Label(tally_frame, font=STATUS_FONT, bg=self["bg"], fg=TEXT_COLOR); self.tally_status_label.pack(side=tk.LEFT)

        # --- Center Area: Sync Progress ---
        self.sync_frame = tk.Frame(self, bg=self["bg"]); self.sync_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=pad_y)
        self.sync_label = tk.Label(self.sync_frame, text="", font=STATUS_FONT, bg=self["bg"], fg=MUTED_COLOR); self.sync_label.pack(side=tk.LEFT, padx=(0, 5))
        self.sync_progress = ttk.Progressbar(self.sync_frame, orient='horizontal', length=150, mode='determinate') # Defined but not packed

        # --- Right Side: Version & Internet ---
        internet_frame = tk.Frame(self, bg=self["bg"]); internet_frame.pack(side=tk.RIGHT, padx=(0, pad_x), pady=pad_y)
        wifi_icon = self._load_icon("wifi.png");
        if wifi_icon: icon_label = tk.Label(internet_frame, image=wifi_icon, bg=self["bg"]); icon_label.pack(side=tk.LEFT, padx=(0, 5)); icon_label.image = wifi_icon # Keep reference
        tk.Label(internet_frame, text="Internet: CONNECTED", font=STATUS_FONT, bg=self["bg"], fg=TEXT_COLOR).pack(side=tk.LEFT) # Placeholder text
        tk.Label(self, text="v1.1.0", font=STATUS_FONT, bg=self["bg"], fg=MUTED_COLOR).pack(side=tk.RIGHT, padx=(0, pad_x), pady=pad_y) # Version packed last

    def update_tally_status(self, connected: bool | None = None, checking: bool = False):
        """Updates the Tally connection status indicator and text."""
        # ... (Implementation remains the same) ...
        if checking: status_text, color = "Tally: CHECKING...", STATUS_CHECKING_COLOR
        elif connected: status_text, color = "Tally: CONNECTED", STATUS_CONNECTED_COLOR
        elif connected is False: status_text, color = "Tally: DISCONNECTED", STATUS_DISCONNECTED_COLOR
        else: status_text, color = "Tally: UNKNOWN", MUTED_COLOR
        try:
            if hasattr(self, 'tally_indicator_label') and self.tally_indicator_label.winfo_exists(): self.tally_indicator_label.config(fg=color)
            if hasattr(self, 'tally_status_label') and self.tally_status_label.winfo_exists(): self.tally_status_label.config(text=status_text)
            if self.winfo_exists(): self.update_idletasks()
        except tk.TclError as e: logger.warning(f"Error updating tally status: {e}")

    def update_sync_progress(self, current: int, total: int, message: str = ""):
        """Updates the sync progress bar and label. Shows the progress bar."""
        logger.debug(f"Status bar update: Sync {current}/{total} - {message}")
        try:
            if not hasattr(self, 'sync_frame') or not self.sync_frame.winfo_exists(): return
            if hasattr(self, 'sync_label') and self.sync_label.winfo_exists(): self.sync_label.config(text=f"{message} ({current}/{total})")
            if hasattr(self, 'sync_progress') and self.sync_progress.winfo_exists():
                if total > 0 and current >= 0: # Basic validation
                    progress_val = min(100, (current / total) * 100) # Ensure value <= 100
                    self.sync_progress.config(value=progress_val)
                    if not self.sync_progress.winfo_ismapped(): logger.debug("Packing sync progress bar."); self.sync_progress.pack(in_=self.sync_frame, side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
                else: # Hide if total <= 0 or current < 0
                     if self.sync_progress.winfo_ismapped(): logger.debug("Unpacking sync progress bar (invalid total/current)."); self.sync_progress.pack_forget()
            if self.winfo_exists(): self.update_idletasks()
        except tk.TclError as e: logger.warning(f"Error updating sync progress: {e}")

    def clear_sync_progress(self):
        """Hides the sync progress bar and clears the label."""
        logger.debug("Clearing sync progress from status bar")
        try:
            if not hasattr(self, 'sync_frame') or not self.sync_frame.winfo_exists(): return
            if hasattr(self, 'sync_label') and self.sync_label.winfo_exists(): self.sync_label.config(text="")
            if hasattr(self, 'sync_progress') and self.sync_progress.winfo_ismapped(): logger.debug("Unpacking sync progress bar."); self.sync_progress.pack_forget()
            if self.winfo_exists(): self.update_idletasks()
        except tk.TclError as e: logger.warning(f"Error clearing sync progress: {e}")
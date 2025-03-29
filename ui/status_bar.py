# TallyPrimeConnect/ui/status_bar.py
import tkinter as tk
from PIL import Image, ImageTk
import os

try:
    from utils.helpers import BASE_DIR
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
ICONS_DIR = os.path.join(ASSETS_DIR, 'icons')

STATUS_CONNECTED_COLOR = "#2ecc71" # Green
STATUS_DISCONNECTED_COLOR = "#e74c3c" # Red
STATUS_CHECKING_COLOR = "#f39c12" # Orange/Yellow

class StatusBar(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, bg="#f0f0f0", height=30, bd=1, relief=tk.SUNKEN, *args, **kwargs)
        self.pack_propagate(False)
        self.icon_cache = {}
        self._create_widgets()
        # Set initial state (can be updated later)
        self.update_tally_status(connected=True) # Assume connected initially or based on last known state

    def _load_icon(self, icon_name, size=(16, 16)):
        # (Keep the existing _load_icon method)
        if icon_name in self.icon_cache:
            return self.icon_cache[icon_name]

        icon_path = os.path.join(ICONS_DIR, icon_name)
        if not os.path.exists(icon_path):
            print(f"Warning: Status icon not found at {icon_path}")
            return None # Handle missing icon gracefully
        try:
            img = Image.open(icon_path).resize(size, Image.Resampling.LANCZOS)
            photo_img = ImageTk.PhotoImage(img)
            self.icon_cache[icon_name] = photo_img
            return photo_img
        except Exception as e:
            print(f"Error loading status icon {icon_name}: {e}")
            return None

    def _create_widgets(self):
        status_font = ("Arial", 9)
        pad_x = 10
        pad_y = 5

        # --- Tally Status (Left) ---
        tally_frame = tk.Frame(self, bg=self["bg"])
        tally_frame.pack(side=tk.LEFT, padx=(pad_x, 0), pady=pad_y)

        # Store indicator and label for updating
        self.tally_indicator_label = tk.Label(
            tally_frame,
            text="●",
            bg=self["bg"],
            font=("Arial", 12)
        )
        self.tally_indicator_label.pack(side=tk.LEFT, padx=(0, 5))

        self.tally_status_label = tk.Label(
            tally_frame,
            font=status_font,
            bg=self["bg"],
            fg="#333333"
        )
        self.tally_status_label.pack(side=tk.LEFT)

        # --- Version (Center) ---
        version_label = tk.Label(
            self,
            text="v2.5.6", # You might want to load this dynamically too
            font=status_font,
            bg=self["bg"],
            fg="#555555"
        )
        version_label.pack(side=tk.LEFT, expand=True, pady=pad_y)

        # --- Internet Status (Right) ---
        # (Keep existing internet status part)
        internet_frame = tk.Frame(self, bg=self["bg"])
        internet_frame.pack(side=tk.RIGHT, padx=pad_x, pady=pad_y)
        wifi_icon = self._load_icon("wifi.png")
        if wifi_icon:
            icon_label = tk.Label(internet_frame, image=wifi_icon, bg=self["bg"])
            icon_label.pack(side=tk.LEFT, padx=(0, 5))
            icon_label.image = wifi_icon
        internet_label = tk.Label(
            internet_frame,
            text="Internet: CONNECTED", # Make this dynamic if needed later
            font=status_font,
            bg=self["bg"],
            fg="#333333"
        )
        internet_label.pack(side=tk.LEFT)


    def update_tally_status(self, connected: bool = None, checking: bool = False):
        """Updates the Tally status indicator and text.

        Args:
            connected (bool, optional): True for connected, False for disconnected. Defaults to None.
            checking (bool, optional): True to show a 'checking' state. Defaults to False.
        """
        if checking:
            status_text = "Tally: CHECKING..."
            color = STATUS_CHECKING_COLOR
        elif connected is True:
            status_text = "Tally: CONNECTED"
            color = STATUS_CONNECTED_COLOR
        elif connected is False:
            status_text = "Tally: DISCONNECTED"
            color = STATUS_DISCONNECTED_COLOR
        else:
            # Handle cases where status is unknown or unset, perhaps default to disconnected?
            status_text = "Tally: UNKNOWN"
            color = "gray" # Or default disconnected color

        self.tally_indicator_label.config(fg=color)
        self.tally_status_label.config(text=status_text)
        # Force UI update if needed, especially during/after potentially blocking operations
        self.update_idletasks()

# Example usage (if run directly)
if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("800x50")
    root.title("Status Bar Test")
    statusbar = StatusBar(root)
    statusbar.pack(fill=tk.X, side=tk.BOTTOM)

    # Example updates
    statusbar.update_tally_status(connected=False)
    root.after(2000, lambda: statusbar.update_tally_status(checking=True))
    root.after(4000, lambda: statusbar.update_tally_status(connected=True))

    root.mainloop()
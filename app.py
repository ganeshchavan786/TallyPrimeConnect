# TallyPrimeConnect/app.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import logging.config
import json
import os
from PIL import Image, ImageTk

# --- Setup Logging ---
log_config_path = os.path.join(os.path.dirname(__file__), 'config', 'logging_config.json'); log_file_path = os.path.join(os.path.dirname(__file__), 'app.log')
try:
    os.makedirs(os.path.dirname(log_config_path), exist_ok=True)
    if os.path.exists(log_config_path):
        with open(log_config_path, 'rt', encoding='utf-8') as f: config = json.load(f);
        if 'file' in config.get('handlers', {}): config['handlers']['file']['filename'] = log_file_path
        logging.config.dictConfig(config); print(f"Logging configured from {log_config_path}")
    else: raise FileNotFoundError(f"Log config not found: {log_config_path}")
except Exception as e: logging.basicConfig(level=logging.INFO); logging.error(f"Log config fail: {e}", exc_info=True); print(f"WARN: Log config fail: {e}")
logger = logging.getLogger(__name__)

# --- Constants ---
try: BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError: BASE_DIR = os.getcwd()
ASSETS_DIR = os.path.join(BASE_DIR, 'assets'); APP_WIDTH = 800; APP_HEIGHT = 550; HEADER_HEIGHT = 40; HEADER_BG = "#00a0e4"; WINDOW_BG = "#ffffff"

# --- Imports (After Logging) ---
try:
    # UI Components (Import functional and placeholder panels)
    from ui.sidebar import Sidebar
    from ui.tabs import Tabs
    from ui.status_bar import StatusBar
    from ui.tally_config import TallyConfigPanel # Functional from Stage 3
    from ui.add_company import AddCompanyPanel    # Placeholder Stage 4
    from ui.my_companies import MyCompaniesPanel  # Placeholder Stage 4
    from ui.license_info import LicenseInfoPanel  # Placeholder Stage 4
    # Utilities
    from utils.database import init_db # Keep DB init
    # from utils.helpers import BASE_DIR # Not strictly needed here anymore
except ImportError as e: logger.critical(f"Import fail: {e}", exc_info=True); messagebox.showerror("Import Error", f"Critical component failed:\n{e}\nApp cannot start."); import sys; sys.exit(1)


class TallyPrimeConnectApp:
    """Main application class."""
    def __init__(self, root: tk.Tk):
        """Initialize the application UI and components."""
        logger.info("Initializing TallyPrimeConnectApp (Stage 4 Update)")
        self.root = root; self.root.title("Biz Analyst"); self.root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}"); self.root.configure(bg=WINDOW_BG)
        try: init_db() # Initialize DB early
        except Exception as e: logger.exception("DB Init Error."); messagebox.showerror("DB Error", f"Failed DB init: {e}"); self.root.destroy(); return
        self.logo_image = self._load_logo(); self.panels = {} # Panel dictionary
        # Create UI structure
        self._create_header(); self._create_main_content_area(); self._create_status_bar();
        self._create_sidebar(command_callback=self.show_panel); # Pass show_panel as callback
        self._create_right_panel()
        # Instantiate all panels and store them
        self._instantiate_panels()
        # Show the default panel
        self.show_panel("Settings")
        logger.info("Application initialized successfully.")

    def _load_logo(self, size=(24, 24)) -> ImageTk.PhotoImage | None:
        logo_path = os.path.join(ASSETS_DIR, 'logo.png'); logger.debug(f"Loading logo: {logo_path}")
        os.makedirs(ASSETS_DIR, exist_ok=True) # Ensure assets dir exists
        try:
            if not os.path.exists(logo_path): raise FileNotFoundError(f"Logo not found: {logo_path}")
            img = Image.open(logo_path).resize(size, Image.Resampling.LANCZOS); return ImageTk.PhotoImage(img)
        except FileNotFoundError as e: logger.error(e)
        except Exception as e: logger.exception(f"Error loading logo: {e}")
        return None

    def _create_header(self):
        logger.debug("Creating header"); header = tk.Frame(self.root, height=HEADER_HEIGHT, bg=HEADER_BG); header.pack(fill=tk.X, side=tk.TOP); header.pack_propagate(False)
        if self.logo_image: logo_h=self.logo_image.height(); pad_y=(HEADER_HEIGHT-logo_h)//2; tk.Label(header, image=self.logo_image, bg=HEADER_BG).pack(side=tk.LEFT, padx=10, pady=pad_y)
        else: logger.warning("Logo not loaded.")
        tk.Label(header, text="Biz Analyst", bg=HEADER_BG, fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5, pady=5)

    def _create_main_content_area(self):
        logger.debug("Creating main area"); self.main_area = tk.Frame(self.root, bg=WINDOW_BG); self.main_area.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

    def _create_status_bar(self):
        logger.debug("Creating status bar");
        try: self.status_bar = StatusBar(self.root); self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        except Exception as e: logger.exception("Failed status bar creation."); self.status_bar = None

    def _create_sidebar(self, command_callback=None): # Accepts callback
        logger.debug("Creating sidebar");
        try: self.sidebar = Sidebar(self.main_area, command_callback=command_callback); self.sidebar.pack(fill=tk.Y, side=tk.LEFT)
        except Exception as e: logger.exception("Failed sidebar creation."); self.sidebar = None

    def _create_right_panel(self):
        logger.debug("Creating right panel"); self.right_panel = tk.Frame(self.main_area, bg=WINDOW_BG); self.right_panel.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)
        try: self.tabs = Tabs(self.right_panel) # Create Tabs instance
        except Exception as e: logger.exception("Failed tabs creation."); self.tabs = None
        # Content frame sits below tabs (if tabs are packed)
        self.content_frame = tk.Frame(self.right_panel, bg=WINDOW_BG); self.content_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

    def _instantiate_panels(self):
        """Creates instances of ALL content panels and stores them in self.panels dictionary."""
        panel_errors = []
        logger.debug("Instantiating UI panels...")
        if not hasattr(self, 'content_frame') or not self.content_frame: logger.critical("Cannot instantiate panels - content_frame missing."); return
        try:
            status_bar_ref = self.status_bar if hasattr(self, 'status_bar') else None
            # Instantiate all panels, using placeholders where needed for Stage 4
            self.panels["Settings"] = TallyConfigPanel(self.content_frame)
            self.panels["AddCompany"] = AddCompanyPanel(self.content_frame)
            self.panels["MyCompanies"] = MyCompaniesPanel(self.content_frame, status_bar_ref=status_bar_ref)
            self.panels["LicenseInfo"] = LicenseInfoPanel(self.content_frame)
            # Placeholders for remaining items
            self.panels["Profile"] = self._create_placeholder_panel("Profile")
            self.panels["SystemInfo"] = self._create_placeholder_panel("System Info")
            self.panels["Tutorial"] = self._create_placeholder_panel("Tutorial")
            self.panels["Support"] = self._create_placeholder_panel("Support")
            logger.debug(f"Panels created: {list(self.panels.keys())}")
        except Exception as e: logger.exception(f"Error instantiating panel: {e}"); panel_errors.append(str(e))
        if panel_errors: messagebox.showerror("UI Error", f"Failed panel creation:\n{'; '.join(panel_errors)}")

    def _create_placeholder_panel(self, name: str) -> tk.Widget:
        """Creates a simple placeholder label for unimplemented panels."""
        if not hasattr(self, 'content_frame') or not self.content_frame or not self.content_frame.winfo_exists(): return tk.Frame(self.root)
        return tk.Label(self.content_frame, text=f"{name}\n(Placeholder)", bg=WINDOW_BG, font=("Arial", 14), fg="#aaaaaa", justify=tk.CENTER)

    # --- Panel Switching Logic (Stage 4 Core) ---
    def show_panel(self, panel_identifier: str):
        """
        Shows the requested panel based on identifier, hides others,
        controls tab visibility, updates sidebar active state,
        and triggers data refresh for the shown panel.
        """
        logger.info(f"Switching to panel: {panel_identifier}")
        panel_to_show = self.panels.get(panel_identifier) # Get panel from dictionary

        if not panel_to_show:
            logger.error(f"Panel identifier '{panel_identifier}' not found in self.panels dictionary.")
            messagebox.showerror("Navigation Error", f"Panel '{panel_identifier}' could not be found.")
            return # Cannot proceed if panel doesn't exist

        # Ensure content_frame exists before trying to pack/unpack
        if not hasattr(self, 'content_frame') or not self.content_frame or not self.content_frame.winfo_exists():
             logger.error("Cannot show panel - content_frame missing or destroyed.")
             return

        # Hide all *other* currently visible panels within the content_frame
        logger.debug("Hiding other panels...")
        # Iterate through the known panels in the dictionary
        for identifier, panel in self.panels.items():
            if panel and isinstance(panel, tk.Widget) and identifier != panel_identifier:
                 # Check if the panel is currently being managed by 'pack' within the content_frame
                 if panel.master == self.content_frame and panel.winfo_ismapped():
                      try:
                          panel.pack_forget()
                          logger.debug(f"Hid panel: {identifier}")
                      except tk.TclError: pass # Ignore if already gone

        # Show the selected panel by packing it into the content_frame
        logger.debug(f"Packing panel: {panel_identifier}")
        try:
            # Ensure panel is packed within the correct parent
            panel_to_show.pack(in_=self.content_frame, fill=tk.BOTH, expand=True)
            panel_to_show.tkraise() # Bring to the front
        except tk.TclError as e:
            logger.exception(f"Failed to pack/display panel {panel_identifier}: {e}")
            messagebox.showerror("UI Error", f"Failed display panel: {panel_identifier}")
            return # Stop if panel cannot be shown

        # Control Tabs Visibility based on the *newly shown* panel
        self._update_tab_visibility(panel_identifier)

        # Refresh data *for the specific panel being shown* (if it has a load/refresh method)
        self._refresh_panel_data(panel_identifier, panel_to_show)

        # Update sidebar highlighting *after* successfully showing panel
        if hasattr(self, 'sidebar') and self.sidebar:
            self.sidebar.set_active(panel_identifier)
        else:
            logger.warning("Sidebar object missing, cannot set active state.")

    def _update_tab_visibility(self, panel_identifier: str):
        """Shows or hides the top tab bar based on the active panel identifier."""
        if not hasattr(self, 'tabs') or not self.tabs:
            logger.debug("Tabs widget not available for visibility update.")
            return

        try:
            if not self.tabs.winfo_exists(): return # Check if widget still exists

            # Determine if tabs should be visible
            show_tabs = (panel_identifier == "Settings")

            if show_tabs:
                # If tabs should be shown and are not currently visible
                if not self.tabs.winfo_ismapped():
                     logger.debug("Showing tabs for Settings panel.")
                     # Pack tabs within right_panel, *before* the content_frame
                     # This ensures correct stacking order
                     self.tabs.pack(in_=self.right_panel, fill=tk.X, side=tk.TOP, before=self.content_frame)
            else:
                # If tabs should be hidden and are currently visible
                if self.tabs.winfo_ismapped():
                     logger.debug(f"Hiding tabs for {panel_identifier} panel.")
                     self.tabs.pack_forget()

        except tk.TclError as e:
             logger.warning(f"Error managing tabs visibility: {e} (widget might be destroyed)")

    def _refresh_panel_data(self, panel_identifier: str, panel_instance):
        """Calls the appropriate refresh/load method for panels that need it when shown."""
        if not panel_instance or not isinstance(panel_instance, tk.Widget): return

        refresh_method = None
        logger.debug(f"Checking for refresh method on panel: {panel_identifier}")
        # Map identifiers to their data loading methods safely using hasattr
        if panel_identifier == "AddCompany" and hasattr(panel_instance, 'load_companies'):
            refresh_method = panel_instance.load_companies
        elif panel_identifier == "MyCompanies" and hasattr(panel_instance, 'refresh_list'):
            refresh_method = panel_instance.refresh_list
        elif panel_identifier == "LicenseInfo" and hasattr(panel_instance, 'load_license_info'):
            refresh_method = panel_instance.load_license_info
        # Add other panels that need refreshing here...

        if refresh_method:
            logger.info(f"Triggering data refresh for panel {panel_identifier}")
            try:
                refresh_method() # Call the panel's specific load/refresh method
            except Exception as e:
                logger.exception(f"Error during data refresh for panel {panel_identifier}: {e}")
                messagebox.showerror("Load Error", f"Failed to load data for {panel_identifier}.")
        else:
             logger.debug(f"No refresh method defined or needed for panel {panel_identifier}")


    def run(self):
        """Starts the Tkinter main event loop."""
        logger.info("Starting application main loop")
        try: self.root.mainloop()
        except Exception as e: logger.critical(f"Unhandled exception in mainloop: {e}", exc_info=True)
        finally: logger.info("Application closed")

# --- Main Execution ---
if __name__ == "__main__":
    logger.info("Application starting")
    root = tk.Tk()
    app_instance = None
    try:
        app_instance = TallyPrimeConnectApp(root)
        if root.winfo_exists(): # Check if window still exists after init
             app_instance.run()
    except Exception as e:
         logger.critical(f"Unhandled exception during app startup or run: {e}", exc_info=True)
         messagebox.showerror("Critical Error", f"An unexpected error occurred: {e}\nApplication will close.")
         if root and root.winfo_exists(): root.destroy()
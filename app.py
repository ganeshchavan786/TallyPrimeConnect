# TallyPrimeConnect/app.py
import tkinter as tk
import logging
import logging.config
import json
import os
from PIL import Image, ImageTk

# --- Setup Logging ---
# Load logging configuration from file relative to this script
log_config_path = os.path.join(os.path.dirname(__file__), 'config', 'logging_config.json')
log_file_path_in_config = os.path.join(os.path.dirname(__file__), 'app.log') # Define absolute path for log file

try:
    with open(log_config_path, 'rt') as f:
        config_data = json.load(f)
        # Update log file path dynamically
        if 'file' in config_data.get('handlers', {}):
            config_data['handlers']['file']['filename'] = log_file_path_in_config
        logging.config.dictConfig(config_data)
except (IOError, json.JSONDecodeError, KeyError) as e:
    # Fallback basic config if file fails
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.error(f"Failed to load logging config from {log_config_path}. Using basic config. Error: {e}")

logger = logging.getLogger(__name__)

# --- Constants ---
try:
    # Determine BASE_DIR robustly
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError: # Fallback for environments where __file__ might not be defined
    BASE_DIR = os.getcwd()

ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
APP_WIDTH = 800
APP_HEIGHT = 550
HEADER_HEIGHT = 40
HEADER_BG = "#00a0e4"
WINDOW_BG = "#ffffff"

# --- Imports (After Logging Setup) ---
# Standard library imports first (already done: tk, logging, json, os)
# Third-party imports (Pillow)
# Local application imports
from ui.sidebar import Sidebar
from ui.tabs import Tabs
from ui.tally_config import TallyConfigPanel
from ui.status_bar import StatusBar
from ui.add_company import AddCompanyPanel
from ui.my_companies import MyCompaniesPanel
from utils.database import init_db


class TallyPrimeConnectApp:
    """
    Main application class for the Biz Analyst Tally Connector UI clone.
    Orchestrates UI components and interactions.
    """
    def __init__(self, root: tk.Tk):
        """Initialize the application UI and components."""
        logger.info("Initializing TallyPrimeConnectApp")
        self.root = root
        self.root.title("Biz Analyst")
        self.root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.root.configure(bg=WINDOW_BG)
        # self.root.resizable(False, False) # Optional: Prevent resizing

        # Initialize Database
        try:
            init_db()
        except Exception as e:
            logger.exception("Fatal error during database initialization. Exiting.")
            # Optionally show a critical error message to the user
            # messagebox.showerror("Database Error", f"Failed to initialize database: {e}\nApplication cannot start.")
            self.root.destroy() # Stop app if DB fails critically
            return

        self.logo_image = self._load_logo()
        self.panels = {} # Dictionary to hold content panels

        # --- Create UI Structure ---
        self._create_header()
        self._create_main_content_area() # Creates self.main_area
        self._create_status_bar()
        self._create_sidebar(command_callback=self.show_panel) # Pass switching method
        self._create_right_panel() # Creates self.right_panel, self.tabs, self.content_frame

        # --- Instantiate Panels ---
        logger.debug("Instantiating UI panels")
        self._instantiate_panels()

        # --- Show Default Panel ---
        self.show_panel("Settings") # Start with settings view
        logger.info("Application initialized successfully")

    def _load_logo(self, size=(24, 24)) -> ImageTk.PhotoImage | None:
        """Loads the application logo from the assets directory."""
        logo_path = os.path.join(ASSETS_DIR, 'logo.png')
        try:
            img = Image.open(logo_path).resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except FileNotFoundError:
            logger.error(f"Logo file not found at {logo_path}")
        except Exception as e:
            logger.exception(f"Error loading logo: {e}")
        return None

    def _create_header(self):
        """Creates the top header bar with logo and title."""
        logger.debug("Creating header")
        header_frame = tk.Frame(self.root, height=HEADER_HEIGHT, bg=HEADER_BG)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)
        if self.logo_image:
            tk.Label(header_frame, image=self.logo_image, bg=HEADER_BG).pack(
                side=tk.LEFT, padx=10, pady=(HEADER_HEIGHT - self.logo_image.height()) // 2
            )
        tk.Label(header_frame, text="Biz Analyst", bg=HEADER_BG, fg="white", font=("Arial", 12, "bold")).pack(
            side=tk.LEFT, padx=5, pady=5
        )

    def _create_main_content_area(self):
        """Creates the main area frame below the header."""
        logger.debug("Creating main content area")
        self.main_area = tk.Frame(self.root, bg=WINDOW_BG)
        self.main_area.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

    def _create_status_bar(self):
        """Creates the bottom status bar."""
        logger.debug("Creating status bar")
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _create_sidebar(self, command_callback=None):
        """Creates the left sidebar navigation."""
        logger.debug("Creating sidebar")
        self.sidebar = Sidebar(self.main_area, command_callback=command_callback)
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT)

    def _create_right_panel(self):
        """Creates the right panel containing tabs and the content frame."""
        logger.debug("Creating right panel")
        self.right_panel = tk.Frame(self.main_area, bg=WINDOW_BG)
        self.right_panel.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)
        # Tabs are created here but visibility controlled by show_panel
        self.tabs = Tabs(self.right_panel)
        # Content frame holds the switchable panels
        self.content_frame = tk.Frame(self.right_panel, bg=WINDOW_BG)
        self.content_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

    def _instantiate_panels(self):
        """Creates instances of all content panels."""
        # Use constants or enums for panel identifiers if complexity grows
        self.panels["Settings"] = TallyConfigPanel(self.content_frame, status_bar=self.status_bar)
        self.panels["AddCompany"] = AddCompanyPanel(self.content_frame)
        self.panels["MyCompanies"] = MyCompaniesPanel(self.content_frame)
        # Placeholder panels
        self.panels["Profile"] = self._create_placeholder_panel("Profile")
        self.panels["SystemInfo"] = self._create_placeholder_panel("System Info")
        self.panels["Tutorial"] = self._create_placeholder_panel("Tutorial")
        self.panels["Support"] = self._create_placeholder_panel("Support")

    def _create_placeholder_panel(self, name: str) -> tk.Label:
        """Creates a simple placeholder label for unimplemented panels."""
        return tk.Label(self.content_frame, text=f"{name} (Not Implemented)", bg=WINDOW_BG, font=("Arial", 14))

    def show_panel(self, panel_identifier: str):
        """
        Shows the requested panel, controls tab visibility, and triggers data refresh.

        Args:
            panel_identifier: The string identifier of the panel to show (e.g., "Settings").
        """
        logger.info(f"Switching to panel: {panel_identifier}")
        panel_to_show = self.panels.get(panel_identifier)
        if not panel_to_show:
            logger.error(f"Panel identifier '{panel_identifier}' not found.")
            return

        # Hide all other panels first
        for identifier, panel in self.panels.items():
            if identifier != panel_identifier:
                panel.pack_forget()

        # Show the selected panel
        # Pack it below the tabs if tabs are visible, otherwise directly in content_frame
        if panel_identifier == "Settings":
             # Ensure tabs are packed before the content frame's content
             if hasattr(self, 'tabs'):
                 self.tabs.pack(fill=tk.X, side=tk.TOP, before=self.content_frame)
             else:
                 logger.warning("Tabs object not found when trying to show Settings")
        panel_to_show.pack(fill=tk.BOTH, expand=True)


        # Control Tabs Visibility
        self._update_tab_visibility(panel_identifier)

        # Refresh data for relevant panels when shown
        self._refresh_panel_data(panel_identifier, panel_to_show)

        # Update sidebar highlighting
        if hasattr(self, 'sidebar'):
            self.sidebar.set_active(panel_identifier)
        else:
            logger.warning("Sidebar object not found for highlighting")

    def _update_tab_visibility(self, panel_identifier: str):
        """Shows or hides the top tab bar based on the active panel."""
        if not hasattr(self, 'tabs'):
            logger.warning("Tabs object not found in _update_tab_visibility")
            return

        if panel_identifier == "Settings":
            logger.debug("Showing tabs for Settings panel")
            # Packing is handled in show_panel to ensure order
            # self.tabs.pack(fill=tk.X, side=tk.TOP, before=self.content_frame)
            pass # Tabs packed in show_panel
        else:
            logger.debug(f"Hiding tabs for {panel_identifier} panel")
            self.tabs.pack_forget()

    def _refresh_panel_data(self, panel_identifier: str, panel_instance):
        """Calls the appropriate refresh/load method for specific panels."""
        try:
            if panel_identifier == "AddCompany" and isinstance(panel_instance, AddCompanyPanel):
                logger.debug("Refreshing AddCompany panel data")
                panel_instance.load_companies()
            elif panel_identifier == "MyCompanies" and isinstance(panel_instance, MyCompaniesPanel):
                logger.debug("Refreshing MyCompanies panel data")
                panel_instance.refresh_list()
        except Exception as e:
            logger.exception(f"Error refreshing data for panel {panel_identifier}: {e}")
            # Optionally show user error message
            # messagebox.showerror("Error", f"Failed to load data for {panel_identifier}.")


    def run(self):
        """Starts the Tkinter main event loop."""
        logger.info("Starting application main loop")
        self.root.mainloop()
        logger.info("Application closed")

# --- Main Execution ---
if __name__ == "__main__":
    logger.info("Application starting")
    root = tk.Tk()
    try:
        app = TallyPrimeConnectApp(root)
        # Only run if initialization didn't fail
        if root.winfo_exists():
             app.run()
    except Exception as e:
         logger.critical(f"Unhandled exception during app startup or execution: {e}", exc_info=True)
         # Optionally show critical error messagebox
         # messagebox.showerror("Critical Error", f"An unexpected error occurred: {e}\nApplication will close.")
         if root.winfo_exists():
             root.destroy()
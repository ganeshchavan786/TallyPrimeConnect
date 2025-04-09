import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import queue
from utils.helpers import load_settings, save_settings, check_tally_connection, DEFAULT_SETTINGS

logger = logging.getLogger(__name__)

# --- UI Constants ---
PANEL_BG = "#ffffff"
FORM_AREA_BG = "#f8f8f8"
TITLE_FONT = ("Arial", 16, "bold")
LABEL_FONT = ("Arial", 9)
ENTRY_FONT = ("Arial", 10)
BUTTON_FONT = ("Arial", 10, "bold")
CHECK_BTN_BG = "#3498db"
CHECK_BTN_FG = "#ffffff"
CHECK_BTN_ACTIVE_BG = "#2980b9"
SAVE_BTN_BG = "#e74c3c"
SAVE_BTN_FG = "#ffffff"
SAVE_BTN_ACTIVE_BG = "#c0392b"

class TallyConfigPanel(tk.Frame):
    """Panel for configuring Tally settings and checking the connection."""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, bg=PANEL_BG, *args, **kwargs)
        self.host_var = tk.StringVar()
        self.port_var = tk.StringVar()
        self.is_checking_connection = False
        self._create_widgets()
        self._load_initial_data()
        logger.debug("TallyConfigPanel initialized.")

    def _create_widgets(self):
        """Creates widgets for Tally configuration and connection check."""
        logger.debug("Creating TallyConfigPanel widgets.")

        # --- Config Section ---
        tk.Label(self, text="Tally Configuration", font=TITLE_FONT, bg=PANEL_BG, anchor="w").pack(pady=(20, 5), padx=30, anchor="w")
        form_cont = tk.Frame(self, bg=FORM_AREA_BG, padx=50, pady=30, bd=1, relief=tk.GROOVE)
        form_cont.pack(pady=10, padx=50, fill=tk.X)
        form_cont.grid_columnconfigure(0, weight=1)

        # Host Input
        tk.Label(form_cont, text="Tally Host (e.g., localhost) *", font=LABEL_FONT, bg=FORM_AREA_BG, anchor="w").grid(row=0, column=0, sticky="w", pady=(0, 2))
        host_entry = ttk.Entry(form_cont, textvariable=self.host_var, width=50, font=ENTRY_FONT)
        host_entry.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        # Port Input
        tk.Label(form_cont, text="Tally Port (e.g., 9000) *", font=LABEL_FONT, bg=FORM_AREA_BG, anchor="w").grid(row=2, column=0, sticky="w", pady=(0, 2))
        port_entry = ttk.Entry(form_cont, textvariable=self.port_var, width=50, font=ENTRY_FONT)
        port_entry.grid(row=3, column=0, sticky="ew", pady=(0, 25))

        # Buttons
        config_btn_frame = tk.Frame(self, bg=PANEL_BG)
        config_btn_frame.pack(pady=(0, 10))
        self.check_button = tk.Button(
            config_btn_frame,
            text="Check Connection",
            command=self._check_connection_threaded,
            bg=CHECK_BTN_BG,
            fg=CHECK_BTN_FG,
            font=BUTTON_FONT,
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2",
            activebackground=CHECK_BTN_ACTIVE_BG,
        )
        self.check_button.pack(side=tk.LEFT, padx=(0, 10))
        save_button = tk.Button(
            config_btn_frame,
            text="SAVE",
            command=self._save_action,
            bg=SAVE_BTN_BG,
            fg=SAVE_BTN_FG,
            font=BUTTON_FONT,
            relief=tk.FLAT,
            padx=30,
            pady=8,
            cursor="hand2",
            activebackground=SAVE_BTN_ACTIVE_BG,
        )
        save_button.pack(side=tk.LEFT)

    def _load_initial_data(self):
        """Loads settings from file and populates the form variables."""
        logger.debug("Loading initial Tally config data.")
        try:
            settings = load_settings()
            self.host_var.set(settings.get("tally_host", DEFAULT_SETTINGS["tally_host"]))
            self.port_var.set(settings.get("tally_port", DEFAULT_SETTINGS["tally_port"]))
        except Exception as e:
            logger.exception(f"Error loading initial settings: {e}")
            messagebox.showerror("Load Error", f"Failed to load settings: {e}\nUsing application defaults.")
            self.host_var.set(DEFAULT_SETTINGS["tally_host"])
            self.port_var.set(DEFAULT_SETTINGS["tally_port"])

    def _validate_inputs(self) -> tuple[str | None, str | None]:
        """Validates host/port. Returns (host, port_string) or indicates failure with None."""
        host = self.host_var.get().strip()
        port_str = self.port_var.get().strip()

        if not host or not port_str:
            messagebox.showwarning("Input Error", "Tally Host and Port cannot be empty.")
            return None, None

        try:
            port_int = int(port_str)
            if not (0 < port_int < 65536):
                raise ValueError("Port number out of valid range")
        except ValueError:
            messagebox.showwarning("Input Error", "Please enter a valid Port number (1-65535).")
            return host, None

        return host, port_str

    def _save_action(self):
        """Saves the Tally configuration settings."""
        logger.debug("Save clicked.")
        host, port = self._validate_inputs()
        if host is None or port is None:
            return

        settings = {"tally_host": host, "tally_port": port}
        try:
            save_settings(settings)
            logger.info(f"Settings saved: {host}:{port}")
            messagebox.showinfo("Success", "Config saved.")
        except Exception as e:
            logger.exception("Error saving settings.")
            messagebox.showerror("Save Error", f"Failed to save settings: {e}")

    def _check_connection_threaded(self):
        """Checks the connection to Tally in a background thread."""
        logger.debug("Check Connection clicked.")
        if self.is_checking_connection:
            logger.warning("Check already running.")
            return

        host, port = self._validate_inputs()
        if host is None or port is None:
            return

        self.is_checking_connection = True
        try:
            self.check_button.config(state=tk.DISABLED, text="Checking...")
            self.update_idletasks()
        except tk.TclError:
            logger.warning("Error updating UI before check.")
            self.is_checking_connection = False
            return

        thread = threading.Thread(target=self._perform_check, args=(host, port), daemon=True)
        thread.start()

    def _perform_check(self, host: str, port: str):
        """Performs the connection check to Tally."""
        logger.info(f"Checking connection to {host}:{port}...")
        is_connected = False
        try:
            is_connected = check_tally_connection(host, port)
            logger.info(f"Check result: {is_connected}")
        except Exception as e:
            logger.exception(f"Error during connection check: {e}")
            is_connected = False
        finally:
            self.after(0, self._update_ui_after_check, is_connected, host, port)

    def _update_ui_after_check(self, is_connected: bool, host: str, port: str):
        """Updates the UI after the connection check."""
        logger.debug(f"Updating UI after check (Result: {is_connected}).")
        self.is_checking_connection = False
        try:
            self.check_button.config(state=tk.NORMAL, text="Check Connection")
            if is_connected:
                messagebox.showinfo("Success", f"Connected to Tally at {host}:{port}")
            else:
                messagebox.showerror("Failed", f"Could not connect to Tally at {host}:{port}.\nCheck settings, Tally status, and firewall.")
        except tk.TclError:
            logger.warning("Error updating UI after check.")
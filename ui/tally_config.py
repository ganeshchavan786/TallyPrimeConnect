# TallyPrimeConnect/ui/tally_config.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import webbrowser
import threading

# --- Import necessary helpers ---
from utils.helpers import load_settings, save_settings, check_tally_connection, DEFAULT_SETTINGS # <-- Added DEFAULT_SETTINGS

logger = logging.getLogger(__name__)

# --- UI Constants ---
PANEL_BG="#ffffff"; FORM_AREA_BG="#f8f8f8"; TITLE_FONT=("Arial", 16, "bold"); LABEL_FONT=("Arial", 9); ENTRY_FONT=("Arial", 10); BUTTON_FONT=("Arial", 10, "bold"); HELP_FONT=("Arial", 10, "underline"); HELP_LINK_COLOR="blue"; SAVE_BTN_BG="#e74c3c"; SAVE_BTN_FG="#ffffff"; SAVE_BTN_ACTIVE_BG="#c0392b"; CHECK_BTN_BG="#3498db"; CHECK_BTN_FG="#ffffff"; CHECK_BTN_ACTIVE_BG="#2980b9"; HELP_URL="https://bizanalyst.in/faq/"

class TallyConfigPanel(tk.Frame):
    """Panel for configuring and checking Tally connection settings."""
    def __init__(self, parent, status_bar=None, *args, **kwargs):
        """Initializes the Tally Configuration panel."""
        super().__init__(parent, bg=PANEL_BG, *args, **kwargs)
        self.status_bar = status_bar
        self.host_var = tk.StringVar()
        self.port_var = tk.StringVar()
        self._create_widgets()
        self._load_initial_data() # Load data after widgets are created
        logger.debug("TallyConfigPanel initialized.")

    def _create_widgets(self):
        """Creates the widgets for the configuration form."""
        logger.debug("Creating TallyConfigPanel widgets.")
        # --- Title & Subtitle ---
        tk.Label(self, text="Tally Configuration", font=TITLE_FONT, bg=PANEL_BG, anchor="w").pack(pady=(20, 5), padx=30, anchor="w")
        sub_frame = tk.Frame(self, bg=PANEL_BG); sub_frame.pack(pady=(0, 5), padx=30, anchor="w")
        tk.Label(sub_frame, text="Connect Tally using ODBC configuration.", font=LABEL_FONT, bg=PANEL_BG).pack(side=tk.LEFT) # Simplified text
        help_link = tk.Label(sub_frame, text="Click here", font=HELP_FONT, fg=HELP_LINK_COLOR, cursor="hand2", bg=PANEL_BG); help_link.pack(side=tk.LEFT, padx=(5,0)); help_link.bind("<Button-1>", self._open_help)
        tk.Label(sub_frame, text=" for help.", font=LABEL_FONT, bg=PANEL_BG).pack(side=tk.LEFT)

        # --- Form Area ---
        form_cont = tk.Frame(self, bg=FORM_AREA_BG, padx=50, pady=30); form_cont.pack(pady=30, padx=50, fill=tk.X)
        form_cont.grid_columnconfigure(0, weight=1); form_cont.grid_columnconfigure(1, weight=1) # Make columns expandable

        # Host Entry
        tk.Label(form_cont, text="Tally Host (eg. localhost) *", font=LABEL_FONT, bg=FORM_AREA_BG, anchor="w").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))
        host_entry = ttk.Entry(form_cont, textvariable=self.host_var, width=50, font=ENTRY_FONT); host_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # Port Entry
        tk.Label(form_cont, text="Tally Port (eg. 9000) *", font=LABEL_FONT, bg=FORM_AREA_BG, anchor="w").grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 2))
        port_entry = ttk.Entry(form_cont, textvariable=self.port_var, width=50, font=ENTRY_FONT); port_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 25))

        # Buttons Frame (centered using pack within a frame that spans grid)
        btn_frame = tk.Frame(form_cont, bg=FORM_AREA_BG); btn_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))

        # Check Connection Button
        self.check_button = tk.Button(btn_frame, text="Check Connection", command=self._check_connection_threaded, bg=CHECK_BTN_BG, fg=CHECK_BTN_FG, font=BUTTON_FONT, relief=tk.FLAT, padx=15, pady=8, cursor="hand2", activebackground=CHECK_BTN_ACTIVE_BG); self.check_button.pack(side=tk.LEFT, padx=(0, 10))

        # Save Button
        save_button = tk.Button(btn_frame, text="SAVE", command=self._save_action, bg=SAVE_BTN_BG, fg=SAVE_BTN_FG, font=BUTTON_FONT, relief=tk.FLAT, padx=30, pady=8, cursor="hand2", activebackground=SAVE_BTN_ACTIVE_BG); save_button.pack(side=tk.LEFT)

    def _load_initial_data(self):
        """Loads settings from file and populates the form."""
        logger.debug("Loading initial Tally config data.")
        try:
            settings = load_settings()
            # --- Use imported DEFAULT_SETTINGS ---
            self.host_var.set(settings.get("tally_host", DEFAULT_SETTINGS["tally_host"]))
            self.port_var.set(settings.get("tally_port", DEFAULT_SETTINGS["tally_port"]))
            # -------------------------------------
        except Exception as e:
            logger.exception(f"Error loading initial settings: {e}")
            messagebox.showerror("Load Error", f"Failed to load settings: {e}\nUsing application defaults.")
            # Set defaults manually if load failed completely
            if not self.host_var.get(): self.host_var.set(DEFAULT_SETTINGS["tally_host"])
            if not self.port_var.get(): self.port_var.set(DEFAULT_SETTINGS["tally_port"])

    def _open_help(self, event=None):
        """Opens the help URL in a web browser."""
        logger.info(f"Opening help link: {HELP_URL}")
        try: webbrowser.open(HELP_URL, new=2)
        except Exception as e: logger.exception(f"Error opening help link: {e}"); messagebox.showerror("Error", f"Could not open help link:\n{e}")

    def _validate_inputs(self) -> tuple[str | None, str | None]:
        """Validates host/port. Returns (host, port) or (None, None) / (host, None)."""
        host = self.host_var.get().strip(); port = self.port_var.get().strip()
        if not host or not port: messagebox.showwarning("Input Error", "Host and Port required."); return None, None
        if not port.isdigit() or not 0 < int(port) < 65536: messagebox.showwarning("Input Error", "Invalid Port (1-65535)."); return host, None
        return host, port

    def _save_action(self):
        """Saves the current host and port values after validation."""
        logger.debug("Save button clicked.")
        host, port = self._validate_inputs()
        if host is None or port is None: return
        settings = {"tally_host": host, "tally_port": port}
        try: save_settings(settings); logger.info(f"Settings saved: {host}:{port}"); messagebox.showinfo("Success", "Configuration saved.")
        except Exception as e: logger.exception("Error saving."); messagebox.showerror("Save Error", f"Failed save: {e}")

    def _check_connection_threaded(self):
        """Starts the connection check in a background thread."""
        logger.debug("Check Connection button clicked.")
        host, port = self._validate_inputs()
        if host is None or port is None: return
        try:
            self.check_button.config(state=tk.DISABLED, text="Checking...")
            if self.status_bar and hasattr(self.status_bar, 'update_tally_status'): self.status_bar.update_tally_status(checking=True)
            if self.winfo_exists(): self.update_idletasks()
        except tk.TclError: logger.warning("Error updating UI before check."); return
        thread = threading.Thread(target=self._perform_check, args=(host, port), daemon=True); thread.start()

    def _perform_check(self, host: str, port: str):
        """Performs connection check (called by thread). Schedules UI update."""
        logger.info(f"Checking connection to {host}:{port}..."); is_connected = False
        try: is_connected = check_tally_connection(host, port); logger.info(f"Check result: {is_connected}")
        except Exception as e: logger.exception(f"Error during check call: {e}"); is_connected = False
        finally: # Schedule UI update in main thread
            def update_ui():
                try:
                    if hasattr(self, 'check_button') and self.check_button.winfo_exists(): self.check_button.config(state=tk.NORMAL, text="Check Connection")
                    if self.status_bar and hasattr(self.status_bar, 'update_tally_status') and self.status_bar.winfo_exists(): self.status_bar.update_tally_status(connected=is_connected)
                    if is_connected: messagebox.showinfo("Success", f"Connected to Tally at {host}:{port}")
                    else: messagebox.showerror("Failed", f"Could not connect to Tally at {host}:{port}.\nCheck settings, Tally status, firewall.")
                except tk.TclError: logger.warning("Error updating check UI (widget destroyed?).")
                except Exception as e_ui: logger.exception(f"Unexpected UI update error after check: {e_ui}")
            if hasattr(self, 'winfo_exists') and self.winfo_exists(): self.after(0, update_ui)
            else: logger.warning("Panel destroyed before check UI update.")
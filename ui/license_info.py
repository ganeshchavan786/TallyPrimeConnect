# TallyPrimeConnect/ui/license_info.py
import tkinter as tk
from tkinter import ttk, font, messagebox
import logging

# Import the specific fetch function
from utils.odbc_helper import fetch_tally_license_info_odbc

logger = logging.getLogger(__name__)

# --- UI Constants --- Consistent styling
PANEL_BG = "#ffffff"
DATA_AREA_BG = "#f8f8f8" # Background for the data grid
TITLE_FONT = ("Arial", 16, "bold")
LABEL_FONT = ("Arial", 10)
VALUE_FONT = ("Arial", 10, "bold") # Make values stand out
ERROR_COLOR = "red"
INFO_COLOR = "black"
MUTED_COLOR = "gray"

# Define the fields to display and their labels (matches LICENSE_FIELD_MAP keys from odbc_helper)
LICENSE_DISPLAY_FIELDS = {
    "serial_number": "Serial Number",
    "account_id": "Account ID",
    "site_id": "Site ID",
    "admin_email": "Admin Email ID",
    "is_indian": "Is Indian License?",
    "license_type": "License Type", # Derived below
    "is_licensed": "Is Licensed Mode?",
    "version": "Installed Version",
    "gateway_server": "Gateway Server",
    "acting_as": "Acting As",
    "odbc_enabled": "ODBC Enabled",
    "odbc_port": "ODBC Port"
}

class LicenseInfoPanel(tk.Frame):
    """Panel to display Tally License information fetched via ODBC."""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, bg=PANEL_BG, *args, **kwargs)
        self.license_data_vars = {} # Store StringVars for display fields {key: StringVar}
        self._create_widgets()
        logger.debug("LicenseInfoPanel initialized.")

    def _create_widgets(self):
        """Creates the static widgets for the panel."""
        logger.debug("Creating widgets for LicenseInfoPanel")
        # Title
        tk.Label(self, text="Tally License Information", font=TITLE_FONT, bg=PANEL_BG, anchor="w").pack(
            pady=(10, 10), padx=30, anchor="w"
        )

        # Data Container with background
        data_container = tk.Frame(self, bg=DATA_AREA_BG, bd=1, relief=tk.SUNKEN)
        data_container.pack(pady=10, padx=50, fill=tk.BOTH, expand=True)

        # Status Label (for loading/errors)
        self.status_label = tk.Label(data_container, text="Loading...", font=LABEL_FONT, bg=DATA_AREA_BG, fg=MUTED_COLOR)
        self.status_label.pack(pady=20)

        # Grid Frame for aligned data
        self.grid_frame = tk.Frame(data_container, bg=DATA_AREA_BG)
        # Grid frame will be packed later when data is loaded

        # Create Label/Value pairs using grid layout
        row_index = 0
        for key, label_text in LICENSE_DISPLAY_FIELDS.items():
            # Create Label (Title) - Right aligned within its cell
            label = tk.Label(self.grid_frame, text=f"{label_text}:", font=LABEL_FONT, bg=DATA_AREA_BG, anchor='e')
            label.grid(row=row_index, column=0, padx=(10, 5), pady=3, sticky='ew') # East-West sticky

            # Create StringVar and Readonly Entry/Label for Value - Left aligned within its cell
            data_var = tk.StringVar(value="...") # Initial placeholder
            self.license_data_vars[key] = data_var
            # Use readonly Entry to allow copying, looks slightly different than Label
            value_display = ttk.Entry(self.grid_frame, textvariable=data_var, font=VALUE_FONT, state='readonly', justify='left')
            value_display.grid(row=row_index, column=1, padx=(0, 10), pady=3, sticky='ew') # East-West sticky

            row_index += 1

        # Configure grid columns to allocate space
        self.grid_frame.grid_columnconfigure(0, weight=1) # Label column gets some weight
        self.grid_frame.grid_columnconfigure(1, weight=3) # Value column gets more weight

        # Optional: Add a refresh button?
        # refresh_btn = tk.Button(self, text="Refresh", command=self.load_license_info)
        # refresh_btn.pack(pady=(5, 10))

    def load_license_info(self):
        """Fetches license info via ODBC and updates the display variables."""
        logger.info("Loading Tally License information...")
        # Reset display and show status
        for key, var in self.license_data_vars.items():
            var.set("...") # Reset to placeholder
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
             self.status_label.pack(pady=20); self.status_label.config(text="Fetching...", fg=MUTED_COLOR)
        if hasattr(self, 'grid_frame') and self.grid_frame.winfo_ismapped(): self.grid_frame.pack_forget()
        try: self.update_idletasks()
        except tk.TclError: pass # Ignore if widget destroyed

        # Fetch data (this might block briefly, consider threading if it takes too long)
        license_info = None
        try:
            license_info = fetch_tally_license_info_odbc() # Call the helper
        except Exception as e:
            logger.exception("Unexpected error calling fetch_tally_license_info_odbc.")
            if hasattr(self, 'status_label') and self.status_label.winfo_exists(): self.status_label.config(text="Error fetching.", fg=ERROR_COLOR)
            messagebox.showerror("Fetch Error", f"Failed to get license info: {e}")
            return # Stop processing

        # Update UI based on result
        if not hasattr(self, 'status_label') or not self.status_label.winfo_exists(): return # Stop if UI gone

        if license_info is None:
            logger.error("Failed to fetch license info (None returned). Check ODBC/Tally.")
            self.status_label.config(text="Failed fetch.\nCheck Tally/ODBC.", fg=ERROR_COLOR)
            self.status_label.pack(pady=20) # Ensure visible
            if hasattr(self, 'grid_frame') and self.grid_frame.winfo_ismapped(): self.grid_frame.pack_forget() # Hide grid
        else:
            logger.info("License info fetched successfully. Updating UI.")
            self.status_label.pack_forget() # Hide status label
            if hasattr(self, 'grid_frame') and not self.grid_frame.winfo_ismapped():
                 # Pack grid frame inside data_container if not already visible
                 self.grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # --- Update StringVars with fetched data ---
            for key, var in self.license_data_vars.items():
                value = license_info.get(key) # Get value using the dict key

                # Format the value for display
                display_value = "N/A" # Default for None
                if key == "is_indian" or key == "is_licensed" or key == "odbc_enabled" or key == "is_silver" or key == "is_gold":
                    # Handle Booleans explicitly
                    display_value = "Yes" if value else "No"
                elif key == "license_type":
                    # Derive license type from is_silver/is_gold
                    is_silver = license_info.get("is_silver") # Should be bool or None
                    is_gold = license_info.get("is_gold")
                    if is_gold: display_value = "Gold"
                    elif is_silver: display_value = "Silver"
                    else: display_value = "Unknown/Edu/Other" # Handle other cases
                elif value is not None:
                    # Convert other non-None values to string for display
                    display_value = str(value)

                # Set the StringVar, which updates the Entry widget
                var.set(display_value)
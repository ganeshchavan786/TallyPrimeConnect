# TallyPrimeConnect/ui/add_company.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import queue # Keep for potential future use

# --- Import necessary helpers AND DEFAULTS ---
from utils.helpers import load_settings, get_tally_companies, DEFAULT_SETTINGS
from utils.database import add_company_to_db, get_added_companies

logger = logging.getLogger(__name__)

# --- UI Constants ---
PANEL_BG="#ffffff"; LIST_AREA_BG="#f8f8f8"; TITLE_FONT=("Arial", 16, "bold"); LABEL_FONT=("Arial", 10); LIST_TITLE_FONT=("Arial", 9, "bold"); RADIO_FONT=("Arial", 10); ADD_BTN_BG="#e74c3c"; ADD_BTN_FG="#ffffff"; ADD_BTN_ACTIVE_BG="#c0392b"; ERROR_COLOR="red"; INFO_COLOR="black"; MUTED_COLOR="gray"

class AddCompanyPanel(tk.Frame):
    """Panel to display available Tally companies and add them to local DB."""
    def __init__(self, parent, *args, **kwargs):
        """Initializes the Add Company panel."""
        super().__init__(parent, bg=PANEL_BG, *args, **kwargs)
        self.selected_company_var = tk.StringVar(value=None)
        self.company_data_cache = {} # Cache of *available* companies {name: {'name':.., 'number':..}}
        self.is_loading = False # Prevent multiple concurrent loads
        self._create_widgets()
        logger.debug("AddCompanyPanel initialized.")

    def _create_widgets(self):
        """Creates the static widgets for the panel."""
        logger.debug("Creating AddCompanyPanel widgets.")
        tk.Label(self, text="Add Company", font=TITLE_FONT, bg=PANEL_BG, anchor="w").pack(pady=(10, 10), padx=30, anchor="w")
        self.list_container = tk.Frame(self, bg=LIST_AREA_BG); self.list_container.pack(pady=10, padx=50, fill=tk.BOTH, expand=True)
        self.status_label = tk.Label(self.list_container, text="Initializing...", font=LABEL_FONT, bg=LIST_AREA_BG, fg=MUTED_COLOR, justify=tk.LEFT); self.status_label.pack(pady=20, padx=20)
        self.radio_frame = tk.Frame(self.list_container, bg=LIST_AREA_BG); self.radio_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        self.add_button = tk.Button(self.list_container, text="+ ADD", command=self._add_selected_company_action, bg=ADD_BTN_BG, fg=ADD_BTN_FG, font=("Arial", 10, "bold"), relief=tk.FLAT, padx=30, pady=8, cursor="hand2", activebackground=ADD_BTN_ACTIVE_BG, state=tk.DISABLED); self.add_button.pack(pady=(10, 20))

    def load_companies(self):
        """Starts the background process to fetch/filter/display available companies."""
        if self.is_loading:
            logger.warning("Already loading companies, request ignored.")
            return
        logger.info("Load companies requested for Add Company panel.")
        self.is_loading = True
        self._update_ui_for_loading() # Show loading state immediately
        # Run fetch/filter in background thread
        thread = threading.Thread(target=self._fetch_and_filter_companies, daemon=True)
        thread.start()

    def _update_ui_for_loading(self):
        """Updates UI elements to show loading state."""
        logger.debug("Updating AddCompany UI for loading state.")
        try:
            # Clear previous radio buttons safely
            if hasattr(self, 'radio_frame') and self.radio_frame.winfo_exists():
                for widget in self.radio_frame.winfo_children(): widget.destroy()
            # Reset selection and cache
            self.selected_company_var.set(None)
            self.company_data_cache = {}
            # Show status label, hide radio frame
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.pack(pady=20, padx=20) # Ensure visible
                self.status_label.config(text="Fetching available companies from Tally...", fg=MUTED_COLOR)
            if hasattr(self, 'radio_frame') and self.radio_frame.winfo_ismapped():
                 self.radio_frame.pack_forget()
            # Disable Add button
            if hasattr(self, 'add_button') and self.add_button.winfo_exists():
                 self.add_button.config(state=tk.DISABLED)
            # Update UI immediately
            if self.winfo_exists(): self.update_idletasks()
        except tk.TclError: logger.warning("Error updating UI loading state (widget destroyed?).")
        except Exception as e: logger.exception(f"Unexpected error in _update_ui_for_loading: {e}")


    def _fetch_and_filter_companies(self):
        """Worker function (run in thread) to fetch Tally & DB lists and find available ones."""
        logger.debug("Starting background fetch/filter for available companies.")
        available_companies = []; error_message = None
        try:
            # 1. Get already added companies from local DB
            added_companies_list = get_added_companies()
            # Create a set of numbers (as strings) for efficient lookup
            added_numbers = {str(comp.get('tally_company_number')) for comp in added_companies_list if comp.get('tally_company_number')}
            logger.debug(f"Found {len(added_numbers)} locally added company numbers: {added_numbers}")

            # 2. Get all companies currently available in Tally via HTTP XML
            settings = load_settings()
            host = settings.get("tally_host", DEFAULT_SETTINGS["tally_host"])
            port = settings.get("tally_port", DEFAULT_SETTINGS["tally_port"])
            tally_companies = get_tally_companies(host, port) # Uses helpers.py

            if tally_companies is None:
                error_message = f"Error fetching list from Tally ({host}:{port}).\nCheck connection & Tally status."
            elif not tally_companies:
                 error_message = "No companies found in Tally response."; logger.info("get_tally_companies returned empty list.")
            else:
                # 3. Filter Tally list against added list
                # Ensure comparison uses string format for numbers
                available_companies = [comp for comp in tally_companies if str(comp.get('number')) not in added_numbers]
                logger.info(f"Found {len(available_companies)} companies available to add.")
                if not available_companies:
                     error_message = "All companies found in Tally are already added."

        except Exception as e:
            logger.exception("Error during company fetch/filter process.")
            error_message = f"An unexpected error occurred:\n{e}"
        finally:
            self.is_loading = False # Reset loading flag regardless of outcome

        # Schedule UI update back in the main thread safely
        try:
             if hasattr(self, 'winfo_exists') and self.winfo_exists():
                 # Pass results to the UI update method
                 self.after(0, self._update_company_list_ui, available_companies, error_message)
        except tk.TclError: logger.warning("AddCompanyPanel destroyed before UI update schedule.")


    def _update_company_list_ui(self, available_companies: list, error_message: str | None):
        """Updates the UI (radio buttons or status message) in the main thread."""
        logger.debug(f"Updating Add Company UI. Available: {len(available_companies)}, Error: {error_message}")
        try:
             # Ensure widgets needed for update exist
             if not (hasattr(self, 'radio_frame') and self.radio_frame.winfo_exists() and \
                     hasattr(self, 'status_label') and self.status_label.winfo_exists() and \
                     hasattr(self, 'add_button') and self.add_button.winfo_exists()):
                 logger.error("UI widgets missing during _update_company_list_ui.")
                 return

             # Clear previous radio buttons
             for widget in self.radio_frame.winfo_children(): widget.destroy()

             if error_message:
                 # Show error or info message
                 is_info = "All companies" in error_message or "No companies found" in error_message
                 self.status_label.config(text=error_message, fg=INFO_COLOR if is_info else ERROR_COLOR);
                 self.status_label.pack(pady=20, padx=20); self.radio_frame.pack_forget(); self.add_button.config(state=tk.DISABLED)
             elif available_companies:
                 # Populate list
                 self.status_label.pack_forget(); self.radio_frame.pack(fill=tk.X, padx=20, pady=(0, 10));
                 # Update cache ONLY with currently available companies
                 self.company_data_cache = {comp['name']: comp for comp in available_companies}
                 tk.Label(self.radio_frame, text="AVAILABLE TALLY COMPANIES", font=LIST_TITLE_FONT, bg=LIST_AREA_BG, anchor='w').pack(fill=tk.X, pady=(5,5))
                 for company in available_companies:
                     name = company['name']; tk.Radiobutton(self.radio_frame, text=f" {name}", variable=self.selected_company_var, value=name, anchor='w', bg=LIST_AREA_BG, activebackground=LIST_AREA_BG, selectcolor=LIST_AREA_BG, font=RADIO_FONT).pack(fill=tk.X, pady=2)
                 self.add_button.config(state=tk.NORMAL) # Enable add button
             else:
                  # This case means fetch was successful, no errors, but list is empty AFTER filtering
                  self.status_label.config(text="No new companies available from Tally.", fg=INFO_COLOR); self.status_label.pack(pady=20, padx=20); self.radio_frame.pack_forget(); self.add_button.config(state=tk.DISABLED)

        except tk.TclError: logger.warning("Error updating add company UI (widget destroyed?).")
        except Exception as e: logger.exception("Unexpected error updating add company UI.")


    def _add_selected_company_action(self):
        """Adds selected company to the DB and refreshes this panel's list."""
        selected_name = self.selected_company_var.get();
        if not selected_name or selected_name == 'None':
            messagebox.showwarning("No Selection", "Please select a company from the list first."); return

        # Get data from the cache populated by load_companies
        selected_data = self.company_data_cache.get(selected_name)
        if not selected_data or not selected_data.get('number'):
             logger.error(f"Data cache missing for selected company: {selected_name}")
             messagebox.showerror("Internal Error", f"Could not find data for '{selected_name}'. Please refresh the list."); return

        num = selected_data['number']; logger.info(f"Attempting to add company: {selected_name} ({num})")

        # Disable button during DB operation safely
        try:
             if hasattr(self, 'add_button') and self.add_button.winfo_exists():
                 self.add_button.config(state=tk.DISABLED)
             if self.winfo_exists(): self.update_idletasks()
        except tk.TclError: logger.warning("Error disabling add button during add action.")

        try:
            was_added = add_company_to_db(selected_name, num) # Call DB function
            if was_added:
                 messagebox.showinfo("Success", f"Company '{selected_name}' added successfully.")
                 # Refresh the list immediately to remove the added company
                 self.load_companies()
            else:
                 # This means company already existed (active or inactive but DB func handled it) or DB error occurred
                 # add_company_to_db logs specifics
                 messagebox.showinfo("Already Exists / Error", f"Company '{selected_name}' may already be in your list or could not be added (check logs).")
                 # Refresh anyway, as state might have changed (reactivation) or Tally list might differ
                 self.load_companies()
        except Exception as e:
            logger.exception(f"Unexpected error occurred while adding company {selected_name} to DB.")
            messagebox.showerror("Database Error", f"Failed to add company:\n{e}")
            # Re-enable button only if list wasn't refreshed due to error
            # load_companies() above handles re-enabling if successful
            try:
                 if hasattr(self, 'add_button') and self.add_button.winfo_exists():
                      # Re-enable only if there might still be items to add
                      if self.company_data_cache: self.add_button.config(state=tk.NORMAL)
                      else: self.add_button.config(state=tk.DISABLED)
            except tk.TclError: pass
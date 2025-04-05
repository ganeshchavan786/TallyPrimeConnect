# TallyPrimeConnect/ui/add_company.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import queue # Keep queue import if needed for future async ops in this panel

# --- Import necessary helpers ---
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
        self.selected_company_var = tk.StringVar(value=None) # Holds name of selected radio button
        self.company_data_cache = {} # Cache of *available* Tally companies {name: {'name':.., 'number':..}}
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
        """Starts the process to fetch and display available Tally companies."""
        logger.info("Load companies requested for Add Company panel.")
        self._update_ui_for_loading() # Show loading state
        # Run the blocking network/DB operations in a separate thread
        thread = threading.Thread(target=self._fetch_and_filter_companies, daemon=True)
        thread.start()

    def _update_ui_for_loading(self):
        """Updates UI elements to show loading state."""
        try:
            if hasattr(self, 'radio_frame') and self.radio_frame.winfo_exists(): [w.destroy() for w in self.radio_frame.winfo_children()]
            self.selected_company_var.set(None); self.company_data_cache = {}
            if hasattr(self, 'status_label') and self.status_label.winfo_exists(): self.status_label.pack(pady=20, padx=20); self.status_label.config(text="Fetching available companies...", fg=MUTED_COLOR)
            if hasattr(self, 'radio_frame') and self.radio_frame.winfo_ismapped(): self.radio_frame.pack_forget()
            if hasattr(self, 'add_button') and self.add_button.winfo_exists(): self.add_button.config(state=tk.DISABLED)
            if self.winfo_exists(): self.update_idletasks()
        except tk.TclError: logger.warning("Error updating UI loading state (widget destroyed?).")

    def _fetch_and_filter_companies(self):
        """Worker function (run in thread) to fetch Tally & DB lists and find available ones."""
        logger.debug("Starting background fetch for available companies.")
        available_companies = []; error_message = None
        try:
            added_companies_list = get_added_companies()
            added_numbers = {comp.get('tally_company_number') for comp in added_companies_list if comp.get('tally_company_number')}
            logger.debug(f"Found {len(added_numbers)} locally added company numbers.")

            settings = load_settings()
            host = settings.get("tally_host", DEFAULT_SETTINGS["tally_host"])
            port = settings.get("tally_port", DEFAULT_SETTINGS["tally_port"])
            tally_companies = get_tally_companies(host, port) # This uses HTTP XML

            if tally_companies is None: error_message = f"Error fetching from Tally at {host}:{port}.\nCheck connection and Tally."
            elif not tally_companies: error_message = "No companies found in Tally\n(or none could be parsed)."; logger.info("get_tally_companies returned empty list.")
            else:
                available_companies = [comp for comp in tally_companies if comp.get('number') not in added_numbers]
                logger.info(f"Found {len(available_companies)} companies available to add.")
                if not available_companies: error_message = "All companies from Tally are already added."
        except Exception as e: logger.exception("Error during fetch/filter process."); error_message = f"An unexpected error occurred:\n{e}"

        # Schedule UI update back in the main thread safely
        try:
             if hasattr(self, 'winfo_exists') and self.winfo_exists():
                 # Pass results to the UI update method
                 self.after(0, self._update_company_list_ui, available_companies, error_message)
        except tk.TclError: logger.warning("AddCompanyPanel destroyed before UI update could be scheduled.")


    def _update_company_list_ui(self, available_companies: list, error_message: str | None):
        """Updates the UI (radio buttons or status message) in the main thread."""
        logger.debug(f"Updating Add Company UI. Available: {len(available_companies)}, Error: {error_message}")
        try:
             # Ensure widgets needed for update exist
             if not hasattr(self, 'radio_frame') or not self.radio_frame.winfo_exists() or \
                not hasattr(self, 'status_label') or not self.status_label.winfo_exists() or \
                not hasattr(self, 'add_button') or not self.add_button.winfo_exists():
                 logger.error("UI widgets missing during update in AddCompanyPanel.")
                 return

             # Clear previous radio buttons first
             for widget in self.radio_frame.winfo_children(): widget.destroy()

             if error_message: # Display error or info message
                 self.status_label.config(text=error_message, fg=INFO_COLOR if "All companies" in error_message else ERROR_COLOR); self.status_label.pack(pady=20, padx=20); self.radio_frame.pack_forget(); self.add_button.config(state=tk.DISABLED)
             elif available_companies: # Display available companies
                 self.status_label.pack_forget(); self.radio_frame.pack(fill=tk.X, padx=20, pady=(0, 10)); self.company_data_cache = {c['name']: c for c in available_companies}
                 tk.Label(self.radio_frame, text="AVAILABLE TALLY COMPANIES", font=LIST_TITLE_FONT, bg=LIST_AREA_BG, anchor='w').pack(fill=tk.X, pady=(5,5))
                 for company in available_companies: name = company['name']; tk.Radiobutton(self.radio_frame, text=f" {name}", variable=self.selected_company_var, value=name, anchor='w', bg=LIST_AREA_BG, activebackground=LIST_AREA_BG, selectcolor=LIST_AREA_BG, font=RADIO_FONT).pack(fill=tk.X, pady=2)
                 self.add_button.config(state=tk.NORMAL) # Enable button only if there are companies
             else: # No available companies, but no specific error from fetch
                  self.status_label.config(text="No new companies available to add.", fg=INFO_COLOR); self.status_label.pack(pady=20, padx=20); self.radio_frame.pack_forget(); self.add_button.config(state=tk.DISABLED)

        except tk.TclError: logger.warning("Error updating add company UI (widget likely destroyed).")
        except Exception as e: logger.exception("Unexpected error updating add company UI.")


    def _add_selected_company_action(self):
        """Adds selected company to the DB and refreshes this panel's list."""
        selected_name = self.selected_company_var.get();
        if not selected_name or selected_name == 'None': messagebox.showwarning("No Selection", "Please select a company from the list first."); return

        selected_data = self.company_data_cache.get(selected_name)
        if not selected_data or not selected_data.get('number'): messagebox.showerror("Error", f"Internal data error for '{selected_name}'. Please refresh."); return

        num = selected_data['number']; logger.info(f"Adding company: {selected_name} ({num})")

        # Disable button during operation safely
        try:
             if hasattr(self, 'add_button') and self.add_button.winfo_exists():
                 self.add_button.config(state=tk.DISABLED)
             if self.winfo_exists(): self.update_idletasks()
        except tk.TclError: logger.warning("Error disabling add button.")

        # --- Corrected try...except block ---
        try:
            was_added = add_company_to_db(selected_name, num) # Call DB function
            if was_added:
                messagebox.showinfo("Success", f"Company '{selected_name}' added successfully.")
            else:
                # This means company already existed (or DB error occurred - logged by add_company_to_db)
                messagebox.showinfo("Already Added", f"Company '{selected_name}' was already present in your list.")

            # Always refresh the list after attempting an add
            self.load_companies()

        except Exception as e:
            # Catch any unexpected error during the DB add process
            logger.exception(f"Unexpected error occurred while adding company {selected_name} to DB.")
            messagebox.showerror("Database Error", f"Failed to add company:\n{e}")
            # Re-enable button only if refresh didn't happen due to error
            # (load_companies above will handle enabling if successful)
            try:
                 if hasattr(self, 'add_button') and self.add_button.winfo_exists():
                     # Check if there are still companies in cache to decide state
                     if self.company_data_cache: self.add_button.config(state=tk.NORMAL)
                     else: self.add_button.config(state=tk.DISABLED)
            except tk.TclError: pass # Ignore if button destroyed
        # --- End of corrected block ---
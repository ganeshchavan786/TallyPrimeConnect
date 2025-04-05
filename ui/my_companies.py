# TallyPrimeConnect/ui/my_companies.py
import tkinter as tk
from tkinter import ttk, font, messagebox
import logging
import threading
import queue
import time # Optional for delay

# --- Local Imports ---
# Database functions
from utils.database import (
    get_added_companies, get_company_details, edit_company_in_db,
    soft_delete_company, update_company_details, update_company_sync_status,
    log_change
)
# --- Use ODBC HELPER FOR FETCHING DETAILS ---
from utils.odbc_helper import fetch_company_details_odbc
# --- Load Settings might be needed if using DSN-less ODBC connection ---
# from utils.helpers import load_settings # Uncomment if odbc_helper needs it

# --- Setup Logger ---
logger = logging.getLogger(__name__)

# --- UI Constants ---
PANEL_BG = "#ffffff"
LIST_AREA_BG = "#f8f8f8"
TITLE_FONT = ("Arial", 16, "bold")
LABEL_FONT = ("Arial", 10)
COMPANY_NAME_FONT = ("Arial", 10, "bold")
COMPANY_NUM_FONT = ("Arial", 9)
BUTTON_FONT = ("Arial", 9)

# Colors
ERROR_COLOR = "red"
INFO_COLOR = "black"
MUTED_COLOR = "gray"
WARN_POPUP_BG = "#f8d7da" # Light red background for delete confirmation
WARN_POPUP_FG = "#721c24" # Dark red text for delete confirmation
SYNCED_COLOR = "#28a745" # Green dot for Synced status
NOT_SYNCED_COLOR = "#6c757d" # Gray dot for Not Synced status
FAILED_COLOR = "#dc3545" # Red dot for Sync Failed status

class MyCompaniesPanel(tk.Frame):
    """
    Panel to display and manage companies added to the local database.
    Includes functionality to sync detailed company data via ODBC (per company).
    Handles Edit and Soft Delete operations via modal popups.
    Uses threading for non-blocking sync operations.
    """
    def __init__(self, parent, status_bar_ref=None, *args, **kwargs):
        """
        Initialize the MyCompaniesPanel.

        Args:
            parent: The parent tkinter widget.
            status_bar_ref: A reference to the main application's status bar object.
        """
        super().__init__(parent, bg=PANEL_BG, *args, **kwargs)
        self.status_bar = status_bar_ref
        self.sync_queue = queue.Queue()
        self.is_syncing = False # Prevents multiple simultaneous syncs
        self._create_widgets()
        self._schedule_queue_check() # Start the loop to check for messages
        logger.debug("MyCompaniesPanel initialized (using Per-Company ODBC sync).")

    def _schedule_queue_check(self):
        """Safely schedules the next check of the sync queue using 'after'."""
        try:
            if self.winfo_exists(): self.after(100, self._process_sync_queue)
        except tk.TclError: logger.info("MyCompaniesPanel destroyed, stopping queue check.")

    def _create_widgets(self):
        """Creates the static widgets for the panel layout (title, list area)."""
        logger.debug("Creating widgets for MyCompaniesPanel")
        header_frame = tk.Frame(self, bg=PANEL_BG); header_frame.pack(fill=tk.X, padx=30, pady=(10, 0))
        tk.Label(header_frame, text="My Companies", font=TITLE_FONT, bg=PANEL_BG, anchor="w").pack(side=tk.LEFT)
        self.list_container = tk.Frame(self, bg=LIST_AREA_BG); self.list_container.pack(pady=10, padx=50, fill=tk.BOTH, expand=True)
        self.status_label = tk.Label(self.list_container, text="Initializing...", font=LABEL_FONT, bg=LIST_AREA_BG, fg=MUTED_COLOR); self.status_label.pack(pady=20, padx=20)
        self.companies_frame = tk.Frame(self.list_container, bg=LIST_AREA_BG); self.companies_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    def refresh_list(self):
        """Fetches the list of active companies from the database and updates the UI display."""
        logger.info("Refreshing My Companies list")
        if hasattr(self, 'companies_frame') and self.companies_frame.winfo_exists(): [w.destroy() for w in self.companies_frame.winfo_children()]
        else: logger.error("Cannot refresh: Companies frame missing."); return
        if hasattr(self, 'status_label') and self.status_label.winfo_exists(): self.status_label.pack(pady=20, padx=20); self.status_label.config(text="Loading...", fg=MUTED_COLOR); self.update_idletasks()
        else: logger.warning("Status label unavailable.")
        try: added_companies = get_added_companies()
        except Exception as e: logger.exception("Error fetching companies DB."); self._show_load_error(e); return
        if not added_companies:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists(): self.status_label.config(text="No active companies found.", fg=INFO_COLOR)
            logger.info("No active companies found.")
        else:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists(): self.status_label.pack_forget()
            self._display_companies(added_companies)

    def _show_load_error(self, error):
        """Helper method to display loading errors consistently."""
        if hasattr(self, 'status_label') and self.status_label.winfo_exists(): self.status_label.config(text="Error loading.", fg=ERROR_COLOR)
        messagebox.showerror("Database Error", f"Failed load: {error}")

    def _display_companies(self, company_list: list[dict]):
        """Populates companies_frame with rows."""
        logger.info(f"Displaying {len(company_list)} companies.")
        if not hasattr(self, 'companies_frame') or not self.companies_frame.winfo_exists(): logger.error("Companies frame missing."); return
        for company in company_list:
            num = company.get('tally_company_number'); name = company.get('tally_company_name', 'N/A'); status = company.get('sync_status', 'Not Synced')
            frame = tk.Frame(self.companies_frame, bg=self.companies_frame['bg']); frame.pack(fill=tk.X, pady=3)
            info = tk.Frame(frame, bg=frame['bg']); info.pack(side=tk.LEFT, fill=tk.X, expand=True)
            color = NOT_SYNCED_COLOR;
            if status == 'Synced': color = SYNCED_COLOR
            elif status == 'Sync Failed': color = FAILED_COLOR
            tk.Label(info, text="●", font=("Arial", 12), fg=color, bg=frame['bg']).pack(side=tk.LEFT, padx=(0, 5))
            tk.Label(info, text=name, font=COMPANY_NAME_FONT, bg=frame['bg'], anchor='w').pack(side=tk.LEFT, padx=(0, 10))
            tk.Label(info, text=f"(No: {num or 'N/A'})", font=COMPANY_NUM_FONT, fg=MUTED_COLOR, bg=frame['bg'], anchor='w').pack(side=tk.LEFT)
            actions = tk.Frame(frame, bg=frame['bg']); actions.pack(side=tk.RIGHT)
            tk.Button(actions, text="Sync", font=BUTTON_FONT, width=6, relief=tk.GROOVE, command=lambda n=num, nm=name: self._start_single_company_sync(n, nm)).pack(side=tk.LEFT, padx=(0, 5))
            tk.Button(actions, text="Edit", font=BUTTON_FONT, width=6, relief=tk.GROOVE, command=lambda n=num: self._open_edit_popup(n)).pack(side=tk.LEFT, padx=(0, 5))
            tk.Button(actions, text="Delete", font=BUTTON_FONT, width=6, relief=tk.GROOVE, fg=ERROR_COLOR, command=lambda n=num, nm=name: self._open_delete_popup(n, nm)).pack(side=tk.LEFT)

    # --- Edit Popup Logic ---
    def _open_edit_popup(self, company_number: str):
        if not company_number: logger.warning("Edit attempt no number."); messagebox.showwarning("Error", "Cannot edit."); return
        logger.info(f"Opening edit for {company_number}"); details = None
        try: details = get_company_details(company_number)
        except Exception as e: logger.exception(f"Failed get details {company_number}."); messagebox.showerror("DB Error", f"Could not fetch: {e}"); return
        if not details: logger.error(f"{company_number} not found/inactive."); messagebox.showerror("Error", f"Company {company_number} not found/inactive."); return
        try:
            popup = tk.Toplevel(self); popup.title("Edit Details"); popup.geometry("450x300"); popup.resizable(False, False); popup.configure(bg=PANEL_BG); popup.transient(self.winfo_toplevel()); popup.grab_set();
            self._create_edit_popup_widgets(popup, details);
            self.root = self.winfo_toplevel(); popup.update_idletasks(); w=popup.winfo_width(); h=popup.winfo_height(); sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight(); x=(sw//2)-(w//2); y=(sh//2)-(h//2); popup.geometry(f"{w}x{h}+{x}+{y}")
            self.winfo_toplevel().wait_window(popup); logger.debug(f"Edit popup closed {company_number}.")
        except Exception as e: logger.exception(f"Error creating edit popup: {e}"); messagebox.showerror("UI Error", f"Failed open edit: {e}");

    def _create_edit_popup_widgets(self, parent: tk.Toplevel, details: dict):
        content = tk.Frame(parent, bg=PANEL_BG, padx=20, pady=15); content.pack(fill=tk.BOTH, expand=True); tk.Label(content, text="Company Name*", font=LABEL_FONT, bg=PANEL_BG, anchor='w').pack(fill=tk.X); name_var = tk.StringVar(value=details.get('tally_company_name', '')); name_entry = ttk.Entry(content, textvariable=name_var, font=LABEL_FONT); name_entry.pack(fill=tk.X, pady=(2, 10)); name_entry.focus_set(); tk.Label(content, text="Description", font=LABEL_FONT, bg=PANEL_BG, anchor='w').pack(fill=tk.X); desc_entry = tk.Text(content, height=4, font=LABEL_FONT, relief=tk.SOLID, bd=1, wrap=tk.WORD); desc_entry.insert("1.0", details.get('description', '')); desc_entry.pack(fill=tk.X, pady=(2, 10)); sync_var = tk.IntVar(value=1); tk.Checkbutton(content, text="Sync Data", variable=sync_var, bg=PANEL_BG, activebackground=PANEL_BG, font=LABEL_FONT, anchor='w').pack(fill=tk.X, pady=(5, 15)); ttk.Separator(content, orient='horizontal').pack(fill='x', pady=(5, 15)); button_frame = tk.Frame(content, bg=PANEL_BG); button_frame.pack(fill=tk.X, side=tk.BOTTOM); save_btn = tk.Button(button_frame, text="SAVE", width=12, bg="#007bff", fg="white", relief=tk.FLAT, font=(LABEL_FONT[0], 10, "bold"), command=lambda: self._save_edit(details.get('tally_company_number'), name_var, desc_entry, parent)); save_btn.pack(side=tk.LEFT); cancel_btn = tk.Button(button_frame, text="CANCEL", width=12, relief=tk.GROOVE, font=(LABEL_FONT[0], 10), command=parent.destroy); cancel_btn.pack(side=tk.RIGHT)

    def _save_edit(self, company_number: str, name_var: tk.StringVar, desc_widget: tk.Text, popup: tk.Toplevel):
        """Handles the save action triggered from the edit popup."""
        new_name = name_var.get().strip(); new_description = desc_widget.get("1.0", tk.END).strip();
        if not new_name: messagebox.showerror("Input Error", "Name cannot be empty.", parent=popup); return
        logger.info(f"Saving edits for {company_number}")
        try:
            success = edit_company_in_db(company_number, new_name, new_description)
            if success:
                 logger.info(f"Updated {company_number}."); messagebox.showinfo("Success", "Details updated.", parent=popup); popup.destroy(); self.refresh_list()
            else:
                 logger.warning(f"Failed update {company_number}."); messagebox.showwarning("Update Failed", "Could not update.\n(Name exists or inactive?)", parent=popup)
        except Exception as e:
             logger.exception(f"Unexpected error saving edit: {e}")
             messagebox.showerror("Error", f"An unexpected error occurred while saving:\n{e}", parent=popup)

    # --- Delete Popup Logic ---
    def _open_delete_popup(self, company_number: str, company_name: str):
        if not company_number: logger.warning("Delete attempt no number."); return
        logger.info(f"Opening delete confirm {company_number} ('{company_name}')")
        try:
            popup = tk.Toplevel(self); popup.title("Confirm Delete"); popup.geometry("450x220"); popup.resizable(False, False); popup.configure(bg=WARN_POPUP_BG); popup.transient(self.winfo_toplevel()); popup.grab_set();
            self._create_delete_popup_widgets(popup, company_number, company_name);
            self.root = self.winfo_toplevel(); popup.update_idletasks(); w=popup.winfo_width(); h=popup.winfo_height(); sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight(); x=(sw//2)-(w//2); y=(sh//2)-(h//2); popup.geometry(f"{w}x{h}+{x}+{y}")
            self.winfo_toplevel().wait_window(popup); logger.debug("Delete confirm closed.")
        except Exception as e: logger.exception(f"Error creating delete popup: {e}"); messagebox.showerror("UI Error", f"Failed open delete confirm: {e}");

    def _create_delete_popup_widgets(self, parent: tk.Toplevel, company_number: str, company_name: str):
        content = tk.Frame(parent, bg=parent['bg'], padx=20, pady=15); content.pack(fill=tk.BOTH, expand=True); tk.Label(content, text="This action will hide company", font=LABEL_FONT, fg=WARN_POPUP_FG, bg=parent['bg'], justify=tk.CENTER).pack(pady=(5, 0)); tk.Label(content, text=f"'{company_name}' (Number: {company_number})", font=LABEL_FONT, fg=WARN_POPUP_FG, bg=parent['bg'], justify=tk.CENTER).pack(pady=(0, 0)); tk.Label(content, text="from Biz Analyst.", font=LABEL_FONT, fg=WARN_POPUP_FG, bg=parent['bg'], justify=tk.CENTER).pack(pady=(0, 10)); tk.Label(content, text="It WILL NOT affect data in Tally.", font=LABEL_FONT, fg=WARN_POPUP_FG, bg=parent['bg'], justify=tk.CENTER).pack(pady=(5, 10)); tk.Label(content, text="Confirm Delete?", font=LABEL_FONT, fg=WARN_POPUP_FG, bg=parent['bg'], justify=tk.CENTER).pack(pady=(5, 15)); button_frame = tk.Frame(content, bg=parent['bg']); button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0)); delete_confirm_btn = tk.Button(button_frame, text="DELETE COMPANY", width=15, bg="#dc3545", fg="white", relief=tk.FLAT, font=(LABEL_FONT[0], 10, "bold"), command=lambda: self._perform_soft_delete(company_number, parent)); delete_confirm_btn.pack(side=tk.RIGHT, padx=(10, 0)); cancel_btn = tk.Button(button_frame, text="CANCEL", width=12, relief=tk.GROOVE, font=(LABEL_FONT[0], 10), command=parent.destroy); cancel_btn.pack(side=tk.RIGHT)

    def _perform_soft_delete(self, company_number: str, popup: tk.Toplevel):
        """Handles the soft delete action after confirmation."""
        logger.info(f"Performing soft delete for {company_number}");
        try: # Close confirmation popup safely
            if popup and popup.winfo_exists(): popup.destroy()
        except tk.TclError: pass
        try:
            success = soft_delete_company(company_number)
            if success:
                 logger.info(f"Soft deleted {company_number}."); messagebox.showinfo("Success", "Company marked inactive."); self.refresh_list()
            else:
                 logger.warning(f"Soft delete fail {company_number}."); messagebox.showwarning("Delete Failed", "Could not mark inactive.\n(Already inactive/error).")
        except Exception as e:
             logger.exception(f"Unexpected error occurred during soft delete for {company_number}: {e}")
             messagebox.showerror("Error", f"An unexpected error occurred during deletion:\n{e}")

    # --- Asynchronous Syncing Logic (ODBC Per-Company) ---
    def _start_single_company_sync(self, company_number: str, company_name: str):
        """Initiates sync for a single company via ODBC after user confirmation."""
        if self.is_syncing: logger.warning("Sync busy."); messagebox.showwarning("Sync Busy", "Sync running."); return
        if not company_number or not company_name: logger.error("Cannot sync: Missing info."); return
        logger.info(f"Requesting confirm sync: {company_name} ({company_number})")
        msg = f"Ensure company:\n'{company_name}'\nis loaded in Tally Prime.\n\nClick OK to sync details."
        if messagebox.askokcancel("Confirm Tally Company", msg, icon='info'):
            logger.info(f"User confirmed. Starting ODBC sync for {company_number}")
            self.is_syncing = True; self._update_sync_ui_start(company_name)
            company_to_sync = {'tally_company_number': company_number, 'tally_company_name': company_name}
            sync_thread = threading.Thread(target=self._sync_worker_odbc, args=([company_to_sync],), daemon=True); sync_thread.start()
        else: logger.info(f"User cancelled sync for {company_number}.")

    def _update_sync_ui_start(self, company_name):
        """Safely updates UI elements when sync starts."""
        try:
            if self.status_bar and self.status_bar.winfo_exists() and hasattr(self.status_bar, 'update_sync_progress'):
                 self.status_bar.update_sync_progress(0, 1, f"Starting: {company_name}...")
        except tk.TclError: logger.warning("Error updating status bar at sync start.")
        # Add logic here to disable *all* Sync/Edit/Delete buttons globally if desired

    def _sync_worker_odbc(self, companies: list):
        """Background worker using ODBC fetch (processes list, usually 1 item)."""
        total_companies = len(companies); logger.info(f"ODBC Sync worker started for {total_companies} companies.")
        for i, company in enumerate(companies):
            num=company.get('tally_company_number'); name=company.get('tally_company_name');
            if not num or not name: logger.warning(f"Skipping in ODBC sync: {company}"); continue
            logger.info(f"Processing {i+1}/{total_companies}: {name} ({num})"); self.sync_queue.put({"type": "progress", "current": i + 1, "total": total_companies, "message": f"Syncing: {name}..."})
            try:
                logger.debug(f"Calling ODBC fetch. Ensure '{name}' loaded."); details = fetch_company_details_odbc(num); success = False
                if details:
                    fetched_name = details.get('tally_company_name')
                    if fetched_name and fetched_name.lower() != name.lower(): logger.error(f"ODBC Mismatch! Expected '{name}', got '{fetched_name}'."); update_company_sync_status(num, 'Sync Failed'); log_change(num, "SYNC_FAIL", f"Mismatch: Got '{fetched_name}'"); self.sync_queue.put({"type": "error", "message": f"Sync Failed: Wrong company ('{fetched_name}') active in Tally."})
                    else:
                        success = update_company_details(num, details);
                        # --- Corrected Indentation ---
                        if not success:
                             # Log failure only if DB update failed after fetch attempt
                             log_change(num, "SYNC_FAIL", "DB update failed after ODBC fetch")
                        # --- End Correction ---
                else:
                    logger.warning(f"ODBC fetch failed/no data for {num}."); update_company_sync_status(num, 'Sync Failed'); self.sync_queue.put({"type": "error", "message": f"Sync Failed: Could not fetch ODBC details.\n(Tally running? Company open?)"})
                logger.info(f"Sync result {num} (ODBC): {'Success' if success else 'Failed'}")
            except Exception as e:
                 logger.exception(f"Error syncing {name} via ODBC: {e}");
                 try: update_company_sync_status(num, 'Sync Failed'); log_change(num, "SYNC_FAIL", f"Error: {e}")
                 except Exception as ie: logger.error(f"Failed mark {num} failed: {ie}")
                 self.sync_queue.put({"type": "error", "message": f"Error syncing {name}:\n{e}"})
            # time.sleep(0.5) # Optional delay
        self.sync_queue.put({"type": "finished"}); logger.info("ODBC Sync worker finished.")

    # --- Queue Processing and UI Reset ---
    def _process_sync_queue(self):
        """Checks the queue for messages from the worker thread and updates the UI."""
        try:
            while True: # Process all available messages
                message = self.sync_queue.get_nowait(); msg_type = message.get("type")
                if msg_type == "error": logger.error(f"Error from sync worker: {message.get('message')}"); messagebox.showerror("Sync Error", message.get('message', 'Unknown sync error.')); continue
                status_bar_ok = self.status_bar and self.status_bar.winfo_exists() and hasattr(self.status_bar, 'update_sync_progress')
                if msg_type == "progress" and status_bar_ok: self.status_bar.update_sync_progress(message['current'], message['total'], message['message'])
                elif msg_type == "finished": logger.info("Sync finished message received."); messagebox.showinfo("Sync Complete", "Company detail sync finished."); self._sync_finished(); self.refresh_list();
                elif msg_type not in ["progress", "finished"]: logger.warning(f"Unknown queue message: {message}")
        except queue.Empty: pass
        except Exception as e: logger.exception(f"Error processing sync queue: {e}");
        finally: self._schedule_queue_check() # Always reschedule

    def _sync_finished(self):
        """Resets the UI elements related to syncing."""
        logger.debug("Resetting sync UI state."); self.is_syncing = False;
        try: # Safely update UI elements
             # No global sync button to reset in this version
            if self.status_bar and self.status_bar.winfo_exists() and hasattr(self.status_bar, 'clear_sync_progress'): self.status_bar.clear_sync_progress()
        except tk.TclError as e: logger.warning(f"Error resetting sync UI elements: {e}")
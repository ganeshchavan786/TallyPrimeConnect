# TallyPrimeConnect/ui/my_companies.py
import tkinter as tk
from tkinter import ttk, font, messagebox
import logging
import threading
import queue
import time # Optional for delay

# --- Local Imports ---
from utils.database import (
    get_added_companies, get_company_details, edit_company_in_db,
    soft_delete_company, update_company_details, update_company_sync_status,
    log_change
)
from utils.odbc_helper import fetch_company_details_odbc
# from utils.helpers import load_settings

logger = logging.getLogger(__name__)

# --- UI Constants ---
PANEL_BG = "#ffffff"; LIST_AREA_BG = "#f8f8f8"; TITLE_FONT = ("Arial", 16, "bold"); LABEL_FONT = ("Arial", 10); COMPANY_NAME_FONT = ("Arial", 10, "bold"); COMPANY_NUM_FONT = ("Arial", 9); BUTTON_FONT = ("Arial", 9)
ERROR_COLOR = "red"; INFO_COLOR = "black"; MUTED_COLOR = "gray"; WARN_POPUP_BG = "#f8d7da"; WARN_POPUP_FG = "#721c24"; SYNCED_COLOR = "#28a745"; NOT_SYNCED_COLOR = "#6c757d"; FAILED_COLOR = "#dc3545"

class MyCompaniesPanel(tk.Frame):
    """Displays/manages added companies, triggers sync via ODBC (per company)."""
    def __init__(self, parent, status_bar_ref=None, *args, **kwargs):
        super().__init__(parent, bg=PANEL_BG, *args, **kwargs)
        self.status_bar = status_bar_ref; self.sync_queue = queue.Queue(); self.is_syncing = False
        self._create_widgets(); self._schedule_queue_check(); logger.debug("MyCompaniesPanel initialized (ODBC).")

    def _schedule_queue_check(self):
        """Safely schedules next queue check."""
        try:
            if self.winfo_exists(): self.after(100, self._process_sync_queue)
        except tk.TclError: logger.info("MyCompaniesPanel destroyed, stopping queue checks.")

    def _create_widgets(self):
        """Creates static panel widgets."""
        logger.debug("Creating MyCompaniesPanel widgets."); header = tk.Frame(self, bg=PANEL_BG); header.pack(fill=tk.X, padx=30, pady=(10, 0))
        tk.Button(header, text="Sync All", font=BUTTON_FONT, bg="#007bff", fg="white", relief=tk.FLAT, command=self._start_all_companies_sync).pack(side=tk.RIGHT, padx=(0, 10))
        self.list_cont = tk.Frame(self, bg=LIST_AREA_BG); self.list_cont.pack(pady=10, padx=50, fill=tk.BOTH, expand=True)
        self.status_lbl = tk.Label(self.list_cont, text="Init...", font=LABEL_FONT, bg=LIST_AREA_BG, fg=MUTED_COLOR); self.status_lbl.pack(pady=20, padx=20)
        self.comp_frame = tk.Frame(self.list_cont, bg=LIST_AREA_BG); self.comp_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    def refresh_list(self):
        """Fetches active companies from DB and updates display."""
        logger.info("Refreshing My Companies list")
        if hasattr(self,'comp_frame') and self.comp_frame.winfo_exists(): [w.destroy() for w in self.comp_frame.winfo_children()]
        else: logger.error("Companies frame missing."); return
        if hasattr(self,'status_lbl') and self.status_lbl.winfo_exists(): self.status_lbl.pack(pady=20,padx=20); self.status_lbl.config(text="Loading...", fg=MUTED_COLOR); self.update_idletasks()
        else: logger.warning("Status label unavailable.")
        try: added = get_added_companies()
        except Exception as e: logger.exception("DB Error fetch."); self._show_load_error(e); return
        if not added:
            if hasattr(self,'status_lbl') and self.status_lbl.winfo_exists(): self.status_lbl.config(text="No active companies found.", fg=INFO_COLOR)
            logger.info("No active companies found.")
        else:
            if hasattr(self,'status_lbl') and self.status_lbl.winfo_exists(): self.status_lbl.pack_forget()
            self._display_companies(added)

    def _show_load_error(self, error):
        if hasattr(self,'status_lbl') and self.status_lbl.winfo_exists(): self.status_lbl.config(text="Error loading.", fg=ERROR_COLOR)
        messagebox.showerror("DB Error", f"Failed load: {error}")

    def _display_companies(self, company_list: list[dict]):
        logger.info(f"Displaying {len(company_list)} companies.")
        if not hasattr(self,'comp_frame') or not self.comp_frame.winfo_exists(): return
        for co in company_list:
            num=co.get('tally_company_number'); name=co.get('tally_company_name','N/A'); status=co.get('sync_status','Not Synced')
            frm=tk.Frame(self.comp_frame, bg=self.comp_frame['bg']); frm.pack(fill=tk.X, pady=3)
            inf=tk.Frame(frm, bg=frm['bg']); inf.pack(side=tk.LEFT, fill=tk.X, expand=True)
            clr=NOT_SYNCED_COLOR;
            if status=='Synced': clr=SYNCED_COLOR
            elif status=='Sync Failed': clr=FAILED_COLOR
            tk.Label(inf, text="●", font=("Arial", 12), fg=clr, bg=frm['bg']).pack(side=tk.LEFT, padx=(0, 5))
            tk.Label(inf, text=name, font=COMPANY_NAME_FONT, bg=frm['bg'], anchor='w').pack(side=tk.LEFT, padx=(0, 10))
            tk.Label(inf, text=f"(No: {num or 'N/A'})", font=COMPANY_NUM_FONT, fg=MUTED_COLOR, bg=frm['bg'], anchor='w').pack(side=tk.LEFT)
            act=tk.Frame(frm, bg=frm['bg']); act.pack(side=tk.RIGHT)
            tk.Button(act, text="Sync", font=BUTTON_FONT, width=6, relief=tk.GROOVE, command=lambda n=num, nm=name: self._start_single_company_sync(n, nm)).pack(side=tk.LEFT, padx=(0, 5))
            tk.Button(act, text="Edit", font=BUTTON_FONT, width=6, relief=tk.GROOVE, command=lambda n=num: self._open_edit_popup(n)).pack(side=tk.LEFT, padx=(0, 5))
            tk.Button(act, text="Delete", font=BUTTON_FONT, width=6, relief=tk.GROOVE, fg=ERROR_COLOR, command=lambda n=num, nm=name: self._open_delete_popup(n, nm)).pack(side=tk.LEFT)

    # --- Edit Popup Logic ---
    def _open_edit_popup(self, company_number: str):
        if not company_number: logger.warning("Edit no number."); messagebox.showwarning("Error", "Cannot edit."); return
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
        new_name = name_var.get().strip(); new_desc = desc_widget.get("1.0", tk.END).strip();
        if not new_name: messagebox.showerror("Input Error", "Name empty.", parent=popup); return
        logger.info(f"Saving edits for {company_number}")
        try:
            success = edit_company_in_db(company_number, new_name, new_desc);
            if success: logger.info(f"Updated {company_number}."); messagebox.showinfo("Success", "Details updated.", parent=popup); popup.destroy(); self.refresh_list()
            else: logger.warning(f"Failed update {company_number}."); messagebox.showwarning("Update Failed", "Could not update.\n(Name exists/inactive?)", parent=popup)
        except Exception as e: logger.exception(f"Error saving edit: {e}"); messagebox.showerror("Error", f"Error: {e}", parent=popup)

    # --- Delete Popup Logic ---
    def _open_delete_popup(self, company_number: str, company_name: str):
        if not company_number: logger.warning("Delete no number."); return
        logger.info(f"Opening delete confirm {company_number} ('{company_name}')")
        try:
            popup = tk.Toplevel(self); popup.title("Confirm Delete"); popup.geometry("450x220"); popup.resizable(False, False); popup.configure(bg=WARN_POPUP_BG); popup.transient(self.winfo_toplevel()); popup.grab_set();
            self._create_delete_popup_widgets(popup, company_number, company_name);
            self.root = self.winfo_toplevel(); popup.update_idletasks(); w=popup.winfo_width(); h=popup.winfo_height(); sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight(); x=(sw//2)-(w//2); y=(sh//2)-(h//2); popup.geometry(f"{w}x{h}+{x}+{y}")
            self.winfo_toplevel().wait_window(popup); logger.debug("Delete confirm closed.")
        except Exception as e: logger.exception(f"Error creating delete popup: {e}"); messagebox.showerror("UI Error", f"Failed open delete: {e}");

    def _create_delete_popup_widgets(self, parent: tk.Toplevel, company_number: str, company_name: str):
        content = tk.Frame(parent, bg=parent['bg'], padx=20, pady=15); content.pack(fill=tk.BOTH, expand=True); tk.Label(content, text="This action will hide company", font=LABEL_FONT, fg=WARN_POPUP_FG, bg=parent['bg'], justify=tk.CENTER).pack(pady=(5, 0)); tk.Label(content, text=f"'{company_name}' (Number: {company_number})", font=LABEL_FONT, fg=WARN_POPUP_FG, bg=parent['bg'], justify=tk.CENTER).pack(pady=(0, 0)); tk.Label(content, text="from Biz Analyst.", font=LABEL_FONT, fg=WARN_POPUP_FG, bg=parent['bg'], justify=tk.CENTER).pack(pady=(0, 10)); tk.Label(content, text="It WILL NOT affect data in Tally.", font=LABEL_FONT, fg=WARN_POPUP_FG, bg=parent['bg'], justify=tk.CENTER).pack(pady=(5, 10)); tk.Label(content, text="Confirm Delete?", font=LABEL_FONT, fg=WARN_POPUP_FG, bg=parent['bg'], justify=tk.CENTER).pack(pady=(5, 15)); button_frame = tk.Frame(content, bg=parent['bg']); button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0)); delete_confirm_btn = tk.Button(button_frame, text="DELETE COMPANY", width=15, bg="#dc3545", fg="white", relief=tk.FLAT, font=(LABEL_FONT[0], 10, "bold"), command=lambda: self._perform_soft_delete(company_number, parent)); delete_confirm_btn.pack(side=tk.RIGHT, padx=(10, 0)); cancel_btn = tk.Button(button_frame, text="CANCEL", width=12, relief=tk.GROOVE, font=(LABEL_FONT[0], 10), command=parent.destroy); cancel_btn.pack(side=tk.RIGHT)

    def _perform_soft_delete(self, company_number: str, popup: tk.Toplevel):
        """Handles the soft delete action after confirmation."""
        logger.info(f"Performing soft delete for {company_number}");
        try: # Close confirmation popup safely first
            if popup and popup.winfo_exists():
                popup.destroy()
        except tk.TclError: pass # Ignore error if popup already closed

        # --- !!! CORRECTED try...except block !!! ---
        try:
            success = soft_delete_company(company_number) # Call the DB function
            if success:
                logger.info(f"Soft deleted {company_number}.")
                messagebox.showinfo("Success", "Company marked as inactive.")
                self.refresh_list() # Refresh the list to remove it visually
            else:
                # soft_delete_company logs specific reasons (e.g., not found/inactive)
                logger.warning(f"Soft delete failed for {company_number} (see DB logs).")
                messagebox.showwarning("Delete Failed", "Could not mark company as inactive.\n(It might already be inactive or a database error occurred).")
        except Exception as e:
            # Catch any other unexpected error during the DB operation
            logger.exception(f"Unexpected error occurred during soft delete for {company_number}: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred during deletion:\n{e}")
        # --- End corrected block ---


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
            if self.status_bar and self.status_bar.winfo_exists() and hasattr(self.status_bar, 'update_sync_progress'): self.status_bar.update_sync_progress(0, 1, f"Starting: {company_name}...")
        except tk.TclError: logger.warning("Error updating status bar sync start.")
        # Consider disabling buttons here

    def _sync_worker_odbc(self, companies: list):
        """Background worker using ODBC fetch (processes list, usually 1 item)."""
        total_companies = len(companies)
        logger.info(f"ODBC Sync worker started for {total_companies} companies.")
    
        for i, company in enumerate(companies):
            num = company.get('tally_company_number')
            name = company.get('tally_company_name')
            if not num or not name:
                logger.warning(f"Skipping in ODBC sync: {company}")
                continue

            logger.info(f"Processing {i+1}/{total_companies}: {name} ({num})")
            self.sync_queue.put({"type": "progress", "current": i + 1, "total": total_companies, "message": f"Syncing: {name}..."})

            try:
            # Fetch company details
                logger.debug(f"Calling ODBC fetch for company details. Ensure '{name}' is loaded.")
                details = fetch_company_details_odbc(num)
                success = False

                if details:
                    fetched_name = details.get('tally_company_name')
                    if fetched_name and fetched_name.lower() != name.lower():
                        logger.error(f"ODBC Mismatch! Expected '{name}', got '{fetched_name}'.")
                        update_company_sync_status(num, 'Sync Failed')
                        log_change(num, "SYNC_FAIL", f"Mismatch: Got '{fetched_name}'")
                        self.sync_queue.put({"type": "error", "message": f"Sync Failed: Wrong company ('{fetched_name}') active in Tally."})
                    else:
                        success = update_company_details(num, details)
                        if not success:
                            log_change(num, "SYNC_FAIL", "DB update failed after ODBC fetch")
            
            # Fetch additional data (e.g., ledgers, stock items, etc.)
                if success:
                    logger.info(f"Fetching additional data for {name} ({num})...")
                
                # Fetch ledgers
                    ledgers = fetch_ledgers_odbc()
                    if ledgers:
                        logger.info(f"Fetched {len(ledgers)} ledgers for {name}.")
                        save_ledgers(ledgers)
                    else:
                        logger.warning(f"No ledgers fetched for {name}.")

                # Fetch stock items
                    stock_items = fetch_stock_items_odbc()
                    if stock_items:
                        logger.info(f"Fetched {len(stock_items)} stock items for {name}.")
                        save_stock_items(stock_items)
                    else:
                        logger.warning(f"No stock items fetched for {name}.")

                # Fetch stock groups
                    stock_groups = fetch_stock_groups_odbc()
                    if stock_groups:
                        logger.info(f"Fetched {len(stock_groups)} stock groups for {name}.")
                        save_stock_groups(stock_groups)
                    else:
                        logger.warning(f"No stock groups fetched for {name}.")

                # Add more fetch/save calls as needed (e.g., cost centers, vouchers, etc.)
            
                else:
                    logger.warning(f"ODBC fetch failed/no data for {num}.")
                    update_company_sync_status(num, 'Sync Failed')
                    self.sync_queue.put({"type": "error", "message": f"Sync Failed: Could not fetch ODBC details.\n(Tally running? Company open?)"})

                logger.info(f"Sync result {num} (ODBC): {'Success' if success else 'Failed'}")
        
            except Exception as e:
                logger.exception(f"Error syncing {name} via ODBC: {e}")
                try:
                    update_company_sync_status(num, 'Sync Failed')
                    log_change(num, "SYNC_FAIL", f"Error: {e}")
                except Exception as ie:
                    logger.error(f"Failed to mark {num} as failed: {ie}")
                self.sync_queue.put({"type": "error", "message": f"Error syncing {name}:\n{e}"})

        self.sync_queue.put({"type": "finished"})
        logger.info("ODBC Sync worker finished.")
     
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
            # Re-enable individual sync buttons might be needed here if they were disabled globally
            if self.status_bar and self.status_bar.winfo_exists() and hasattr(self.status_bar, 'clear_sync_progress'): self.status_bar.clear_sync_progress()
        except tk.TclError as e: logger.warning(f"Error resetting sync UI elements: {e}")

    
    
    def _start_all_companies_sync(self):
        """Initiates sync for all companies."""
        if self.is_syncing:
            logger.warning("Sync busy.")
            messagebox.showwarning("Sync Busy", "Sync running.")
            return

        logger.info("Starting sync for all companies.")
        try:
            companies = get_added_companies()
            if not companies:
                messagebox.showinfo("No Companies", "No active companies to sync.")
                return

            self.is_syncing = True
            self._update_sync_ui_start("All Companies")
            sync_thread = threading.Thread(target=self._sync_worker_odbc, args=(companies,), daemon=True)
            sync_thread.start()
        except Exception as e:
            logger.exception("Error starting sync for all companies.")
            messagebox.showerror("Error", f"Failed to start sync: {e}")

from utils.odbc_helper import (
    fetch_ledgers_odbc, fetch_stock_items_odbc, fetch_stock_groups_odbc,
    fetch_units_odbc, fetch_accounting_groups_odbc, fetch_ledgerbillwise_odbc,
    fetch_costcategory_odbc, fetch_costcenter_odbc, fetch_currency_odbc,
    fetch_vouchertype_odbc, fetch_stockgroupwithgst_odbc, fetch_stockcategory_odbc,
    fetch_godown_odbc, fetch_stockitem_gst_odbc, fetch_stockitem_mrp_odbc,
    fetch_stockitem_bom_odbc, fetch_stockitem_standardcost_odbc,
    fetch_stockitem_standardprice_odbc, fetch_stockitem_batchdetails_odbc
)
from utils.database import (
    save_ledgers, save_stock_items, save_stock_groups, save_units,
    save_accounting_groups, save_ledgerbillwise, save_costcategory,
    save_costcenter, save_currency, save_vouchertype,
    save_stockgroupwithgst, save_stockcategory, save_godown,
    save_stockitem_gst, save_stockitem_mrp, save_stockitem_bom,
    save_stockitem_standardcost, save_stockitem_standardprice,
    save_stockitem_batchdetails
)

# Inside the MyCompaniesPanel class

def _start_single_company_sync(self, company_number: str, company_name: str):
    """Initiates sync for a single company via ODBC after user confirmation."""
    if self.is_syncing:
        logger.warning("Sync busy.")
        messagebox.showwarning("Sync Busy", "Sync running.")
        return

    if not company_number or not company_name:
        logger.error("Cannot sync: Missing info.")
        return

    logger.info(f"Requesting confirm sync: {company_name} ({company_number})")
    msg = f"Ensure company:\n'{company_name}'\nis loaded in Tally Prime.\n\nClick OK to sync details."
    if messagebox.askokcancel("Confirm Tally Company", msg, icon='info'):
        logger.info(f"User confirmed. Starting ODBC sync for {company_number}")
        self.is_syncing = True
        self._update_sync_ui_start(company_name)

        # Define the sync logic in a background thread
        sync_thread = threading.Thread(
            target=self._sync_company_data,
            args=(company_number, company_name),
            daemon=True
        )
        sync_thread.start()
    else:
        logger.info(f"User cancelled sync for {company_number}.")

def _sync_company_data(self, company_number: str, company_name: str):
    """Handles the synchronization of company data."""
    try:
        # Fetch company details
        logger.info(f"Fetching details for company: {company_name} ({company_number})")
        details = fetch_company_details_odbc(company_number)
        if not details:
            logger.error(f"Failed to fetch details for company: {company_name}")
            update_company_sync_status(company_number, 'Sync Failed')
            return

        # Update company details in the database
        success = update_company_details(company_number, details)
        if not success:
            logger.error(f"Failed to update company details for {company_name}")
            update_company_sync_status(company_number, 'Sync Failed')
            return

        # Fetch and save additional master data
        self._fetch_and_save_master_data(company_name)

        # Mark sync as successful
        update_company_sync_status(company_number, 'Synced')
        logger.info(f"Sync completed successfully for {company_name}")
        messagebox.showinfo("Sync Complete", f"Sync completed successfully for {company_name}")

    except Exception as e:
        logger.exception(f"Error syncing company {company_name}: {e}")
        update_company_sync_status(company_number, 'Sync Failed')
        messagebox.showerror("Sync Error", f"An error occurred while syncing {company_name}:\n{e}")

    finally:
        self.is_syncing = False
        self.refresh_list()

def _fetch_and_save_master_data(self, company_name: str):
    """Fetches and saves master data for the company."""
    logger.info(f"Fetching additional data for {company_name}...")

    # Define the master data to sync
    masters_to_sync = [
        {'name': 'Ledgers', 'fetch': fetch_ledgers_odbc, 'save': save_ledgers},
        {'name': 'Stock Items', 'fetch': fetch_stock_items_odbc, 'save': save_stock_items},
        {'name': 'Stock Groups', 'fetch': fetch_stock_groups_odbc, 'save': save_stock_groups},
        {'name': 'Units', 'fetch': fetch_units_odbc, 'save': save_units},
        {'name': 'Accounting Groups', 'fetch': fetch_accounting_groups_odbc, 'save': save_accounting_groups},
        {'name': 'Ledger Billwise', 'fetch': fetch_ledgerbillwise_odbc, 'save': save_ledgerbillwise},
        {'name': 'Cost Categories', 'fetch': fetch_costcategory_odbc, 'save': save_costcategory},
        {'name': 'Cost Centers', 'fetch': fetch_costcenter_odbc, 'save': save_costcenter},
        {'name': 'Currencies', 'fetch': fetch_currency_odbc, 'save': save_currency},
        {'name': 'Voucher Types', 'fetch': fetch_vouchertype_odbc, 'save': save_vouchertype},
        {'name': 'Stock Groups GST', 'fetch': fetch_stockgroupwithgst_odbc, 'save': save_stockgroupwithgst},
        {'name': 'Stock Categories', 'fetch': fetch_stockcategory_odbc, 'save': save_stockcategory},
        {'name': 'Godowns', 'fetch': fetch_godown_odbc, 'save': save_godown},
        {'name': 'Stock Item GST', 'fetch': fetch_stockitem_gst_odbc, 'save': save_stockitem_gst},
        {'name': 'Stock Item MRP', 'fetch': fetch_stockitem_mrp_odbc, 'save': save_stockitem_mrp},
        {'name': 'Stock Item BOM', 'fetch': fetch_stockitem_bom_odbc, 'save': save_stockitem_bom},
        {'name': 'Stock Item Cost', 'fetch': fetch_stockitem_standardcost_odbc, 'save': save_stockitem_standardcost},
        {'name': 'Stock Item Price', 'fetch': fetch_stockitem_standardprice_odbc, 'save': save_stockitem_standardprice},
        {'name': 'Stock Item Batch', 'fetch': fetch_stockitem_batchdetails_odbc, 'save': save_stockitem_batchdetails},
    ]

    # Process each master type
    for master in masters_to_sync:
        name = master['name']
        fetch_func = master['fetch']
        save_func = master['save']

        try:
            logger.info(f"Fetching {name}...")
            data = fetch_func()
            if data:
                logger.info(f"Fetched {len(data)} records for {name}. Saving to database...")
                save_func(data)
            else:
                logger.warning(f"No data found for {name}.")
        except Exception as e:
            logger.exception(f"Error syncing {name}: {e}")


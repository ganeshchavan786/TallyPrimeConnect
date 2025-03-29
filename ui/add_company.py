# TallyPrimeConnect/ui/add_company.py
import tkinter as tk
from tkinter import ttk, messagebox
from utils.helpers import load_settings, get_tally_companies
from utils.database import add_company_to_db, get_added_companies

class AddCompanyPanel(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, bg="#ffffff", *args, **kwargs)
        self.selected_company_var = tk.StringVar(value=None)
        self.company_data = {} # Cache of *available* Tally companies {name: data}
        self._create_widgets()

    def _create_widgets(self):
        title_label = tk.Label(self, text="Add Company", font=("Arial", 16, "bold"), bg="#ffffff", anchor="w")
        title_label.pack(pady=(10, 10), padx=30, anchor="w")
        list_bg = "#f8f8f8"
        self.list_container = tk.Frame(self, bg=list_bg)
        self.list_container.pack(pady=10, padx=50, fill=tk.BOTH, expand=True)
        self.status_label = tk.Label(self.list_container, text="Fetching companies...", font=("Arial", 10), bg=list_bg, fg="gray", justify=tk.LEFT)
        self.status_label.pack(pady=20, padx=20)
        self.radio_frame = tk.Frame(self.list_container, bg=list_bg)
        self.radio_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        self.add_button = tk.Button(self.list_container, text="+ ADD", command=self._add_selected_company, bg="#e74c3c", fg="#ffffff", font=("Arial", 10, "bold"), relief=tk.FLAT, padx=30, pady=8, cursor="hand2", activebackground="#c0392b", activeforeground="#ffffff", state=tk.DISABLED)
        self.add_button.pack(pady=(10, 20))

    def load_companies(self):
        """Fetches Tally companies and displays only those not already added."""
        print("Loading companies for Add Company panel...")
        for widget in self.radio_frame.winfo_children(): widget.destroy()
        self.status_label.config(text="Fetching available companies...", fg="gray")
        self.status_label.pack(pady=20, padx=20)
        self.add_button.config(state=tk.DISABLED)
        self.selected_company_var.set(None)
        self.company_data = {}
        self.update_idletasks()

        added_companies_list = get_added_companies()
        added_company_numbers = {comp.get('tally_company_number') for comp in added_companies_list if comp.get('tally_company_number')}
        print(f"Already added company numbers: {added_company_numbers}")

        settings = load_settings()
        tally_companies = get_tally_companies(settings.get("tally_host"), settings.get("tally_port"))

        if tally_companies is None:
            self.status_label.config(text="Error: Could not fetch companies from Tally.\nCheck connection and ensure Tally/Company is open.", fg="red")
            return

        available_companies = [comp for comp in tally_companies if comp.get('number') not in added_company_numbers]
        print(f"Available companies to add: {[c['name'] for c in available_companies]}")

        if not available_companies:
             self.status_label.config(text="No new companies available to add from Tally.", fg="black")
        else:
            self.status_label.pack_forget()
            self.company_data = {comp['name']: comp for comp in available_companies}

            tk.Label(self.radio_frame, text="TALLY COMPANIES", font=("Arial", 9, "bold"), bg=self.radio_frame['bg'], anchor='w').pack(fill=tk.X, pady=(5,5))

            for company in available_companies:
                comp_name = company['name']
                rb = tk.Radiobutton(self.radio_frame, text=f" {comp_name}", variable=self.selected_company_var, value=comp_name, anchor='w', bg=self.radio_frame['bg'], activebackground=self.radio_frame['bg'], selectcolor=self.radio_frame['bg'], font=("Arial", 10))
                rb.pack(fill=tk.X, pady=2)

            self.add_button.config(state=tk.NORMAL)

    def _add_selected_company(self):
        """Adds selected company to the DB and refreshes the list."""
        selected_name = self.selected_company_var.get()
        if not selected_name or selected_name == 'None':
            messagebox.showwarning("No Selection", "Please select a company first.")
            return

        selected_data = self.company_data.get(selected_name)
        if not selected_data or not selected_data.get('number'):
             messagebox.showerror("Error", f"Data error for company '{selected_name}'.")
             return

        company_number = selected_data['number']
        self.add_button.config(state=tk.DISABLED)
        self.update_idletasks()
        try:
            was_added = add_company_to_db(selected_name, company_number)
            if was_added:
                messagebox.showinfo("Success", f"Company '{selected_name}' added.")
                self.load_companies() # Refresh this list
            else:
                messagebox.showinfo("Info", f"Company '{selected_name}' already exists or failed to add.")
                self.load_companies() # Refresh anyway
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error adding company: {e}")
        finally:
            # load_companies will re-enable button if needed
             pass
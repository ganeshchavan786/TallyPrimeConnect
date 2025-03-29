# TallyPrimeConnect/ui/my_companies.py
import tkinter as tk
from tkinter import ttk, font, messagebox
# Updated imports
from utils.database import get_added_companies, get_company_details, edit_company_in_db, soft_delete_company

class MyCompaniesPanel(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, bg="#ffffff", *args, **kwargs)
        self._create_widgets()

    def _create_widgets(self):
        # ... (title, list_container, status_label, companies_frame remain the same) ...
        title_label = tk.Label(self, text="My Companies", font=("Arial", 16, "bold"), bg="#ffffff", anchor="w")
        title_label.pack(pady=(10, 10), padx=30, anchor="w")
        list_bg = "#f8f8f8"
        self.list_container = tk.Frame(self, bg=list_bg)
        self.list_container.pack(pady=10, padx=50, fill=tk.BOTH, expand=True)
        self.status_label = tk.Label(self.list_container, text="Loading added companies...", font=("Arial", 10), bg=list_bg, fg="gray")
        self.status_label.pack(pady=20, padx=20)
        self.companies_frame = tk.Frame(self.list_container, bg=list_bg)
        self.companies_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    def refresh_list(self):
        """Fetches active companies from the database and updates the display."""
        print("Refreshing My Companies list...")
        for widget in self.companies_frame.winfo_children(): widget.destroy()
        self.status_label.pack(pady=20, padx=20)
        self.status_label.config(text="Loading added companies...", fg="gray")
        self.update_idletasks()

        added_companies = get_added_companies() # Gets only active companies

        if not added_companies:
            self.status_label.config(text="No active companies found.", fg="black")
        else:
            self.status_label.pack_forget()
            bold_font = font.Font(family="Arial", size=10, weight="bold")
            normal_font = font.Font(family="Arial", size=9)
            button_font = font.Font(family="Arial", size=9)

            for company in added_companies:
                comp_frame = tk.Frame(self.companies_frame, bg=self.companies_frame['bg'])
                comp_frame.pack(fill=tk.X, pady=3)

                # --- Company Info (Left Aligned) ---
                info_frame = tk.Frame(comp_frame, bg=comp_frame['bg'])
                info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

                name_label = tk.Label(info_frame, text=company.get('tally_company_name', 'N/A'), font=bold_font, bg=comp_frame['bg'], anchor='w')
                name_label.pack(side=tk.LEFT, padx=(0, 10))
                num_label = tk.Label(info_frame, text=f"(Number: {company.get('tally_company_number', 'N/A')})", font=normal_font, fg="gray", bg=comp_frame['bg'], anchor='w')
                num_label.pack(side=tk.LEFT)

                # --- Action Buttons (Right Aligned) ---
                action_frame = tk.Frame(comp_frame, bg=comp_frame['bg'])
                action_frame.pack(side=tk.RIGHT)

                company_number = company.get('tally_company_number') # Get number for commands

                edit_btn = tk.Button(
                    action_frame, text="Edit", font=button_font, width=6, relief=tk.GROOVE,
                    command=lambda num=company_number: self._open_edit_popup(num)
                )
                edit_btn.pack(side=tk.LEFT, padx=(0, 5))

                delete_btn = tk.Button(
                    action_frame, text="Delete", font=button_font, width=6, relief=tk.GROOVE,
                    fg='red', # Indicate danger
                    command=lambda num=company_number, name=company.get('tally_company_name'): self._open_delete_popup(num, name)
                )
                delete_btn.pack(side=tk.LEFT)


    # --- Edit Functionality ---
    def _open_edit_popup(self, company_number):
        if not company_number: return
        details = get_company_details(company_number)
        if not details:
            messagebox.showerror("Error", f"Could not fetch details for company number {company_number}.")
            return

        popup = tk.Toplevel(self)
        popup.title("Edit Company Details")
        popup.geometry("450x300")
        popup.resizable(False, False)
        popup.configure(bg="white")
        # Center popup (optional)
        # parent_x = self.winfo_rootx()
        # parent_y = self.winfo_rooty()
        # parent_width = self.winfo_width()
        # parent_height = self.winfo_height()
        # popup_width = 450
        # popup_height = 300
        # popup.geometry(f"{popup_width}x{popup_height}+{parent_x + (parent_width - popup_width)//2}+{parent_y + (parent_height - popup_height)//2}")


        # --- Content Frame ---
        content = tk.Frame(popup, bg="white", padx=20, pady=15)
        content.pack(fill=tk.BOTH, expand=True)

        # Company Name
        tk.Label(content, text="Company Name*", font=("Arial", 10), bg="white", anchor='w').pack(fill=tk.X)
        name_var = tk.StringVar(value=details.get('tally_company_name', ''))
        name_entry = ttk.Entry(content, textvariable=name_var, font=("Arial", 10))
        name_entry.pack(fill=tk.X, pady=(2, 10))

        # Description
        tk.Label(content, text="Description", font=("Arial", 10), bg="white", anchor='w').pack(fill=tk.X)
        desc_var = tk.StringVar(value=details.get('description', ''))
        # Use Text widget for multi-line description
        desc_entry = tk.Text(content, height=4, font=("Arial", 10), relief=tk.SOLID, bd=1)
        desc_entry.insert(tk.END, desc_var.get()) # Insert initial value
        desc_entry.pack(fill=tk.X, pady=(2, 10))

        # Sync Data Checkbox (Visual Placeholder)
        sync_var = tk.IntVar(value=1) # Default checked?
        sync_check = tk.Checkbutton(content, text="Sync Data", variable=sync_var, bg="white", activebackground="white", font=("Arial", 10), anchor='w')
        sync_check.pack(fill=tk.X, pady=(5, 15))

        # Separator
        ttk.Separator(content, orient='horizontal').pack(fill='x', pady=(5, 15))


        # --- Button Frame ---
        button_frame = tk.Frame(content, bg="white")
        button_frame.pack(fill=tk.X) # Buttons at bottom

        save_btn = tk.Button(
            button_frame, text="SAVE", width=12, bg="#007bff", fg="white", relief=tk.FLAT, font=("Arial", 10, "bold"),
            command=lambda: self._save_edit(company_number, name_var, desc_entry, popup)
        )
        save_btn.pack(side=tk.LEFT) # Align left

        # --- Additional Settings (Visual Placeholder) ---
        # tk.Label(content, text="Additional settings", fg="blue", cursor="hand2", font=("Arial", 9, "underline"), bg="white").pack(pady=(10,0))


        # Make popup modal (grab focus)
        popup.transient(self.winfo_toplevel()) # Associate with main window
        popup.grab_set()
        self.winfo_toplevel().wait_window(popup) # Wait until popup is closed


    def _save_edit(self, company_number, name_var, desc_widget, popup):
        new_name = name_var.get().strip()
        # Get text from Text widget correctly
        new_description = desc_widget.get("1.0", tk.END).strip()

        if not new_name:
            messagebox.showerror("Input Error", "Company Name cannot be empty.", parent=popup)
            return

        # Call DB function
        success = edit_company_in_db(company_number, new_name, new_description)

        if success:
            messagebox.showinfo("Success", "Company details updated successfully.", parent=popup)
            popup.destroy() # Close popup on success
            self.refresh_list() # Refresh the main list
        else:
            # edit_company_in_db prints specific errors (duplicate name, not found)
            # Show a generic failure message here or rely on console output
            messagebox.showerror("Update Failed", "Could not update company details.\nCheck console for errors (e.g., duplicate name).", parent=popup)


    # --- Delete Functionality ---
    def _open_delete_popup(self, company_number, company_name):
        if not company_number: return

        popup = tk.Toplevel(self)
        popup.title("Confirm Delete Company")
        popup.geometry("450x200") # Adjust size
        popup.resizable(False, False)
        popup.configure(bg="#f8d7da") # Light red background for warning

        # Center popup (optional)
        # ... (centering code) ...

        content = tk.Frame(popup, bg=popup['bg'], padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)

        # Warning Icon (Optional - using text for simplicity)
        # tk.Label(content, text="!", font=("Arial", 24, "bold"), fg="#721c24", bg=popup['bg']).pack()

        # Warning Message (Multi-line)
        warning_text = (f"This action is irreversible and will hide company\n"
                        f"'{company_name}' (Number: {company_number})\n"
                        f"from Biz Analyst permanently.\n\n"
                        f"This WILL NOT affect your data in Tally.\n\n"
                        f"Confirm Delete?")
        tk.Label(content, text=warning_text, font=("Arial", 10), fg="#721c24", bg=popup['bg'], justify=tk.CENTER).pack(pady=(5, 20))

        # Button Frame
        button_frame = tk.Frame(content, bg=popup['bg'])
        button_frame.pack(fill=tk.X)

        # Place buttons centered maybe? Use pack with side=tk.LEFT/RIGHT and padding
        spacer_left = tk.Frame(button_frame, bg=popup['bg'])
        spacer_left.pack(side=tk.LEFT, expand=True)

        cancel_btn = tk.Button(
            button_frame, text="CANCEL", width=12, relief=tk.GROOVE, font=("Arial", 10),
            command=popup.destroy
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)

        delete_confirm_btn = tk.Button(
            button_frame, text="DELETE COMPANY", width=15, bg="#dc3545", fg="white", relief=tk.FLAT, font=("Arial", 10, "bold"),
            command=lambda: self._perform_soft_delete(company_number, popup)
        )
        delete_confirm_btn.pack(side=tk.LEFT, padx=10)

        spacer_right = tk.Frame(button_frame, bg=popup['bg'])
        spacer_right.pack(side=tk.LEFT, expand=True)


        # Make popup modal
        popup.transient(self.winfo_toplevel())
        popup.grab_set()
        self.winfo_toplevel().wait_window(popup)


    def _perform_soft_delete(self, company_number, popup):
        print(f"Attempting soft delete for: {company_number}") # Debug
        success = soft_delete_company(company_number) # Call DB function

        popup.destroy() # Close confirmation popup regardless of success

        if success:
            messagebox.showinfo("Success", "Company marked as inactive successfully.")
            self.refresh_list() # Refresh the main list
        else:
            messagebox.showerror("Delete Failed", "Could not mark company as inactive.\nIt might already be inactive or an error occurred.")
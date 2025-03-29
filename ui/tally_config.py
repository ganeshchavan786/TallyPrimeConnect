# TallyPrimeConnect/ui/tally_config.py
import tkinter as tk
from tkinter import ttk, messagebox
# Import the specific function and helpers
from utils.helpers import load_settings, save_settings, check_tally_connection # <-- Added check_tally_connection
import webbrowser

class TallyConfigPanel(tk.Frame):
    # Accept status_bar instance in constructor
    def __init__(self, parent, status_bar, *args, **kwargs):
        super().__init__(parent, bg="#ffffff", *args, **kwargs)
        self.status_bar = status_bar # Store reference to status bar

        self.host_var = tk.StringVar()
        self.port_var = tk.StringVar()

        self._load_initial_data()
        self._create_widgets()

    def _load_initial_data(self):
        settings = load_settings()
        self.host_var.set(settings.get("tally_host", "localhost"))
        self.port_var.set(settings.get("tally_port", "9000"))
        # Optional: Perform an initial check on load?
        # self._check_connection_action(show_messages=False) # Don't show popups on load

    def _create_widgets(self):
        # --- Title, Subtitle, Help Link --- (Keep existing code)
        title_label = tk.Label(self, text="Tally Configuration", font=("Arial", 16, "bold"), bg="#ffffff", anchor="w")
        title_label.pack(pady=(20, 5), padx=30, anchor="w")
        subtitle_frame = tk.Frame(self, bg="#ffffff")
        subtitle_frame.pack(pady=(0, 5), padx=30, anchor="w")
        subtitle_label = tk.Label(subtitle_frame, text="Connect your Tally to Biz Analyst using ODBC configuration.", font=("Arial", 10), bg="#ffffff", anchor="w")
        subtitle_label.pack(side=tk.LEFT)
        help_link = tk.Label(subtitle_frame, text="Click here", font=("Arial", 10, "underline"), fg="blue", cursor="hand2", bg="#ffffff", anchor="w")
        help_link.pack(side=tk.LEFT, padx=(5,0))
        help_link.bind("<Button-1>", self._open_help)
        need_help_label = tk.Label(subtitle_frame, text=" if you need help.", font=("Arial", 10), bg="#ffffff", anchor="w")
        need_help_label.pack(side=tk.LEFT)

        # --- Form Area --- (Keep existing code)
        form_bg = "#f8f8f8"
        form_container = tk.Frame(self, bg=form_bg, padx=50, pady=30)
        form_container.pack(pady=30, padx=50, fill=tk.X)

        host_label = tk.Label(form_container, text="Tally Host (eg. localhost/127.0.0.1) *", font=("Arial", 9), bg=form_bg, anchor="w")
        host_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 2)) # Span 2 cols now
        host_entry = ttk.Entry(form_container, textvariable=self.host_var, width=50, font=("Arial", 10))
        host_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        port_label = tk.Label(form_container, text="Tally Port (eg. 9000) *", font=("Arial", 9), bg=form_bg, anchor="w")
        port_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 2)) # Span 2 cols
        port_entry = ttk.Entry(form_container, textvariable=self.port_var, width=50, font=("Arial", 10))
        port_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 25))

        form_container.grid_columnconfigure(0, weight=1) # Make column 0 expandable
        form_container.grid_columnconfigure(1, weight=1) # Make column 1 expandable

        # --- Buttons Frame ---
        button_frame = tk.Frame(form_container, bg=form_bg)
        # Place button frame spanning across columns, centered using grid options if possible, or pack within frame
        button_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0)) # Span 2 columns


        # --- Check Connection Button ---
        self.check_button = tk.Button(
            button_frame, # Place in button frame
            text="Check Connection",
            command=self._check_connection_action,
            bg="#3498db",  # Blue background
            fg="#ffffff",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=15, # Adjusted padding
            pady=8,
            cursor="hand2",
            activebackground="#2980b9", # Darker blue
            activeforeground="#ffffff"
        )
        self.check_button.pack(side=tk.LEFT, padx=(0, 10)) # Pack left in the frame

        # --- Save Button ---
        save_button = tk.Button(
            button_frame, # Place in button frame
            text="SAVE",
            command=self._save_action,
            bg="#e74c3c",
            fg="#ffffff",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=30,
            pady=8,
            cursor="hand2",
            activebackground="#c0392b",
            activeforeground="#ffffff"
        )
        save_button.pack(side=tk.LEFT) # Pack next to check button

    def _open_help(self, event=None):
        # (Keep existing method)
        help_url = "https://bizanalyst.in/faq/" # More relevant URL?
        print(f"Opening help link: {help_url}")
        try:
            webbrowser.open(help_url)
        except Exception as e:
            print(f"Error opening help link: {e}")
            messagebox.showerror("Error", f"Could not open the help link:\n{e}")

    def _save_action(self):
        # (Keep existing method, maybe add a check after saving?)
        host = self.host_var.get().strip()
        port = self.port_var.get().strip()

        if not host or not port:
            messagebox.showwarning("Input Error", "Tally Host and Port cannot be empty.")
            return
        if not port.isdigit() or not 0 < int(port) < 65536:
             messagebox.showwarning("Input Error", "Please enter a valid Port number (1-65535).")
             return

        settings = {"tally_host": host, "tally_port": port}
        save_settings(settings)
        print(f"Settings saved: Host={host}, Port={port}")
        messagebox.showinfo("Success", "Tally configuration saved successfully.")
        # Optional: Automatically check connection after saving
        # self._check_connection_action(show_messages=False)

    # --- New Method for Connection Check ---
    def _check_connection_action(self, show_messages=True):
        """Checks the Tally connection using entered details."""
        host = self.host_var.get().strip()
        port = self.port_var.get().strip()

        if not host or not port:
            if show_messages:
                messagebox.showwarning("Input Error", "Please enter Tally Host and Port before checking.")
            return

        if not port.isdigit() or not 0 < int(port) < 65536:
             if show_messages:
                messagebox.showwarning("Input Error", "Please enter a valid Port number (1-65535).")
             return

        # Provide visual feedback during check
        self.check_button.config(state=tk.DISABLED, text="Checking...")
        if self.status_bar:
             self.status_bar.update_tally_status(checking=True)
        self.update_idletasks() # Force UI update

        is_connected = False # Default to false
        try:
            is_connected = check_tally_connection(host, port)
        finally:
            # Ensure button is re-enabled and text restored even if check errors out
            self.check_button.config(state=tk.NORMAL, text="Check Connection")
            if self.status_bar:
                self.status_bar.update_tally_status(connected=is_connected)

        if show_messages:
            if is_connected:
                messagebox.showinfo("Connection Success", f"Successfully connected to Tally at {host}:{port}")
            else:
                messagebox.showerror("Connection Failed", f"Could not connect to Tally at {host}:{port}.\n\n"
                                     "Please ensure:\n"
                                     "- Tally is running.\n"
                                     "- The company is open.\n"
                                     "- Tally's 'Enable ODBC Server' is set to 'Yes'.\n"
                                     "- The Port number matches Tally's configuration.\n"
                                     "- No firewall is blocking the connection.")


# Example usage (if run directly - requires passing a mock status bar)
if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("600x450") # Adjusted size
    root.title("Tally Config Test")

    # Create a mock status bar for testing
    mock_statusbar = tk.Frame(root, height=30, bg="lightgrey")
    mock_statusbar.pack(fill=tk.X, side=tk.BOTTOM)
    mock_statusbar.update_tally_status = lambda connected=None, checking=False: print(f"Mock Status Update: connected={connected}, checking={checking}") # Mock method

    config_panel = TallyConfigPanel(root, status_bar=mock_statusbar) # Pass the mock status bar
    config_panel.pack(fill=tk.BOTH, expand=True)

    root.mainloop()
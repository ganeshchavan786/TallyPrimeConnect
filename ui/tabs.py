# TallyPrimeConnect/ui/tabs.py
import tkinter as tk
from tkinter import ttk

class Tabs(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, bg="#ffffff", height=50, *args, **kwargs)
        self.pack_propagate(False)
        self.tab_buttons = {}
        self.active_tab = "TALLY"
        self._create_widgets()
        self.update_tabs()

    def _create_widgets(self):
        # ... (keep existing widget creation logic) ...
        tab_names = ["TALLY", "SYNC", "ADDITIONAL"]
        container = tk.Frame(self, bg="#ffffff")
        container.pack(side=tk.LEFT, padx=20, pady=(10,0)) # Padding for positioning

        for name in tab_names:
            frame = tk.Frame(container, bg="#ffffff") # Frame for button and underline
            frame.pack(side=tk.LEFT, padx=15)

            btn = tk.Button(
                frame,
                text=name,
                relief=tk.FLAT,
                bg="#ffffff",
                fg="#555555", # Default text color
                activebackground="#ffffff",
                activeforeground="#0078d4", # Color on click
                font=("Arial", 10, "bold"),
                cursor="hand2",
                command=lambda n=name: self.set_active_tab(n)
            )
            btn.pack(side=tk.TOP)

            underline = tk.Frame(frame, height=2, bg="#ffffff") # Hidden by default
            underline.pack(fill=tk.X, pady=(2,0))

            self.tab_buttons[name] = {"button": btn, "underline": underline}


    def set_active_tab(self, tab_name):
        # ... (keep existing logic) ...
        if tab_name in self.tab_buttons:
            self.active_tab = tab_name
            self.update_tabs()
            print(f"Tab selected: {self.active_tab}")
        else:
            print(f"Warning: Tab '{tab_name}' not found.")

    def update_tabs(self):
        # ... (keep existing logic) ...
        active_color = "#0078d4"
        inactive_color = "#555555"
        underline_color = "#0078d4"

        for name, widgets in self.tab_buttons.items():
            is_active = (name == self.active_tab)
            widgets["button"].config(fg=active_color if is_active else inactive_color)
            widgets["underline"].config(bg=underline_color if is_active else "#ffffff")

    # --- New Methods ---
    def show(self):
        """Makes the tab bar visible."""
        # Use the same packing options as in app.py
        self.pack(fill=tk.X, side=tk.TOP)
        print("Tabs shown") # Debug

    def hide(self):
        """Hides the tab bar."""
        self.pack_forget()
        print("Tabs hidden") # Debug
    # --- End New Methods ---


# Example usage remains the same
if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("600x100")
    root.title("Tabs Test")
    tabs = Tabs(root)
    tabs.pack(fill=tk.X)
    root.after(2000, tabs.hide)
    root.after(4000, tabs.show)
    root.mainloop()
"""Tkinter GUI for EasyHID"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable


class SharingGUI:
    """Main GUI window for the sharing application"""
    
    def __init__(self, share_callback: Optional[Callable[[], None]] = None,
                 stop_callback: Optional[Callable[[], None]] = None):
        """
        Initialize GUI.
        
        Args:
            share_callback: Called when Share button is clicked
            stop_callback: Called when Stop button is clicked
        """
        self.share_callback = share_callback
        self.stop_callback = stop_callback
        
        self.root = tk.Tk()
        self.root.title("Bluetooth Keyboard & Mouse Sharing")
        self.root.geometry("500x250")
        self.root.resizable(False, False)
        
        self.is_sharing = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create and layout GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="EasyHID",
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Share/Stop button
        self.action_button = ttk.Button(
            main_frame,
            text="Share",
            command=self._on_action_button_clicked,
            width=20
        )
        self.action_button.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text="Status: Not connected",
            font=("Arial", 10)
        )
        self.status_label.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Escape key message
        escape_frame = ttk.Frame(main_frame)
        escape_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))
        
        escape_label = ttk.Label(
            escape_frame,
            text="Simultaneously press and hold Left Shift + Space + Right Shift to stop sharing.",
            font=("Arial", 9),
            foreground="gray",
            wraplength=450,
            justify=tk.CENTER
        )
        escape_label.pack()
    
    def _on_action_button_clicked(self):
        """Handle Share/Stop button click"""
        if self.is_sharing:
            if self.stop_callback:
                self.stop_callback()
        else:
            if self.share_callback:
                self.share_callback()
    
    def set_sharing(self, sharing: bool, status_text: Optional[str] = None):
        """
        Update sharing state and UI.
        
        Args:
            sharing: True if currently sharing, False otherwise
            status_text: Optional custom status text
        """
        self.is_sharing = sharing
        
        if sharing:
            self.action_button.config(text="Stop")
            if status_text:
                self.status_label.config(text=f"Status: {status_text}")
            else:
                self.status_label.config(text="Status: Sharing... Waiting for connection")
        else:
            self.action_button.config(text="Share")
            if status_text:
                self.status_label.config(text=f"Status: {status_text}")
            else:
                self.status_label.config(text="Status: Not connected")
    
    def update_status(self, text: str):
        """
        Update status label text.
        
        Args:
            text: Status text to display
        """
        self.status_label.config(text=f"Status: {text}")
    
    def run(self):
        """Start GUI main loop"""
        self.root.mainloop()
    
    def quit(self):
        """Quit GUI"""
        self.root.quit()
        self.root.destroy()

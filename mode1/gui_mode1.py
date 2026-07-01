import os
import sys
import subprocess
import tkinter as tk

class Mode1Window:
    def __init__(self, root: tk.Misc, i18n=None):
        self.root = root
        self.i18n = i18n
        self._on_home_callback = None
        
        # Withdraw the root window to hide it
        self.root.withdraw()
        
        # Start the webview subprocess
        self._launch_webview()
        
    def _launch_webview(self):
        # Path to python script
        dir_path = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(dir_path, "run_webview.py")
        
        # Spawn subprocess
        try:
            self.process = subprocess.Popen(
                [sys.executable, script_path],
                cwd=dir_path
            )
            # Start checking for completion
            self.root.after(100, self._check_process)
        except Exception as e:
            # If fail, restore root and show error
            self.root.deiconify()
            import tkinter.messagebox as mbox
            mbox.showerror("Error", f"Failed to start Mode 1 webview:\n{e}")
            if self._on_home_callback:
                self._on_home_callback()

    def _check_process(self):
        if self.process.poll() is None:
            # Process is still running, check again in 100ms
            self.root.after(100, self._check_process)
        else:
            # Process finished, restore root and trigger home callback
            self.root.deiconify()
            if self._on_home_callback:
                self._on_home_callback()

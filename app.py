import os
import sys
import time
import tkinter as tk
from tkinter import ttk

import ttkbootstrap as tb
from PIL import Image, ImageTk

from i18n.runtime_i18n import RuntimeI18n
from common.auth_manager import AuthManager

try:
    from version import APP_VERSION
except ImportError:
    APP_VERSION = "1.0.0"

# Optional modules
try:
    from common.help_window import HelpWindow
except ImportError:
    HelpWindow = None

try:
    from help_editor.gui_help_editor import HelpEditorWindow
except ImportError:
    HelpEditorWindow = None

from mode1.gui_mode1 import Mode1Window

print("RUNNING:", __file__)
print("Python Executable:", sys.executable)
print("Python Path:", sys.path)


def resource_path(relative_path: str) -> str:
    """
    Trả về path tuyệt đối tới file tài nguyên (logo, icon...)
    Chạy ổn cả khi build PyInstaller --onefile.
    """
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class RoundedButton(tk.Canvas):
    """Custom button with rounded corners and cyan background."""
    
    def __init__(self, parent, text, command, width=450, height=52, radius=14, **kwargs):
        super().__init__(parent, width=width, height=height, bg="white", 
                        highlightthickness=0, **kwargs)
        
        self.command = command
        self.text = text
        self.width = width
        self.height = height
        self.radius = radius
        
        self.bg_normal = "#00A8E8"
        self.bg_hover = "#0096D6"
        self.bg_pressed = "#0085C2"
        self.fg_color = "white"
        
        self.current_bg = self.bg_normal
        
        self._draw_button()
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        
        self.configure(cursor="hand2")
    
    def _draw_button(self):
        """Draw rounded rectangle button."""
        self.delete("all")
        
        x1, y1 = 0, 0
        x2, y2 = self.width, self.height
        r = self.radius
        
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1
        ]
        
        self.create_polygon(points, fill=self.current_bg, smooth=True, outline="")
        
        self.create_text(
            self.width // 2, 
            self.height // 2,
            text=self.text,
            fill=self.fg_color,
            font=("Segoe UI", 14, "bold")
        )
    
    def _on_enter(self, event):
        self.current_bg = self.bg_hover
        self._draw_button()
    
    def _on_leave(self, event):
        self.current_bg = self.bg_normal
        self._draw_button()
    
    def _on_press(self, event):
        self.current_bg = self.bg_pressed
        self._draw_button()
    
    def _on_release(self, event):
        self.current_bg = self.bg_hover
        self._draw_button()
        if self.command:
            self.command()
    
    def update_text(self, new_text):
        """Update button text (for i18n)."""
        self.text = new_text
        self._draw_button()


class MainLauncher:
    def __init__(self, root: tb.Window):
        self.root = root

        self.i18n = RuntimeI18n(
            locales_dir=resource_path(os.path.join("i18n", "locales")),
            default_lang="vi",
        )
        
        self.auth = AuthManager()
        self.user_data = None
        self.license_info = (False, None, "") # (is_valid, expiry_date, message)

        _ver_suffix = f"  {APP_VERSION}" if APP_VERSION else ""
        self.root.title(f"WOODSOFT EXTEND{_ver_suffix}")

        # Set window icon
        try:
            icon_path = resource_path("light.ico")
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Cannot load icon: {e}")

        # Set window size - default and limits
        self.root.geometry("1000x650")
        self.root.minsize(900, 600)
        self.root.maxsize(1000, 650)
        
        # Prevent window from starting maximized
        self.root.state('normal')

        # Keep HOME window constraints so we can restore after opening full-screen modes
        self._home_geom = "1000x650"
        self._home_minsize = (900, 600)
        self._home_maxsize = (1000, 650)
        self.logo_img: ImageTk.PhotoImage | None = None
        self.search_img: ImageTk.PhotoImage | None = None
        self.icon1_img: ImageTk.PhotoImage | None = None
        self.icon2_img: ImageTk.PhotoImage | None = None
        self.icon3_img: ImageTk.PhotoImage | None = None

        self.flag_imgs: dict[str, ImageTk.PhotoImage] = {}
        self._lang_buttons: dict[str, tk.Label] = {}
        self._main_buttons: list[RoundedButton] = []

        self._opened_windows = []
        self._help_win = None
        self._help_editor_win = None

        # Hidden admin triggers
        self._logo_click_times: list[float] = []
        self._logo_label: tk.Label | None = None
        
        # Start with login screen
        self._show_login_screen()

    def _show_login_screen(self):
        """Build the login UI."""
        self._clear_window()
        self.root.title(self._get_app_title())
        self.root.configure(bg="white")
        
        # Language Switcher at Top Right
        lang_frame = tk.Frame(self.root, bg="white")
        lang_frame.place(relx=0.98, rely=0.02, anchor="ne")
        self._load_flag_images()
        for lang_code in ["vi", "en", "ru"]:
            btn = tk.Label(lang_frame, image=self.flag_imgs.get(lang_code), bg="white", cursor="hand2")
            btn.pack(side=tk.LEFT, padx=5)
            btn.bind("<Button-1>", lambda e, lc=lang_code: self._set_lang_login(lc))

        # Container
        login_frame = tk.Frame(self.root, bg="white")
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Logo
        try:
            img = Image.open(resource_path("logo.png"))
            w, h = img.size
            img = img.resize((int(w * 100 / h), 100), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            tk.Label(login_frame, image=self.logo_img, bg="white").pack(pady=(0, 40))
        except: pass
        
        # Load saved settings
        saved = self.auth.load_auth_settings()

        # Email
        tk.Label(login_frame, text=self.i18n.tr("Email"), bg="white", font=("Segoe UI", 10)).pack(anchor="w", padx=25)
        self.email_entry = tb.Entry(login_frame, width=40, font=("Segoe UI", 12))
        self.email_entry.pack(pady=(5, 15), padx=25)
        self.email_entry.insert(0, saved.get("email", "xdetector@gmail.com"))
        
        # Password
        tk.Label(login_frame, text=self.i18n.tr("Password"), bg="white", font=("Segoe UI", 10)).pack(anchor="w", padx=25)
        self.pass_entry = tb.Entry(login_frame, width=40, font=("Segoe UI", 12), show="*")
        self.pass_entry.pack(pady=(5, 10), padx=25)
        self.pass_entry.insert(0, saved.get("password", "@Dmin123"))
        
        # Remember Password Checkbox
        self.remember_var = tk.BooleanVar(value=saved.get("remember", False))
        cb = tb.Checkbutton(
            login_frame, 
            text=self.i18n.tr("Remember password"), 
            variable=self.remember_var,
            bootstyle="info"
        )
        cb.pack(anchor="w", padx=25, pady=(0, 15))

        # Error Label
        self.error_label = tk.Label(login_frame, text="", fg="red", bg="white", font=("Segoe UI", 10))
        self.error_label.pack()
        
        # Login Button
        self.login_btn = RoundedButton(
            login_frame,
            text=self.i18n.tr("Login"),
            command=self._handle_login,
            width=350,
            height=50
        )
        self.login_btn.pack(pady=10)

    def _set_lang_login(self, lang_code):
        self.i18n.set_lang(lang_code)
        self._show_login_screen()

    def _handle_login(self):
        email = self.email_entry.get()
        password = self.pass_entry.get()
        remember = self.remember_var.get()
        
        self.error_label.config(text=self.i18n.tr("Authenticating..."), fg="#00A8E8")
        self.root.update_idletasks()
        
        success, result = self.auth.login(email, password)
        if success:
            # Save credentials
            self.auth.save_auth_settings(email, password, remember)
            
            self.user_data = result.get("user")
            self.license_info = self.auth.get_license_info(self.user_data)
            self._build_ui()
            self.i18n.apply_to(self.root)
            
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(1000, lambda: self.root.attributes("-topmost", False))
            self.root.focus_force()
        else:
            self.error_label.config(text=self.i18n.tr(result), fg="red")

    def _clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def _get_app_title(self):
        """Return the application title."""
        base = self.i18n.tr("WOODSOFT EXTEND")
        return f"{base}  {APP_VERSION}" if APP_VERSION else base

    def _set_lang(self, lang_code: str):
        """Set language + apply + update flag UI."""
        try:
            if hasattr(self, "i18n") and self.i18n:
                self.i18n.set_lang(lang_code)
                self.i18n.apply_to(self.root)

                pass

            self._update_lang_button_highlight()
            self._update_button_texts()
        except Exception as e:
            print("[i18n] _set_lang error:", e)

    def _update_button_texts(self):
        """Update custom button texts after language change."""
        if len(self._main_buttons) >= 1:
            self._main_buttons[0].update_text(self.i18n.tr("Design Packing list từ BAZIS - Bao gói"))

    def _update_lang_button_highlight(self):
        """Highlight active language flag."""
        current_lang = getattr(self.i18n, "lang", "vi")
        for lang_code, btn in self._lang_buttons.items():
            if lang_code == current_lang:
                btn.configure(
                    relief="solid",
                    bd=1,
                    borderwidth=1,
                    highlightbackground="#c0c0c0",
                    highlightthickness=0
                )
            else:
                btn.configure(
                    relief="flat",
                    bd=0,
                    highlightbackground="white",
                    highlightthickness=0
                )

    def _load_flag_images(self):
        """Load language flag icons."""
        self.flag_imgs = {}
        flags = {
            "vi": "vietnamese.png",
            "en": "english.png",
            "ru": "russian.png",
        }
        FLAG_SIZE = (38, 38)
        for lang, filename in flags.items():
            try:
                img = Image.open(resource_path(filename)).convert("RGBA")
                bg = Image.new("RGBA", FLAG_SIZE, (255, 255, 255, 255))
                img = img.resize(FLAG_SIZE, Image.LANCZOS)
                bg.paste(img, (0, 0), img)
                self.flag_imgs[lang] = ImageTk.PhotoImage(bg)
            except Exception as e:
                print(f"[FLAG] Cannot load {filename}:", e)

    def _relax_root_constraints(self) -> None:
        try:
            self.root.update_idletasks()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
        except Exception:
            sw, sh = 1920, 1080

        try:
            self.root.minsize(1, 1)
        except Exception:
            pass
        try:
            self.root.maxsize(sw, sh)
        except Exception:
            pass

    def _restore_home_constraints(self) -> None:
        try:
            self.root.attributes("-fullscreen", False)
        except Exception:
            pass
        try:
            self.root.state('normal')
        except Exception:
            pass
        try:
            self.root.geometry(self._home_geom)
        except Exception:
            pass
        try:
            self.root.minsize(*self._home_minsize)
        except Exception:
            pass
        try:
            self.root.maxsize(*self._home_maxsize)
        except Exception:
            pass

    def _build_ui(self) -> None:
        self.root.configure(bg="white")
        self._load_flag_images()

        # ================= HEADER =================
        header = tk.Frame(self.root, bg="white", height=120)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)

        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=0)

        # ----- COLUMN 0: LOGO -----
        left_header = tk.Frame(header, bg="white")
        left_header.grid(row=0, column=0, sticky="w", padx=30, pady=15)

        try:
            img = Image.open(resource_path("logo.png"))
            w, h = img.size
            new_height = 75
            new_width = int(w * (new_height / h))
            img = img.resize((new_width, new_height), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            self._logo_label = tk.Label(left_header, image=self.logo_img, bg="white", cursor="arrow")
            self._logo_label.pack()
            self._logo_label.bind("<Button-1>", self._on_logo_click)
        except Exception as e:
            print("Logo error:", e)

        # ----- COLUMN 1: TITLE -----
        center_header = tk.Frame(header, bg="white")
        center_header.grid(row=0, column=1, sticky="nsew")

        title_container = tk.Frame(center_header, bg="white")
        title_container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            title_container,
            text=self.i18n.tr("WOODSOFT EXTEND"),
            bg="white",
            fg="#3D3D3D",
            font=("Segoe UI", 20, "bold"),
        ).pack()



        tk.Label(
            title_container,
            text=self.i18n.tr("Built Around Your Needs"),
            bg="white",
            fg="#5B6777",
            font=("Segoe UI", 10),
        ).pack()

        # ----- COLUMN 2: SEARCH & FLAGS -----
        right_header = tk.Frame(header, bg="white")
        right_header.grid(row=0, column=2, sticky="e", padx=30, pady=15)



        flags_frame = tk.Frame(right_header, bg="white")
        flags_frame.pack(side=tk.LEFT)

        for lang_code in ["vi", "en", "ru"]:
            flag_btn = tk.Label(
                flags_frame,
                image=self.flag_imgs.get(lang_code),
                bg="white",
                cursor="hand2",
                relief="flat",
                bd=0,
            )
            flag_btn.pack(side=tk.LEFT, padx=3)
            flag_btn.bind("<Button-1>", lambda e, lc=lang_code: self._set_lang(lc))
            self._lang_buttons[lang_code] = flag_btn

        self._update_lang_button_highlight()

        try:
            self.root.bind_all("<Control-Shift-E>", lambda e: self._open_help_editor())
        except Exception:
            pass

        # ================= DIVIDER 1 =================
        divider1 = tk.Canvas(self.root, height=1, bg="#CBD5E1", highlightthickness=0)
        divider1.pack(side=tk.TOP, fill=tk.X)
        divider1.create_line(0, 0, 2000, 0, fill="#D8DEE6", width=2)

        # ================= FOOTER =================
        footer = tk.Frame(self.root, bg="#F0F3F7", height=56)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        footer.pack_propagate(False)

        tk.Label(
            footer,
            text=self.i18n.tr("Developed by Anhltv@woodsoft.vn"),
            bg="#F0F3F7",
            fg="#888888",
            font=("Segoe UI", 9),
        ).pack(side=tk.LEFT, padx=30)
        
        if self.license_info[1]:
            expiry_text = self.i18n.tr("License expires on: ") + self.license_info[1]
            tk.Label(
                footer,
                text=expiry_text,
                bg="#F0F3F7",
                fg="#00A8E8",
                font=("Segoe UI", 9, "bold"),
            ).pack(side=tk.RIGHT, padx=30)

        # ================= DIVIDER 2 =================
        divider2 = tk.Canvas(self.root, height=1, bg="#D8DEE6", highlightthickness=0)
        divider2.pack(side=tk.BOTTOM, fill=tk.X)
        divider2.create_line(0, 0, 2000, 0, fill="#D8DEE6", width=1)

        # ================= BODY =================
        body = tk.Frame(self.root, bg="white")
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        content_container = tk.Frame(body, bg="white")
        content_container.place(relx=0.5, rely=0.5, anchor="center")

        if not self.license_info[0]:
            warning_frame = tk.Frame(content_container, bg="white")
            warning_frame.pack()
            
            tk.Label(warning_frame, text="⚠️", font=("Segoe UI", 48), bg="white").pack()
            
            error_msg = self.license_info[2]
            if error_msg in ("License expired", "Service not activated"):
                error_msg = self.i18n.tr("Service not activated or expired")
                
            tk.Label(
                warning_frame,
                text=error_msg,
                font=("Segoe UI", 16, "bold"),
                fg="#E74C3C",
                bg="white",
                wraplength=600
            ).pack(pady=10)
            return

        buttons_container = tk.Frame(content_container, bg="white")
        buttons_container.pack()

        # Load icons
        try:
            img1 = Image.open(resource_path("icon1.png"))
            img1.thumbnail((110, 110), Image.LANCZOS)
            self.icon1_img = ImageTk.PhotoImage(img1)
        except Exception: self.icon1_img = None

        self._main_buttons.clear()

        # Button 1
        btn1 = RoundedButton(
            buttons_container,
            text=self.i18n.tr("Design Packing list từ BAZIS - Bao gói"),
            command=self.open_mode1,
            width=560,
            height=52,
            radius=14
        )
        btn1.grid(row=0, column=0, pady=18)
        self._main_buttons.append(btn1)
        if self.icon1_img:
            icon1 = tk.Label(body, image=self.icon1_img, bg="white")
            icon1.place(in_=btn1, relx=-0.01, rely=0.3, anchor="e", x=-35)

    def _open_help(self) -> None:
        """Open Help window."""
        if HelpWindow is None:
            import tkinter.messagebox as mbox
            mbox.showinfo(
                self.i18n.tr("Help"),
                self.i18n.tr("Chức năng trợ giúp đang được xây dựng.")
            )
            return

        try:
            if self._help_win is not None and self._help_win.winfo_exists():
                self._help_win.lift()
                self._help_win.focus_force()
                return
        except Exception:
            self._help_win = None

        try:
            project_root = os.path.dirname(os.path.abspath(__file__))
            self._help_win = HelpWindow(self.root, self.i18n, project_root=project_root)
            self._help_win.protocol("WM_DELETE_WINDOW", self._on_close_help)
        except Exception as e:
            print(f"[HELP] Failed to open HelpWindow: {e}")

    def _on_close_help(self) -> None:
        try:
            if self._help_win is not None and self._help_win.winfo_exists():
                self._help_win.destroy()
        except Exception: pass
        self._help_win = None

    def _open_help_editor(self) -> None:
        """Open Help Editor window."""
        if HelpEditorWindow is None:
            return
        try:
            if self._help_editor_win is not None and self._help_editor_win.winfo_exists():
                self._help_editor_win.lift()
                self._help_editor_win.focus_force()
                return
        except Exception:
            self._help_editor_win = None

        try:
            project_root = os.path.dirname(os.path.abspath(__file__))
            self._help_editor_win = HelpEditorWindow(self.root, self.i18n, project_root=project_root)
            self._help_editor_win.protocol("WM_DELETE_WINDOW", self._on_close_help_editor)
        except Exception as e:
            print(f"[HELP_EDITOR] Failed to open: {e}")

    def _on_close_help_editor(self) -> None:
        try:
            if self._help_editor_win is not None and self._help_editor_win.winfo_exists():
                self._help_editor_win.destroy()
        except Exception: pass
        self._help_editor_win = None

    def _on_logo_click(self, event=None) -> None:
        """Hidden admin trick: click logo 5 times to open Help Editor."""
        try:
            now = time.time()
            self._logo_click_times.append(now)
            self._logo_click_times = [t for t in self._logo_click_times if now - t <= 2.0]
            if len(self._logo_click_times) >= 5:
                self._logo_click_times.clear()
                self._open_help_editor()
        except Exception:
            self._logo_click_times = []

    def open_mode1(self) -> None:
        self.mode1_win = Mode1Window(self.root, i18n=self.i18n)
        self._opened_windows.append(self.mode1_win)
        self.mode1_win._on_home_callback = self._rebuild_home

    def _rebuild_home(self) -> None:
        self._restore_home_constraints()
        for w in list(self.root.winfo_children()):
            try:
                w.destroy()
            except Exception: pass
        self._opened_windows = []
        self._help_win = None
        self._lang_buttons = {}
        self._main_buttons = []
        self._build_ui()
        self.i18n.apply_to(self.root)


def main() -> None:
    app_win = tb.Window(themename="flatly")
    MainLauncher(app_win)
    app_win.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        import tkinter.messagebox as mbox
        error_msg = f"Application failed to start:\n\n{e}\n\n{traceback.format_exc()}"
        print(error_msg)
        try:
            root = tk.Tk()
            root.withdraw()
            mbox.showerror("Startup Error", error_msg)
            root.destroy()
        except: pass

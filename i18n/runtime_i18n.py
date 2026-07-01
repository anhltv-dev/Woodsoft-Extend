from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, Any, Optional

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None


def _norm(s: str) -> str:
    return (s or "").strip()


@dataclass
class LocalePack:
    lang: str
    name: str
    mapping: Dict[str, str]


class RuntimeI18n:
    """Runtime i18n for Tkinter/ttkbootstrap apps using per-language dictionaries.

    Strategy:
    - Keep the original displayed text as the *base string* (usually Vietnamese).
    - On first apply, cache base strings on each widget (title/text/headings/tabs).
    - When language changes, traverse widget tree and replace displayed strings
      using mapping[base] -> translated. Missing keys fall back to base.

    Notes:
    - filedialog/messagebox strings are NOT part of widget tree; translate those at call-time.
    - ttk.Notebook tab titles also need explicit handling; supported here.
    """

    def __init__(self, locales_dir: str, default_lang: str = "vi"):
        self.locales_dir = locales_dir
        self.packs: Dict[str, LocalePack] = {}
        self.lang = default_lang
        self.load_all()
        if default_lang not in self.packs and self.packs:
            self.lang = next(iter(self.packs.keys()))

        # Expose the most recently created instance as the global singleton
        # so existing code that instantiates RuntimeI18n() directly remains compatible.
        global _GLOBAL_I18N, _GLOBAL_LOCALES_DIR
        _GLOBAL_LOCALES_DIR = os.path.abspath(self.locales_dir)
        _GLOBAL_I18N = self

    def load_all(self) -> None:
        self.packs.clear()
        if not os.path.isdir(self.locales_dir):
            return
        for fn in os.listdir(self.locales_dir):
            if not fn.lower().endswith(".json"):
                continue
            path = os.path.join(self.locales_dir, fn)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                lang = data.get("__lang__", os.path.splitext(fn)[0])
                name = data.get("__name__", lang)
                mapping = {k: v for k, v in data.items() if not k.startswith("__")}
                self.packs[lang] = LocalePack(lang=lang, name=name, mapping=mapping)
            except Exception:
                continue

    def available(self) -> Dict[str, str]:
        return {k: v.name for k, v in self.packs.items()}

    def set_lang(self, lang: str) -> None:
        if lang in self.packs:
            self.lang = lang

    def tr(self, base_text: str) -> str:
        base_text = _norm(base_text)
        pack = self.packs.get(self.lang)
        if not pack:
            return base_text
        return pack.mapping.get(base_text, base_text)

    # -------------------- APPLY --------------------
    def apply_to(self, root_widget: Any) -> None:
        if tk is None:
            return
        self._apply_window_title(root_widget)
        self._walk(root_widget)

    def _apply_window_title(self, w: Any) -> None:
        try:
            base = getattr(w, "_i18n_base_title", None)
            if base is None:
                base = w.title()
                setattr(w, "_i18n_base_title", base)
            w.title(self.tr(base))
        except Exception:
            pass

    def _walk(self, w: Any) -> None:
        self._apply_widget_text(w)
        self._apply_treeview_headings(w)
        self._apply_notebook_tabs(w)

        try:
            for child in w.winfo_children():
                self._walk(child)
        except Exception:
            return

    # ✅ PATCHED: translate widgets even if they were created after an earlier apply_to()
    def _apply_widget_text(self, w: Any) -> None:
        # Many widgets support cget/configure for "text"
        try:
            cur = w.cget("text")
        except Exception:
            return

        if not cur:
            return

        try:
            # If base is not cached yet, treat current text as base.
            base = getattr(w, "_i18n_base_text", None)
            if base is None:
                base = cur
                setattr(w, "_i18n_base_text", base)

            new_text = self.tr(base)

            if new_text and new_text != cur:
                try:
                    w.configure(text=new_text)
                except Exception:
                    pass
        except Exception:
            pass

    def _apply_treeview_headings(self, w: Any) -> None:
        if ttk is None:
            return
        if not isinstance(w, ttk.Treeview):
            return

        try:
            cols = list(w["columns"])
        except Exception:
            cols = []

        cols = ["#0"] + cols

        base_map: Optional[Dict[str, str]] = getattr(w, "_i18n_base_headings", None)
        if base_map is None:
            base_map = {}
            for c in cols:
                try:
                    base_map[c] = w.heading(c).get("text", "")
                except Exception:
                    base_map[c] = ""
            setattr(w, "_i18n_base_headings", base_map)

        for c in cols:
            base_text = base_map.get(c, "")
            if not base_text:
                continue
            new_text = self.tr(base_text)
            try:
                w.heading(c, text=new_text)
            except Exception:
                pass

    def _apply_notebook_tabs(self, w: Any) -> None:
        if ttk is None:
            return
        if not isinstance(w, ttk.Notebook):
            return

        base_tabs: Optional[Dict[str, str]] = getattr(w, "_i18n_base_tabs", None)
        if base_tabs is None:
            base_tabs = {}
            try:
                for tab_id in w.tabs():
                    base_tabs[tab_id] = w.tab(tab_id).get("text", "")
            except Exception:
                pass
            setattr(w, "_i18n_base_tabs", base_tabs)

        try:
            for tab_id, base_text in base_tabs.items():
                if not base_text:
                    continue
                w.tab(tab_id, text=self.tr(base_text))
        except Exception:
            pass


# -------------------- GLOBAL SINGLETON --------------------
# All modules must share the same i18n instance (same locales_dir).
_GLOBAL_I18N: Optional[RuntimeI18n] = None
_GLOBAL_LOCALES_DIR: Optional[str] = None


def get_i18n(locales_dir: str, default_lang: str = "vi") -> RuntimeI18n:
    """Return a process-wide singleton RuntimeI18n."""
    global _GLOBAL_I18N, _GLOBAL_LOCALES_DIR
    locales_dir = os.path.abspath(locales_dir)
    if _GLOBAL_I18N is None or _GLOBAL_LOCALES_DIR != locales_dir:
        _GLOBAL_LOCALES_DIR = locales_dir
        _GLOBAL_I18N = RuntimeI18n(locales_dir, default_lang=default_lang)
    return _GLOBAL_I18N


def tr(base_text: str) -> str:
    """Global translation helper using the singleton."""
    global _GLOBAL_I18N
    if _GLOBAL_I18N is not None:
        return _GLOBAL_I18N.tr(base_text)
    return (base_text or "").strip()

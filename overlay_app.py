"""Diablo II: Resurrected desktop overlay (Windows).

Features:
- Auto-detects and attaches to d2r.exe window
- Transparent always-on-top overlay that tracks game window position/size
- Adjustable transparency slider
- Notes, timer, and simple status panel

Run on Windows:
    pip install -r requirements.txt
    python overlay_app.py
"""

from __future__ import annotations

import ctypes
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk

import psutil

try:
    import win32con
    import win32gui
    import win32process
except ImportError as exc:  # pragma: no cover - runtime dependency check
    raise SystemExit(
        "This app requires pywin32. Install dependencies with: pip install -r requirements.txt"
    ) from exc


D2R_EXE_NAME = "d2r.exe"
POLL_SECONDS = 0.35


@dataclass
class WindowBinding:
    hwnd: int
    pid: int


class D2ROverlayApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("D2R Python Overlay")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#141414")
        self.root.attributes("-alpha", 0.82)

        self.bound: WindowBinding | None = None
        self.running = True

        self.timer_start: float | None = None
        self.timer_job: str | None = None

        self.status_text = tk.StringVar(value="Searching for d2r.exe ...")
        self.alpha_text = tk.StringVar(value="Overlay Transparency: 82%")
        self.timer_text = tk.StringVar(value="Timer: stopped")

        self._build_ui()
        self._set_taskbar_hidden()

        self.worker = threading.Thread(target=self._attach_loop, daemon=True)
        self.worker.start()

        self.root.protocol("WM_DELETE_WINDOW", self._shutdown)

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=10)
        container.pack(fill="both", expand=True)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background="#141414")
        style.configure("TLabel", background="#141414", foreground="#f5deb3")
        style.configure("TButton", foreground="#f5deb3", background="#3f2310")

        ttk.Label(container, text="D2R Overlay (Auto-Attach)").pack(anchor="w")
        ttk.Label(container, textvariable=self.status_text).pack(anchor="w", pady=(0, 8))

        ttk.Label(container, text="Run Notes").pack(anchor="w")
        self.notes = tk.Text(container, height=8, width=40, bg="#111", fg="#f5deb3", insertbackground="#f5deb3")
        self.notes.pack(fill="x", pady=(0, 8))

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(0, 8))

        ttk.Button(actions, text="+ Add Note Stamp", command=self._add_note_stamp).pack(side="left", padx=(0, 6))
        self.timer_button = ttk.Button(actions, text="Start Timer", command=self._toggle_timer)
        self.timer_button.pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Clear Notes", command=self._clear_notes).pack(side="left")

        ttk.Label(container, textvariable=self.timer_text).pack(anchor="w", pady=(0, 8))

        ttk.Label(container, textvariable=self.alpha_text).pack(anchor="w")
        self.alpha_scale = ttk.Scale(container, from_=25, to=100, orient="horizontal", command=self._update_alpha)
        self.alpha_scale.set(82)
        self.alpha_scale.pack(fill="x")

        footer = ttk.Frame(container)
        footer.pack(fill="x", pady=(10, 0))
        ttk.Button(footer, text="Hide/Show (F10)", command=self._toggle_visibility).pack(side="left")
        ttk.Button(footer, text="Exit", command=self._shutdown).pack(side="right")

        self.root.bind("<F10>", lambda _e: self._toggle_visibility())

    def _set_taskbar_hidden(self) -> None:
        hwnd = self.root.winfo_id()
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        ex_style |= win32con.WS_EX_TOOLWINDOW
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

    def _toggle_visibility(self) -> None:
        if self.root.state() == "withdrawn":
            self.root.deiconify()
        else:
            self.root.withdraw()

    def _add_note_stamp(self) -> None:
        stamp = time.strftime("%H:%M:%S")
        prefix = "" if self.notes.index("end-1c") == "1.0" else "\n"
        self.notes.insert("end", f"{prefix}[{stamp}] ")
        self.notes.see("end")

    def _clear_notes(self) -> None:
        self.notes.delete("1.0", "end")

    def _toggle_timer(self) -> None:
        if self.timer_start is None:
            self.timer_start = time.time()
            self.timer_button.configure(text="Stop Timer")
            self._tick_timer()
            return

        self.timer_start = None
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        self.timer_text.set("Timer: stopped")
        self.timer_button.configure(text="Start Timer")

    def _tick_timer(self) -> None:
        if self.timer_start is None:
            return

        elapsed = int(time.time() - self.timer_start)
        minutes, seconds = divmod(elapsed, 60)
        self.timer_text.set(f"Timer: {minutes:02d}:{seconds:02d}")
        self.timer_job = self.root.after(250, self._tick_timer)

    def _update_alpha(self, value: str) -> None:
        pct = max(25, min(100, int(float(value))))
        self.root.attributes("-alpha", pct / 100.0)
        self.alpha_text.set(f"Overlay Transparency: {pct}%")

    def _attach_loop(self) -> None:
        while self.running:
            try:
                binding = self._find_d2r_window()
                if binding is None:
                    self.bound = None
                    self.root.after(0, lambda: self.status_text.set("Searching for d2r.exe ..."))
                    time.sleep(POLL_SECONDS)
                    continue

                if self.bound is None or self.bound.hwnd != binding.hwnd:
                    self.bound = binding
                    self.root.after(0, lambda: self.status_text.set("Attached to d2r.exe"))

                rect = win32gui.GetWindowRect(binding.hwnd)
                left, top, right, bottom = rect
                width = max(300, right - left)
                height = max(200, bottom - top)

                self.root.after(0, lambda l=left, t=top, w=width, h=height: self._sync_overlay_bounds(l, t, w, h))
            except Exception as exc:  # pragma: no cover - defensive runtime guard
                self.root.after(0, lambda e=exc: self.status_text.set(f"Attach error: {e}"))
            time.sleep(POLL_SECONDS)

    def _sync_overlay_bounds(self, left: int, top: int, width: int, height: int) -> None:
        self.root.geometry(f"{width}x{height}+{left}+{top}")

    def _find_d2r_window(self) -> WindowBinding | None:
        pids = {
            proc.info["pid"]
            for proc in psutil.process_iter(["pid", "name"])
            if (proc.info.get("name") or "").lower() == D2R_EXE_NAME
        }
        if not pids:
            return None

        matches: list[WindowBinding] = []

        def callback(hwnd: int, _extra: int) -> bool:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            if win32gui.GetParent(hwnd) != 0:
                return True
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid in pids:
                matches.append(WindowBinding(hwnd=hwnd, pid=pid))
            return True

        win32gui.EnumWindows(callback, 0)
        return matches[0] if matches else None

    def _shutdown(self) -> None:
        self.running = False
        self.timer_start = None
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def _enable_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


if __name__ == "__main__":
    _enable_dpi_awareness()
    app = D2ROverlayApp()
    app.run()

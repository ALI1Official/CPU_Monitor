"""
Real-Time CPU Monitor
----------------------
Made by ALI1
"""

import tkinter as tk
from tkinter import ttk
import psutil
from collections import deque

UPDATE_INTERVAL_MS = 1000       # how often to refresh, in milliseconds
HISTORY_LENGTH = 60              # how many seconds of history the graph keeps

BG = "#1e212a"
PANEL = "#272b36"
TEXT = "#f0f1f5"
MUTED = "#9aa0ab"
ACCENT = "#6b85ff"
BAR_BG = "#3a3f4d"


class CPUMonitor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Real-Time CPU Monitor")
        self.configure(bg=BG)
        self.geometry("560x640")
        self.minsize(480, 560)

        self.core_count = psutil.cpu_count(logical=True) or 1
        self.history = deque([0] * HISTORY_LENGTH, maxlen=HISTORY_LENGTH)

        self._build_layout()
        self._schedule_update()

    # ---------- UI construction ----------

    def _build_layout(self):
        header = tk.Label(
            self, text="CPU Monitor", font=("Segoe UI", 18, "bold"),
            bg=BG, fg=TEXT
        )
        header.pack(pady=(16, 4))

        self.overall_label = tk.Label(
            self, text="0%", font=("Segoe UI", 36, "bold"), bg=BG, fg=ACCENT
        )
        self.overall_label.pack()

        self.freq_label = tk.Label(
            self, text="", font=("Segoe UI", 10), bg=BG, fg=MUTED
        )
        self.freq_label.pack(pady=(0, 10))

        # Rolling history graph
        self.graph = tk.Canvas(self, width=520, height=90, bg=PANEL, highlightthickness=0)
        self.graph.pack(pady=(0, 14))

        # Per-core bars
        core_frame = tk.Frame(self, bg=BG)
        core_frame.pack(fill="both", expand=False, padx=20)

        tk.Label(
            core_frame, text="Per-Core Usage", font=("Segoe UI", 11, "bold"),
            bg=BG, fg=TEXT
        ).pack(anchor="w", pady=(0, 6))

        self.core_bars = []
        self.core_labels = []
        for i in range(self.core_count):
            row = tk.Frame(core_frame, bg=BG)
            row.pack(fill="x", pady=2)

            label = tk.Label(row, text=f"Core {i}", width=8, anchor="w",
                              font=("Segoe UI", 9), bg=BG, fg=MUTED)
            label.pack(side="left")

            bar_bg = tk.Canvas(row, height=14, bg=BAR_BG, highlightthickness=0)
            bar_bg.pack(side="left", fill="x", expand=True, padx=(6, 6))

            pct_label = tk.Label(row, text="0%", width=5, anchor="e",
                                  font=("Segoe UI", 9), bg=BG, fg=TEXT)
            pct_label.pack(side="left")

            self.core_bars.append(bar_bg)
            self.core_labels.append(pct_label)

        # Memory panel
        stats_frame = tk.Frame(self, bg=PANEL)
        stats_frame.pack(fill="x", padx=20, pady=(18, 10))

        self.mem_label = tk.Label(
            stats_frame, text="Memory: —", font=("Segoe UI", 10),
            bg=PANEL, fg=TEXT, anchor="w", justify="left", padx=12, pady=10
        )
        self.mem_label.pack(fill="x", pady=(0, 10))

    # ---------- Data refresh ----------

    def _schedule_update(self):
        self._update_once()
        self.after(UPDATE_INTERVAL_MS, self._schedule_update)

    def _update_once(self):
        overall = psutil.cpu_percent(interval=None)
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        # Note: first call after startup may report 0.0 for both; this
        # self-corrects on the next tick since no interval blocking is used.

        self.overall_label.config(text=f"{overall:.0f}%")
        self.history.append(overall)
        self._draw_graph()

        self._update_core_bars(per_core)
        self._update_frequency()
        self._update_memory()


    def _update_core_bars(self, per_core):
        for i, pct in enumerate(per_core):
            if i >= len(self.core_bars):
                break
            canvas = self.core_bars[i]
            canvas.delete("fill")
            width = canvas.winfo_width() or 200
            fill_width = max(2, int(width * pct / 100))
            color = self._color_for_pct(pct)
            canvas.create_rectangle(0, 0, fill_width, 14, fill=color, outline="", tags="fill")
            self.core_labels[i].config(text=f"{pct:.0f}%")

    def _update_frequency(self):
        try:
            freq = psutil.cpu_freq()
            if freq:
                self.freq_label.config(text=f"{freq.current:.0f} MHz  (max {freq.max:.0f} MHz)")
            else:
                self.freq_label.config(text="Frequency: not available on this system")
        except Exception:
            self.freq_label.config(text="Frequency: not available on this system")

    def _update_memory(self):
        mem = psutil.virtual_memory()
        used_gb = mem.used / (1024 ** 3)
        total_gb = mem.total / (1024 ** 3)
        self.mem_label.config(
            text=f"Memory: {mem.percent:.0f}%  ({used_gb:.1f} GB / {total_gb:.1f} GB)"
        )

    # ---------- Graph drawing ----------

    def _draw_graph(self):
        self.graph.delete("all")
        w = self.graph.winfo_width() or 520
        h = self.graph.winfo_height() or 90

        # gridlines
        for frac in (0.25, 0.5, 0.75):
            y = h * (1 - frac)
            self.graph.create_line(0, y, w, y, fill="#3a3f4d")

        points = []
        step = w / (HISTORY_LENGTH - 1)
        for i, value in enumerate(self.history):
            x = i * step
            y = h - (value / 100) * h
            points.extend([x, y])

        if len(points) >= 4:
            self.graph.create_line(*points, fill=ACCENT, width=2, smooth=True)

    @staticmethod
    def _color_for_pct(pct):
        if pct < 50:
            return "#4fcf8a"   # green
        elif pct < 80:
            return "#f5c451"   # amber
        else:
            return "#ff6b6b"   # red


if __name__ == "__main__":
    app = CPUMonitor()
    app.mainloop()

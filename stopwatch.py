"""
Study Stopwatch & Daily Tracker
--------------------------------
A stopwatch app: Start/Stop/Reset.
Each time "Stop" is pressed, the elapsed time is added to that day's
total study time and saved to study_log.json (persistent storage).
The bottom section shows a summary table of the last 7 days (a simple
"calendar" view).
"""

import tkinter as tk
from tkinter import ttk
import json
import os
from datetime import datetime, timedelta

# ---------- Constants ----------
DATA_FILE = "study_log.json"
DAYS_TO_SHOW = 7

# ---------- Themes ----------
THEMES = {
    "dark": {
        "BG": "#1e1e1e",
        "FG": "#ffffff",
        "BTN_BG": "#3c3c3c",
        "BTN_FG": "#ffffff",
        "ENTRY_BG": "#2d2d2d",
        "ENTRY_FG": "#ffffff",
        "TABLE_BG": "#2d2d2d",
        "TABLE_FG": "#ffffff",
        "ACCENT": "#4ec9b0",
        "ICON": "☀️",
    },
    "light": {
        "BG": "#f5f5f5",
        "FG": "#1e1e1e",
        "BTN_BG": "#e0e0e0",
        "BTN_FG": "#1e1e1e",
        "ENTRY_BG": "#ffffff",
        "ENTRY_FG": "#1e1e1e",
        "TABLE_BG": "#ffffff",
        "TABLE_FG": "#1e1e1e",
        "ACCENT": "#0f6e56",
        "ICON": "🌙",
    },
}


# ---------- Data layer ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}


def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=2)


def add_seconds_to_today(seconds, category="General"):
    data = load_data()
    today_str = datetime.now().strftime("%Y-%m-%d")
    day_data = data.get(today_str, {})
    if not isinstance(day_data, dict):
        day_data = {"General": day_data}
    day_data[category] = day_data.get(category, 0) + seconds
    data[today_str] = day_data
    save_data(data)
    return data


def get_day_total(day_data):
    if isinstance(day_data, dict):
        return sum(day_data.values())
    return day_data


def calculate_streak(data):
    streak = 0
    today = datetime.now()
    for i in range(365):
        day_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if get_day_total(data.get(day_str, {})) > 0:
            streak += 1
        else:
            break
    return streak


# ---------- Application ----------
class StudyTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Study Stopwatch")
        self.root.geometry("650x680")
        self.root.resizable(False, False)

        self.running = False
        self.elapsed_seconds = 0
        self.timer_job = None
        self.daily_goal_seconds = None
        self.current_theme = "dark"

        self._apply_ttk_style()

        canvas = tk.Canvas(self.root, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

        # Store references to all themed widgets so we can recolor them on toggle
        self._themed_labels = []
        self._themed_buttons = []
        self._themed_entries = []
        self._themed_frames = []
        self.canvas = canvas

        self.build_widgets()
        self._apply_theme()
        self.refresh_summary_table()

    def _apply_ttk_style(self):
        t = THEMES[self.current_theme]
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=t["TABLE_BG"], foreground=t["TABLE_FG"],
                        fieldbackground=t["TABLE_BG"], rowheight=25)
        style.configure("Treeview.Heading", background=t["BTN_BG"], foreground=t["FG"])
        style.configure("TSeparator", background="#555555")
        style.configure("Vertical.TScrollbar", background=t["BTN_BG"], troughcolor=t["BG"])
        style.configure("TProgressbar", troughcolor=t["BTN_BG"], background=t["ACCENT"])

    def _apply_theme(self):
        """Recolors every widget according to the current theme."""
        t = THEMES[self.current_theme]
        self.root.configure(bg=t["BG"])
        self.canvas.configure(bg=t["BG"])
        self.scrollable_frame.configure(bg=t["BG"])

        for frame in self._themed_frames:
            frame.configure(bg=t["BG"])
        for label, role in self._themed_labels:
            fg = t["ACCENT"] if role == "accent" else t["FG"]
            label.configure(bg=t["BG"], fg=fg)
        for btn in self._themed_buttons:
            btn.configure(bg=t["BTN_BG"], fg=t["BTN_FG"])
        for entry in self._themed_entries:
            entry.configure(bg=t["ENTRY_BG"], fg=t["ENTRY_FG"], insertbackground=t["FG"])

        self._apply_ttk_style()
        self.theme_button.configure(text=t["ICON"], bg=t["BTN_BG"], fg=t["BTN_FG"])

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self._apply_theme()

    def _label(self, parent, role="normal", **kwargs):
        """Helper: creates a Label and registers it for theme updates."""
        lbl = tk.Label(parent, **kwargs)
        self._themed_labels.append((lbl, role))
        return lbl

    def _button(self, parent, **kwargs):
        btn = tk.Button(parent, **kwargs)
        self._themed_buttons.append(btn)
        return btn

    def _entry(self, parent, **kwargs):
        ent = tk.Entry(parent, **kwargs)
        self._themed_entries.append(ent)
        return ent

    def _frame(self, parent, **kwargs):
        frm = tk.Frame(parent, **kwargs)
        self._themed_frames.append(frm)
        return frm

    def build_widgets(self):
        # Theme toggle button (top right)
        top_bar = self._frame(self.scrollable_frame)
        top_bar.pack(fill="x", padx=10, pady=(10, 0))
        self.theme_button = tk.Button(top_bar, text="☀️", font=("Arial", 14),
                                       command=self.toggle_theme, relief="flat", cursor="hand2")
        self._themed_buttons.append(self.theme_button)
        self.theme_button.pack(side="right")

        self._label(self.scrollable_frame, text="Study Stopwatch",
                    font=("Arial", 18, "bold"), role="accent").pack(pady=(5, 10))

        self.time_label = self._label(self.scrollable_frame, text="00:00:00", font=("Consolas", 48))
        self.time_label.pack(pady=10)

        category_frame = self._frame(self.scrollable_frame)
        category_frame.pack(pady=(0, 5))
        self._label(category_frame, text="Category:").grid(row=0, column=0, padx=5)
        self.timer_category_entry = self._entry(category_frame, width=15)
        self.timer_category_entry.grid(row=0, column=1, padx=5)
        self.timer_category_entry.insert(0, "General")

        button_frame = self._frame(self.scrollable_frame)
        button_frame.pack(pady=10)
        self.start_button = self._button(button_frame, text="Start", width=10, command=self.start_timer)
        self.start_button.grid(row=0, column=0, padx=5)
        self.stop_button = self._button(button_frame, text="Stop", width=10,
                                         command=self.stop_timer, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=5)
        self.reset_button = self._button(button_frame, text="Reset", width=10, command=self.reset_timer)
        self.reset_button.grid(row=0, column=2, padx=5)

        ttk.Separator(self.scrollable_frame, orient="horizontal").pack(fill="x", pady=20, padx=20)

        self._label(self.scrollable_frame, text="Last 7 Days Summary",
                    font=("Arial", 14, "bold")).pack()

        self.tree = ttk.Treeview(self.scrollable_frame, columns=("date", "duration"),
                                  show="headings", height=7)
        self.tree.heading("date", text="Date")
        self.tree.heading("duration", text="Duration")
        self.tree.column("date", width=250, anchor="center")
        self.tree.column("duration", width=250, anchor="center")
        self.tree.pack(pady=10)

        self.total_label = self._label(self.scrollable_frame, text="7-Day Total: 0h 0m 0s",
                                        font=("Arial", 12, "bold"))
        self.total_label.pack(pady=(0, 5))

        self.average_label = self._label(self.scrollable_frame, text="Daily Average: 0h 0m 0s",
                                          font=("Arial", 12))
        self.average_label.pack(pady=(0, 5))

        self.streak_label = self._label(self.scrollable_frame, text="🔥 Streak: 0 days",
                                         font=("Arial", 12, "bold"), role="accent")
        self.streak_label.pack(pady=(0, 5))

        self.category_breakdown_label = self._label(self.scrollable_frame, text="",
                                                     font=("Arial", 11), justify="center",
                                                     wraplength=600)
        self.category_breakdown_label.pack(pady=(0, 5))

        ttk.Separator(self.scrollable_frame, orient="horizontal").pack(fill="x", pady=(10, 10), padx=20)

        goal_frame = self._frame(self.scrollable_frame)
        goal_frame.pack(pady=5)
        self._label(goal_frame, text="Daily goal (hours):").grid(row=0, column=0, padx=5)
        self.goal_entry = self._entry(goal_frame, width=6)
        self.goal_entry.grid(row=0, column=1, padx=5)
        self._button(goal_frame, text="Set Goal", command=self.set_daily_goal).grid(row=0, column=2, padx=5)

        self.goal_status_label = self._label(self.scrollable_frame, text="No goal set yet.",
                                              font=("Arial", 12, "bold"))
        self.goal_status_label.pack(pady=(5, 5))

        self.goal_progress_bar = ttk.Progressbar(self.scrollable_frame, length=300,
                                                  mode="determinate", maximum=100)
        self.goal_progress_bar.pack(pady=(0, 10))

        ttk.Separator(self.scrollable_frame, orient="horizontal").pack(fill="x", pady=(10, 10), padx=20)

        self._label(self.scrollable_frame, text="Add Manual Study Time",
                    font=("Arial", 13, "bold")).pack()

        manual_frame = self._frame(self.scrollable_frame)
        manual_frame.pack(pady=10)
        self._label(manual_frame, text="Minutes studied:").grid(row=0, column=0, padx=5)
        self.manual_entry = self._entry(manual_frame, width=8)
        self.manual_entry.grid(row=0, column=1, padx=5)
        self._label(manual_frame, text="Category:").grid(row=0, column=2, padx=5)
        self.manual_category_entry = self._entry(manual_frame, width=12)
        self.manual_category_entry.grid(row=0, column=3, padx=5)
        self.manual_category_entry.insert(0, "General")
        self._button(manual_frame, text="Add to Today",
                     command=self.add_manual_time).grid(row=0, column=4, padx=5)

        self.manual_feedback_label = self._label(self.scrollable_frame, text="")
        self.manual_feedback_label.pack(pady=(0, 20))

    # ---------- Stopwatch logic ----------
    def start_timer(self):
        if self.running:
            return
        self.running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.tick()

    def tick(self):
        if not self.running:
            return
        self.elapsed_seconds += 1
        self.update_time_label()
        self.timer_job = self.root.after(1000, self.tick)

    def stop_timer(self):
        if not self.running:
            return
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        if self.timer_job is not None:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        if self.elapsed_seconds > 0:
            category = self.timer_category_entry.get().strip() or "General"
            add_seconds_to_today(self.elapsed_seconds, category)
            self.refresh_summary_table()
            self.check_goal_status()
        self.elapsed_seconds = 0
        self.update_time_label()

    def reset_timer(self):
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        if self.timer_job is not None:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        self.elapsed_seconds = 0
        self.update_time_label()

    # ---------- Manual time entry ----------
    def add_manual_time(self):
        raw_value = self.manual_entry.get()
        try:
            minutes = int(raw_value)
        except ValueError:
            self.manual_feedback_label.config(text="Please enter a whole number.", fg="red")
            return
        if minutes <= 0:
            self.manual_feedback_label.config(text="Minutes must be greater than 0.", fg="red")
            return
        seconds = minutes * 60
        category = self.manual_category_entry.get().strip() or "General"
        add_seconds_to_today(seconds, category)
        self.refresh_summary_table()
        self.check_goal_status()
        self.manual_feedback_label.config(text=f"Added {minutes} minute(s) to today.", fg="green")
        self.manual_entry.delete(0, tk.END)

    # ---------- Daily goal ----------
    def set_daily_goal(self):
        raw_value = self.goal_entry.get()
        try:
            hours = float(raw_value)
        except ValueError:
            self.goal_status_label.config(text="Please enter a valid number of hours.", fg="red")
            return
        if hours <= 0:
            self.goal_status_label.config(text="Goal must be greater than 0.", fg="red")
            return
        self.daily_goal_seconds = int(hours * 3600)
        self.check_goal_status()

    def check_goal_status(self):
        if self.daily_goal_seconds is None:
            self.goal_status_label.config(text="No goal set yet.",
                                           fg=THEMES[self.current_theme]["FG"])
            self.goal_progress_bar["value"] = 0
            return
        data = load_data()
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_seconds = get_day_total(data.get(today_str, {}))
        percent = min(100, (today_seconds / self.daily_goal_seconds) * 100)
        self.goal_progress_bar["value"] = percent
        if today_seconds >= self.daily_goal_seconds:
            self.goal_status_label.config(text="✅ Goal reached today!", fg="green")
        else:
            remaining = self.daily_goal_seconds - today_seconds
            self.goal_status_label.config(
                text=f"❌ Not yet — {self.format_duration(remaining)} left", fg="red"
            )

    def update_time_label(self):
        hours, remainder = divmod(self.elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.time_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    # ---------- Summary table ----------
    def refresh_summary_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        data = load_data()
        today = datetime.now()
        total_seconds = 0
        for i in range(DAYS_TO_SHOW):
            day = today - timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            day_data = data.get(day_str, {})
            seconds = get_day_total(day_data)
            total_seconds += seconds
            display_date = day.strftime("%d.%m.%Y") + (" (Today)" if i == 0 else "")
            self.tree.insert("", "end", values=(display_date, self.format_duration(seconds)))

        self.total_label.config(text=f"7-Day Total: {self.format_duration(total_seconds)}")
        self.average_label.config(text=f"Daily Average: {self.format_duration(total_seconds // DAYS_TO_SHOW)}")

        streak = calculate_streak(data)
        self.streak_label.config(text=f"🔥 Streak: {streak} day{'s' if streak != 1 else ''}")

        self.update_category_breakdown(data)

    def update_category_breakdown(self, data):
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_data = data.get(today_str, {})
        if not isinstance(today_data, dict) or not today_data:
            self.category_breakdown_label.config(text="No categories logged today yet.")
            return
        parts = [f"{cat}: {self.format_duration(secs)}" for cat, secs in today_data.items()]
        self.category_breakdown_label.config(text="Today by category — " + " | ".join(parts))

    @staticmethod
    def format_duration(seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours}h {minutes}m {secs}s"


# ---------- Run the app ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = StudyTimerApp(root)
    root.mainloop()

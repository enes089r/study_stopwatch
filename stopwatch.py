"""
Study Stopwatch & Daily Tracker
--------------------------------
Sidebar navigation: click a tab on the left to switch panels on the right.
Main screen always shows the stopwatch, streak, today's category breakdown,
and the theme toggle. Other features live in dedicated sidebar panels.
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
        "BG": "#1e1e1e", "FG": "#ffffff", "BTN_BG": "#3c3c3c", "BTN_FG": "#ffffff",
        "ENTRY_BG": "#2d2d2d", "ENTRY_FG": "#ffffff", "TABLE_BG": "#2d2d2d",
        "TABLE_FG": "#ffffff", "ACCENT": "#4ec9b0", "SIDEBAR_BG": "#252526",
        "SIDEBAR_ACTIVE": "#37373d", "ICON": "☀️",
    },
    "light": {
        "BG": "#f5f5f5", "FG": "#1e1e1e", "BTN_BG": "#e0e0e0", "BTN_FG": "#1e1e1e",
        "ENTRY_BG": "#ffffff", "ENTRY_FG": "#1e1e1e", "TABLE_BG": "#ffffff",
        "TABLE_FG": "#1e1e1e", "ACCENT": "#0f6e56", "SIDEBAR_BG": "#e8e8e8",
        "SIDEBAR_ACTIVE": "#d0d0d0", "ICON": "🌙",
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


def format_duration(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h {minutes}m {secs}s"


def save_session(start_time, end_time, duration_seconds, category):
    """Saves a single study session with start/end times to the JSON file."""
    data = load_data()
    if "sessions" not in data:
        data["sessions"] = []
    data["sessions"].append({
        "date": start_time.strftime("%Y-%m-%d"),
        "start": start_time.strftime("%H:%M"),
        "end": end_time.strftime("%H:%M"),
        "duration_seconds": duration_seconds,
        "category": category,
    })
    save_data(data)
    data = load_data()
    data["goal_hours"] = hours
    save_data(data)


def load_goal():
    data = load_data()
    return data.get("goal_hours", None)


def save_theme(theme_name):
    data = load_data()
    data["theme"] = theme_name
    save_data(data)


def load_theme():
    data = load_data()
    return data.get("theme", "dark")


# ---------- Application ----------
class StudyTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Study Stopwatch")
        self.root.geometry("750x560")
        self.root.resizable(False, False)

        self.running = False
        self.elapsed_seconds = 0
        self.timer_job = None
        self.daily_goal_seconds = None
        self.session_start_time = None
        self.current_theme = load_theme()
        self.active_panel = None
        self._themed_widgets = []

        saved_goal = load_goal()
        if saved_goal is not None:
            self.daily_goal_seconds = int(saved_goal * 3600)

        self._build_layout()
        self._apply_theme()
        self.refresh_stats()

    def _build_layout(self):
        self.sidebar = tk.Frame(self.root, width=160)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content_area = tk.Frame(self.root)
        self.content_area.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._build_main_panel()

    def _build_sidebar(self):
        title_btn = tk.Button(self.sidebar, text="Study\nStopwatch", font=("Arial", 12, "bold"),
                               pady=15, relief="flat", cursor="hand2",
                               command=self._build_main_panel)
        title_btn.pack(fill="x")
        self._reg(title_btn, "SIDEBAR_BG", "FG")

        self.sidebar_buttons = {}
        tabs = [
            ("📅", "Summary", self._show_summary),
            ("📊", "Stats", self._show_stats),
            ("🎯", "Goal", self._show_goal),
            ("✍️", "Manual", self._show_manual),
            ("🔗", "Chain", self._show_chain),
            ("📋", "Sessions", self._show_sessions),
            ("📈", "Insights", self._show_insights),
        ]
        for icon, label, cmd in tabs:
            btn = tk.Button(self.sidebar, text=f"  {icon}  {label}",
                            anchor="w", relief="flat", pady=10,
                            command=lambda c=cmd, l=label: self._sidebar_click(c, l))
            btn.pack(fill="x", padx=5, pady=2)
            self.sidebar_buttons[label] = btn
            self._reg(btn, "SIDEBAR_BG", "FG")

        self.theme_btn = tk.Button(self.sidebar, text="☀️", font=("Arial", 14),
                                    relief="flat", command=self.toggle_theme)
        self.theme_btn.pack(side="bottom", pady=10)
        self._reg(self.theme_btn, "SIDEBAR_BG", "FG")

    def _sidebar_click(self, cmd, label):
        for lbl, btn in self.sidebar_buttons.items():
            btn.configure(bg=THEMES[self.current_theme]["SIDEBAR_BG"])
        self.sidebar_buttons[label].configure(bg=THEMES[self.current_theme]["SIDEBAR_ACTIVE"])
        cmd()

    def _clear_content(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
        self._themed_widgets = [(w, bk, fk) for w, bk, fk in self._themed_widgets
                                 if w.winfo_exists()]

    def _reg(self, widget, bg_key, fg_key="FG"):
        self._themed_widgets.append((widget, bg_key, fg_key))

    def _build_main_panel(self):
        self._clear_content()
        self.active_panel = "main"

        self.time_label = tk.Label(self.content_area, text="00:00:00", font=("Consolas", 52))
        self.time_label.pack(pady=(30, 5))
        self._reg(self.time_label, "BG", "FG")

        cat_frame = tk.Frame(self.content_area)
        cat_frame.pack()
        self._reg(cat_frame, "BG")

        cat_lbl = tk.Label(cat_frame, text="Category:")
        cat_lbl.grid(row=0, column=0, padx=5)
        self._reg(cat_lbl, "BG", "FG")

        self.timer_category_entry = tk.Entry(cat_frame, width=15)
        self.timer_category_entry.grid(row=0, column=1, padx=5)
        self.timer_category_entry.insert(0, "General")
        self._reg(self.timer_category_entry, "ENTRY_BG", "ENTRY_FG")

        btn_frame = tk.Frame(self.content_area)
        btn_frame.pack(pady=10)
        self._reg(btn_frame, "BG")

        self.start_button = tk.Button(btn_frame, text="Start", width=9, command=self.start_timer)
        self.start_button.grid(row=0, column=0, padx=5)
        self._reg(self.start_button, "BTN_BG", "BTN_FG")

        self.stop_button = tk.Button(btn_frame, text="Stop", width=9,
                                      command=self.stop_timer, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=5)
        self._reg(self.stop_button, "BTN_BG", "BTN_FG")

        self.reset_button = tk.Button(btn_frame, text="Reset", width=9, command=self.reset_timer)
        self.reset_button.grid(row=0, column=2, padx=5)
        self._reg(self.reset_button, "BTN_BG", "BTN_FG")

        ttk.Separator(self.content_area, orient="horizontal").pack(fill="x", padx=20, pady=15)

        self.today_total_label = tk.Label(self.content_area, text="Today: 0h 0m 0s",
                                          font=("Arial", 12))
        self.today_total_label.pack(pady=(0, 5))
        self._reg(self.today_total_label, "BG", "FG")

        self.streak_label = tk.Label(self.content_area, text="🔥 Streak: 0 days",
                                      font=("Arial", 12, "bold"))
        self.streak_label.pack()
        self._reg(self.streak_label, "BG", "ACCENT")

        self.category_breakdown_label = tk.Label(self.content_area, text="",
                                                  font=("Arial", 10), wraplength=500,
                                                  justify="center")
        self.category_breakdown_label.pack(pady=(8, 0))
        self._reg(self.category_breakdown_label, "BG", "FG")

        self._apply_theme()
        self.refresh_stats()

    def _show_summary(self):
        self._clear_content()
        self.active_panel = "summary"

        lbl = tk.Label(self.content_area, text="Study Summary", font=("Arial", 14, "bold"))
        lbl.pack(pady=(20, 10))
        self._reg(lbl, "BG", "FG")

        # Range selector
        range_frame = tk.Frame(self.content_area)
        range_frame.pack(pady=(0, 10))
        self._reg(range_frame, "BG")

        self.summary_range = tk.StringVar(value="Week")

        for label in ["Week", "Month", "All"]:
            btn = tk.Radiobutton(range_frame, text=label, variable=self.summary_range,
                                 value=label, command=self._refresh_summary_table,
                                 indicatoron=False, width=7, relief="flat", padx=6)
            btn.pack(side="left", padx=3)
            self._reg(btn, "BTN_BG", "BTN_FG")

        self.tree = ttk.Treeview(self.content_area, columns=("date", "duration"),
                                  show="headings", height=12)
        self.tree.heading("date", text="Date")
        self.tree.heading("duration", text="Duration")
        self.tree.column("date", width=230, anchor="center")
        self.tree.column("duration", width=200, anchor="center")
        self.tree.pack(padx=20, pady=5)

        self.summary_total_lbl = tk.Label(self.content_area, text="", font=("Arial", 11, "bold"))
        self.summary_total_lbl.pack(pady=(5, 0))
        self._reg(self.summary_total_lbl, "BG", "FG")

        self._apply_theme()
        self._refresh_summary_table()

    def _refresh_summary_table(self):
        if not hasattr(self, "tree") or not self.tree.winfo_exists():
            return

        for row in self.tree.get_children():
            self.tree.delete(row)

        data = load_data()
        today = datetime.now()
        selected = self.summary_range.get()

        if selected == "Week":
            days = [(today - timedelta(days=i)) for i in range(7)]
        elif selected == "Month":
            days = [(today - timedelta(days=i)) for i in range(30)]
        else:  # All
            all_dates = sorted(
                [k for k in data.keys()
                 if k not in ("goal_hours", "theme", "sessions")],
                reverse=True
            )
            days = [datetime.strptime(d, "%Y-%m-%d") for d in all_dates]

        total_seconds = 0
        for day in days:
            day_str = day.strftime("%Y-%m-%d")
            seconds = get_day_total(data.get(day_str, {}))
            total_seconds += seconds
            display_date = day.strftime("%d.%m.%Y")
            if day.date() == today.date():
                display_date += " (Today)"
            self.tree.insert("", "end", values=(display_date, format_duration(seconds)))

        self.summary_total_lbl.config(
            text=f"Total: {format_duration(total_seconds)}  ({len(days)} days)"
        )

    def _show_stats(self):
        self._clear_content()
        self.active_panel = "stats"

        lbl = tk.Label(self.content_area, text="Statistics", font=("Arial", 14, "bold"))
        lbl.pack(pady=(30, 20))
        self._reg(lbl, "BG", "FG")

        self.total_label = tk.Label(self.content_area, text="7-Day Total: —",
                                     font=("Arial", 13, "bold"))
        self.total_label.pack(pady=8)
        self._reg(self.total_label, "BG", "FG")

        self.average_label = tk.Label(self.content_area, text="Daily Average: —",
                                       font=("Arial", 13))
        self.average_label.pack(pady=8)
        self._reg(self.average_label, "BG", "FG")

        ttk.Separator(self.content_area, orient="horizontal").pack(fill="x", padx=40, pady=15)

        # Session quality stats
        data = load_data()
        sessions = data.get("sessions", [])

        if sessions:
            durations = [s.get("duration_seconds", 0) for s in sessions if s.get("duration_seconds", 0) > 0]
            if durations:
                avg_sec = sum(durations) // len(durations)
                longest = max(durations)
                shortest = min(durations)
                total_sessions = len(durations)

                short = sum(1 for d in durations if d < 1800)       # < 30 min
                medium = sum(1 for d in durations if 1800 <= d < 3600)  # 30-60 min
                long_ = sum(1 for d in durations if d >= 3600)       # > 60 min

                stats = [
                    ("Total sessions", str(total_sessions)),
                    ("Average session", format_duration(avg_sec)),
                    ("Longest session", format_duration(longest)),
                    ("Shortest session", format_duration(shortest)),
                    ("Short  (< 30 min)", f"{short} session{'s' if short != 1 else ''}"),
                    ("Medium (30–60 min)", f"{medium} session{'s' if medium != 1 else ''}"),
                    ("Long   (> 60 min)", f"{long_} session{'s' if long_ != 1 else ''}"),
                ]

                for label, value in stats:
                    row = tk.Frame(self.content_area)
                    row.pack(fill="x", padx=80, pady=3)
                    self._reg(row, "BG")

                    tk.Label(row, text=label, font=("Arial", 11), anchor="w", width=20).pack(side="left")
                    self._reg(row.winfo_children()[-1], "BG", "FG")

                    tk.Label(row, text=value, font=("Arial", 11, "bold"), anchor="w").pack(side="left")
                    self._reg(row.winfo_children()[-1], "BG", "ACCENT")
        else:
            no_lbl = tk.Label(self.content_area,
                              text="No session data yet.",
                              font=("Arial", 11))
            no_lbl.pack(pady=10)
            self._reg(no_lbl, "BG", "FG")

        self._apply_theme()
        self.refresh_stats()

    def _show_goal(self):
        self._clear_content()
        self.active_panel = "goal"

        lbl = tk.Label(self.content_area, text="Daily Goal", font=("Arial", 14, "bold"))
        lbl.pack(pady=(30, 20))
        self._reg(lbl, "BG", "FG")

        goal_frame = tk.Frame(self.content_area)
        goal_frame.pack()
        self._reg(goal_frame, "BG")

        gl = tk.Label(goal_frame, text="Daily goal:")
        gl.grid(row=0, column=0, padx=5)
        self._reg(gl, "BG", "FG")

        self.goal_hours_entry = tk.Entry(goal_frame, width=4)
        self.goal_hours_entry.grid(row=0, column=1, padx=(5, 0))
        self._reg(self.goal_hours_entry, "ENTRY_BG", "ENTRY_FG")

        h_lbl = tk.Label(goal_frame, text="h")
        h_lbl.grid(row=0, column=2, padx=(2, 5))
        self._reg(h_lbl, "BG", "FG")

        self.goal_mins_entry = tk.Entry(goal_frame, width=4)
        self.goal_mins_entry.grid(row=0, column=3, padx=(0, 0))
        self._reg(self.goal_mins_entry, "ENTRY_BG", "ENTRY_FG")

        m_lbl = tk.Label(goal_frame, text="min")
        m_lbl.grid(row=0, column=4, padx=(2, 10))
        self._reg(m_lbl, "BG", "FG")

        # Pre-fill with saved goal if available
        saved_goal = load_goal()
        if saved_goal is not None:
            total_mins = int(saved_goal * 60)
            self.goal_hours_entry.insert(0, str(total_mins // 60))
            self.goal_mins_entry.insert(0, str(total_mins % 60))
        else:
            self.goal_hours_entry.insert(0, "0")
            self.goal_mins_entry.insert(0, "0")

        set_btn = tk.Button(goal_frame, text="Set Goal", command=self.set_daily_goal)
        set_btn.grid(row=0, column=5, padx=5)
        self._reg(set_btn, "BTN_BG", "BTN_FG")

        self.goal_status_label = tk.Label(self.content_area, text="No goal set yet.",
                                           font=("Arial", 12, "bold"))
        self.goal_status_label.pack(pady=(20, 5))
        self._reg(self.goal_status_label, "BG", "FG")

        self.goal_progress_bar = ttk.Progressbar(self.content_area, length=300,
                                                  mode="determinate", maximum=100)
        self.goal_progress_bar.pack(pady=(0, 10))

        self._apply_theme()
        self.check_goal_status()

    def _show_manual(self):
        self._clear_content()
        self.active_panel = "manual"

        lbl = tk.Label(self.content_area, text="Add Manual Study Time",
                       font=("Arial", 14, "bold"))
        lbl.pack(pady=(30, 20))
        self._reg(lbl, "BG", "FG")

        manual_frame = tk.Frame(self.content_area)
        manual_frame.pack()
        self._reg(manual_frame, "BG")

        ml = tk.Label(manual_frame, text="Minutes:")
        ml.grid(row=0, column=0, padx=5)
        self._reg(ml, "BG", "FG")

        self.manual_entry = tk.Entry(manual_frame, width=8)
        self.manual_entry.grid(row=0, column=1, padx=5)
        self._reg(self.manual_entry, "ENTRY_BG", "ENTRY_FG")

        cl = tk.Label(manual_frame, text="Category:")
        cl.grid(row=0, column=2, padx=5)
        self._reg(cl, "BG", "FG")

        self.manual_category_entry = tk.Entry(manual_frame, width=12)
        self.manual_category_entry.grid(row=0, column=3, padx=5)
        self.manual_category_entry.insert(0, "General")
        self._reg(self.manual_category_entry, "ENTRY_BG", "ENTRY_FG")

        add_btn = tk.Button(manual_frame, text="Add to Today", command=self.add_manual_time)
        add_btn.grid(row=0, column=4, padx=5)
        self._reg(add_btn, "BTN_BG", "BTN_FG")

        # Optional time range row
        time_frame = tk.Frame(self.content_area)
        time_frame.pack(pady=(10, 0))
        self._reg(time_frame, "BG")

        opt_lbl = tk.Label(time_frame, text="Time range (optional):", font=("Arial", 10))
        opt_lbl.grid(row=0, column=0, padx=5)
        self._reg(opt_lbl, "BG", "FG")

        self.manual_start_entry = tk.Entry(time_frame, width=7)
        self.manual_start_entry.grid(row=0, column=1, padx=3)
        self._reg(self.manual_start_entry, "ENTRY_BG", "ENTRY_FG")

        sep_lbl = tk.Label(time_frame, text="→")
        sep_lbl.grid(row=0, column=2, padx=3)
        self._reg(sep_lbl, "BG", "FG")

        self.manual_end_entry = tk.Entry(time_frame, width=7)
        self.manual_end_entry.grid(row=0, column=3, padx=3)
        self._reg(self.manual_end_entry, "ENTRY_BG", "ENTRY_FG")

        # Auto-calculate minutes when time range is filled
        def auto_calc_minutes(*args):
            start_raw = self.manual_start_entry.get().strip()
            end_raw = self.manual_end_entry.get().strip()
            if not start_raw or not end_raw:
                return
            try:
                start_dt = datetime.strptime(start_raw, "%H:%M")
                end_dt = datetime.strptime(end_raw, "%H:%M")
                diff_min = int((end_dt - start_dt).total_seconds() // 60)
                if diff_min > 0:
                    self.manual_entry.delete(0, tk.END)
                    self.manual_entry.insert(0, str(diff_min))
            except ValueError:
                pass

        self.manual_end_entry.bind("<FocusOut>", auto_calc_minutes)
        self.manual_start_entry.bind("<FocusOut>", auto_calc_minutes)

        hint_lbl = tk.Label(time_frame, text="(HH:MM format, optional)", font=("Arial", 9))
        hint_lbl.grid(row=0, column=4, padx=5)
        self._reg(hint_lbl, "BG", "FG")

        self.manual_feedback_label = tk.Label(self.content_area, text="", font=("Arial", 11))
        self.manual_feedback_label.pack(pady=15)
        self._reg(self.manual_feedback_label, "BG", "FG")

        self._apply_theme()

    def _show_chain(self):
        self._clear_content()
        self.active_panel = "chain"

        lbl = tk.Label(self.content_area, text="Don't Break the Chain!",
                       font=("Arial", 14, "bold"))
        lbl.pack(pady=(25, 5))
        self._reg(lbl, "BG", "FG")

        if self.daily_goal_seconds is None:
            info_lbl = tk.Label(self.content_area,
                                text="Set a daily goal first (Goal tab) to use the chain.",
                                font=("Arial", 11), wraplength=450, justify="center")
            info_lbl.pack(pady=20)
            self._reg(info_lbl, "BG", "FG")
            self._apply_theme()
            return

        goal_hours = self.daily_goal_seconds / 3600
        sub_lbl = tk.Label(self.content_area,
                           text=f"Goal: {goal_hours:g}h per day",
                           font=("Arial", 10))
        sub_lbl.pack(pady=(0, 15))
        self._reg(sub_lbl, "BG", "FG")

        data = load_data()
        today = datetime.now()
        t = THEMES[self.current_theme]

        days_to_show = 30
        cols = 6
        grid_frame = tk.Frame(self.content_area)
        grid_frame.pack(pady=5)
        self._reg(grid_frame, "BG")

        for i in range(days_to_show - 1, -1, -1):
            day = today - timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            day_total = get_day_total(data.get(day_str, {}))
            reached = day_total >= self.daily_goal_seconds

            idx = days_to_show - 1 - i
            row_idx = idx // cols
            col_idx = idx % cols

            cell = tk.Canvas(grid_frame, width=70, height=70,
                             bg=t["BG"], highlightthickness=1,
                             highlightbackground=t["ACCENT"])
            cell.grid(row=row_idx, column=col_idx, padx=4, pady=4)

            # Date label inside the box
            cell.create_text(35, 15, text=day.strftime("%d.%m"),
                             fill=t["FG"], font=("Arial", 8))

            if reached:
                # Draw an X across the box
                cell.create_line(10, 28, 60, 65, fill=t["ACCENT"], width=3)
                cell.create_line(60, 28, 10, 65, fill=t["ACCENT"], width=3)

        # Current streak
        streak = 0
        for i in range(365):
            day_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            if get_day_total(data.get(day_str, {})) >= self.daily_goal_seconds:
                streak += 1
            else:
                break

        streak_lbl = tk.Label(self.content_area,
                               text=f"🔥 Current chain: {streak} day{'s' if streak != 1 else ''}",
                               font=("Arial", 13, "bold"))
        streak_lbl.pack(pady=(20, 5))
        self._reg(streak_lbl, "BG", "ACCENT")

        self._apply_theme()

    def _show_sessions(self):
        self._clear_content()
        self.active_panel = "sessions"

        lbl = tk.Label(self.content_area, text="This Week's Sessions",
                       font=("Arial", 14, "bold"))
        lbl.pack(pady=(20, 10))
        self._reg(lbl, "BG", "FG")

        data = load_data()
        sessions = data.get("sessions", [])

        today = datetime.now()
        week_ago = (today - timedelta(days=6)).strftime("%Y-%m-%d")
        this_week = [s for s in sessions if s.get("date", "") >= week_ago]

        # ---------- Hourly bar chart ----------
        # Count minutes worked per hour (0-23) across this week's sessions
        hour_minutes = [0] * 24
        for s in this_week:
            try:
                start_h = int(s.get("start", "00:00").split(":")[0])
                end_h = int(s.get("end", "00:00").split(":")[0])
                dur_min = s.get("duration_seconds", 0) // 60
                # Distribute minutes across hours spanned
                span = max(1, end_h - start_h + 1)
                per_hour = dur_min // span
                for h in range(start_h, min(end_h + 1, 24)):
                    hour_minutes[h] += per_hour
            except (ValueError, IndexError):
                pass

        t = THEMES[self.current_theme]
        max_min = max(hour_minutes) if max(hour_minutes) > 0 else 1

        chart_frame = tk.Frame(self.content_area)
        chart_frame.pack(padx=15, pady=(0, 10))
        self._reg(chart_frame, "BG")

        canvas_w, canvas_h = 540, 120
        bar_w = canvas_w // 24

        chart = tk.Canvas(chart_frame, width=canvas_w, height=canvas_h,
                          bg=t["BG"], highlightthickness=0)
        chart.pack()

        for h in range(24):
            bar_h = int((hour_minutes[h] / max_min) * 90) if max_min > 0 else 0
            x0 = h * bar_w + 2
            x1 = x0 + bar_w - 4
            y0 = canvas_h - 20 - bar_h
            y1 = canvas_h - 20

            # Bar
            color = t["ACCENT"] if bar_h > 0 else t["BTN_BG"]
            chart.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

            # Hour label (every 3 hours)
            if h % 3 == 0:
                chart.create_text(x0 + (bar_w // 2) - 2, canvas_h - 8,
                                  text=f"{h:02d}", fill=t["FG"],
                                  font=("Arial", 7))

        chart_lbl = tk.Label(self.content_area, text="Activity by hour (this week)",
                             font=("Arial", 9), fg=t["FG"])
        chart_lbl.pack()
        self._reg(chart_lbl, "BG", "FG")

        # ---------- Peak block ----------
        if max(hour_minutes) > 0:
            # Find the most productive 2-hour block
            best_start = 0
            best_total = 0
            for h in range(23):
                block = hour_minutes[h] + hour_minutes[h + 1]
                if block > best_total:
                    best_total = block
                    best_start = h

            peak_lbl = tk.Label(
                self.content_area,
                text=f"⚡ Peak block: {best_start:02d}:00 – {best_start + 2:02d}:00  ({best_total} min this week)",
                font=("Arial", 11, "bold")
            )
            peak_lbl.pack(pady=(6, 0))
            self._reg(peak_lbl, "BG", "ACCENT")

            # Dead zones: consecutive hours with zero activity during typical waking hours (07-23)
            dead_zones = []
            zone_start = None
            for h in range(7, 24):
                if hour_minutes[h] == 0:
                    if zone_start is None:
                        zone_start = h
                else:
                    if zone_start is not None and h - zone_start >= 2:
                        dead_zones.append((zone_start, h - 1))
                    zone_start = None
            if zone_start is not None and 23 - zone_start >= 1:
                dead_zones.append((zone_start, 23))

            if dead_zones:
                # Show the longest dead zone only
                longest = max(dead_zones, key=lambda z: z[1] - z[0])
                dead_lbl = tk.Label(
                    self.content_area,
                    text=f"💤 Longest gap: {longest[0]:02d}:00 – {longest[1] + 1:02d}:00  ({longest[1] - longest[0] + 1}h with no activity)",
                    font=("Arial", 10)
                )
                dead_lbl.pack(pady=(4, 0))
                self._reg(dead_lbl, "BG", "FG")

        # ---------- Sessions table ----------
        ttk.Separator(self.content_area, orient="horizontal").pack(fill="x", padx=15, pady=10)

        tree = ttk.Treeview(self.content_area,
                            columns=("date", "start", "end", "duration", "category"),
                            show="headings", height=7)
        tree.heading("date", text="Date")
        tree.heading("start", text="Start")
        tree.heading("end", text="End")
        tree.heading("duration", text="Duration")
        tree.heading("category", text="Category")

        tree.column("date", width=90, anchor="center")
        tree.column("start", width=60, anchor="center")
        tree.column("end", width=60, anchor="center")
        tree.column("duration", width=90, anchor="center")
        tree.column("category", width=110, anchor="center")
        tree.pack(padx=10, pady=5, fill="x")

        for s in reversed(this_week):
            tree.insert("", "end", values=(
                s.get("date", ""),
                s.get("start", ""),
                s.get("end", ""),
                format_duration(s.get("duration_seconds", 0)),
                s.get("category", "General"),
            ))

        if not this_week:
            no_lbl = tk.Label(self.content_area,
                              text="No sessions recorded this week yet.",
                              font=("Arial", 11))
            no_lbl.pack(pady=15)
            self._reg(no_lbl, "BG", "FG")

        self._apply_theme()

    def _show_insights(self):
        self._clear_content()
        self.active_panel = "insights"

        lbl = tk.Label(self.content_area, text="Insights", font=("Arial", 14, "bold"))
        lbl.pack(pady=(20, 5))
        self._reg(lbl, "BG", "FG")

        data = load_data()
        sessions = data.get("sessions", [])
        t = THEMES[self.current_theme]

        if not sessions:
            no_lbl = tk.Label(self.content_area,
                              text="No session data yet. Start the stopwatch to begin tracking.",
                              font=("Arial", 11), wraplength=450, justify="center")
            no_lbl.pack(pady=30)
            self._reg(no_lbl, "BG", "FG")
            self._apply_theme()
            return

        # ---------- Build hour_minutes from ALL sessions ----------
        hour_minutes = [0] * 24
        for s in sessions:
            try:
                start_h = int(s.get("start", "00:00").split(":")[0])
                end_h = int(s.get("end", "00:00").split(":")[0])
                dur_min = s.get("duration_seconds", 0) // 60
                span = max(1, end_h - start_h + 1)
                per_hour = dur_min // span
                for h in range(start_h, min(end_h + 1, 24)):
                    hour_minutes[h] += per_hour
            except (ValueError, IndexError):
                pass

        max_min = max(hour_minutes) if max(hour_minutes) > 0 else 1

        # ---------- Heatmap: 24 colored cells ----------
        sub_lbl = tk.Label(self.content_area, text="Hour-of-day heatmap (all time)",
                           font=("Arial", 10))
        sub_lbl.pack(pady=(0, 6))
        self._reg(sub_lbl, "BG", "FG")

        heatmap_frame = tk.Frame(self.content_area)
        heatmap_frame.pack()
        self._reg(heatmap_frame, "BG")

        # Parse accent color for intensity blending
        accent = t["ACCENT"]  # e.g. "#4ec9b0"
        bg = t["BG"]

        def blend_color(intensity):
            """Returns a hex color blended between bg and accent based on intensity (0.0–1.0)."""
            def parse(c): return int(c, 16)
            r1, g1, b1 = parse(bg[1:3]), parse(bg[3:5]), parse(bg[5:7])
            r2, g2, b2 = parse(accent[1:3]), parse(accent[3:5]), parse(accent[5:7])
            r = int(r1 + (r2 - r1) * intensity)
            g = int(g1 + (g2 - g1) * intensity)
            b = int(b1 + (b2 - b1) * intensity)
            return f"#{r:02x}{g:02x}{b:02x}"

        for h in range(24):
            intensity = hour_minutes[h] / max_min
            cell_color = blend_color(intensity)

            cell = tk.Canvas(heatmap_frame, width=22, height=40,
                             bg=cell_color, highlightthickness=1,
                             highlightbackground=t["BTN_BG"])
            cell.grid(row=0, column=h)

            # Hour label below cell
            lbl_h = tk.Label(heatmap_frame, text=f"{h:02d}", font=("Arial", 7))
            lbl_h.grid(row=1, column=h)
            self._reg(lbl_h, "BG", "FG")

        # ---------- Tendency: morning vs evening ----------
        morning = sum(hour_minutes[6:12])
        afternoon = sum(hour_minutes[12:18])
        evening = sum(hour_minutes[18:24])
        total = morning + afternoon + evening or 1

        tend_lbl = tk.Label(self.content_area, text="Study tendency (all time)",
                            font=("Arial", 10))
        tend_lbl.pack(pady=(18, 6))
        self._reg(tend_lbl, "BG", "FG")

        tend_frame = tk.Frame(self.content_area)
        tend_frame.pack()
        self._reg(tend_frame, "BG")

        for i, (label, val) in enumerate([("🌅 Morning\n06–12", morning),
                                           ("☀️ Afternoon\n12–18", afternoon),
                                           ("🌙 Evening\n18–24", evening)]):
            pct = int(val / total * 100)
            block = tk.Frame(tend_frame, padx=15, pady=8)
            block.grid(row=0, column=i, padx=10)
            self._reg(block, "BG")

            tk.Label(block, text=label, font=("Arial", 10), justify="center").pack()
            self._reg(block.winfo_children()[-1], "BG", "FG")

            tk.Label(block, text=f"{pct}%", font=("Arial", 16, "bold")).pack()
            self._reg(block.winfo_children()[-1], "BG", "ACCENT")

            tk.Label(block, text=f"{val} min", font=("Arial", 9)).pack()
            self._reg(block.winfo_children()[-1], "BG", "FG")

        # ---------- Weekly trend: avg minutes per weekday ----------
        week_lbl = tk.Label(self.content_area, text="Average study time by weekday (all time)",
                            font=("Arial", 10))
        week_lbl.pack(pady=(18, 6))
        self._reg(week_lbl, "BG", "FG")

        # Accumulate minutes and count per weekday (0=Mon, 6=Sun)
        day_total_min = [0] * 7
        day_count = [0] * 7
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for s in sessions:
            try:
                date_obj = datetime.strptime(s.get("date", ""), "%Y-%m-%d")
                wd = date_obj.weekday()
                day_total_min[wd] += s.get("duration_seconds", 0) // 60
                day_count[wd] += 1
            except ValueError:
                pass

        avg_by_day = [
            day_total_min[i] // day_count[i] if day_count[i] > 0 else 0
            for i in range(7)
        ]
        max_avg = max(avg_by_day) if max(avg_by_day) > 0 else 1

        week_frame = tk.Frame(self.content_area)
        week_frame.pack()
        self._reg(week_frame, "BG")

        bar_max_h = 60
        for i, (name, avg) in enumerate(zip(day_names, avg_by_day)):
            col_frame = tk.Frame(week_frame)
            col_frame.grid(row=0, column=i, padx=6)
            self._reg(col_frame, "BG")

            bar_h = int((avg / max_avg) * bar_max_h)
            spacer = tk.Label(col_frame, text="", height=(bar_max_h - bar_h) // 10 or 1)
            spacer.pack()
            self._reg(spacer, "BG", "FG")

            if bar_h > 0:
                bar = tk.Frame(col_frame, width=30, height=bar_h,
                               bg=t["ACCENT"])
                bar.pack()
                bar.pack_propagate(False)

            avg_lbl = tk.Label(col_frame, text=f"{avg}m", font=("Arial", 8))
            avg_lbl.pack()
            self._reg(avg_lbl, "BG", "FG")

            day_lbl = tk.Label(col_frame, text=name, font=("Arial", 9, "bold"))
            day_lbl.pack()
            self._reg(day_lbl, "BG", "FG")

        # ---------- Category breakdown: last 30 days ----------
        cat_lbl = tk.Label(self.content_area, text="Category breakdown (last 30 days)",
                           font=("Arial", 10))
        cat_lbl.pack(pady=(18, 6))
        self._reg(cat_lbl, "BG", "FG")

        data30 = load_data()
        today = datetime.now()
        cutoff = (today - timedelta(days=29)).strftime("%Y-%m-%d")
        cat_minutes = {}

        for day_str, day_data in data30.items():
            if day_str < cutoff or not isinstance(day_data, dict):
                continue
            for cat, secs in day_data.items():
                if isinstance(secs, (int, float)):
                    cat_minutes[cat] = cat_minutes.get(cat, 0) + secs // 60

        if cat_minutes:
            total_cat = sum(cat_minutes.values()) or 1
            sorted_cats = sorted(cat_minutes.items(), key=lambda x: x[1], reverse=True)

            cat_frame = tk.Frame(self.content_area)
            cat_frame.pack(padx=20, fill="x")
            self._reg(cat_frame, "BG")

            for cat, mins in sorted_cats:
                pct = int(mins / total_cat * 100)

                row = tk.Frame(cat_frame)
                row.pack(fill="x", pady=3)
                self._reg(row, "BG")

                name_lbl = tk.Label(row, text=f"{cat}", font=("Arial", 10), width=14, anchor="w")
                name_lbl.pack(side="left")
                self._reg(name_lbl, "BG", "FG")

                bar_frame = tk.Frame(row, height=14, width=int(pct * 2.5),
                                     bg=THEMES[self.current_theme]["ACCENT"])
                bar_frame.pack(side="left", padx=(4, 6))
                bar_frame.pack_propagate(False)

                pct_lbl = tk.Label(row, text=f"{pct}%  ({mins}m)", font=("Arial", 9))
                pct_lbl.pack(side="left")
                self._reg(pct_lbl, "BG", "FG")
        else:
            no_cat_lbl = tk.Label(self.content_area, text="No category data in the last 30 days.",
                                  font=("Arial", 10))
            no_cat_lbl.pack(pady=5)
            self._reg(no_cat_lbl, "BG", "FG")

        # ---------- Chronotype detection ----------
        chrono_lbl = tk.Label(self.content_area, text="Your study chronotype",
                              font=("Arial", 10))
        chrono_lbl.pack(pady=(18, 6))
        self._reg(chrono_lbl, "BG", "FG")

        if morning + afternoon + evening > 0:
            dominant = max(
                [("morning", morning), ("afternoon", afternoon), ("evening", evening)],
                key=lambda x: x[1]
            )[0]

            chrono_map = {
                "morning": (
                    "🌅 Early bird",
                    "You tend to study in the morning. Protect your mornings — avoid scheduling meetings or distractions before noon."
                ),
                "afternoon": (
                    "☀️ Afternoon worker",
                    "You're most active in the afternoon. Use your mornings for lighter tasks and save deep work for after lunch."
                ),
                "evening": (
                    "🌙 Night owl",
                    "You study mostly in the evenings. Make sure you're not sacrificing sleep — consistency matters more than late-night sessions."
                ),
            }

            title, tip = chrono_map[dominant]

            chrono_title = tk.Label(self.content_area, text=title, font=("Arial", 13, "bold"))
            chrono_title.pack()
            self._reg(chrono_title, "BG", "ACCENT")

            chrono_tip = tk.Label(self.content_area, text=tip, font=("Arial", 10),
                                  wraplength=450, justify="center")
            chrono_tip.pack(pady=(6, 10))
            self._reg(chrono_tip, "BG", "FG")
        else:
            no_chrono = tk.Label(self.content_area,
                                 text="Not enough data yet to detect your chronotype.",
                                 font=("Arial", 10))
            no_chrono.pack(pady=5)
            self._reg(no_chrono, "BG", "FG")

        self._apply_theme()

    def _apply_theme(self):
        t = THEMES[self.current_theme]
        self.root.configure(bg=t["BG"])
        self.sidebar.configure(bg=t["SIDEBAR_BG"])
        self.content_area.configure(bg=t["BG"])

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=t["TABLE_BG"], foreground=t["TABLE_FG"],
                        fieldbackground=t["TABLE_BG"], rowheight=25)
        style.configure("Treeview.Heading", background=t["BTN_BG"], foreground=t["FG"])
        style.configure("TProgressbar", troughcolor=t["BTN_BG"], background=t["ACCENT"])

        for widget, bg_key, fg_key in self._themed_widgets:
            if widget.winfo_exists():
                try:
                    widget.configure(bg=t[bg_key], fg=t[fg_key])
                    if isinstance(widget, tk.Entry):
                        widget.configure(insertbackground=t["FG"])
                except tk.TclError:
                    pass

        for btn in self.sidebar_buttons.values():
            btn.configure(bg=t["SIDEBAR_BG"], fg=t["FG"])
        self.theme_btn.configure(text=t["ICON"], bg=t["SIDEBAR_BG"], fg=t["FG"])

        for w in self.sidebar.winfo_children():
            if isinstance(w, tk.Label):
                w.configure(bg=t["SIDEBAR_BG"], fg=t["FG"])

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        save_theme(self.current_theme)
        self._apply_theme()

    def start_timer(self):
        if self.running:
            return
        self.running = True
        self.session_start_time = datetime.now()
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.tick()

    def tick(self):
        if not self.running:
            return
        self.elapsed_seconds += 1
        h, r = divmod(self.elapsed_seconds, 3600)
        m, s = divmod(r, 60)
        self.time_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")
        self.timer_job = self.root.after(1000, self.tick)

    def stop_timer(self):
        if not self.running:
            return
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        if self.elapsed_seconds > 0:
            category = self.timer_category_entry.get().strip() or "General"
            end_time = datetime.now()
            save_session(self.session_start_time, end_time, self.elapsed_seconds, category)
            add_seconds_to_today(self.elapsed_seconds, category)
            self.refresh_stats()
            self.check_goal_status()
        self.elapsed_seconds = 0
        self.time_label.config(text="00:00:00")

    def reset_timer(self):
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        self.elapsed_seconds = 0
        self.time_label.config(text="00:00:00")

    def add_manual_time(self):
        try:
            minutes = int(self.manual_entry.get())
        except ValueError:
            self.manual_feedback_label.config(text="Please enter a whole number.", fg="red")
            return
        if minutes <= 0:
            self.manual_feedback_label.config(text="Minutes must be greater than 0.", fg="red")
            return

        category = self.manual_category_entry.get().strip() or "General"
        seconds = minutes * 60
        add_seconds_to_today(seconds, category)

        # Optional: save as a session if valid time range provided
        start_raw = self.manual_start_entry.get().strip()
        end_raw = self.manual_end_entry.get().strip()

        if start_raw and end_raw:
            try:
                today_str = datetime.now().strftime("%Y-%m-%d")
                start_dt = datetime.strptime(f"{today_str} {start_raw}", "%Y-%m-%d %H:%M")
                end_dt = datetime.strptime(f"{today_str} {end_raw}", "%Y-%m-%d %H:%M")
                save_session(start_dt, end_dt, seconds, category)
            except ValueError:
                self.manual_feedback_label.config(
                    text=f"Added {minutes} min — time range skipped (use HH:MM format).",
                    fg="orange")
                self.manual_entry.delete(0, tk.END)
                self.refresh_stats()
                self.check_goal_status()
                return

        self.refresh_stats()
        self.check_goal_status()
        self.manual_feedback_label.config(text=f"Added {minutes} minute(s) to today.", fg="green")
        self.manual_entry.delete(0, tk.END)

    def set_daily_goal(self):
        try:
            hours = int(self.goal_hours_entry.get() or 0)
            mins = int(self.goal_mins_entry.get() or 0)
        except ValueError:
            self.goal_status_label.config(text="Please enter whole numbers.", fg="red")
            return
        if hours < 0 or mins < 0 or mins > 59:
            self.goal_status_label.config(text="Hours ≥ 0, minutes 0–59.", fg="red")
            return
        total_hours = hours + mins / 60
        if total_hours <= 0:
            self.goal_status_label.config(text="Goal must be greater than 0.", fg="red")
            return
        self.daily_goal_seconds = int(total_hours * 3600)
        save_goal(total_hours)
        self.check_goal_status()

    def check_goal_status(self):
        if self.active_panel != "goal" or not hasattr(self, "goal_status_label"):
            return
        if self.daily_goal_seconds is None:
            self.goal_status_label.config(text="No goal set yet.",
                                           fg=THEMES[self.current_theme]["FG"])
            self.goal_progress_bar["value"] = 0
            return
        data = load_data()
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_seconds = get_day_total(data.get(today_str, {}))
        self.goal_progress_bar["value"] = min(100, (today_seconds / self.daily_goal_seconds) * 100)
        if today_seconds >= self.daily_goal_seconds:
            self.goal_status_label.config(text="✅ Goal reached today!", fg="green")
        else:
            remaining = self.daily_goal_seconds - today_seconds
            self.goal_status_label.config(
                text=f"❌ Not yet — {format_duration(remaining)} left", fg="red")

    def refresh_stats(self):
        data = load_data()
        today = datetime.now()
        total_seconds = 0

        if self.active_panel == "summary" and hasattr(self, "tree"):
            self._refresh_summary_table()

        for i in range(DAYS_TO_SHOW):
            day = today - timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            seconds = get_day_total(data.get(day_str, {}))
            total_seconds += seconds

        if self.active_panel == "stats":
            if hasattr(self, "total_label"):
                self.total_label.config(text=f"7-Day Total: {format_duration(total_seconds)}")
            if hasattr(self, "average_label"):
                self.average_label.config(
                    text=f"Daily Average: {format_duration(total_seconds // DAYS_TO_SHOW)}")

        if hasattr(self, "streak_label"):
            streak = calculate_streak(data)
            self.streak_label.config(text=f"🔥 Streak: {streak} day{'s' if streak != 1 else ''}")

        if hasattr(self, "today_total_label"):
            today_seconds = get_day_total(data.get(today.strftime("%Y-%m-%d"), {}))
            self.today_total_label.config(text=f"Today: {format_duration(today_seconds)}")

        if hasattr(self, "category_breakdown_label"):
            today_data = data.get(today.strftime("%Y-%m-%d"), {})
            if isinstance(today_data, dict) and today_data:
                parts = [f"{cat}: {format_duration(secs)}" for cat, secs in today_data.items()]
                self.category_breakdown_label.config(
                    text="Today by category — " + " | ".join(parts))
            else:
                self.category_breakdown_label.config(text="No categories logged today yet.")


# ---------- Run ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = StudyTimerApp(root)
    root.mainloop()

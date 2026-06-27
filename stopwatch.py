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
DAYS_TO_SHOW = 7  # how many days to show in the summary table


# ---------- Data layer (JSON read/write) ----------
def load_data():
    """Reads past records from the JSON file. Returns an empty dict if the file doesn't exist."""
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            # If the file is corrupted or empty, start fresh instead of crashing
            return {}


def save_data(data):
    """Writes the dictionary to the JSON file."""
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=2)


def add_seconds_to_today(seconds, category="General"):
    """Adds to today's total study time (in seconds) for a given category and saves it."""
    data = load_data()
    today_str = datetime.now().strftime("%Y-%m-%d")
    day_data = data.get(today_str, {})
    if not isinstance(day_data, dict):
        # Old format: today was a plain number. Convert it into the new dict format.
        day_data = {"General": day_data}
    day_data[category] = day_data.get(category, 0) + seconds
    data[today_str] = day_data
    save_data(data)
    return data


def get_day_total(day_data):
    """Sums all category seconds for a single day's data (a dict of category -> seconds).
    Also handles old-format data, where a day was just a plain number instead of a dict."""
    if isinstance(day_data, dict):
        return sum(day_data.values())
    return day_data  # old format: already a plain number of seconds


# ---------- Application ----------
class StudyTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Study Stopwatch")
        self.root.geometry("650x680")
        self.root.resizable(False, False)

        # Stopwatch state
        self.running = False
        self.elapsed_seconds = 0   # time elapsed in the current session
        self.timer_job = None      # job id returned by after(), needed to cancel it
        self.daily_goal_seconds = None  # set when the user defines a goal

        # ---------- Scrollable container ----------
        # Everything is built inside a Canvas + Scrollbar so the window can stay
        # a fixed size even as more sections get added below.
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

        # Let the mouse wheel scroll the canvas while hovering over the window
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

        self.build_widgets()
        self.refresh_summary_table()

    # ---------- Build UI ----------
    def build_widgets(self):
        title_label = tk.Label(self.scrollable_frame, text="Study Stopwatch", font=("Arial", 18, "bold"))
        title_label.pack(pady=(20, 10))

        self.time_label = tk.Label(self.scrollable_frame, text="00:00:00", font=("Consolas", 48))
        self.time_label.pack(pady=10)

        category_frame = tk.Frame(self.scrollable_frame)
        category_frame.pack(pady=(0, 5))

        category_label = tk.Label(category_frame, text="Category:")
        category_label.grid(row=0, column=0, padx=5)

        self.timer_category_entry = tk.Entry(category_frame, width=15)
        self.timer_category_entry.grid(row=0, column=1, padx=5)
        self.timer_category_entry.insert(0, "General")

        button_frame = tk.Frame(self.scrollable_frame)
        button_frame.pack(pady=10)

        self.start_button = tk.Button(button_frame, text="Start", width=10, command=self.start_timer)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = tk.Button(button_frame, text="Stop", width=10, command=self.stop_timer, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=5)

        self.reset_button = tk.Button(button_frame, text="Reset", width=10, command=self.reset_timer)
        self.reset_button.grid(row=0, column=2, padx=5)

        separator = ttk.Separator(self.scrollable_frame, orient="horizontal")
        separator.pack(fill="x", pady=20, padx=20)

        summary_title = tk.Label(self.scrollable_frame, text="Last 7 Days Summary", font=("Arial", 14, "bold"))
        summary_title.pack()

        # Table (Treeview) - date and duration columns
        self.tree = ttk.Treeview(self.scrollable_frame, columns=("date", "duration"), show="headings", height=7)
        self.tree.heading("date", text="Date")
        self.tree.heading("duration", text="Duration")
        self.tree.column("date", width=250, anchor="center")
        self.tree.column("duration", width=250, anchor="center")
        self.tree.pack(pady=10)

        self.total_label = tk.Label(self.scrollable_frame, text="7-Day Total: 0h 0m 0s", font=("Arial", 12, "bold"))
        self.total_label.pack(pady=(0, 5))

        self.average_label = tk.Label(self.scrollable_frame, text="Daily Average: 0h 0m 0s", font=("Arial", 12))
        self.average_label.pack(pady=(0, 5))

        self.category_breakdown_label = tk.Label(self.scrollable_frame, text="", font=("Arial", 11),
                                                   justify="center", wraplength=600)
        self.category_breakdown_label.pack(pady=(0, 5))

        # ---------- Daily goal ----------
        goal_separator = ttk.Separator(self.scrollable_frame, orient="horizontal")
        goal_separator.pack(fill="x", pady=(10, 10), padx=20)

        goal_frame = tk.Frame(self.scrollable_frame)
        goal_frame.pack(pady=5)

        goal_label = tk.Label(goal_frame, text="Daily goal (hours):")
        goal_label.grid(row=0, column=0, padx=5)

        self.goal_entry = tk.Entry(goal_frame, width=6)
        self.goal_entry.grid(row=0, column=1, padx=5)

        self.set_goal_button = tk.Button(goal_frame, text="Set Goal", command=self.set_daily_goal)
        self.set_goal_button.grid(row=0, column=2, padx=5)

        self.goal_status_label = tk.Label(self.scrollable_frame, text="No goal set yet.", font=("Arial", 12, "bold"))
        self.goal_status_label.pack(pady=(5, 5))

        self.goal_progress_bar = ttk.Progressbar(self.scrollable_frame, length=300,
                                                   mode="determinate", maximum=100)
        self.goal_progress_bar.pack(pady=(0, 10))

        # ---------- Manual time entry (for time studied away from the laptop) ----------
        manual_separator = ttk.Separator(self.scrollable_frame, orient="horizontal")
        manual_separator.pack(fill="x", pady=(10, 10), padx=20)

        manual_title = tk.Label(self.scrollable_frame, text="Add Manual Study Time", font=("Arial", 13, "bold"))
        manual_title.pack()

        manual_frame = tk.Frame(self.scrollable_frame)
        manual_frame.pack(pady=10)

        manual_label = tk.Label(manual_frame, text="Minutes studied:")
        manual_label.grid(row=0, column=0, padx=5)

        self.manual_entry = tk.Entry(manual_frame, width=8)
        self.manual_entry.grid(row=0, column=1, padx=5)

        manual_category_label = tk.Label(manual_frame, text="Category:")
        manual_category_label.grid(row=0, column=2, padx=5)

        self.manual_category_entry = tk.Entry(manual_frame, width=12)
        self.manual_category_entry.grid(row=0, column=3, padx=5)
        self.manual_category_entry.insert(0, "General")

        self.add_manual_button = tk.Button(manual_frame, text="Add to Today",
                                            command=self.add_manual_time)
        self.add_manual_button.grid(row=0, column=4, padx=5)

        self.manual_feedback_label = tk.Label(self.scrollable_frame, text="", fg="green")
        self.manual_feedback_label.pack()

    # ---------- Stopwatch logic ----------
    def start_timer(self):
        if self.running:
            return  # don't restart if already running
        self.running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.tick()

    def tick(self):
        """Function that repeatedly calls itself every second. Used INSTEAD of a while loop in tkinter."""
        if not self.running:
            return
        self.elapsed_seconds += 1
        self.update_time_label()
        # Call itself again after 1000 ms (1 second)
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

        # Add the elapsed time to today's total and save it
        if self.elapsed_seconds > 0:
            category = self.timer_category_entry.get().strip() or "General"
            add_seconds_to_today(self.elapsed_seconds, category)
            self.refresh_summary_table()
            self.check_goal_status()

        self.elapsed_seconds = 0
        self.update_time_label()

    def reset_timer(self):
        """Resets without saving (in case you started it by mistake)."""
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        if self.timer_job is not None:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        self.elapsed_seconds = 0
        self.update_time_label()

    # ---------- Manual time entry logic ----------
    def add_manual_time(self):
        """Reads the minutes typed by the user, validates it, and adds it to today's total."""
        raw_value = self.manual_entry.get()

        # input() in the console always gives a string; Entry widgets do too.
        # That's why we still need int() here, and it can still fail.
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

    # ---------- Daily goal logic ----------
    def set_daily_goal(self):
        """Reads the goal in hours, validates it, and stores it as seconds."""
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
        """Compares today's total against the goal and updates the ✅/❌ label and progress bar."""
        if self.daily_goal_seconds is None:
            self.goal_status_label.config(text="No goal set yet.", fg="black")
            self.goal_progress_bar["value"] = 0
            return

        data = load_data()
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_seconds = get_day_total(data.get(today_str, {}))

        # Cap at 100 so the bar doesn't try to go past full when the goal is exceeded
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
        """Reads the data from JSON and renders the last 7 days into the table."""
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
            duration_text = self.format_duration(seconds)
            display_date = day.strftime("%d.%m.%Y") + (" (Today)" if i == 0 else "")
            self.tree.insert("", "end", values=(display_date, duration_text))

        self.total_label.config(text=f"7-Day Total: {self.format_duration(total_seconds)}")

        average_seconds = total_seconds // DAYS_TO_SHOW
        self.average_label.config(text=f"Daily Average: {self.format_duration(average_seconds)}")

        self.update_category_breakdown(data)

    def update_category_breakdown(self, data):
        """Shows today's time split by category, e.g. 'Python: 0h 30m 0s | English: 0h 15m 0s'."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_data = data.get(today_str, {})

        if not isinstance(today_data, dict) or not today_data:
            self.category_breakdown_label.config(text="No categories logged today yet.")
            return

        parts = [f"{category}: {self.format_duration(seconds)}" for category, seconds in today_data.items()]
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

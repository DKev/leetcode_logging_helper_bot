import time
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import json
import os

CONFIG_FILE = "config.json"
LOG_FILE = "session_log.json"
log = []
current_stage_display = None
current_stage_index = 0
current_stage_start_time = None
answer_input = None
idea_input = None
note_input = None
idea_source = None
answer_source = None
question_title = ""
stage_times = {}
stage_durations = {}

question_entry = None

default_config = {
    "name": "",
    "read_time": 300,
    "think_time": 90,
    "code_time": 600,
    "search_time": 600
}

stage_sequence = [
    ("\U0001F4D6 Reading", "read_time"),
    ("\U0001F9E0 Thinking", "think_time"),
    ("💻 Coding", "code_time"),
    ("📖 Reviewing Others' Solutions", "search_time")
]

config = {}

session_finished = False

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return prompt_config()
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def prompt_config():
    def submit():
        cfg = {
            "name": name_entry.get(),
            "read_time": int(read_entry.get()),
            "think_time": int(think_entry.get()),
            "code_time": int(code_entry.get()),
            "search_time": int(search_entry.get())
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        settings.destroy()
        global config
        config = cfg

    settings = tk.Tk()
    settings.title("Initial Configuration")
    settings.geometry("500x600")
    settings.configure(bg="#f5f5f5")

    def section(label_text, explanation):
        frame = tk.Frame(settings, bg="#f5f5f5")
        tk.Label(frame, text=label_text, font=("Helvetica", 14, "bold"), bg="#f5f5f5").pack(anchor="w")
        tk.Label(frame, text=explanation, wraplength=480, justify="left", bg="#f5f5f5").pack(anchor="w")
        frame.pack(pady=(10, 0), padx=20, anchor="w")
        entry = tk.Entry(settings, font=("Helvetica", 12))
        entry.pack(pady=5)
        return entry

    name_entry = section("\U0001F464 Your Name:", "Used to personalize logs or future features like syncing.")
    read_entry = section("\U0001F4D6 Max Reading Time (sec):", "Maximum time allowed for reading the problem before moving on.")
    read_entry.insert(0, str(default_config["read_time"]))
    think_entry = section("\U0001F9E0 Thinking Time (sec):", "How long you want to think about the solution before coding.")
    think_entry.insert(0, str(default_config["think_time"]))
    code_entry = section("💻 Coding Time (sec):", "Time limit to implement your solution.")
    code_entry.insert(0, str(default_config["code_time"]))
    search_entry = section("🔍 Review Others' Time (sec):", "Time for reviewing community solutions or learning from others.")
    search_entry.insert(0, str(default_config["search_time"]))

    tk.Button(settings, text="Save Settings", command=submit, font=("Helvetica", 12), bg="#4CAF50", fg="white", padx=10, pady=5).pack(pady=20)
    settings.mainloop()
    return config

def log_event(event_type, detail=None):
    log.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "detail": detail
    })

def append_stage_display(title, text, font=("Helvetica", 14), color="#222"):
    separator = tk.Frame(root, height=2, bg="#ccc")
    separator.pack(fill="x", padx=20, pady=8)
    block = tk.Label(root, text=f"{title}: {text}", font=font, bg="#f5f5f5", fg=color, wraplength=480, justify="left")
    block.pack(pady=(5, 0), anchor="w", padx=20)
    return block

def toggle_label(textvar):
    return tk.Checkbutton(root, text=textvar, font=("Helvetica", 11), bg="#f5f5f5")

def timer(stage_name, duration_secs, stop_callback):
    global current_stage_display, current_stage_start_time, timer_running
    stop_btn.config(command=stop_callback)
    stop_btn.place(relx=0.5, rely=0.9, anchor='center')
    current_stage_start_time = time.time()
    current_stage_display = append_stage_display(stage_name, "Starting...")
    timer_running = True

    def tick():
        if not timer_running or current_stage_display is None:
            return
        elapsed = time.time() - current_stage_start_time
        remaining = int(duration_secs - elapsed)
        if remaining <= 0:
            stop_callback()
        else:
            mins = remaining // 60
            secs = remaining % 60
            current_stage_display.config(text=f"{stage_name}: {mins:02}:{secs:02}")
            root.after(1000, tick)

    tick()

def stop_stage():
    global current_stage_display, current_stage_index, timer_running, session_finished, note_input, idea_source, answer_source
    timer_running = False
    stop_btn.place_forget()
    stage_name, _ = stage_sequence[current_stage_index]
    elapsed = int(time.time() - current_stage_start_time)
    stage_durations[stage_name] = elapsed
    log_event(f"{stage_name} Duration", f"{elapsed} seconds")
    append_stage_display(f"✅ {stage_name} Complete", f"Duration: {elapsed} seconds", font=("Helvetica", 12, "italic"))
    current_stage_display = None

    def continue_after_input():
        global current_stage_index, session_finished
        current_stage_index += 1
        if current_stage_index < len(stage_sequence):
            next_stage_name, duration_key = stage_sequence[current_stage_index]
            timer(next_stage_name, config[duration_key], stop_stage)
        else:
            append_stage_display("🎉 Session Finished", "Good job!")
            log_event("Session Finished")
            save_log()
            session_finished = True
            tk.Button(root, text="Start Another Session", command=restart_flow, font=("Helvetica", 13), bg="#4CAF50", fg="white").pack(pady=10)

    if stage_name == "\U0001F9E0 Thinking":
        append_stage_display("\U0001F4A1 Your Idea", "Write your idea below (or summarize someone else's):", font=("Helvetica", 13, "bold"))
        idea_input = tk.Text(root, height=4, font=("Helvetica", 12), wrap="word")
        idea_input.pack(fill="x", padx=20, pady=(5, 2))
        idea_source = tk.StringVar(value="self")
        tk.Checkbutton(root, text="This is someone else's idea", variable=idea_source, onvalue="other", offvalue="self", bg="#f5f5f5").pack(pady=(0, 10))
        tk.Button(root, text="Submit Idea", command=continue_after_input, font=("Helvetica", 12), bg="#2196F3", fg="white").pack(pady=5)
        return

    if stage_name == "💻 Coding":
        append_stage_display("✅ Your Answer", "Write your solution below (or summarize someone else's code):", font=("Helvetica", 13, "bold"))
        answer_input = tk.Text(root, height=4, font=("Helvetica", 12), wrap="word")
        answer_input.pack(fill="x", padx=20, pady=(5, 2))
        answer_source = tk.StringVar(value="self")
        tk.Checkbutton(root, text="This is someone else's code", variable=answer_source, onvalue="other", offvalue="self", bg="#f5f5f5").pack(pady=(0, 10))
        tk.Button(root, text="Submit Answer", command=continue_after_input, font=("Helvetica", 12), bg="#2196F3", fg="white").pack(pady=5)
        return

    if stage_name == "📖 Reviewing Others' Solutions":
        append_stage_display("📝 Notes", "Take some notes while reviewing other solutions:", font=("Helvetica", 13, "bold"))
        note_input = tk.Text(root, height=4, font=("Helvetica", 12), wrap="word")
        note_input.pack(fill="x", padx=20, pady=(5, 10))
        tk.Button(root, text="Submit Notes", command=continue_after_input, font=("Helvetica", 12), bg="#2196F3", fg="white").pack(pady=5)
        return

    continue_after_input()

def run_flow():
    global current_stage_index, question_title, session_finished
    current_stage_index = 0
    session_finished = False
    for widget in root.pack_slaves():
        if isinstance(widget, tk.Label) and widget.cget("text").startswith("Welcome"):
            widget.destroy()
    start_btn.pack_forget()

    question_title = question_entry.get().strip()
    if not question_title:
        messagebox.showwarning("Missing Info", "Please enter the problem title or URL before starting.")
        return

    question_entry.pack_forget()
    append_stage_display("\U0001F4CC Problem", question_title, font=("Helvetica", 14, "bold"))
    log_event("Problem", question_title)

    stage_name, duration_key = stage_sequence[0]
    timer(stage_name, config[duration_key], stop_stage)

def restart_flow():
    global idea_input, answer_input, note_input, stage_durations
    idea_input = None
    answer_input = None
    note_input = None
    stage_durations = {}
    run_flow()

def save_log():
    total_time = sum(stage_durations.values())
    entry = {
        "problem": question_title,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "durations": stage_durations,
        "total_time": total_time,
        "thought": idea_input.get("1.0", "end").strip() if idea_input else None,
        "answer": answer_input.get("1.0", "end").strip() if answer_input else None,
        "notes": note_input.get("1.0", "end").strip() if note_input else None,
        "thought_source": idea_source.get() if idea_source else "self",
        "answer_source": answer_source.get() if answer_source else "self"
    }
    if not os.path.exists(LOG_FILE):
        all_logs = []
    else:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            all_logs = json.load(f)
    all_logs.append(entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(all_logs, f, indent=2)

    with open("session_log.md", "a", encoding="utf-8") as md:
        md.write(f"## {entry['timestamp']}\n")
        md.write(f"**Problem**: {entry['problem']}\n\n")
        for stage, duration in entry["durations"].items():
            md.write(f"- {stage}: {duration} sec\n")
        md.write(f"- Total Time: {entry['total_time']} sec\n")
        md.write(f"\n**Idea ({entry['thought_source']})**:\n\n{entry['thought']}\n")
        md.write(f"\n**Answer ({entry['answer_source']})**:\n\n{entry['answer']}\n")
        if entry["notes"]:
            md.write(f"\n**Notes:**\n\n{entry['notes']}\n")
        md.write("\n---\n")

config = load_config()

root = tk.Tk()
root.title("Algorithm Timer Bot")
screen_height = root.winfo_screenheight()
root.geometry(f"500x{screen_height}+0+0")
root.configure(bg="#f5f5f5")

welcome_label = tk.Label(root, text=f"\U0001F44B Welcome, {config['name']}!", font=("Helvetica", 16, "bold"), bg="#f5f5f5")
welcome_label.pack(pady=(20, 5))

question_entry = tk.Entry(root, font=("Helvetica", 12))
question_entry.pack(fill="x", padx=20, pady=(5, 10))
question_entry.insert(0, "Enter today's problem URL or title here")

start_btn = tk.Button(root, text="Start Session", command=run_flow, font=("Helvetica", 14), bg="#4CAF50", fg="white", padx=20, pady=10)
start_btn.pack(pady=(10, 10))

stop_btn = tk.Button(root, text="Stop Current Stage", font=("Helvetica", 12), bg="#f44336", fg="white", padx=15, pady=8)
stop_btn.place_forget()

root.mainloop()
import os
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

EXTENSION_MAP = {
    "PDFs": [".pdf"],
    "Images": [".png", ".jpeg", ".jpg", ".gif"],
    "TextFiles": [".txt", ".md"],
    "Archives": [".zip", ".rar", ".tar", ".gz"],
    "Code": [".py", ".js", ".java", ".cpp", ".html", ".css"],
}

SKIP_FILES = {"day_01.py"}
LOG_FILE = "sort_log.txt"
RESTORE_LOG = "restore_log.txt"


def get_destination_folder(filename):
    ext = os.path.splitext(filename)[1].lower()
    for folder, extensions in EXTENSION_MAP.items():
        if ext in extensions:
            return folder
    return "Others"


def unique_filename(dest_path, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_name = filename
    while os.path.exists(os.path.join(dest_path, new_name)):
        new_name = f"{base}_{counter}{ext}"
        counter += 1
    return new_name


def log_message(message, file=LOG_FILE):
    with open(file, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {message}\n")


def log_restore(original, new):
    with open(RESTORE_LOG, "a", encoding="utf-8") as f:
        f.write(f"{original}||{new}\n")


def sort_files(folder_path, dry_run=False, recursive=False, output_box=None, progress=None):
    summary = {}
    total_files = 0
    for root, dirs, files in os.walk(folder_path):
        if not recursive:
            dirs[:] = []
        for file in files:
            if file not in SKIP_FILES:
                total_files += 1

    processed = 0
    if progress:
        progress["maximum"] = total_files
        progress["value"] = 0

    for root, dirs, files in os.walk(folder_path):
        if not recursive:
            dirs[:] = []

        for file in files:
            if file in SKIP_FILES:
                msg = f"⏭️ Skipped: {file}"
                if output_box:
                    output_box.insert(tk.END, msg + "\n")
                continue

            full_path = os.path.join(root, file)
            if not os.path.isfile(full_path):
                continue

            dest_folder = get_destination_folder(file)
            dest_path = os.path.join(folder_path, dest_folder)
            os.makedirs(dest_path, exist_ok=True)

            new_name = unique_filename(dest_path, file)
            target_path = os.path.join(dest_path, new_name)

            if dry_run:
                msg = f"[DRY RUN] {file} → {dest_folder}/{new_name}"
                if output_box:
                    output_box.insert(tk.END, msg + "\n")
            else:
                shutil.move(full_path, target_path)
                msg = f"✅ Moved: {file} → {dest_folder}/{new_name}"
                if output_box:
                    output_box.insert(tk.END, msg + "\n")
                log_message(msg)
                log_restore(full_path, target_path)
                summary[dest_folder] = summary.get(dest_folder, 0) + 1

            processed += 1
            if progress:
                progress["value"] = processed
                progress.update()

    if output_box:
        output_box.insert(tk.END, "\n📊 Summary Report:\n")
        for folder, count in summary.items():
            output_box.insert(tk.END, f"- {folder}: {count} file(s)\n")


def undo_sorting(output_box=None):
    if not os.path.exists(RESTORE_LOG):
        if output_box:
            output_box.insert(tk.END, "❌ No restore log found.\n")
        return

    restored = 0
    with open(RESTORE_LOG, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in reversed(lines):
        try:
            original, new = line.strip().split("||")
            if os.path.exists(new):
                os.makedirs(os.path.dirname(original), exist_ok=True)
                shutil.move(new, original)
                if output_box:
                    output_box.insert(
                        tk.END, f"↩️ Restored: {new} → {original}\n")
                restored += 1
        except Exception as e:
            if output_box:
                output_box.insert(
                    tk.END, f"⚠️ Failed to restore: {line.strip()} ({e})\n")

    if output_box:
        output_box.insert(
            tk.END, f"\n✅ Undo complete. Restored {restored} file(s).\n")

    os.remove(RESTORE_LOG)

# ----------------- GUI -----------------


def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)


def run_sorter():
    folder = folder_var.get()
    if not folder or not os.path.isdir(folder):
        messagebox.showerror("Error", "Please select a valid folder!")
        return

    dry_run = dry_var.get()
    recursive = recursive_var.get()

    output_box.delete(1.0, tk.END)
    progress_bar["value"] = 0

    sort_files(folder, dry_run=dry_run, recursive=recursive,
               output_box=output_box, progress=progress_bar)
    output_box.insert(tk.END, "\n✨ Sorting completed ! ✨\n")


def run_undo():
    output_box.delete(1.0, tk.END)
    undo_sorting(output_box=output_box)


# ----------------- Modern UI -----------------
root = tk.Tk()
root.title("✨📂 Sortify :-- Smart File Arrangement Tool 📂✨")
root.geometry("717x717")
root.resizable(False, False)

style = ttk.Style()
style.theme_use("clam")

colors = ["#ff9a9e", "#fad0c4", "#a1c4fd", "#c2e9fb", "#fbc2eb", "#a6c1ee"]
color_index = 0


def animate_bg():
    global color_index
    next_color = colors[color_index % len(colors)]
    root.configure(bg=next_color)
    color_index += 1
    root.after(1000, animate_bg)


animate_bg()

folder_var = tk.StringVar()
tk.Label(root, text="📂 Select Folder : 📂", bg="#ffffff",
         font=("Segoe UI", 11, "bold")).pack(pady=5)
tk.Entry(root, textvariable=folder_var, width=60,
         font=("Segoe UI", 10)).pack(padx=10)
tk.Button(root, text="Browse", command=browse_folder, bg="#2196F3", fg="white",
          activebackground="#0b79d0", relief="flat", padx=10, pady=5).pack(pady=5)

dry_var = tk.BooleanVar()
recursive_var = tk.BooleanVar()
tk.Checkbutton(root, text="Dry Run (preview only)",
               variable=dry_var, bg="#ffffff").pack()
tk.Checkbutton(root, text="Sort Subfolders (Recursive)",
               variable=recursive_var, bg="#ffffff").pack()


def on_enter(e): e.widget.config(bg="#4CAF50")
def on_leave(e): e.widget.config(bg="green")
def on_enter_red(e): e.widget.config(bg="#e53935")
def on_leave_red(e): e.widget.config(bg="red")


btn_sort = tk.Button(root, text="Start Sorting", command=run_sorter,
                     bg="green", fg="white", padx=12, pady=6, relief="flat", font=("Segoe UI", 10, "bold"))
btn_sort.pack(pady=10)
btn_sort.bind("<Enter>", on_enter)
btn_sort.bind("<Leave>", on_leave)

btn_undo = tk.Button(root, text="Undo Last Sorting", command=run_undo,
                     bg="red", fg="white", padx=12, pady=6, relief="flat", font=("Segoe UI", 10, "bold"))
btn_undo.pack(pady=5)
btn_undo.bind("<Enter>", on_enter_red)
btn_undo.bind("<Leave>", on_leave_red)

progress_bar = ttk.Progressbar(
    root, orient="horizontal", length=500, mode="determinate")
progress_bar.pack(pady=10)

output_box = scrolledtext.ScrolledText(
    root, width=85, height=20, wrap=tk.WORD, font=("Consolas", 10))
output_box.pack(padx=10, pady=10)

root.mainloop()

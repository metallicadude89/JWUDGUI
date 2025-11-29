import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import urllib.request

# --- Config ---
JWUD_JAR = "JWUDTool.jar"
COMMON_KEY_FILE = "common.key.txt"

# --- Auto-download JWUDTool.jar ---
if not os.path.exists(JWUD_JAR):
    try:
        print("Downloading JWUDTool.jar...")
        urllib.request.urlretrieve(
            "https://github.com/Maschell/JWUDTool/releases/download/0.4/JWUDTool-0.4.jar",
            JWUD_JAR
        )
        print("JWUDTool.jar downloaded.")
    except Exception as e:
        print("Failed to download JWUDTool.jar:", e)
        messagebox.showerror("Error", f"Failed to download JWUDTool.jar:\n{e}")

# --- Load saved common key ---
if os.path.exists(COMMON_KEY_FILE):
    with open(COMMON_KEY_FILE, "r") as f:
        saved_key = f.read().strip()
else:
    saved_key = ""

# --- Utility functions ---
def append_output(text_widget, text):
    try:
        text_widget.insert(tk.END, text + "\n")
        text_widget.see(tk.END)
    except:
        pass

def save_common_key(key):
    with open(COMMON_KEY_FILE, "w") as f:
        f.write(key)

def run_jwud_command(cmd, text_widget, progress_bar):
    append_output(text_widget, f"Running: {cmd}")
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
        for line in process.stdout:
            line = line.strip()
            append_output(text_widget, line)
            # Extract percentage from output like: "Decompressing: 195.00MB done (0.82%)"
            if "(" in line and "%" in line:
                try:
                    perc = float(line.split("(")[1].split("%")[0])
                    progress_bar['value'] = perc
                except:
                    pass
        process.wait()
        append_output(text_widget, "Finished!")
        progress_bar['value'] = 100
        messagebox.showinfo("Done", "JWUDTool finished running.")
    except Exception as e:
        append_output(text_widget, f"Error: {e}")
        messagebox.showerror("Error", f"Failed to run JWUDTool:\n{e}")
    finally:
        progress_bar.stop()

def run_threaded_command(cmd, text_widget, progress_bar):
    threading.Thread(target=run_jwud_command, args=(cmd, text_widget, progress_bar), daemon=True).start()

# --- Tooltip class ---
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)
    def show(self, event=None):
        if self.tip or not self.text: return
        x, y = self.widget.winfo_rootx()+20, self.widget.winfo_rooty()+20
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, background="lightyellow", relief="solid", borderwidth=1).pack()
    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

# --- GUI Setup ---
root = tk.Tk()
root.title("JWUDTool GUI")
root.geometry("1000x750")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

tab_control = ttk.Notebook(root)

# --- Tabs ---
def create_tab(name, action, file_types):
    tab = ttk.Frame(tab_control)
    tab_control.add(tab, text=name)
    for i in range(3):
        tab.columnconfigure(i, weight=1, uniform="col")
    for r in range(9):
        tab.rowconfigure(r, weight=1)

    # Batch Files List
    tk.Label(tab, text="Files (Add or Remove, batch processing):").grid(row=0, column=0, columnspan=3, sticky="w", pady=2)
    batch_list = tk.Listbox(tab, selectmode=tk.EXTENDED, height=8)
    batch_list.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=5, padx=5)

    def add_files():
        files = filedialog.askopenfilenames(filetypes=[("Files", " ".join(file_types))])
        for f in files:
            if os.path.isfile(f):
                batch_list.insert(tk.END, f)

    def remove_selected():
        selected = batch_list.curselection()
        for i in reversed(selected):
            batch_list.delete(i)

    tk.Button(tab, text="Add File(s)", command=add_files, width=15).grid(row=2, column=0, pady=5)
    tk.Button(tab, text="Remove Selected", command=remove_selected, width=15).grid(row=2, column=1, pady=5)

    # Output Folder
    output_var = tk.StringVar()
    tk.Label(tab, text="Output Folder:").grid(row=3, column=0, sticky="w", pady=2)
    tk.Entry(tab, textvariable=output_var).grid(row=3, column=1, sticky="ew", padx=2)
    tk.Button(tab, text="Browse", command=lambda: output_var.set(filedialog.askdirectory()), width=15).grid(row=3, column=2, pady=2)

    # RAM allocation
    ram_var = tk.StringVar(value="4")
    tk.Label(tab, text="Java RAM (GB, optional):").grid(row=4, column=0, sticky="w")
    tk.Entry(tab, textvariable=ram_var, width=6).grid(row=4, column=1, sticky="w")
    ToolTip(tab.grid_slaves(row=4,column=1)[0],
            "Sets maximum RAM for Java (e.g., 4 for 4GB).\nOnly change if your system has enough free RAM.")

    # Options
    no_verify_var = tk.BooleanVar()
    dev_var = tk.BooleanVar()
    overwrite_var = tk.BooleanVar()
    tk.Checkbutton(tab, text="-noVerify", variable=no_verify_var).grid(row=5, column=0, sticky="w")
    tk.Checkbutton(tab, text="-dev", variable=dev_var).grid(row=5, column=1, sticky="w")
    tk.Checkbutton(tab, text="-overwrite", variable=overwrite_var).grid(row=5, column=2, sticky="w")
    ToolTip(tab.grid_slaves(row=5,column=0)[0], "Disables verification after (de)compressing")
    ToolTip(tab.grid_slaves(row=5,column=1)[0], "Use dev mode, required for discs without a titlekey")
    ToolTip(tab.grid_slaves(row=5,column=2)[0], "Overwrite existing files if present")

    # Progress / Output
    progress = ttk.Progressbar(tab, mode="determinate", maximum=100)
    progress.grid(row=6, column=0, columnspan=3, sticky="ew", pady=5, padx=5)
    output_text = tk.Text(tab)
    output_text.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=5, padx=5)

    # Action
    def run_action():
        files = batch_list.get(0, tk.END)
        out_folder = output_var.get()
        if not files or not out_folder:
            messagebox.showwarning("Warning","Select files and output folder!")
            return
        try:
            ram_value = int(float(ram_var.get()))
            ram_option = f"-Xmx{ram_value}G"
        except:
            ram_option = ""
        for file in files:
            base_name = os.path.splitext(os.path.basename(file))[0]
            out_file = os.path.join(out_folder, base_name + (".wud" if action == "-decompress" else ".wux"))
            os.makedirs(os.path.dirname(out_file), exist_ok=True)
            cmd = f'java {ram_option} -jar "{JWUD_JAR}" {action} -in "{file}" -out "{out_file}"'
            if no_verify_var.get(): cmd += " -noVerify"
            if dev_var.get(): cmd += " -dev"
            if overwrite_var.get(): cmd += " -overwrite"
            run_threaded_command(cmd, output_text, progress)

    # Centered "GO" button
    go_btn = tk.Button(tab, text="GO", command=run_action, bg="lightgrey", width=15)
    go_btn.grid(row=8, column=1, pady=10)

    return tab

# Create Tabs
create_tab("WUX -> WUD", "-decompress", ["*.wux","*.wud","*.wua"])
create_tab("WUD -> WUX", "-compress", ["*.wud"])
create_tab("WUA -> WUX", "-compress", ["*.wua"])
create_tab("WUD -> WUA", "-compress -format wua", ["*.wud"])
decrypt_tab = create_tab("Decrypt WUD", "-decrypt", ["*.wud","*.wux","*.wua"])
tk.Label(decrypt_tab, text="Wii U Common Key (hex):").grid(row=4, column=0, sticky="w")
commonkey_var = tk.StringVar(value=saved_key)
tk.Entry(decrypt_tab, textvariable=commonkey_var).grid(row=4, column=1, columnspan=2, sticky="ew")
tk.Label(decrypt_tab, text="Title Key (hex):").grid(row=5, column=0, sticky="w")
titlekey_var = tk.StringVar()
tk.Entry(decrypt_tab, textvariable=titlekey_var).grid(row=5, column=1, columnspan=2, sticky="ew")

tab_control.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
root.mainloop()

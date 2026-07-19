import ast
import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def collect_tests_from_file(file_path):
    """Parses a single Python file using AST to find all test functions and test classes/methods."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            node = ast.parse(f.read(), filename=file_path)

        tests = []
        for top_level_item in node.body:
            # Standalone functions starting with 'test_'
            if isinstance(top_level_item, ast.FunctionDef):
                if top_level_item.name.startswith("test_"):
                    tests.append(top_level_item.name)

            # Classes starting with 'Test'
            elif isinstance(top_level_item, ast.ClassDef):
                if top_level_item.name.startswith("Test"):
                    for sub_item in top_level_item.body:
                        if isinstance(sub_item, ast.FunctionDef):
                            if sub_item.name.startswith("test_"):
                                tests.append(
                                    f"{top_level_item.name}::{sub_item.name}"
                                )
        return tests
    except Exception as e:
        return [f"Error parsing file: {e}"]


def collect_tests_from_folder(folder_path):
    """Scans all Python files in the given directory and collects their test cases."""
    all_results = {}
    try:
        files = [f for f in os.listdir(folder_path) if f.endswith(".py")]
        for file_name in files:
            full_path = os.path.join(folder_path, file_name)
            tests = collect_tests_from_file(full_path)
            if tests:
                all_results[file_name] = tests
        return all_results
    except Exception as e:
        messagebox.showerror("Error", f"Could not read directory:\n{e}")
        return {}


class PytestGranularGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Pytest Selective Test Runner & Exporter")
        self.root.geometry("1000x780")

        self.selected_files = []
        self.current_folder = ""

        # Top Section - Choose Target(s)
        file_frame = ttk.LabelFrame(root, text="Step 1: Choose Target(s)")
        file_frame.pack(fill="x", padx=15, pady=5)

        self.files_display_var = tk.StringVar(value="No files selected.")
        ttk.Entry(
            file_frame, textvariable=self.files_display_var, state="readonly"
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        ttk.Button(
            file_frame, text="Browse Files (Multi)", command=self.browse_files
        ).grid(row=0, column=2, padx=10, pady=5, sticky="e")

        self.folder_path_var = tk.StringVar(value="No folder selected.")
        ttk.Entry(
            file_frame, textvariable=self.folder_path_var, state="readonly"
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        ttk.Button(
            file_frame, text="Browse Folder", command=self.browse_folder
        ).grid(row=1, column=2, padx=10, pady=5, sticky="e")

        file_frame.columnconfigure(1, weight=1)

        # Middle Section - Discovery Buttons
        disc_frame = ttk.Frame(root)
        disc_frame.pack(fill="x", padx=15, pady=5)

        ttk.Button(
            disc_frame,
            text="🔍 Discover Tests from Selected Files",
            command=self.discover_from_files,
        ).pack(side="left", fill="x", expand=True, padx=5)

        ttk.Button(
            disc_frame,
            text="🔍 Discover Tests from Selected Folder",
            command=self.discover_from_folder,
        ).pack(side="right", fill="x", expand=True, padx=5)

        # Content Split Layout (Left: Test Listbox | Right: Live Console)
        content_pane = ttk.PanedWindow(root, orient="horizontal")
        content_pane.pack(fill="both", expand=True, padx=15, pady=5)

        # Left Column - Interactive Test Selector
        list_frame = ttk.LabelFrame(content_pane, text="Discovered Tests (Select single/multiple)")
        content_pane.add(list_frame, weight=1)

        self.test_listbox = tk.Listbox(
            list_frame, selectmode=tk.MULTIPLE, font=("Courier", 10), exportselection=False
        )
        self.test_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        list_scroll = ttk.Scrollbar(list_frame, command=self.test_listbox.yview)
        list_scroll.pack(side="right", fill="y")
        self.test_listbox.config(yscrollcommand=list_scroll.set)

        # Right Column - Execution Log Console
        console_frame = ttk.LabelFrame(content_pane, text="Execution Output Console")
        content_pane.add(console_frame, weight=1)

        self.txt_output = tk.Text(
            console_frame, wrap="word", font=("Courier", 9), bg="#1e1e1e", fg="#ffffff"
        )
        self.txt_output.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        console_scroll = ttk.Scrollbar(console_frame, command=self.txt_output.yview)
        console_scroll.pack(side="right", fill="y")
        self.txt_output.config(yscrollcommand=console_scroll.set)

        # Bottom Section - Run & Export Controls
        btn_control_frame = ttk.Frame(root)
        btn_control_frame.pack(fill="x", padx=15, pady=10)

        # Running the tests
        ttk.Button(
            btn_control_frame,
            text="Run Highlighted Tests 🏃",
            command=self.run_highlighted_tests_thread,
            style="Accent.TButton",
        ).pack(side="left", fill="x", expand=True, padx=5, ipady=5)

        # Exporting output
        ttk.Button(
            btn_control_frame,
            text="💾 Export Console Log",
            command=self.export_console_log,
        ).pack(side="right", fill="x", expand=True, padx=5, ipady=5)

    def browse_files(self):
        files_selected = filedialog.askopenfilenames(
            filetypes=[("Python Files", "*.py")]
        )
        if files_selected:
            self.selected_files = list(files_selected)
            names = [os.path.basename(f) for f in self.selected_files]
            self.files_display_var.set(f"({len(names)} files) " + ", ".join(names))
            self.folder_path_var.set("No folder selected.")
            self.current_folder = ""

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path_var.set(folder_selected)
            self.selected_files = []
            self.files_display_var.set("No files selected.")
            self.current_folder = folder_selected

    def print_to_console(self, text_str):
        self.txt_output.insert(tk.END, text_str)
        self.txt_output.see(tk.END)

    def discover_from_files(self):
        if not self.selected_files:
            messagebox.showwarning("Warning", "Select files to search first!")
            return

        self.test_listbox.delete(0, tk.END)
        for file_path in self.selected_files:
            test_cases = collect_tests_from_file(file_path)
            for test in test_cases:
                self.test_listbox.insert(tk.END, f"{file_path}::{test}")

    def discover_from_folder(self):
        if not self.current_folder:
            messagebox.showwarning("Warning", "Select a folder to search first!")
            return

        self.test_listbox.delete(0, tk.END)
        discovered_data = collect_tests_from_folder(self.current_folder)
        for file_name, tests in discovered_data.items():
            full_file_path = os.path.join(self.current_folder, file_name)
            for test in tests:
                self.test_listbox.insert(tk.END, f"{full_file_path}::{test}")

    def run_highlighted_tests_thread(self):
        selected_indices = self.test_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one test case from the list!")
            return

        selected_tests = [self.test_listbox.get(idx) for idx in selected_indices]

        threading.Thread(
            target=self.execute_pytest_subprocess, args=(selected_tests,), daemon=True
        ).start()

    def execute_pytest_subprocess(self, test_targets):
        self.txt_output.delete("1.0", tk.END)
        self.print_to_console(f"🚀 Running {len(test_targets)} selected tests...\n")
        self.print_to_console("=" * 60 + "\n")

        try:
            process = subprocess.Popen(
                ["python", "-m", "pytest", "-v"] + test_targets,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    self.print_to_console(line)

            process.wait()
            self.print_to_console("\n" + "=" * 60 + "\n")
            self.print_to_console(
                f"Execution finished with exit code {process.returncode}\n"
            )

        except Exception as e:
            self.print_to_console(f"\nSubprocess crash:\n{e}\n")

    def export_console_log(self):
        """Saves the current contents of the output text box to a file."""
        # Get all text from the console window
        console_content = self.txt_output.get("1.0", tk.END).strip()
        
        if not console_content:
            messagebox.showwarning("Warning", "Console is empty! Nothing to export.")
            return

        # Open a save dialog window
        file_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save Execution Output Log"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(console_content)
                messagebox.showinfo("Success", f"Log successfully saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log file:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use("clam")
    app = PytestGranularGUI(root)
    root.mainloop()
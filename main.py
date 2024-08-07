import os
import shutil
import math
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading

ctk.set_appearance_mode("System")  # Modes: system (default), light, dark
ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green


class AddonSplitterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Garry's Mod Addon Splitter")
        self.geometry("700x600")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(5, weight=1)

        self.create_widgets()

    def create_widgets(self):
        # Input Addon Path
        self.input_path = ctk.StringVar()
        ctk.CTkLabel(self, text="Input Addon Path:").grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))
        ctk.CTkEntry(self, textvariable=self.input_path, width=400).grid(row=0, column=1, padx=(0, 20), pady=(20, 10),
                                                                         sticky="ew")
        ctk.CTkButton(self, text="Browse", command=self.browse_input, width=100).grid(row=0, column=2, padx=(0, 20),
                                                                                      pady=(20, 10))

        # Output Directory
        self.output_path = ctk.StringVar()
        ctk.CTkLabel(self, text="Output Directory:").grid(row=1, column=0, sticky="w", padx=20, pady=10)
        ctk.CTkEntry(self, textvariable=self.output_path, width=400).grid(row=1, column=1, padx=(0, 20), pady=10,
                                                                          sticky="ew")
        ctk.CTkButton(self, text="Browse", command=self.browse_output, width=100).grid(row=1, column=2, padx=(0, 20),
                                                                                       pady=10)

        # Max Size
        self.max_size = ctk.StringVar(value="300")
        ctk.CTkLabel(self, text="Max Size (MB):").grid(row=2, column=0, sticky="w", padx=20, pady=10)
        ctk.CTkEntry(self, textvariable=self.max_size, width=100).grid(row=2, column=1, sticky="w", padx=(0, 20),
                                                                       pady=10)

        # Split Button
        self.split_button = ctk.CTkButton(self, text="Split Addon", command=self.split_addon, width=200)
        self.split_button.grid(row=3, column=1, pady=20)

        # Progress Bar
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.grid(row=4, column=0, columnspan=3, padx=20, pady=(0, 20), sticky="ew")
        self.progress.set(0)

        # Statistics
        self.stats_text = ctk.CTkTextbox(self, height=200, width=400, wrap="word")
        self.stats_text.grid(row=5, column=0, columnspan=3, padx=20, pady=(0, 20), sticky="nsew")

    def browse_input(self):
        path = filedialog.askdirectory()
        if path:
            self.input_path.set(path)
            self.update_statistics()

    def browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_path.set(path)

    def update_statistics(self):
        stats = self.get_addon_statistics(self.input_path.get())
        self.stats_text.delete('0.0', ctk.END)
        self.stats_text.insert(ctk.END, stats)

    def get_addon_statistics(self, path):
        total_size = 0
        file_count = 0
        folder_count = 0
        extension_count = {}

        for root, dirs, files in os.walk(path):
            folder_count += len(dirs)
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                total_size += file_size
                file_count += 1

                _, ext = os.path.splitext(file)
                extension_count[ext] = extension_count.get(ext, 0) + 1

        stats = f"Addon Statistics:\n"
        stats += f"Total Size: {total_size / (1024 * 1024):.2f} MB\n"
        stats += f"Total Files: {file_count}\n"
        stats += f"Total Folders: {folder_count}\n"
        stats += f"File Extensions:\n"
        for ext, count in sorted(extension_count.items(), key=lambda x: x[1], reverse=True):
            stats += f"  {ext}: {count}\n"

        return stats

    def split_addon(self):
        input_path = self.input_path.get()
        output_path = self.output_path.get()
        max_size_mb = int(self.max_size.get())

        if not input_path or not output_path:
            messagebox.showerror("Error", "Please select both input and output paths.")
            return

        self.split_button.configure(state="disabled")
        self.progress.set(0)

        threading.Thread(target=self._split_addon_thread, args=(input_path, output_path, max_size_mb)).start()

    def _split_addon_thread(self, input_path, output_path, max_size_mb):
        max_size_bytes = max_size_mb * 1024 * 1024
        total_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                         for dirpath, _, filenames in os.walk(input_path)
                         for filename in filenames)

        current_part = 1
        current_part_size = 0
        files_to_copy = []

        for root, _, files in os.walk(input_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)

                if current_part_size + file_size > max_size_bytes:
                    self.copy_files(files_to_copy, input_path, output_path, current_part)
                    current_part += 1
                    current_part_size = 0
                    files_to_copy = []

                files_to_copy.append(file_path)
                current_part_size += file_size

                # Update progress
                progress = (current_part_size + (current_part - 1) * max_size_bytes) / total_size
                self.after(0, self.progress.set, progress)

        if files_to_copy:
            self.copy_files(files_to_copy, input_path, output_path, current_part)

        self.after(0, messagebox.showinfo, "Success", f"Addon split into {current_part} parts.")
        self.after(0, self.progress.set, 1)
        self.after(0, self.split_button.configure, {"state": "normal"})  # Re-enable the button

    def copy_files(self, files, source_path, output_dir, part_number):
        part_dir = os.path.join(output_dir, f"addon_part_{part_number}")
        os.makedirs(part_dir, exist_ok=True)

        for file_path in files:
            rel_path = os.path.relpath(file_path, source_path)
            dest_path = os.path.join(part_dir, rel_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(file_path, dest_path)


if __name__ == "__main__":
    app = AddonSplitterApp()
    app.mainloop()
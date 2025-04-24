import customtkinter as ctk
import subprocess
import os
import sys
import threading
import time
import shutil
from PIL import Image, ImageTk
from tkinter import messagebox, simpledialog, filedialog, Toplevel

# Import the version and the name of the application
from version import __version__, __app__

BUTTON_WIDTH = 200  # Fixed width for buttons

class EggsMakerApp:
    def __init__(self, root):
        # Base path: works both in development and after compilation
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        self.root = root
        self.root.title(f"{__app__} - Version {__version__}")

        # Load icon
        icon_image = Image.open(
            os.path.join(
                base_path,
                "assets",
                "eggsmaker.png"))
        icon_photo = ImageTk.PhotoImage(icon_image)
        self.root.iconphoto(True, icon_photo)

        self.password = None
        self.eggs_path = self.detect_eggs_path()

        # Variables for timers and counters
        self.copying = False          # Indicates if copying is in progress
        self.iso_generating = False   # Indicates if ISO generation is in progress
        self.total_running = False    # Controls if the total is running

        self.copy_elapsed = 0         # Time elapsed in copying
        self.iso_elapsed = 0          # Time elapsed in ISO generation

        self.copy_counter = 0         # Counter for copies made

        # Initialize appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Variables for switches
        self.prep_switch_var = ctk.BooleanVar(value=True)
        self.calamares_switch_var = ctk.BooleanVar(value=False)
        self.replica_switch_var = ctk.BooleanVar(value=False)
        self.edit_config_switch_var = ctk.BooleanVar(value=False)
        self.iso_data_switch_var = ctk.BooleanVar(
            value=False)   # No data / with data
        self.iso_comp_switch_var = ctk.BooleanVar(
            value=False)   # Standard / Maximum compression
        self.copy_speed_switch_var = ctk.BooleanVar(
            value=False)   # Slow / Fast copy

        self.create_widgets()
        self.create_action_buttons()
        self.request_password()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update_versions()
        self.adjust_window_size()
        self.label_iso_size = ctk.CTkLabel(
            self.main_frame, text="", font=(
                "Courier", 14, "bold"), text_color="red")
        # Adjust the location according to where the button was
        self.label_iso_size.grid(row=2, column=0, pady=(0, 10))

    def detect_eggs_path(self):
        try:
            path = subprocess.check_output(
                "which eggs", shell=True, text=True).strip()
            return path if path else "/usr/bin/eggs"
        except Exception:
            return "/usr/bin/eggs"

    def create_widgets(self):
        # --- Main Frame ---
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # --- Terminal Area (height 250) ---
        self.terminal_frame = ctk.CTkFrame(self.main_frame)
        self.terminal_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.terminal_text = ctk.CTkTextbox(
            self.terminal_frame,
            fg_color="black",
            text_color="lime",
            wrap="word",
            height=250)
        self.terminal_text.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Top Panel: 4 panels in a row ---
        self.top_controls = ctk.CTkFrame(self.main_frame)
        self.top_controls.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        for col in range(4):
            self.top_controls.grid_columnconfigure(col, weight=1)

        # Panel 1: Previous Actions
        self.frame_actions = ctk.CTkFrame(self.top_controls)
        self.frame_actions.grid(
            row=0, column=0, padx=5, pady=5, sticky="nsew")
        label_actions = ctk.CTkLabel(
            self.frame_actions, text="Previous Actions", font=(
                "Arial", 16, "bold"), text_color="orange")
        label_actions.pack(pady=5)
        self.prep_switch = ctk.CTkSwitch(
            self.frame_actions,
            text="Preparation (Clean and create environment)",
            variable=self.prep_switch_var,
            text_color="white")
        self.prep_switch.pack(anchor="w", padx=5, pady=2)
        self.calamares_switch = ctk.CTkSwitch(
            self.frame_actions,
            text="Install/Update Calamares",
            variable=self.calamares_switch_var,
            text_color="white")
        self.calamares_switch.pack(anchor="w", padx=5, pady=2)
        self.btn_pre = ctk.CTkButton(
            self.frame_actions,
            text="Apply",
            command=self.apply_pre_actions,
            width=BUTTON_WIDTH)
        self.btn_pre.pack(side="bottom", pady=5)

        # Panel 2: Additional Options
        self.frame_options = ctk.CTkFrame(self.top_controls)
        self.frame_options.grid(
            row=0, column=1, padx=5, pady=5, sticky="nsew")
        label_options = ctk.CTkLabel(
            self.frame_options, text="Additional Options", font=(
                "Arial", 16, "bold"), text_color="orange")
        label_options.pack(pady=5)
        self.replica_switch = ctk.CTkSwitch(
            self.frame_options,
            text="Generate replica of the current desktop",
            variable=self.replica_switch_var,
            state="disabled",
            text_color="white")
        self.replica_switch.pack(anchor="w", padx=5, pady=2)
        self.edit_config_switch = ctk.CTkSwitch(
            self.frame_options,
            text="Edit ISO configuration",
            variable=self.edit_config_switch_var,
            state="disabled",
            text_color="white")
        self.edit_config_switch.pack(anchor="w", padx=5, pady=2)
        self.btn_options = ctk.CTkButton(
            self.frame_options,
            text="Apply",
            command=self.apply_additional_options,
            state="disabled",
            width=BUTTON_WIDTH)
        self.btn_options.pack(side="bottom", pady=5)

        # Panel 3: Generate ISO
        self.frame_generate = ctk.CTkFrame(self.top_controls)
        self.frame_generate.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        label_generate = ctk.CTkLabel(
            self.frame_generate, text="Generate ISO", font=(
                "Arial", 16, "bold"), text_color="orange")
        label_generate.pack(pady=5)
        self.iso_data_switch = ctk.CTkSwitch(
            self.frame_generate,
            text="Include data",
            variable=self.iso_data_switch_var,
            state="disabled",
            text_color="white")
        self.iso_data_switch.pack(anchor="w", padx=5, pady=2)
        self.iso_comp_switch = ctk.CTkSwitch(
            self.frame_generate,
            text="Maximum compression",
            variable=self.iso_comp_switch_var,
            text_color="white")
        self.iso_comp_switch.pack(anchor="w", padx=5, pady=2)
        self.btn_generate = ctk.CTkButton(
            self.frame_generate,
            text="Generate ISO",
            command=self.apply_iso_generation,
            state="disabled",
            width=BUTTON_WIDTH)
        self.btn_generate.pack(side="bottom", pady=5)

        # Panel 4: Copy ISO
        self.frame_copy = ctk.CTkFrame(self.top_controls)
        self.frame_copy.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        label_copy = ctk.CTkLabel(
            self.frame_copy, text="Copy ISO", font=(
                "Arial", 16, "bold"), text_color="orange")
        label_copy.pack(pady=5)
        self.copy_speed_switch = ctk.CTkSwitch(
            self.frame_copy,
            text="Fast Copy",
            variable=self.copy_speed_switch_var,
            text_color="white")
        self.copy_speed_switch.pack(anchor="w", padx=5, pady=2)
        self.btn_copy = ctk.CTkButton(self.frame_copy, text="Copy Generated ISO",
                                       command=lambda: self.copy_iso(self.btn_copy), state="disabled", width=BUTTON_WIDTH)
        self.btn_copy.pack(side="bottom", pady=5)

        # --- Bottom Panel: Status and versions ---
        self.bottom_controls = ctk.CTkFrame(self.main_frame)
        self.bottom_controls.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.bottom_controls.grid_columnconfigure(0, weight=2)
        self.bottom_controls.grid_columnconfigure(1, weight=1)

        # Status: label "Running", progress bar, percentage, copy counter and timers.
        self.frame_status = ctk.CTkFrame(self.bottom_controls)
        self.frame_status.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.running_label = ctk.CTkLabel(
            self.frame_status, text="", font=(
                "Arial", 20, "bold"), text_color="orange")
        self.running_label.pack(pady=5)
        self.progress_bar = ctk.CTkProgressBar(
            self.frame_status, height=15, progress_color="orange")
        self.progress_bar.pack(fill="x", padx=5, pady=(5, 2))
        self.copy_percentage_label = ctk.CTkLabel(
            self.frame_status, text="0%", font=("Arial", 12))
        self.copy_percentage_label.pack(padx=5, pady=(0, 2))
        self.counter_label = ctk.CTkLabel(
            self.frame_status,
            text="Copies made: 0",
            font=(
                "Arial",
                12))
        self.counter_label.pack(padx=5, pady=(0, 5))
        self.chrono_frame = ctk.CTkFrame(self.frame_status)
        self.chrono_frame.pack(fill="x", padx=5, pady=(0, 10))
        self.chrono_frame.grid_columnconfigure(0, weight=1)
        self.chrono_frame.grid_columnconfigure(1, weight=1)
        self.chrono_frame.grid_columnconfigure(2, weight=1)
        self.copy_chrono_label = ctk.CTkLabel(
            self.chrono_frame, text="", text_color="cyan", font=(
                "Arial", 20, "bold"), anchor="center")
        self.copy_chrono_label.grid(row=0, column=0, padx=5, sticky="nsew")
        self.iso_chrono_label = ctk.CTkLabel(
            self.chrono_frame, text="", text_color="red", font=(
                "Arial", 20, "bold"), anchor="center")
        self.iso_chrono_label.grid(row=0, column=1, padx=5, sticky="nsew")
        self.total_chrono_label = ctk.CTkLabel(
            self.chrono_frame, text="", text_color="#39FF14", font=(
                "Arial", 20, "bold"), anchor="center")
        self.total_chrono_label.grid(row=0, column=2, padx=5, sticky="nsew")

        # Versions panel
        self.versions_frame = ctk.CTkFrame(self.bottom_controls)
        self.versions_frame.grid(
            row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.version_penguins_label = ctk.CTkLabel(
            self.versions_frame,
            text="Penguins Eggs: N/A",
            font=("Arial", 14),  # Increased font size
            text_color="orange",
            anchor="center",  # Center horizontally
            justify="center"  # Center vertically
        )
        self.version_penguins_label.pack(pady=10, fill="both")  # Adjust space

        self.version_calamares_label = ctk.CTkLabel(
            self.versions_frame,
            text="Calamares: N/A",
            font=("Arial", 14),  # Increased font size
            text_color="orange",
            anchor="center",  # Center horizontally
            justify="center"  # Center vertically
        )
        self.version_calamares_label.pack(pady=10, fill="both")  # Adjust space

        self.version_app_label = ctk.CTkLabel(
            self.versions_frame,
            text=f"{__app__}: {__version__}",
            font=("Arial", 14),  # Increased font size
            text_color="orange",
            anchor="center",  # Center horizontally
            justify="center"  # Center vertically
        )
        self.version_app_label.pack(pady=10, fill="both")  # Adjust space

        # Main grid configuration of main_frame
        self.main_frame.grid_rowconfigure(0, weight=4)  # Terminal
        self.main_frame.grid_rowconfigure(1, weight=1)  # Top controls
        self.main_frame.grid_rowconfigure(2, weight=1)  # Bottom controls
        self.main_frame.grid_columnconfigure(0, weight=1)

    # --- 2) In create_action_buttons(), after defining exit_button, add the new label ---
    def create_action_buttons(self):
        """Create the bottom row with the buttons: Info, Restart eggsmaker and Exit."""
        self.action_frame = ctk.CTkFrame(self.main_frame)
        self.action_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        for i in range(3):
            self.action_frame.grid_columnconfigure(i, weight=1)

        # Info Button
        self.info_button = ctk.CTkButton(
            self.action_frame,
            text="Info",
            command=self.show_info,
            width=BUTTON_WIDTH
        )
        self.info_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # ISO SIZE LABEL (initially hidden)
        self.size_label = ctk.CTkLabel(
            self.action_frame,
            text="ISO Size: N/A",
            font=("Arial", 20, "bold"),
            text_color="red"
        )
        self.size_label.grid(row=0, column=1, padx=5, pady=5)
        self.size_label.grid_remove()  # Hide the label at the start

        # Exit Button
        self.exit_button = ctk.CTkButton(
            self.action_frame,
            text="Exit",
            command=self.on_close,
            width=BUTTON_WIDTH
        )
        self.exit_button.grid(row=0, column=2, padx=5, pady=5, sticky="e")

    def adjust_window_size(self):
        self.root.update_idletasks()
        width = 1000
        min_height = 700
        self.root.geometry(
            f"{width}x{min_height}+{(self.root.winfo_screenwidth() - width) // 2}+50")
        self.root.minsize(width, min_height)

    def update_versions(self):
        def get_eggs_version():
            try:
                result = subprocess.run(f"sudo -S {self.eggs_path} --version",
                                        input=self.password, shell=True, capture_output=True, text=True)
                version = result.stdout.strip().split("\n")[0]
                return version
            except:
                return "N/A"

        def get_calamares_version():
            try:
                result = subprocess.run(
                    "calamares --version",
                    shell=True,
                    capture_output=True,
                    text=True)
                version = result.stdout.strip().split()[-1]
                return version
            except:
                return "N/A"
        eggs_ver = get_eggs_version()
        calamares_ver = get_calamares_version()
        self.version_penguins_label.configure(
            text=f"Penguins Eggs: {eggs_ver}")
        self.version_calamares_label.configure(
            text=f"Calamares: {calamares_ver}")
        self.version_app_label.configure(text=f"{__app__}: {__version__}")

    def request_password(self):
        self.password = simpledialog.askstring(
            "Authentication required",
            "Enter your sudo password:",
            show="*")
        if not self.password:
            messagebox.showerror(
                "Error", "Password required to continue")
            self.root.destroy()

    # ----------- Timer Functions -----------
    def update_copy_timer(self):
        """Update the copy timer label while copying."""
        while self.copying:
            time.sleep(1)
            self.copy_elapsed += 1
            elapsed_str = time.strftime(
                "%H:%M:%S", time.gmtime(
                    self.copy_elapsed))
            self.root.after(
                0, lambda: self.copy_chrono_label.configure(
                    text=f"Copy: {elapsed_str}"))
        # Stop the timer at the end

    def update_iso_timer(self):
        """Update the ISO generation timer label while generating."""
        while self.iso_generating:
            time.sleep(1)
            self.iso_elapsed += 1
            elapsed_str = time.strftime(
                "%H:%M:%S", time.gmtime(
                    self.iso_elapsed))
            self.root.after(
                0, lambda: self.iso_chrono_label.configure(
                    text=f"Generation: {elapsed_str}"))
        # Stop the timer at the end

    def update_total_timer(self):
        """Update the total timer while any action is in progress."""
        while self.total_running:
            time.sleep(1)
            total = self.iso_elapsed + self.copy_elapsed
            total_str = time.strftime("%H:%M:%S", time.gmtime(total))
            self.root.after(
                0, lambda: self.total_chrono_label.configure(
                    text=f"Total: {total_str}"))
            # Stop if no action is in progress
            if not self.iso_generating and not self.copying:
                self.total_running = False
                break

    def start_total_timer(self):
        """Start the total timer if not running."""
        if not self.total_running:
            # Reset the total accumulator for the new action
            self.total_running = True
            threading.Thread(
                target=self.update_total_timer,
                daemon=True).start()

    # ----------- Command Execution -----------

    def execute_command(
            self,
            command,
            button,
            progress_color=None,
            on_complete=None):
        def run_command():
            try:
                proc_text = button.cget(
                    "text") if button is not None else "Running"
                self.root.after(
                    0, lambda: self.running_label.configure(
                        text=f"Running: {proc_text}"))
                if button:
                    self.root.after(
                        0, lambda: button.configure(
                            fg_color="#ff0000", state="disabled"))
                if progress_color:
                    self.root.after(
                        0, lambda: self.progress_bar.configure(
                            progress_color=progress_color))
                self.root.after(0, self.progress_bar.start)
                self.root.after(
                    0, lambda: self.terminal_text.delete(
                        "1.0", "end"))
                full_cmd = f"echo {self.password} | sudo -S {command}"
                process = subprocess.Popen(
                    full_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True)
                while True:
                    output = process.stdout.readline()
                    if not output and process.poll() is not None:
                        break
                    if output:
                        self.root.after(
                            0, lambda: self.terminal_text.insert(
                                "end", output))
                        self.root.after(0, self.terminal_text.see, "end")
                if process.returncode == 0:
                    if button:
                        self.root.after(
                            0, lambda: button.configure(
                                fg_color="#6bdc87", state="normal"))
                    self.root.after(
                        0, lambda: messagebox.showinfo(
                            "Success", "Operation completed"))
                else:
                    raise subprocess.CalledProcessError(
                        process.returncode, command)
            except Exception as e:
                self.root.after(
                    0, lambda: messagebox.showerror(
                        "Error", f"Error: {
                            str(e)}"))
                if button:
                    self.root.after(
                        0, lambda: button.configure(
                            fg_color="#295699", state="normal"))
            finally:
                self.root.after(
                    0, lambda: self.running_label.configure(
                        text=""))
                self.root.after(0, self.progress_bar.stop)
                self.root.after(
                    0, lambda: self.progress_bar.configure(
                        progress_color="orange"))
                if on_complete:
                    self.root.after(0, on_complete)
        threading.Thread(target=run_command, daemon=True).start()

    # ----------- Previous Actions -----------
    def apply_pre_actions(self):
        self.prep_switch.configure(state="disabled")
        self.calamares_switch.configure(state="disabled")
        self.btn_pre.configure(state="disabled")
        commands = []
        if self.prep_switch_var.get():
            commands.append(
                f"{self.eggs_path} kill -n && {self.eggs_path} tools clean -n && sudo {self.eggs_path} dad -d")
        if self.calamares_switch_var.get():
            commands.append(f"sudo {self.eggs_path} calamares --install")
        if commands:
            complete_command = " && ".join(commands)
            self.execute_command(
                complete_command,
                self.btn_pre,
                progress_color="orange",
                on_complete=self.enable_additional_options)
        else:
            self.enable_additional_options()

    def enable_additional_options(self):
        self.replica_switch.configure(state="normal")
        self.edit_config_switch.configure(state="normal")
        self.btn_options.configure(state="normal")
        self.iso_data_switch.configure(state="normal")
        self.iso_comp_switch.configure(state="normal")
        self.btn_generate.configure(state="normal")

    # ----------- Generate ISO -----------
    def apply_iso_generation(self):
        self.btn_generate.configure(state="disabled")
        # Reset the ISO timer for this new generation
        self.iso_elapsed = 0
        self.iso_generating = True
        threading.Thread(target=self.update_iso_timer, daemon=True).start()
        self.start_total_timer()
        if self.iso_comp_switch_var.get():
            cmd = f"sudo {self.eggs_path} produce --max -n"
        else:
            if self.iso_data_switch_var.get():
                cmd = f"sudo {self.eggs_path} produce --clone -n"
            else:
                cmd = f"sudo {self.eggs_path} produce --noicon -n"
        self.execute_command(
            cmd,
            self.btn_generate,
            progress_color="#2065F7",
            on_complete=self.on_iso_generation_complete)

    def on_iso_generation_complete(self):
        self.iso_generating = False
        self.enable_copy_iso()
        self.update_iso_size()
        self.size_label.grid()  # Show the label at the end of generation

    def update_iso_size(self):
        iso_source_dir = "/home/eggs/.mnt/"
        iso_files = [f for f in os.listdir(iso_source_dir) if f.endswith(".iso")]
        if iso_files:
            path = os.path.join(iso_source_dir, iso_files[0])
            tam_Bytes = os.path.getsize(path)
            size_str = self.format_size(tam_Bytes)
            # Here we redirect to the new label:
            self.size_label.configure(text=f"ISO Size: {size_str}")
        else:
            self.size_label.configure(text="ISO Size: N/A")

    # def show_iso_size(self, iso_path):
    #    try:
    #        size_bytes = os.path.getsize(iso_path)
    #        size_mb = round(size_bytes / (1024 * 1024), 2)
    #        # Same, update self.size_label
    #        self.size_label.configure(text=f"ISO Size: {size_mb} MB")
    #    except Exception:
    #        self.size_label.configure(text="Error getting ISO size")

    def format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def enable_copy_iso(self):
        self.btn_copy.configure(state="normal")

    # ----------- Copy ISO -----------
    def copy_iso(self, button):
        # If at least one copy has been made, ask about the type of copy
        if self.copy_counter > 0:
            response = messagebox.askyesno("Copy Type", "Do you want to perform a fast copy?")
            self.copy_speed_switch_var.set(response)
        dest_dir = filedialog.askdirectory(title="Select Destination")
        if not dest_dir:
            return
        # Reset the copy timer for this new action
        self.copy_elapsed = 0
        self.copying = True
        threading.Thread(target=self.update_copy_timer, daemon=True).start()
        self.start_total_timer()
        self.running_label.configure(text="Running: Copy ISO")

        def copy_process():
            success = False
            try:
                proc_text = button.cget("text")
                self.root.after(0, lambda: self.terminal_text.insert("end", f"Running: {proc_text}\n"))
                self.root.after(0, lambda: button.configure(fg_color="#ff0000", state="disabled"))
                self.root.after(0, lambda: self.progress_bar.configure(progress_color="red"))
                iso_source_dir = "/home/eggs/.mnt/"
                iso_files = [f for f in os.listdir(iso_source_dir) if f.endswith(".iso")]
                if not iso_files:
                    raise FileNotFoundError("No ISO files found")
                iso_path = os.path.join(iso_source_dir, iso_files[0])
                dest_path = os.path.join(dest_dir, iso_files[0])
                total_size = os.path.getsize(iso_path)
                chunk_size = 1024 * 1024  # 1 MB
                copied = 0
                with open(iso_path, "rb") as src, open(dest_path, "wb") as dst:
                    while chunk := src.read(chunk_size):
                        dst.write(chunk)
                        copied += len(chunk)
                        progress = copied / total_size
                        # Update the progress bar and the percentage
                        self.root.after(0, lambda p=progress: self.progress_bar.set(p))
                        percent = int(progress * 100)
                        self.root.after(0, lambda p=percent: self.copy_percentage_label.configure(text=f"{p}%"))
                        # If fast copy is not selected, wait a bit
                        if not self.copy_speed_switch_var.get():
                            time.sleep(0.01)
                # When reaching 100%, stop the copy timer
                self.copying = False
                self.copy_counter += 1
                self.root.after(0, lambda: self.counter_label.configure(text=f"Copies made: {self.copy_counter}"))
                if messagebox.askyesno("Additional Copy", "Do you want to make another copy?"):
                    self.root.after(0, lambda: button.configure(fg_color="#0000FF"))
                    self.running_label.configure(text="Running: Copy ISO")
                    self.copy_iso(button)
                else:
                    message = (f"ISO copied successfully!\n\nName: {os.path.basename(dest_path)}\n"
                               f"Size: {total_size/(1024**2):.2f} MB\nLocation: {dest_path}")
                    self.root.after(0, lambda: messagebox.showinfo("Success", message))
                success = True
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                # Ensure to stop the timer in case of error or completion
                self.copying = False
                new_color = "#6bdc87" if success else "#295699"
                self.root.after(0, lambda: button.configure(fg_color=new_color, state="normal"))
                self.root.after(0, lambda: self.progress_bar.configure(progress_color="orange"))
                self.root.after(0, lambda: self.progress_bar.set(0))
                self.root.after(0, lambda: self.copy_percentage_label.configure(text="0%"))
                self.root.after(0, lambda: self.terminal_text.insert("end", "\n"))
        threading.Thread(target=copy_process, daemon=True).start()

    # ----------- Edit Configuration -----------
    def edit_configuration_file(self, button):
        try:
            self.terminal_text.insert("end", "Loading configuration...\n")
            button.configure(fg_color="#ff0000", state="disabled")
            self.root.update()
            config_file = "/etc/penguins-eggs.d/eggs.yaml"
            if not os.path.exists(config_file):
                messagebox.showerror("Error", f"File not found: {config_file}")
                button.configure(fg_color="#6bdc87", state="normal")
                return
            subprocess.run(f'echo {self.password} | sudo -S chmod 666 {config_file}', shell=True, check=True)
            with open(config_file, "r") as file:
                lines = file.readlines()
            current_values = {"root_passwd": "", "snapshot_basename": "", "snapshot_prefix": "", "user_opt_passwd": ""}
            for line in lines:
                if line.startswith("root_passwd:"):
                    current_values["root_passwd"] = line.split(":", 1)[1].strip()
                elif line.startswith("snapshot_basename:"):
                    current_values["snapshot_basename"] = line.split(":", 1)[1].strip()
                elif line.startswith("snapshot_prefix:"):
                    current_values["snapshot_prefix"] = line.split(":", 1)[1].strip()
                elif line.startswith("user_opt_passwd:"):
                    current_values["user_opt_passwd"] = line.split(":", 1)[1].strip()
            edit_window = Toplevel(self.root)
            edit_window.title("Edit ISO Configuration")
            edit_window.configure(bg="#1F1F1F")
            edit_window.wait_visibility()
            edit_window.grab_set()
            edit_window.lift()
            edit_window.focus_force()
            bold_font = ctk.CTkFont(family="Arial", size=12, weight="bold")
            label_texts = {
                "root_passwd": "Root password:",
                "snapshot_basename": "Snapshot base name (e.g., my-distro):",
                "snapshot_prefix": "Snapshot prefix (e.g., custom-):",
                "user_opt_passwd": "User password:"
            }
            entries = {}
            row = 0
            for key, text in label_texts.items():
                lbl = ctk.CTkLabel(edit_window, text=text, font=bold_font)
                lbl.grid(row=row, column=0, padx=10, pady=5, sticky="w")
                entry = ctk.CTkEntry(edit_window, width=300)
                entry.insert(0, current_values.get(key, ""))
                entry.grid(row=row, column=1, padx=10, pady=5)
                entries[key] = entry
                row += 1
            self.config_status_label = ctk.CTkLabel(edit_window, text="", text_color="green", font=bold_font)
            self.config_status_label.grid(row=row, column=0, columnspan=2, pady=5)

            def on_save():
                new_values = {key: entries[key].get() for key in entries}
                updated_lines = []
                for line in lines:
                    if line.startswith("root_passwd:"):
                        updated_lines.append(f"root_passwd: {new_values['root_passwd']}\n")
                    elif line.startswith("snapshot_basename:"):
                        updated_lines.append(f"snapshot_basename: {new_values['snapshot_basename']}\n")
                    elif line.startswith("snapshot_prefix:"):
                        updated_lines.append(f"snapshot_prefix: {new_values['snapshot_prefix']}\n")
                    elif line.startswith("user_opt_passwd:"):
                        updated_lines.append(f"user_opt_passwd: {new_values['user_opt_passwd']}\n")
                    else:
                        updated_lines.append(line)
                with open(config_file, "w") as file:
                    file.writelines(updated_lines)
                self.config_status_label.configure(text="Save successful")
                edit_window.update_idletasks()
                req_width = edit_window.winfo_reqwidth()
                req_height = edit_window.winfo_reqheight()
                edit_window.geometry(f"{req_width}x{req_height}")
                edit_window.after(2000, edit_window.destroy)

            btn_save = ctk.CTkButton(edit_window, text="Save changes", command=on_save, width=BUTTON_WIDTH)
            btn_save.grid(row=row + 1, column=0, padx=10, pady=10)
            btn_cancel = ctk.CTkButton(edit_window, text="Cancel", command=edit_window.destroy, width=BUTTON_WIDTH)
            btn_cancel.grid(row=row + 1, column=1, padx=10, pady=10)

            def on_close_edit():
                subprocess.run(f'echo {self.password} | sudo -S chmod 644 {config_file}', shell=True, check=True)
                edit_window.destroy()

            edit_window.protocol("WM_DELETE_WINDOW", on_close_edit)
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")
            subprocess.run(f'echo {self.password} | sudo -S chmod 644 {config_file}', shell=True, check=True)
        finally:
            button.configure(fg_color="#6bdc87", state="normal")
            self.terminal_text.insert("end", "\n")

    # ----------- Additional Options -----------
    def apply_additional_options(self):
        self.replica_switch.configure(state="disabled")
        self.edit_config_switch.configure(state="disabled")
        self.btn_options.configure(state="disabled")
        if self.replica_switch_var.get():
            self.execute_command(f"sudo {self.eggs_path} tools skel", self.btn_options, progress_color="orange")
        if self.edit_config_switch_var.get():
            self.edit_configuration_file(self.btn_options)

    # ----------- Application Closure -----------
    def on_close(self):
        try:
            if os.path.exists("/home/eggs"):
                cmd = f"echo {self.password} | sudo -S rm -rf /home/eggs"
                subprocess.run(cmd, shell=True, check=True)
                messagebox.showinfo("Cleanup", "Temporary files will be deleted")
        except Exception as e:
            messagebox.showerror("Error", f"Error deleting temporary files: {str(e)}")
        finally:
            self.root.destroy()

    # ----------- Show Info -----------
    def show_info(self):
        info_win = ctk.CTkToplevel(self.root)
        info_win.title("Information")
        info_win.update_idletasks()
        x = (info_win.winfo_screenwidth() - info_win.winfo_reqwidth()) // 2
        y = (info_win.winfo_screenheight() - info_win.winfo_reqheight()) // 2
        info_win.geometry(f"+{x}+{y}")
        bold_font = ctk.CTkFont(family="Arial", size=12, weight="bold")
        info_text = (
            "Eggsmaker created by Jorge Luis Endres (c) 2025 Argentina\n"
            "Penguins Eggs created by Piero Proietti\n\n"
            "For more information, visit:\nhttps://penguins-eggs.net"
        )
        info_label = ctk.CTkLabel(info_win, text=info_text, font=bold_font, justify="center")
        info_label.pack(expand=True, fill="both", padx=20, pady=20)
        info_win.grab_set()
        info_win.focus_force()

if __name__ == "__main__":
    root = ctk.CTk()
    app = EggsMakerApp(root)
    root.mainloop()

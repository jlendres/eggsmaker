import customtkinter as ctk
import subprocess
import os
import sys
import threading
import time
from PIL import Image, ImageTk
from tkinter import messagebox, simpledialog, filedialog

# Importamos la versión y el nombre de la aplicación
from version import __version__, __app__

BUTTON_WIDTH = 200  # Ancho fijo para los botones

class EggsMakerApp:
    def __init__(self, root):
        # percorso base (funziona sia in fase di sviluppo che dopo la compilazione)
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))


        self.root = root
        self.root.title(f"{__app__} - Versión {__version__}")

        # Carica l'icona per Linux/macOS
        icon_image = Image.open(os.path.join(base_path, "assets", "eggsmaker.png"))
        icon_photo = ImageTk.PhotoImage(icon_image)
        self.root.iconphoto(True, icon_photo)  # Imposta l'icona

        self.password = None
        self.eggs_path = self.detect_eggs_path()
        self.copying = False          # Para el cronómetro de copia
        self.iso_generating = False   # Para el cronómetro de generación ISO
        self.iso_elapsed = 0          # Tiempo transcurrido en generar ISO
        self.copy_elapsed = 0         # Tiempo transcurrido en copiar ISO

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Variables para los switches
        self.prep_switch_var = ctk.BooleanVar(value=True)
        self.calamares_switch_var = ctk.BooleanVar(value=False)
        self.replica_switch_var = ctk.BooleanVar(value=False)
        self.edit_config_switch_var = ctk.BooleanVar(value=False)
        self.iso_data_switch_var = ctk.BooleanVar(value=False)   # False: sin datos, True: con datos
        self.iso_comp_switch_var = ctk.BooleanVar(value=False)   # False: standard, True: máxima
        self.copy_speed_switch_var = ctk.BooleanVar(value=False)   # False: copia lenta, True: copia rápida

        self.create_widgets()
        self.request_password()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update_versions()
        self.adjust_window_size()

    def detect_eggs_path(self):
        try:
            path = subprocess.check_output("which eggs", shell=True, text=True).strip()
            return path if path else "/usr/bin/eggs"
        except Exception:
            return "/usr/bin/eggs"

    def create_widgets(self):
        # --- Main Frame ---
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # --- Área de Terminal (altura 250) ---
        self.terminal_frame = ctk.CTkFrame(self.main_frame)
        self.terminal_frame.grid(row=0, column=0, sticky="nsew", pady=(0,10))
        self.terminal_text = ctk.CTkTextbox(self.terminal_frame, fg_color="black", text_color="lime", wrap="word", height=250)
        self.terminal_text.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Panel Superior: 4 Paneles en una fila ---
        self.top_controls = ctk.CTkFrame(self.main_frame)
        self.top_controls.grid(row=1, column=0, sticky="nsew", pady=(0,10))
        for col in range(4):
            self.top_controls.grid_columnconfigure(col, weight=1)

        # Panel 1: Acciones Previas
        self.frame_acciones = ctk.CTkFrame(self.top_controls)
        self.frame_acciones.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        label_acciones = ctk.CTkLabel(self.frame_acciones, text="Acciones Previas", font=("Arial", 16, "bold"))
        label_acciones.pack(pady=5)
        self.prep_switch = ctk.CTkSwitch(self.frame_acciones, text="Preparación (Limpiar y crear entorno)", variable=self.prep_switch_var)
        self.prep_switch.pack(anchor="w", padx=5, pady=2)
        self.calamares_switch = ctk.CTkSwitch(self.frame_acciones, text="Instalar/Actualizar Calamares", variable=self.calamares_switch_var)
        self.calamares_switch.pack(anchor="w", padx=5, pady=2)
        self.btn_pre = ctk.CTkButton(self.frame_acciones, text="Aplicar", command=self.apply_pre_actions, width=BUTTON_WIDTH)
        self.btn_pre.pack(side="bottom", pady=5)

        # Panel 2: Opciones Adicionales
        self.frame_opciones = ctk.CTkFrame(self.top_controls)
        self.frame_opciones.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        label_opciones = ctk.CTkLabel(self.frame_opciones, text="Opciones Adicionales", font=("Arial", 16, "bold"))
        label_opciones.pack(pady=5)
        self.replica_switch = ctk.CTkSwitch(self.frame_opciones, text="Generar réplica del escritorio actual", variable=self.replica_switch_var, state="disabled")
        self.replica_switch.pack(anchor="w", padx=5, pady=2)
        self.edit_config_switch = ctk.CTkSwitch(self.frame_opciones, text="Editar configuración de ISO", variable=self.edit_config_switch_var, state="disabled")
        self.edit_config_switch.pack(anchor="w", padx=5, pady=2)
        self.btn_opciones = ctk.CTkButton(self.frame_opciones, text="Aplicar", command=self.apply_additional_options, state="disabled", width=BUTTON_WIDTH)
        self.btn_opciones.pack(side="bottom", pady=5)

        # Panel 3: Generar ISO
        self.frame_generar = ctk.CTkFrame(self.top_controls)
        self.frame_generar.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        label_generar = ctk.CTkLabel(self.frame_generar, text="Generar ISO", font=("Arial", 16, "bold"))
        label_generar.pack(pady=5)
        self.iso_data_switch = ctk.CTkSwitch(self.frame_generar, text="Incluir datos", variable=self.iso_data_switch_var, state="disabled")
        self.iso_data_switch.pack(anchor="w", padx=5, pady=2)
        self.iso_comp_switch = ctk.CTkSwitch(self.frame_generar, text="Máxima compresión", variable=self.iso_comp_switch_var)
        self.iso_comp_switch.pack(anchor="w", padx=5, pady=2)
        self.btn_generar = ctk.CTkButton(self.frame_generar, text="Generar ISO", command=self.apply_iso_generation, state="disabled", width=BUTTON_WIDTH)
        self.btn_generar.pack(side="bottom", pady=5)

        # Panel 4: Copiar ISO
        self.frame_copiar = ctk.CTkFrame(self.top_controls)
        self.frame_copiar.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        label_copiar = ctk.CTkLabel(self.frame_copiar, text="Copiar ISO", font=("Arial", 16, "bold"))
        label_copiar.pack(pady=5)
        self.copy_speed_switch = ctk.CTkSwitch(self.frame_copiar, text="Copia Rápida", variable=self.copy_speed_switch_var)
        self.copy_speed_switch.pack(anchor="w", padx=5, pady=2)
        self.btn_copiar = ctk.CTkButton(self.frame_copiar, text="Copiar ISO Generada", command=lambda: self.copy_iso(self.btn_copiar), state="disabled", width=BUTTON_WIDTH)
        self.btn_copiar.pack(side="bottom", pady=5)

        # --- Nivel Inferior: Información de versiones y controles finales ---
        self.bottom_controls = ctk.CTkFrame(self.main_frame)
        self.bottom_controls.grid(row=2, column=0, sticky="nsew", pady=(0,10))
        self.bottom_controls.grid_columnconfigure(0, weight=1)
        self.bottom_controls.grid_columnconfigure(1, weight=1)
        # Izquierda: Información de versiones y etiqueta "Ejecutando"
        self.frame_version = ctk.CTkFrame(self.bottom_controls)
        self.frame_version.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.eggs_version_label = ctk.CTkLabel(self.frame_version, text="Penguins Eggs: ...", font=("Arial", 14))
        self.eggs_version_label.pack(pady=2)
        self.calamares_version_label = ctk.CTkLabel(self.frame_version, text="Calamares: ...", font=("Arial", 14))
        self.calamares_version_label.pack(pady=2)
        # Agregamos un label adicional con el nombre y la versión de la aplicación
        self.app_version_label = ctk.CTkLabel(self.frame_version, text=f"{__app__} {__version__}", font=("Arial", 12))
        self.app_version_label.pack(pady=2)
        self.ejecutando_label = ctk.CTkLabel(self.frame_version, text="", font=("Arial", 16, "bold"), text_color="#ff8c00")
        self.ejecutando_label.pack(pady=2)
        # Derecha: Botón Salir, progress bar y cronómetros
        self.frame_exit = ctk.CTkFrame(self.bottom_controls)
        self.frame_exit.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.exit_button = ctk.CTkButton(self.frame_exit, text="Salir", command=self.on_close, width=BUTTON_WIDTH)
        self.exit_button.pack(pady=(10,5))
        self.progress_bar = ctk.CTkProgressBar(self.frame_exit, height=15, progress_color="#15dea2")
        self.progress_bar.pack(fill="x", padx=5, pady=(5,10))
        self.chrono_frame = ctk.CTkFrame(self.frame_exit)
        self.chrono_frame.pack(fill="x", padx=5, pady=(0,10))
        # Usamos grid para centrar los timers con fuente grande y bold
        self.chrono_frame.grid_columnconfigure(0, weight=1)
        self.chrono_frame.grid_columnconfigure(1, weight=1)
        self.chrono_frame.grid_columnconfigure(2, weight=1)
        self.copy_chrono_label = ctk.CTkLabel(self.chrono_frame, text="", text_color="cyan",
                                               font=("Arial", 20, "bold"), anchor="center")
        self.copy_chrono_label.grid(row=0, column=0, padx=5, sticky="nsew")
        self.iso_chrono_label = ctk.CTkLabel(self.chrono_frame, text="", text_color="red",
                                              font=("Arial", 20, "bold"), anchor="center")
        self.iso_chrono_label.grid(row=0, column=1, padx=5, sticky="nsew")
        self.total_chrono_label = ctk.CTkLabel(self.chrono_frame, text="", text_color="#39FF14",
                                                font=("Arial", 20, "bold"), anchor="center")
        self.total_chrono_label.grid(row=0, column=2, padx=5, sticky="nsew")

        # --- Footer: Créditos con secuencia de colores ---
        self.footer_frame = ctk.CTkFrame(self.main_frame)
        self.footer_frame.grid(row=3, column=0, sticky="ew", pady=10)
        # Renglón 1 (Argentina): secuencia celeste, blanco, celeste
        self.footer_line1 = ctk.CTkFrame(self.footer_frame)
        self.footer_line1.pack()
        self.footer_line1_label1 = ctk.CTkLabel(self.footer_line1, text="Eggsmaker creado por ", text_color="#74acdf", font=("Arial", 12))
        self.footer_line1_label1.pack(side="left")
        self.footer_line1_label2 = ctk.CTkLabel(self.footer_line1, text="jorge Luis Endres (c) 2025 ", text_color="#ffffff", font=("Arial", 12))
        self.footer_line1_label2.pack(side="left")
        self.footer_line1_label3 = ctk.CTkLabel(self.footer_line1, text="Argentina - Contribución al Proyecto", text_color="#74acdf", font=("Arial", 12))
        self.footer_line1_label3.pack(side="left")
        # Renglón 2 (Italia): secuencia verde, blanco, rojo
        self.footer_line2 = ctk.CTkFrame(self.footer_frame)
        self.footer_line2.pack()
        self.footer_line2_label1 = ctk.CTkLabel(self.footer_line2, text="Penguins Eggs - creado por ", text_color="#009246", font=("Arial", 12))
        self.footer_line2_label1.pack(side="left")
        self.footer_line2_label2 = ctk.CTkLabel(self.footer_line2, text="Piero Proietti  ", text_color="#ffffff", font=("Arial", 12))
        self.footer_line2_label2.pack(side="left")
        self.footer_line2_label3 = ctk.CTkLabel(self.footer_line2, text="https://penguins-eggs.net/", text_color="#ce2b37", font=("Arial", 12))
        self.footer_line2_label3.pack(side="left")

        # Configuración del grid del main_frame (4 filas)
        self.main_frame.grid_rowconfigure(0, weight=4)  # Terminal
        self.main_frame.grid_rowconfigure(1, weight=1)  # Top controls
        self.main_frame.grid_rowconfigure(2, weight=1)  # Bottom controls
        self.main_frame.grid_rowconfigure(3, weight=0)  # Footer
        self.main_frame.grid_columnconfigure(0, weight=1)

    def adjust_window_size(self):
        self.root.update_idletasks()
        width = 1000
        min_height = 700
        self.root.geometry(f"{width}x{min_height}+{(self.root.winfo_screenwidth()-width)//2}+50")
        self.root.minsize(width, min_height)

    def update_versions(self):
        def get_eggs_version():
            try:
                result = subprocess.run(f"sudo -S {self.eggs_path} --version", input=self.password, shell=True, capture_output=True, text=True)
                version = result.stdout.strip().split("\n")[0]
                return version
            except:
                return "N/A"
        def get_calamares_version():
            try:
                result = subprocess.run("calamares --version", shell=True, capture_output=True, text=True)
                version = result.stdout.strip().split()[-1]
                return version
            except:
                return "N/A"
        eggs_ver = get_eggs_version()
        calamares_ver = get_calamares_version()
        self.eggs_version_label.configure(text=f"Penguins Eggs: {eggs_ver}")
        self.calamares_version_label.configure(text=f"Calamares: {calamares_ver}")

    def request_password(self):
        self.password = simpledialog.askstring("Autenticación requerida", "Introduce tu contraseña de sudo:", show="*")
        if not self.password:
            messagebox.showerror("Error", "Se requiere contraseña para continuar")
            self.root.destroy()

    def update_total_timer(self):
        total = self.iso_elapsed + self.copy_elapsed
        total_str = time.strftime("%H:%M:%S", time.gmtime(total))
        self.root.after(0, lambda: self.total_chrono_label.configure(text=f"Total: {total_str}"))

    def execute_command(self, command, button, progress_color=None, on_complete=None):
        def run_command():
            try:
                proc_text = button.cget("text") if button is not None else "Ejecutando"
                self.root.after(0, lambda: self.ejecutando_label.configure(text=f"Ejecutando: {proc_text}"))
                if button:
                    self.root.after(0, lambda: button.configure(fg_color="#ff0000", state="disabled"))
                if progress_color:
                    self.root.after(0, lambda: self.progress_bar.configure(progress_color=progress_color))
                self.root.after(0, self.progress_bar.start)
                self.root.after(0, lambda: self.terminal_text.delete("1.0", "end"))
                full_cmd = f"echo {self.password} | sudo -S {command}"
                process = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                while True:
                    output = process.stdout.readline()
                    if not output and process.poll() is not None:
                        break
                    if output:
                        self.root.after(0, lambda: self.terminal_text.insert("end", output))
                        self.root.after(0, self.terminal_text.see, "end")
                if process.returncode == 0:
                    if button:
                        self.root.after(0, lambda: button.configure(fg_color="#6bdc87", state="normal"))
                    self.root.after(0, lambda: messagebox.showinfo("Éxito", "Operación completada"))
                else:
                    raise subprocess.CalledProcessError(process.returncode, command)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error: {str(e)}"))
                if button:
                    self.root.after(0, lambda: button.configure(fg_color="#295699", state="normal"))
            finally:
                self.root.after(0, self.progress_bar.stop)
                self.root.after(0, lambda: self.progress_bar.configure(progress_color="#15dea2"))
                self.root.after(0, lambda: self.ejecutando_label.configure(text=""))
                if on_complete:
                    self.root.after(0, on_complete)
        threading.Thread(target=run_command, daemon=True).start()

    # --- Acciones Previas ---
    def apply_pre_actions(self):
        self.prep_switch.configure(state="disabled")
        self.calamares_switch.configure(state="disabled")
        self.btn_pre.configure(state="disabled")
        comandos = []
        if self.prep_switch_var.get():
            comandos.append(f"{self.eggs_path} kill -n && {self.eggs_path} tools clean -n && sudo {self.eggs_path} dad -d")
        if self.calamares_switch_var.get():
            comandos.append(f"sudo {self.eggs_path} calamares --install")
        if comandos:
            comando_completo = " && ".join(comandos)
            self.execute_command(comando_completo, self.btn_pre, progress_color="#15dea2", on_complete=self.enable_additional_options)
        else:
            self.enable_additional_options()

    def enable_additional_options(self):
        self.replica_switch.configure(state="normal")
        self.edit_config_switch.configure(state="normal")
        self.btn_opciones.configure(state="normal")
        self.iso_data_switch.configure(state="normal")
        self.iso_comp_switch.configure(state="normal")
        self.btn_generar.configure(state="normal")

    # --- Generar ISO ---
    def apply_iso_generation(self):
        self.btn_generar.configure(state="disabled")
        self.start_iso_chronometer()  # Inicia cronómetro de generación (texto rojo)
        if self.iso_comp_switch_var.get():
            cmd = f"sudo {self.eggs_path} produce --max"
        else:
            if self.iso_data_switch_var.get():
                cmd = f"sudo {self.eggs_path} produce --clone -n"
            else:
                cmd = f"sudo {self.eggs_path} produce --noicon -n"
        self.execute_command(cmd, self.btn_generar, progress_color="violet", on_complete=self.on_iso_generation_complete)

    def on_iso_generation_complete(self):
        self.iso_generating = False  # Detiene el cronómetro de generación
        self.enable_copy_iso()

    def enable_copy_iso(self):
        self.btn_copiar.configure(state="normal")

    # --- Copiar ISO ---
    def copy_iso(self, button):
        dest_dir = filedialog.askdirectory(title="Seleccionar destino")
        if not dest_dir:
            return
        self.start_chronometer()  # Inicia cronómetro de copia (texto cyan)
        def copy_process():
            success = False
            try:
                proc_text = button.cget("text")
                self.root.after(0, lambda: self.ejecutando_label.configure(text=f"Ejecutando: {proc_text}"))
                self.root.after(0, lambda: button.configure(fg_color="#ff0000", state="disabled"))
                self.root.after(0, lambda: self.progress_bar.configure(progress_color="red"))
                iso_source_dir = "/home/eggs/.mnt/"
                iso_files = [f for f in os.listdir(iso_source_dir) if f.endswith(".iso")]
                if not iso_files:
                    raise FileNotFoundError("No se encontraron archivos ISO")
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
                        self.root.after(0, lambda: self.progress_bar.set(progress))
                        if not self.copy_speed_switch_var.get():
                            time.sleep(0.01)
                if messagebox.askyesno("Limpieza", "¿Eliminar ISO original?"):
                    subprocess.run(f"echo {self.password} | sudo -S rm -f '{iso_path}'", shell=True, check=True)
                message = (f"ISO copiada exitosamente!\n\nNombre: {os.path.basename(dest_path)}\nTamaño: {total_size/(1024**2):.2f} MB\nUbicación: {dest_path}")
                self.root.after(0, lambda: messagebox.showinfo("Éxito", message))
                success = True
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.copying = False  # Detiene el cronómetro de copia
                new_color = "#6bdc87" if success else "#295699"
                self.root.after(0, lambda: button.configure(fg_color=new_color, state="normal"))
                self.root.after(0, lambda: self.progress_bar.configure(progress_color="#15dea2"))
                self.root.after(0, lambda: self.progress_bar.set(0))
                self.root.after(0, lambda: self.ejecutando_label.configure(text=""))
        threading.Thread(target=copy_process, daemon=True).start()

    def start_chronometer(self):
        self.chrono_start_time = time.time()
        self.copying = True
        self.copy_elapsed = 0
        def update():
            while self.copying:
                self.copy_elapsed = time.time() - self.chrono_start_time
                elapsed_str = time.strftime("%H:%M:%S", time.gmtime(self.copy_elapsed))
                self.root.after(0, lambda: self.copy_chrono_label.configure(text=f"Copia: {elapsed_str}"))
                self.update_total_timer()
                time.sleep(1)
            self.copy_elapsed = time.time() - self.chrono_start_time
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(self.copy_elapsed))
            self.root.after(0, lambda: self.copy_chrono_label.configure(text=f"Copia: {elapsed_str}"))
            self.update_total_timer()
        threading.Thread(target=update, daemon=True).start()

    def start_iso_chronometer(self):
        self.iso_start_time = time.time()
        self.iso_generating = True
        self.iso_elapsed = 0
        def update():
            while self.iso_generating:
                self.iso_elapsed = time.time() - self.iso_start_time
                elapsed_str = time.strftime("%H:%M:%S", time.gmtime(self.iso_elapsed))
                self.root.after(0, lambda: self.iso_chrono_label.configure(text=f"Generación: {elapsed_str}"))
                self.update_total_timer()
                time.sleep(1)
            self.iso_elapsed = time.time() - self.iso_start_time
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(self.iso_elapsed))
            self.root.after(0, lambda: self.iso_chrono_label.configure(text=f"Generación: {elapsed_str}"))
            self.update_total_timer()
        threading.Thread(target=update, daemon=True).start()

    # --- Editar Configuración ---
    def edit_configuration_file(self, button):
        try:
            self.ejecutando_label.configure(text="Cargando configuración...")
            button.configure(fg_color="#ff0000", state="disabled")
            self.root.update()
            config_file = "/etc/penguins-eggs.d/eggs.yaml"
            if not os.path.exists(config_file):
                messagebox.showerror("Error", f"Archivo no encontrado: {config_file}")
                button.configure(fg_color="#6bdc87", state="normal")
                self.ejecutando_label.configure(text="")
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
            edit_window = ctk.CTkToplevel(self.root)
            edit_window.title("Editar Configuración ISO")
            edit_window.wait_visibility()
            edit_window.grab_set()
            edit_window.lift()
            edit_window.focus_force()
            label_texts = {
                "root_passwd": "Contraseña de root:",
                "snapshot_basename": "Nombre base del snapshot (ej: mi-distro):",
                "snapshot_prefix": "Prefijo del snapshot (ej: personalizada-):",
                "user_opt_passwd": "Contraseña de usuario:"
            }
            entries = {}
            row = 0
            for key, text in label_texts.items():
                lbl = ctk.CTkLabel(edit_window, text=text)
                lbl.grid(row=row, column=0, padx=10, pady=5, sticky="w")
                entry = ctk.CTkEntry(edit_window, width=300)
                entry.insert(0, current_values.get(key, ""))
                entry.grid(row=row, column=1, padx=10, pady=5)
                entries[key] = entry
                row += 1
            self.config_status_label = ctk.CTkLabel(edit_window, text="", text_color="green")
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
                self.config_status_label.configure(text="Grabación exitosa")
                edit_window.update_idletasks()
                req_width = edit_window.winfo_reqwidth()
                req_height = edit_window.winfo_reqheight()
                edit_window.geometry(f"{req_width}x{req_height}")
                edit_window.after(2000, edit_window.destroy)
            btn_save = ctk.CTkButton(edit_window, text="Guardar cambios", command=on_save, width=BUTTON_WIDTH)
            btn_save.grid(row=row+1, column=0, padx=10, pady=10)
            btn_cancel = ctk.CTkButton(edit_window, text="Cancelar", command=edit_window.destroy, width=BUTTON_WIDTH)
            btn_cancel.grid(row=row+1, column=1, padx=10, pady=10)
            def on_close_edit():
                subprocess.run(f'echo {self.password} | sudo -S chmod 644 {config_file}', shell=True, check=True)
                edit_window.destroy()
            edit_window.protocol("WM_DELETE_WINDOW", on_close_edit)
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")
            subprocess.run(f'echo {self.password} | sudo -S chmod 644 {config_file}', shell=True, check=True)
        finally:
            button.configure(fg_color="#6bdc87", state="normal")
            self.ejecutando_label.configure(text="")

    # --- Opciones Adicionales ---
    def apply_additional_options(self):
        self.replica_switch.configure(state="disabled")
        self.edit_config_switch.configure(state="disabled")
        self.btn_opciones.configure(state="disabled")
        if self.replica_switch_var.get():
            self.execute_command(f"sudo {self.eggs_path} tools skel", self.btn_opciones, progress_color="#15dea2")
        if self.edit_config_switch_var.get():
            self.edit_configuration_file(self.btn_opciones)

    def on_close(self):
        try:
            if os.path.exists("/home/eggs"):
                messagebox.showinfo("Limpieza", "Limpiando archivos temporales")
                subprocess.run(f"echo {self.password} | sudo -S rm -rf /home/eggs", shell=True, check=True)
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar /home/eggs: {str(e)}")
        finally:
            self.root.destroy()

    # --- Cronómetros ---
    def update_total_timer(self):
        total = self.iso_elapsed + self.copy_elapsed
        total_str = time.strftime("%H:%M:%S", time.gmtime(total))
        self.root.after(0, lambda: self.total_chrono_label.configure(text=f"Total: {total_str}"))

    def start_chronometer(self):
        self.chrono_start_time = time.time()
        self.copying = True
        self.copy_elapsed = 0
        def update():
            while self.copying:
                self.copy_elapsed = time.time() - self.chrono_start_time
                elapsed_str = time.strftime("%H:%M:%S", time.gmtime(self.copy_elapsed))
                self.root.after(0, lambda: self.copy_chrono_label.configure(text=f"Copia: {elapsed_str}"))
                self.update_total_timer()
                time.sleep(1)
            self.copy_elapsed = time.time() - self.chrono_start_time
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(self.copy_elapsed))
            self.root.after(0, lambda: self.copy_chrono_label.configure(text=f"Copia: {elapsed_str}"))
            self.update_total_timer()
        threading.Thread(target=update, daemon=True).start()

    def start_iso_chronometer(self):
        self.iso_start_time = time.time()
        self.iso_generating = True
        self.iso_elapsed = 0
        def update():
            while self.iso_generating:
                self.iso_elapsed = time.time() - self.iso_start_time
                elapsed_str = time.strftime("%H:%M:%S", time.gmtime(self.iso_elapsed))
                self.root.after(0, lambda: self.iso_chrono_label.configure(text=f"Generación: {elapsed_str}"))
                self.update_total_timer()
                time.sleep(1)
            self.iso_elapsed = time.time() - self.iso_start_time
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(self.iso_elapsed))
            self.root.after(0, lambda: self.iso_chrono_label.configure(text=f"Generación: {elapsed_str}"))
            self.update_total_timer()
        threading.Thread(target=update, daemon=True).start()

if __name__ == "__main__":
    root = ctk.CTk()
    app = EggsMakerApp(root)
    root.mainloop()

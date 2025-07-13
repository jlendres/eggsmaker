import customtkinter as ctk
import subprocess
import os
import sys
import threading
import time
import shutil
import gettext
import locale
from PIL import Image, ImageTk
from tkinter import messagebox, simpledialog, filedialog, Toplevel

# Importamos la versión y el nombre de la aplicación
from version import __version__, __app__

# Configuración de internacionalización
def get_base_path():
    """Obtiene la ruta base de la aplicación, funciona tanto en desarrollo como compilado"""
    if getattr(sys, 'frozen', False):
        # Ejecutando como ejecutable compilado
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller
            return sys._MEIPASS
        else:
            # Nuitka u otros
            return os.path.dirname(sys.executable)
    else:
        # Ejecutando en desarrollo
        return os.path.dirname(os.path.abspath(__file__))

def setup_i18n():
    try:
        # Intentar configurar el locale del sistema
        try:
            locale.setlocale(locale.LC_ALL, '')
        except locale.Error:
            # Si falla, intentar con las codificaciones más comunes
            for loc in ['es_ES.UTF-8', 'es_ES.utf8', 'es_ES', 'es.UTF-8', 'C.UTF-8', 'C']:
                try:
                    locale.setlocale(locale.LC_ALL, loc)
                    break
                except locale.Error:
                    continue

        # Obtener el idioma del sistema
        system_lang = locale.getlocale()[0]
        if system_lang:
            language = system_lang.split('_')[0]
            # Verificar si el idioma está soportado
            if language not in ['es', 'en', 'pt', 'it']:
                language = 'es'
        else:
            language = 'es'
    except:
        language = 'es'  # Si hay algún error, usar español

    # Usar get_base_path para localizar el directorio de traducciones
    locale_path = os.path.join(get_base_path(), 'locales')

    try:
        # Intentar cargar el idioma del sistema primero
        lang = gettext.translation('eggsmaker', locale_path, languages=[language])
        lang.install()
        return lang.gettext
    except FileNotFoundError:
        try:
            # Si no está disponible, usar español
            lang = gettext.translation('eggsmaker', locale_path, languages=['es'])
            lang.install()
            return lang.gettext
        except FileNotFoundError:
            # Si todo falla, usar gettext básico
            gettext.install('eggsmaker')
            return gettext.gettext

# Inicializar la función de traducción
_ = setup_i18n()

BUTTON_WIDTH = 200  # Ancho fijo para los botones

class EggsMakerApp:
    def __init__(self, root):
        # Oculta la ventana principal antes de pedir la clave
        root.withdraw()

        # Ruta base: funciona tanto en desarrollo como tras compilación
        base_path = get_base_path()

        self.root = root
        self.root.title(f"{__app__} - {_('Versión')} {__version__}")

        # Fondo principal oscuro y color de widgets
        self.root.configure(bg="#23272e")

        # Cargar ícono
        icon_image = Image.open(os.path.join(base_path, "assets", "eggsmaker.png"))
        icon_photo = ImageTk.PhotoImage(icon_image)
        self.root.iconphoto(True, icon_photo)

        self.password = None
        self.eggs_path = self.detect_eggs_path()

        # Variables para cronómetros y contadores
        self.copying = False
        self.iso_generating = False
        self.total_running = False

        self.copy_elapsed = 0
        self.iso_elapsed = 0
        self.copia_contador = 0

        # Fuentes y colores personalizados
        self.font_title = ("Segoe UI", 17, "bold")
        self.font_label = ("Segoe UI", 13)
        self.font_button = ("Segoe UI", 14, "bold")
        self.font_terminal = ("JetBrains Mono", 14)
        self.font_versions = ("JetBrains Mono", 15, "bold")
        self.color_orange = "#FD8637"
        self.color_bg = "#051226"
        self.color_panel = "#001835"
        self.color_button = "#0E48C5"
        self.color_button_hover = "#1741a6"
        self.color_success = "#6bdc87"
        self.color_error = "#ff0000"

        # Inicializar apariencia
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Variables para switches
        self.prep_switch_var = ctk.BooleanVar(value=True)
        self.calamares_switch_var = ctk.BooleanVar(value=False)
        self.replica_switch_var = ctk.BooleanVar(value=False)
        self.edit_config_switch_var = ctk.BooleanVar(value=False)
        self.iso_data_switch_var = ctk.BooleanVar(value=False)
        self.iso_comp_switch_var = ctk.BooleanVar(value=False)
        self.copy_speed_switch_var = ctk.BooleanVar(value=False)

        self.create_widgets()
        self.create_action_buttons()
        self.request_password()
        # Si la contraseña fue ingresada correctamente, muestra la ventana principal
        root.deiconify()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update_versions()
        self.adjust_window_size()
        self.label_iso_size = ctk.CTkLabel(self.main_frame, text="", font=("Courier", 14, "bold"), text_color="red")
        self.label_iso_size.grid(row=2, column=0, pady=(0, 10))

    def detect_eggs_path(self):
        try:
            path = subprocess.check_output("which eggs", shell=True, text=True).strip()
            return path if path else "/usr/bin/eggs"
        except Exception:
            return "/usr/bin/eggs"

    def create_widgets(self):
        # --- Main Frame ---
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=15, fg_color=self.color_panel, border_width=1, border_color="#444C5E")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # --- Área de Terminal (altura 250) ---
        self.terminal_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=self.color_bg, border_width=1, border_color="#444C5E")
        self.terminal_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.terminal_text = ctk.CTkTextbox(
            self.terminal_frame,
            fg_color="#0e1010",
            text_color="lime",
            wrap="word",
            height=250,
            font=self.font_terminal
        )
        self.terminal_text.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Panel Superior: 4 paneles en una fila ---
        self.top_controls = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=self.color_panel, border_width=1, border_color="#444C5E")
        self.top_controls.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        for col in range(4):
            self.top_controls.grid_columnconfigure(col, weight=1)

        # Panel 1: Acciones Previas
        self.frame_acciones = ctk.CTkFrame(self.top_controls, corner_radius=10, fg_color=self.color_bg, border_width=1, border_color="#444C5E")
        self.frame_acciones.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        label_acciones = ctk.CTkLabel(self.frame_acciones, text=_("Acciones Previas"), font=self.font_title, text_color=self.color_orange)
        label_acciones.pack(pady=5)
        self.prep_switch = ctk.CTkSwitch(self.frame_acciones, text=_("Preparación (Limpiar y crear entorno)"), variable=self.prep_switch_var, text_color="white")
        self.prep_switch.pack(anchor="w", padx=5, pady=2)
        self.calamares_switch = ctk.CTkSwitch(self.frame_acciones, text=_("Instalar/Actualizar Calamares"), variable=self.calamares_switch_var, text_color="white")
        self.calamares_switch.pack(anchor="w", padx=5, pady=2)
        self.btn_pre = ctk.CTkButton(self.frame_acciones, text=_("Aplicar"), command=self.apply_pre_actions, width=BUTTON_WIDTH, font=self.font_button, fg_color=self.color_button, hover_color=self.color_button_hover, corner_radius=8)
        self.btn_pre.pack(side="bottom", pady=5)

        # Panel 2: Opciones Adicionales
        self.frame_opciones = ctk.CTkFrame(self.top_controls, corner_radius=10, fg_color=self.color_bg, border_width=1, border_color="#444C5E")
        self.frame_opciones.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        label_opciones = ctk.CTkLabel(self.frame_opciones, text=_("Opciones Adicionales"), font=self.font_title, text_color=self.color_orange)
        label_opciones.pack(pady=5)
        self.replica_switch = ctk.CTkSwitch(self.frame_opciones, text=_("Generar réplica del escritorio actual"), variable=self.replica_switch_var, state="disabled", text_color="white")
        self.replica_switch.pack(anchor="w", padx=5, pady=2)
        self.edit_config_switch = ctk.CTkSwitch(self.frame_opciones, text=_("Editar configuración de ISO"), variable=self.edit_config_switch_var, state="disabled", text_color="white")
        self.edit_config_switch.pack(anchor="w", padx=5, pady=2)
        self.btn_opciones = ctk.CTkButton(self.frame_opciones, text=_("Aplicar"), command=self.apply_additional_options, state="disabled", width=BUTTON_WIDTH, font=self.font_button, fg_color=self.color_button, hover_color=self.color_button_hover, corner_radius=8)
        self.btn_opciones.pack(side="bottom", pady=5)

        # Panel 3: Generar ISO
        self.frame_generar = ctk.CTkFrame(self.top_controls, corner_radius=10, fg_color=self.color_bg, border_width=1, border_color="#444C5E")
        self.frame_generar.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        label_generar = ctk.CTkLabel(self.frame_generar, text=_("Generar ISO"), font=self.font_title, text_color=self.color_orange)
        label_generar.pack(pady=5)
        self.iso_data_switch = ctk.CTkSwitch(self.frame_generar, text=_("Incluir datos"), variable=self.iso_data_switch_var, state="disabled", text_color="white")
        self.iso_data_switch.pack(anchor="w", padx=5, pady=2)
        self.iso_comp_switch = ctk.CTkSwitch(self.frame_generar, text=_("Máxima compresión"), variable=self.iso_comp_switch_var, text_color="white")
        self.iso_comp_switch.pack(anchor="w", padx=5, pady=2)
        self.btn_generar = ctk.CTkButton(self.frame_generar, text=_("Generar ISO"), command=self.apply_iso_generation, state="disabled", width=BUTTON_WIDTH, font=self.font_button, fg_color=self.color_button, hover_color=self.color_button_hover, corner_radius=8)
        self.btn_generar.pack(side="bottom", pady=5)

        # Panel 4: Copiar ISO
        self.frame_copiar = ctk.CTkFrame(self.top_controls, corner_radius=10, fg_color=self.color_bg, border_width=1, border_color="#444C5E")
        self.frame_copiar.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        label_copiar = ctk.CTkLabel(self.frame_copiar, text=_("Copiar ISO"), font=self.font_title, text_color=self.color_orange)
        label_copiar.pack(pady=5)
        self.copy_speed_switch = ctk.CTkSwitch(self.frame_copiar, text=_("Copia Rápida"), variable=self.copy_speed_switch_var, text_color="white")
        self.copy_speed_switch.pack(anchor="w", padx=5, pady=2)
        self.btn_copiar = ctk.CTkButton(self.frame_copiar, text=_("Copiar ISO Generada"), command=lambda: self.copy_iso(self.btn_copiar), state="disabled", width=BUTTON_WIDTH, font=self.font_button, fg_color=self.color_button, hover_color=self.color_button_hover, corner_radius=8)
        self.btn_copiar.pack(side="bottom", pady=5)

        # --- Panel Inferior: Estado y versiones ---
        self.bottom_controls = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=self.color_panel, border_width=1, border_color="#444C5E")
        self.bottom_controls.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.bottom_controls.grid_columnconfigure(0, weight=2)
        self.bottom_controls.grid_columnconfigure(1, weight=1)

        # Estado: etiqueta "Ejecutando", progress bar, porcentaje, contador de copias y cronómetros.
        self.frame_status = ctk.CTkFrame(self.bottom_controls, corner_radius=10, fg_color=self.color_bg, border_width=1, border_color="#444C5E")
        self.frame_status.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.ejecutando_label = ctk.CTkLabel(self.frame_status, text=_("Ejecutando"), font=("Segoe UI", 20, "bold"), text_color=self.color_orange)
        self.ejecutando_label.pack(pady=5)
        self.progress_bar = ctk.CTkProgressBar(self.frame_status, height=20, progress_color=self.color_orange, corner_radius=10)
        self.progress_bar.pack(fill="x", padx=5, pady=(5, 2))
        self.copy_percentage_label = ctk.CTkLabel(self.frame_status, text="0%", font=self.font_label)
        self.copy_percentage_label.pack(padx=5, pady=(0, 2))
        self.contador_label = ctk.CTkLabel(self.frame_status, text=_("Copias realizadas: 0"), font=self.font_label)
        self.contador_label.pack(padx=5, pady=(0, 5))
        self.chrono_frame = ctk.CTkFrame(self.frame_status, corner_radius=8, fg_color=self.color_panel)
        self.chrono_frame.pack(fill="x", padx=5, pady=(0, 10))
        self.chrono_frame.grid_columnconfigure(0, weight=1)
        self.chrono_frame.grid_columnconfigure(1, weight=1)
        self.chrono_frame.grid_columnconfigure(2, weight=1)
        self.copy_chrono_label = ctk.CTkLabel(self.chrono_frame, text="", text_color="#56efef", font=("Segoe UI", 20, "bold"), anchor="center")
        self.copy_chrono_label.grid(row=0, column=0, padx=5, sticky="nsew")
        self.iso_chrono_label = ctk.CTkLabel(self.chrono_frame, text="", text_color="#ff052b", font=("Segoe UI", 20, "bold"), anchor="center")
        self.iso_chrono_label.grid(row=0, column=1, padx=5, sticky="nsew")
        self.total_chrono_label = ctk.CTkLabel(self.chrono_frame, text="", text_color="#39ee39", font=("Segoe UI", 20, "bold"), anchor="center")
        self.total_chrono_label.grid(row=0, column=2, padx=5, sticky="nsew")

        # Panel de versiones
        self.versions_frame = ctk.CTkFrame(self.bottom_controls, corner_radius=10, fg_color=self.color_bg, border_width=1, border_color="#444C5E")
        self.versions_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.version_penguins_label = ctk.CTkLabel(
            self.versions_frame,
            text=f"Penguins Eggs: N/A",
            font=self.font_versions,  # <--- aquí
            text_color=self.color_orange,
            anchor="center",
            justify="center"
        )
        self.version_penguins_label.pack(pady=10, fill="both")
        self.version_calamares_label = ctk.CTkLabel(
            self.versions_frame,
            text=f"Calamares: N/A",
            font=self.font_versions,  # <--- aquí
            text_color=self.color_orange,
            anchor="center",
            justify="center"
        )
        self.version_calamares_label.pack(pady=10, fill="both")
        self.version_app_label = ctk.CTkLabel(
            self.versions_frame,
            text=f"{__app__}: {__version__}",
            font=self.font_versions,  # <--- aquí
            text_color=self.color_orange,
            anchor="center",
            justify="center"
        )
        self.version_app_label.pack(pady=10, fill="both")

        # Configuración del grid principal del main_frame
        self.main_frame.grid_rowconfigure(0, weight=4)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def create_action_buttons(self):
        """Crea la fila inferior con los botones: Info, Reiniciar eggsmaker y Salir."""
        self.action_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=self.color_panel, border_width=1, border_color="#444C5E")
        self.action_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        for i in range(3):
            self.action_frame.grid_columnconfigure(i, weight=1)

        # Botón Info
        self.info_button = ctk.CTkButton(self.action_frame, text=_("Info"), command=self.show_info, width=BUTTON_WIDTH, font=self.font_button, fg_color=self.color_button, hover_color=self.color_button_hover, corner_radius=8)
        self.info_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # ETIQUETA DE TAMAÑO ISO (inicialmente oculta)
        self.size_label = ctk.CTkLabel(self.action_frame, text=_("Tamaño ISO: N/A"), font=("Segoe UI", 20, "bold"), text_color=self.color_orange)
        self.size_label.grid(row=0, column=1, padx=5, pady=5)
        self.size_label.grid_remove()  # Oculta el label al inicio

        # Botón Salir
        self.exit_button = ctk.CTkButton(self.action_frame, text=_("Salir"), command=self.on_close, width=BUTTON_WIDTH, font=self.font_button, fg_color="#ff052b", hover_color="#a8001a", corner_radius=8)
        self.exit_button.grid(row=0, column=2, padx=5, pady=5, sticky="e")

    def adjust_window_size(self):
        self.root.update_idletasks()
        width = 1000
        min_height = 700
        self.root.geometry(f"{width}x{min_height}+{(self.root.winfo_screenwidth() - width) // 2}+50")
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
        self.version_penguins_label.configure(text=f"Penguins Eggs: {eggs_ver}")
        self.version_calamares_label.configure(text=f"Calamares: {calamares_ver}")
        self.version_app_label.configure(text=f"{__app__}: {__version__}")

    def request_password(self):
        # Ventana modal personalizada para contraseña sudo
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(_("Autenticación requerida"))
        dialog.geometry("400x240")
        dialog.configure(bg=self.color_bg)
        dialog.focus_force()
        dialog.resizable(False, False)

        # Centrar ventana
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (240 // 2)
        dialog.geometry(f"+{x}+{y}")

        label = ctk.CTkLabel(dialog, text=_("Introduce tu contraseña de sudo:"), font=self.font_label, text_color=self.color_orange)
        label.pack(pady=(25, 10))

        entry = ctk.CTkEntry(dialog, show="*", width=250, font=self.font_label)
        entry.pack(pady=5)
        entry.focus_set()

        status_label = ctk.CTkLabel(dialog, text="", font=self.font_label, text_color=self.color_error)
        status_label.pack(pady=(5, 0))

        def on_accept(event=None):  # <--- acepta evento opcional
            pwd = entry.get()
            if not pwd:
                status_label.configure(text=_("La contraseña no puede estar vacía"))
                return
            self.password = pwd
            dialog.destroy()

        def on_cancel():
            self.password = None
            dialog.destroy()
            self.root.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color=self.color_bg)
        btn_frame.pack(pady=15)
        ok_btn = ctk.CTkButton(btn_frame, text=_("Aceptar"), command=on_accept, width=100, font=self.font_button, fg_color=self.color_button, hover_color=self.color_button_hover, corner_radius=8)
        ok_btn.grid(row=0, column=0, padx=10)
        cancel_btn = ctk.CTkButton(btn_frame, text=_("Cancelar"), command=on_cancel, width=100, font=self.font_button, fg_color="#ff052b", hover_color="#a8001a", corner_radius=8)
        cancel_btn.grid(row=0, column=1, padx=10)

        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        entry.bind("<Return>", on_accept)  # <--- permite Enter para aceptar
        dialog.wait_visibility()
        dialog.grab_set()
        self.root.wait_window(dialog)

        if not self.password:
            self.show_custom_error(_("Error"), _("Se requiere contraseña para continuar"))
            self.root.destroy()

    # ----------- Funciones de Cronómetro -----------
    def update_copy_timer(self):
        """Actualiza la etiqueta del cronómetro de copia mientras se esté copiando."""
        while self.copying:
            time.sleep(1)
            self.copy_elapsed += 1
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(self.copy_elapsed))
            self.root.after(0, lambda: self.copy_chrono_label.configure(text=f"{_('Copia: ')}{elapsed_str}"))

    def update_iso_timer(self):
        """Actualiza la etiqueta del cronómetro de generación ISO mientras se esté generando."""
        while self.iso_generating:
            time.sleep(1)
            self.iso_elapsed += 1
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(self.iso_elapsed))
            self.root.after(0, lambda: self.iso_chrono_label.configure(text=f"{_('Generación: ')}{elapsed_str}"))

    def update_total_timer(self):
        """Actualiza el cronómetro total mientras haya alguna acción en curso."""
        while self.total_running:
            time.sleep(1)
            total = self.iso_elapsed + self.copy_elapsed
            total_str = time.strftime("%H:%M:%S", time.gmtime(total))
            self.root.after(0, lambda: self.total_chrono_label.configure(text=f"{_('Total: ')}{total_str}"))
            if not self.iso_generating and not self.copying:
                self.total_running = False
                break

    def start_total_timer(self):
        """Inicia el cronómetro total si no está corriendo."""
        if not self.total_running:
            self.total_running = True
            threading.Thread(target=self.update_total_timer, daemon=True).start()

    # ----------- Ejecución de Comandos -----------
    def execute_command(self, command, button, progress_color=None, on_complete=None):
        def run_command():
            try:
                proc_text = button.cget("text") if button is not None else _("Ejecutando")
                self.root.after(0, lambda: self.ejecutando_label.configure(text=f"{_('Ejecutando: ')}{proc_text}"))
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
                    self.root.after(0, lambda: messagebox.showinfo(_("Éxito"), _("Operación completada")))
                else:
                    raise subprocess.CalledProcessError(process.returncode, command)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(_("Error"), f"{_("Error:")}{str(e)}"))
                if button:
                    self.root.after(0, lambda: button.configure(fg_color="#295699", state="normal"))
            finally:
                self.root.after(0, lambda: self.ejecutando_label.configure(text=""))
                self.root.after(0, self.progress_bar.stop)
                self.root.after(0, lambda: self.progress_bar.configure(progress_color="orange"))
                if on_complete:
                    self.root.after(0, on_complete)

        threading.Thread(target=run_command, daemon=True).start()

    # ----------- Acciones Previas -----------
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
            self.execute_command(comando_completo, self.btn_pre, progress_color="orange", on_complete=self.enable_additional_options)
        else:
            self.enable_additional_options()

    def enable_additional_options(self):
        self.replica_switch.configure(state="normal")
        self.edit_config_switch.configure(state="normal")
        self.btn_opciones.configure(state="normal")
        self.iso_data_switch.configure(state="normal")
        self.iso_comp_switch.configure(state="normal")
        self.btn_generar.configure(state="normal")

    # ----------- Generar ISO -----------
    def apply_iso_generation(self):
        self.btn_generar.configure(state="disabled")
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
        self.execute_command(cmd, self.btn_generar, progress_color="#2065F7", on_complete=self.on_iso_generation_complete)

    def on_iso_generation_complete(self):
        self.iso_generating = False
        self.enable_copy_iso()
        self.update_iso_size()
        self.size_label.grid()  # Muestra el label al finalizar la generación

    def update_iso_size(self):
        iso_source_dir = "/home/eggs/.mnt/"
        iso_files = [f for f in os.listdir(iso_source_dir) if f.endswith(".iso")]
        if iso_files:
            ruta = os.path.join(iso_source_dir, iso_files[0])
            tam_Bytes = os.path.getsize(ruta)
            size_str = self.format_size(tam_Bytes)
            self.size_label.configure(text=f"Tamaño ISO: {size_str}")
        else:
            self.size_label.configure(text="Tamaño ISO: N/A")

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
        self.btn_copiar.configure(state="normal")

    # ----------- Copiar ISO -----------
    def copy_iso(self, button):
        if self.copia_contador > 0:
            respuesta = messagebox.askyesno("Tipo de copia", "¿Desea realizar una copia rápida?")
            self.copy_speed_switch_var.set(respuesta)
        dest_dir = filedialog.askdirectory(title="Seleccionar destino")
        if not dest_dir:
            return
        self.copy_elapsed = 0
        self.copying = True
        threading.Thread(target=self.update_copy_timer, daemon=True).start()
        self.start_total_timer()
        self.ejecutando_label.configure(text="Ejecutando: Copiar ISO")

        def copy_process():
            success = False
            try:
                proc_text = button.cget("text")
                self.root.after(0, lambda: self.terminal_text.insert("end", f"Ejecutando: {proc_text}\n"))
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
                        self.root.after(0, lambda p=progress: self.progress_bar.set(p))
                        percent = int(progress * 100)
                        self.root.after(0, lambda p=percent: self.copy_percentage_label.configure(text=f"{p}%"))
                        if not self.copy_speed_switch_var.get():
                            time.sleep(0.01)
                self.copying = False
                self.copia_contador += 1
                self.root.after(0, lambda: self.contador_label.configure(text=f"Copias realizadas: {self.copia_contador}"))
                if messagebox.askyesno("Copia adicional", "¿Desea realizar otra copia?"):
                    self.root.after(0, lambda: button.configure(fg_color="#0000FF"))
                    self.ejecutando_label.configure(text="Ejecutando: Copiar ISO")
                    self.copy_iso(button)
                else:
                    message = (f"ISO copiada exitosamente!\n\nNombre: {os.path.basename(dest_path)}\n"
                               f"Tamaño: {total_size/(1024**2):.2f} MB\nUbicación: {dest_path}")
                    self.root.after(0, lambda: messagebox.showinfo("Éxito", message))
                success = True
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.copying = False
                new_color = "#6bdc87" if success else "#295699"
                self.root.after(0, lambda: button.configure(fg_color=new_color, state="normal"))
                self.root.after(0, lambda: self.progress_bar.configure(progress_color="orange"))
                self.root.after(0, lambda: self.progress_bar.set(0))
                self.root.after(0, lambda: self.copy_percentage_label.configure(text="0%"))
                self.root.after(0, lambda: self.terminal_text.insert("end", "\n"))

        threading.Thread(target=copy_process, daemon=True).start()

    # ----------- Editar Configuración -----------
    def edit_configuration_file(self, button):
        try:
            self.terminal_text.insert("end", "Cargando configuración...\n")
            button.configure(fg_color="#ff0000", state="disabled")
            self.root.update()
            config_file = "/etc/penguins-eggs.d/eggs.yaml"
            if not os.path.exists(config_file):
                messagebox.showerror("Error", f"Archivo no encontrado: {config_file}")
                button.configure(fg_color="#83f6a0", state="normal")
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
            edit_window.title("Editar Configuración ISO")
            edit_window.configure(bg="#1F1F1F")
            edit_window.wait_visibility()
            edit_window.grab_set()
            edit_window.lift()
            edit_window.focus_force()
            bold_font = ctk.CTkFont(family="Arial", size=12, weight="bold")
            label_texts = {
                "root_passwd": _("Contraseña de root:"),
                "snapshot_basename": _("Nombre base del snapshot (ej: mi-distro):"),
                "snapshot_prefix": _("Prefijo del snapshot (ej: personalizada-):"),
                "user_opt_passwd": _("Contraseña de usuario:")
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
                self.config_status_label.configure(text="Grabación exitosa")
                edit_window.update_idletasks()
                req_width = edit_window.winfo_reqwidth()
                req_height = edit_window.winfo_reqheight()
                edit_window.geometry(f"{req_width}x{req_height}")
                edit_window.after(2000, edit_window.destroy)

            btn_save = ctk.CTkButton(edit_window, text=_("Guardar cambios"), command=on_save, width=BUTTON_WIDTH)
            btn_save.grid(row=row+1, column=0, padx=10, pady=10)
            btn_cancel = ctk.CTkButton(edit_window, text=_("Cancelar"), command=edit_window.destroy, width=BUTTON_WIDTH)
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
            self.terminal_text.insert("end", "\n")

    # ----------- Opciones Adicionales -----------
    def apply_additional_options(self):
        self.replica_switch.configure(state="disabled")
        self.edit_config_switch.configure(state="disabled")
        self.btn_opciones.configure(state="disabled")
        if self.replica_switch_var.get():
            self.execute_command(f"sudo {self.eggs_path} tools skel", self.btn_opciones, progress_color="orange")
        if self.edit_config_switch_var.get():
            self.edit_configuration_file(self.btn_opciones)

    # ----------- Cierre de la aplicación -----------
    def on_close(self):
        try:
            if os.path.exists("/home/eggs"):
                cmd = f"echo {self.password} | sudo -S rm -rf /home/eggs"
                subprocess.run(cmd, shell=True, check=True)
                messagebox.showinfo(_("Limpieza"), _("Se eliminaran los archivos temporales"))
        except Exception as e:
            messagebox.showerror(_("Error"), _("Error al eliminar archivos temporales: {str(e)}"))
        finally:
            self.root.destroy()

    # ----------- Mostrar Info -----------
    def show_info(self):
        info_win = ctk.CTkToplevel(self.root)
        info_win.title("Información")
        info_win.configure(bg=self.color_bg)
        info_win.geometry("460x200")
        bold_font = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        info_text = (
            "Eggsmaker creado por Jorge Luis Endres (c) 2025 Argentina\n"
            "Penguins Eggs creado por Piero Proietti\n\n"
            "Para más información, visita:\nhttps://penguins-eggs.net"
        )
        info_label = ctk.CTkLabel(info_win, text=info_text, font=bold_font, justify="center", text_color=self.color_orange)
        info_label.pack(expand=True, fill="both", padx=20, pady=20)
        info_win.grab_set()
        info_win.focus_force()

    def show_custom_info(self, title, message):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x180")
        dialog.configure(bg=self.color_bg)
        dialog.grab_set()
        dialog.focus_force()
        dialog.resizable(False, False)

        label = ctk.CTkLabel(dialog, text=message, font=self.font_label, text_color=self.color_orange, wraplength=360, justify="center")
        label.pack(pady=(30, 20), padx=20)

        btn = ctk.CTkButton(dialog, text=_("Aceptar"), command=dialog.destroy, width=100, font=self.font_button, fg_color=self.color_button, hover_color=self.color_button_hover, corner_radius=8)
        btn.pack(pady=10)

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        self.root.wait_window(dialog)

    def show_custom_error(self, title, message):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x180")
        dialog.configure(bg=self.color_bg)
        dialog.focus_force()
        dialog.resizable(False, False)

        label = ctk.CTkLabel(dialog, text=message, font=self.font_label, text_color=self.color_error, wraplength=360, justify="center")
        label.pack(pady=(30, 20), padx=20)

        btn = ctk.CTkButton(dialog, text=_("Aceptar"), command=dialog.destroy, width=100, font=self.font_button, fg_color="#ff052b", hover_color="#a8001a", corner_radius=8)
        btn.pack(pady=10)

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.wait_visibility()
        dialog.grab_set()
        self.root.wait_window(dialog)

if __name__ == "__main__":
    root = ctk.CTk()
    app = EggsMakerApp(root)
    root.mainloop()

import customtkinter as ctk
import subprocess
import os
import sys
import threading
import re  # Added for version string parsing
import shlex

# Verificar e instalar el módulo distro si es necesario
try:
    import distro
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "distro"])
    import distro
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
    try:
        # Si estamos en un entorno de PyInstaller
        if getattr(sys, 'frozen', False):
            # 1. Verificar si estamos en el directorio temporal de PyInstaller
            if hasattr(sys, '_MEIPASS'):
                meipass = sys._MEIPASS

                # Primero verificar la ruta exacta que está fallando
                if os.path.exists(os.path.join(meipass, 'resources', 'eggsmaker.png')):
                    return os.path.join(meipass, 'resources')

                # Luego verificar la ruta con assets
                if os.path.exists(os.path.join(meipass, 'assets', 'eggsmaker.png')):
                    return meipass

                # Verificar si el archivo está directamente en _MEIPASS
                if os.path.exists(os.path.join(meipass, 'eggsmaker.png')):
                    return meipass

                # Búsqueda recursiva como último recurso
                for root, dirs, files in os.walk(meipass):
                    if 'eggsmaker.png' in files:
                        return root

        # 2. Lista de posibles ubicaciones de los assets
        possible_paths = [
            # Directorio del script actual (desarrollo)
            os.path.dirname(os.path.abspath(__file__)),

            # Para AppImage/paquete instalado
            "/usr/share/eggsmaker",
            "/usr/local/share/eggsmaker",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../share/eggsmaker"),

            # Para PyInstaller/Nuitka - rutas comunes
            os.path.join(os.path.dirname(sys.executable), "resources"),
            os.path.join(os.path.dirname(sys.executable), "assets"),
            os.path.join(os.path.dirname(sys.executable), "../share/eggsmaker"),

            # Directorio actual de trabajo
            os.getcwd(),
            os.path.join(os.getcwd(), "assets"),
            os.path.join(os.getcwd(), "resources"),

            # Directorio de instalación de Python
            os.path.join(os.path.dirname(os.__file__), ".."),

            # Rutas específicas para AppImage
            os.path.join(os.path.dirname(sys.executable), "usr/share/eggsmaker"),
            os.path.join(os.path.dirname(sys.executable), "usr/share/eggsmaker/assets"),
        ]

        # 3. Verificar cada ruta
        for path in possible_paths:
            try:
                path = os.path.normpath(path)  # Normalizar la ruta
                # Verificar si existe el archivo de icono o la carpeta de assets
                if os.path.exists(os.path.join(path, "assets", "eggsmaker.png")):
                    return path
                if os.path.exists(os.path.join(path, "eggsmaker.png")):
                    return path
            except Exception as e:
                print(f"⚠️ Error al verificar ruta {path}: {e}")

        # 4. Si no se encuentra, intentar con la ruta del ejecutable
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS

        # 5. Si todo falla, devolver el directorio actual
        current_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"⚠️ No se pudo encontrar la ruta de los assets, usando: {current_dir}")
        return current_dir

    except Exception as e:
        print(f"Error al obtener la ruta base: {e}")
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
        self.auto_running = False  # Nueva variable para el proceso AUTO
        self.total_running = False

        self.copy_elapsed = 0
        self.iso_elapsed = 0
        self.auto_elapsed = 0  # Nueva variable para cronómetro AUTO
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
        self.color_success = "#8b8b8b"
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

        # Estilos para los switches
        self.switch_on_color = "#00FF00"  # Verde fluo
        self.switch_off_color = "#000000"  # Negro
        self.switch_button_color = "#FFFFFF"  # Blanco para el botón deslizante

        # Track if we're updating eggs/calamares
        self.updating_eggs = False

        self.create_widgets()
        self.create_action_buttons()
        self.request_password()
        # Si la contraseña fue ingresada correctamente, muestra la ventana principal
        root.deiconify()
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
            text_color="#87CEFA",  # Light blue color
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

        # Panel 1: Fase 1
        self.frame_acciones = ctk.CTkFrame(self.top_controls, corner_radius=10, fg_color=self.color_bg, border_width=1, border_color="#444C5E")
        self.frame_acciones.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        label_acciones = ctk.CTkLabel(self.frame_acciones, text=_("Fase 1"), font=self.font_title, text_color="#00BFFF")  # Light blue color
        label_acciones.pack(pady=5)
        def toggle_prep(*args):
            if not hasattr(self, 'prep_switch') or not hasattr(self, 'calamares_switch'):
                return

            if self.updating_eggs:
                return

            self.updating_eggs = True  # Bloquea actualizaciones recursivas

            # Si el switch de preparación está ON -> MODO Manual
            if self.prep_switch_var.get():
                # Texto "Manual"
                try:
                    self.prep_switch.configure(text=_("Manual"))
                except Exception:
                    self.prep_switch.configure(text="Manual")
                # Desactivar AUTO (botón) y restaurar color normal
                try:
                    self.btn_auto.configure(
                        state="disabled",
                        fg_color=self.color_button,  # Color normal
                        hover_color=self.color_button_hover  # Color hover normal
                    )
                    # Habilitar botón Fase 1 en modo Manual
                    self.btn_pre.configure(state="normal")
                except Exception:
                    pass

                # Visual: switches colores
                self.prep_switch.configure(fg_color=self.switch_on_color, progress_color=self.switch_on_color)
                self.calamares_switch.configure(fg_color=self.switch_off_color, progress_color=self.switch_on_color)
            else:
                # Texto "AUTO"
                try:
                    self.prep_switch.configure(text=_("AUTO"))
                except Exception:
                    self.prep_switch.configure(text="AUTO")
                # Activar AUTO con color verde oscuro y deshabilitar Fase 1
                try:
                    dark_green = "#006400"  # verde oscuro
                    self.btn_auto.configure(state="normal", fg_color=dark_green, hover_color="#005000")
                    # Deshabilitar botón Fase 1 en modo AUTO
                    self.btn_pre.configure(state="disabled")
                except Exception:
                    pass

                # Visual: switches colores
                self.prep_switch.configure(fg_color=self.switch_off_color, progress_color=self.switch_on_color)

            self.updating_eggs = False  # Desbloquea actualizaciones

        def toggle_calamares(*args):
            if not hasattr(self, 'calamares_switch') or not hasattr(self, 'prep_switch'):
                return

            if self.updating_eggs:
                return

            self.updating_eggs = True  # Bloquea actualizaciones recursivas

            if self.calamares_switch_var.get():
                self.prep_switch_var.set(False)
                self.calamares_switch.configure(fg_color=self.switch_on_color, progress_color=self.switch_on_color)
                self.prep_switch.configure(fg_color=self.switch_off_color, progress_color=self.switch_on_color)
            else:
                self.calamares_switch.configure(fg_color=self.switch_off_color, progress_color=self.switch_on_color)

            self.updating_eggs = False  # Desbloquea actualizaciones

        # Configurar los traces después de crear los switches
        self.prep_switch_var.trace('w', toggle_prep)
        self.calamares_switch_var.trace('w', toggle_calamares)

        self.prep_switch = ctk.CTkSwitch(self.frame_acciones,
                                       text=_("Inicio"),
                                       variable=self.prep_switch_var,
                                       text_color="white",
                                       fg_color=self.switch_on_color,
                                       progress_color=self.switch_on_color,
                                       button_color=self.switch_button_color,
                                       button_hover_color=self.switch_button_color)
        self.prep_switch.pack(anchor="w", padx=5, pady=2)

        self.calamares_switch = ctk.CTkSwitch(self.frame_acciones,
                                            text=_("Actualizar Eggs y Calamares"),
                                            variable=self.calamares_switch_var,
                                            text_color="white",
                                            fg_color=self.switch_off_color,
                                            progress_color=self.switch_on_color,
                                            button_color=self.switch_button_color,
                                            button_hover_color=self.switch_button_color)
        self.calamares_switch.pack(anchor="w", padx=5, pady=2)
        # Update button text based on selection
        def update_phase1_button_text(*args):
            if self.prep_switch_var.get():
                self.btn_pre.configure(text=_("Fase 1"))
            elif self.calamares_switch_var.get():
                self.btn_pre.configure(text=_("fresh-eggs/calamares"))

        self.prep_switch_var.trace('w', update_phase1_button_text)
        self.calamares_switch_var.trace('w', update_phase1_button_text)

        self.btn_pre = ctk.CTkButton(self.frame_acciones, text=_("Fase 1"), command=self.apply_pre_actions, width=BUTTON_WIDTH, font=self.font_button, fg_color=self.color_button, hover_color=self.color_button_hover, corner_radius=8)
        self.btn_pre.pack(side="bottom", pady=5)

        # Set initial button text
        update_phase1_button_text()

        # Panel 2: Fase 2
        self.frame_opciones = ctk.CTkFrame(self.top_controls, corner_radius=10, fg_color=self.color_bg, border_width=1, border_color="#444C5E")
        self.frame_opciones.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        label_opciones = ctk.CTkLabel(self.frame_opciones, text=_("Fase 2"), font=self.font_title, text_color="#00BFFF")  # Light blue color
        label_opciones.pack(pady=5)
        self.replica_switch = ctk.CTkSwitch(self.frame_opciones,
                                          text=_("Clonar Escritorio"),
                                          variable=self.replica_switch_var,
                                          state="disabled",
                                          text_color="white",
                                          fg_color=self.switch_off_color,
                                          progress_color=self.switch_on_color,
                                          button_color=self.switch_button_color,
                                          button_hover_color=self.switch_button_color)
        self.replica_switch.pack(anchor="w", padx=5, pady=2)

        self.edit_config_switch = ctk.CTkSwitch(self.frame_opciones,
                                              text=_("Personalizar ISO"),
                                              variable=self.edit_config_switch_var,
                                              state="disabled",
                                              text_color="white",
                                              fg_color=self.switch_off_color,
                                              progress_color=self.switch_on_color,
                                              button_color=self.switch_button_color,
                                              button_hover_color=self.switch_button_color)
        self.edit_config_switch.pack(anchor="w", padx=5, pady=2)
        self.btn_opciones = ctk.CTkButton(self.frame_opciones, text=_("Fase 2"), command=self.apply_additional_options, state="disabled", width=BUTTON_WIDTH, font=self.font_button, fg_color=self.color_button, hover_color=self.color_button_hover, corner_radius=8)
        self.btn_opciones.pack(side="bottom", pady=5)

        # Panel 3: Fase 3
        self.frame_generar = ctk.CTkFrame(self.top_controls, corner_radius=10, fg_color=self.color_bg, border_width=1, border_color="#444C5E")
        self.frame_generar.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        label_generar = ctk.CTkLabel(self.frame_generar, text=_("Fase 3"), font=self.font_title, text_color="#00BFFF")  # Light blue color
        label_generar.pack(pady=5)
        self.iso_data_switch = ctk.CTkSwitch(self.frame_generar,
                                           text=_("Incluir datos"),
                                           variable=self.iso_data_switch_var,
                                           state="enabled",
                                           text_color="white",
                                           fg_color=self.switch_off_color,
                                           progress_color=self.switch_on_color,
                                           button_color=self.switch_button_color,
                                           button_hover_color=self.switch_button_color)
        self.iso_data_switch.pack(anchor="w", padx=5, pady=2)
        self.iso_comp_switch = ctk.CTkSwitch(self.frame_generar,
                                           text=_("Máxima compresión"),
                                           variable=self.iso_comp_switch_var,
                                           text_color="white",
                                           fg_color=self.switch_off_color,
                                           progress_color=self.switch_on_color,
                                           button_color=self.switch_button_color,
                                           button_hover_color=self.switch_button_color)
        self.iso_comp_switch.pack(anchor="w", padx=5, pady=2)
        self.btn_generar = ctk.CTkButton(self.frame_generar, text=_("Fase 3"), command=self.apply_iso_generation, state="disabled", width=BUTTON_WIDTH, font=self.font_button, fg_color=self.color_button, hover_color=self.color_button_hover, corner_radius=8)
        self.btn_generar.pack(side="bottom", pady=5)
        # Fase 3 disponible desde el inicio (activada en AUTO y Manual)
        try:
            self.btn_generar.configure(state="normal")
        except Exception:
            pass

        # Panel 4: Botón AUTO (MODIFICADO - Aplicado el esquema de colores consistente)
        self.frame_auto = ctk.CTkFrame(self.top_controls, corner_radius=10, fg_color=self.color_bg, border_width=1, border_color="#444C5E")
        self.frame_auto.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        # Botón AUTO con esquema de colores consistente con el resto de la aplicación
        self.btn_auto = ctk.CTkButton(
            self.frame_auto,
            text="AUTO",
            command=self.execute_auto,
            width=250,
            height=80,
            font=("Segoe UI", 18, "bold"),
            fg_color=self.color_button,      # Usando color consistente
            hover_color=self.color_button_hover,  # Usando color hover consistente
            corner_radius=15
        )
        self.btn_auto.pack(expand=True, pady=20)

        # Estado inicial del botón AUTO basado en el switch de preparación
        try:
            if self.prep_switch_var.get():
                # Si prep está ON -> Modo Manual -> AUTO desactivado
                self.btn_auto.configure(state="disabled")
                # Cambiar texto del switch a Manual
                self.prep_switch.configure(text=_("Manual"))
            else:
                # Si prep está OFF -> mostrar AUTO y activar botón con verde oscuro
                dark_green = "#006400"
                self.btn_auto.configure(state="normal", fg_color=dark_green, hover_color="#005000")
                self.prep_switch.configure(text=_("AUTO"))
        except Exception:
            pass

        # --- Panel Inferior: Estado y Copiar ISO ---
        self.bottom_controls = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=self.color_panel, border_width=1, border_color="#444C5E")
        self.bottom_controls.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.bottom_controls.grid_columnconfigure(0, weight=2)  # Panel de estado más ancho
        self.bottom_controls.grid_columnconfigure(1, weight=1)  # Panel de copiar ISO

        # Estado: etiqueta de fase, progress bar, porcentaje, contador de copias y cronómetros.
        self.frame_status = ctk.CTkFrame(self.bottom_controls, corner_radius=10, fg_color=self.color_bg, border_width=1, border_color="#444C5E")
        self.frame_status.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.phase_label = ctk.CTkLabel(self.frame_status, text="", font=("Segoe UI", 20, "bold"), text_color=self.color_orange)
        self.phase_label.pack(pady=5)

        # Remove any remaining ejecutando_label references
        if hasattr(self, 'ejecutando_label'):
            self.ejecutando_label.destroy()
            del self.ejecutando_label
        self.progress_bar = ctk.CTkProgressBar(self.frame_status, height=20, progress_color="#00BFFF", corner_radius=10)  # Changed to light blue
        self.progress_bar.pack(fill="x", padx=5, pady=(5, 2))

        # Etiqueta de estado de ejecución (usada por varios métodos)
        # Texto "Ejecutando" más grande y color verde fluo
        self.ejecutando_label = ctk.CTkLabel(self.frame_status, text="", font=("Segoe UI", 14, "bold"), text_color="#39ee39")
        self.ejecutando_label.pack(fill="x", padx=5, pady=(0,5))

        # Frame para porcentaje y contador en la misma línea
        self.info_frame = ctk.CTkFrame(self.frame_status, corner_radius=8, fg_color=self.color_panel)
        self.info_frame.pack(fill="x", padx=5, pady=(0, 5))
        self.info_frame.grid_columnconfigure(0, weight=1)
        self.info_frame.grid_columnconfigure(1, weight=1)

        self.copy_percentage_label = ctk.CTkLabel(self.info_frame, text="0%", font=("Segoe UI", 16, "bold"), text_color="white")
        self.copy_percentage_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.contador_label = ctk.CTkLabel(self.info_frame, text=_("Copias realizadas: 0"), font=("Segoe UI", 16, "bold"), text_color="white")
        self.contador_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
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

        # Panel de Copiar ISO (al lado del panel de estado)
        self.frame_copy_iso = ctk.CTkFrame(self.bottom_controls, corner_radius=10, fg_color=self.color_bg, border_width=1, border_color="#444C5E")
        self.frame_copy_iso.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        label_copy_iso = ctk.CTkLabel(self.frame_copy_iso, text=_("Copiar ISO"), font=self.font_title, text_color="#00BFFF")  # Light blue color
        label_copy_iso.pack(pady=5)

        # Initially disable the copy ISO section
        # Mantener siempre activo el botón Copiar ISO y el switch de copia rápida según requisitos.
        for widget in self.frame_copy_iso.winfo_children():
            # Desactivar únicamente los controles que deben comenzar deshabilitados:
            if widget not in (label_copy_iso,):  # Dejamos control manual abajo
                # Activar por defecto copy_speed_switch y btn_copiar/size_label más tarde
                try:
                    # No deshabilitar el switch de copia ni el botón copiar
                    # (si existen, los dejamos tal cual). Solo aseguramos que Fase2/Fase3 sigan desactivadas.
                    pass
                except Exception:
                    pass

        # Switch para copia rápida - centrado
        self.copy_speed_switch = ctk.CTkSwitch(self.frame_copy_iso,
                                             text=_("Copia Rápida"),
                                             variable=self.copy_speed_switch_var,
                                             text_color="white",
                                             fg_color=self.switch_off_color,
                                             progress_color=self.switch_on_color,
                                             button_color=self.switch_button_color,
                                             button_hover_color=self.switch_button_color)
        self.copy_speed_switch.pack(pady=2)
        # Asegurarse que el switch de copia esté siempre habilitado
        try:
            self.copy_speed_switch.configure(state="normal")
        except Exception:
            pass

        # Botón Copiar ISO
        self.btn_copiar = ctk.CTkButton(
            self.frame_copy_iso,
            text=_("Copiar ISO Generada"),
            command=lambda: self.copy_iso(self.btn_copiar),
            state="enabled",
            width=BUTTON_WIDTH,
            font=self.font_button,
            fg_color=self.color_button,
            hover_color=self.color_button_hover,
            corner_radius=8
        )
        self.btn_copiar.pack(pady=(10, 5))
        # Asegurar que el botón copiar ISO permanezca activo siempre
        try:
            self.btn_copiar.configure(state="normal")
        except Exception:
            pass

        # Etiqueta de tamaño ISO - inicialmente oculta
        self.size_label = ctk.CTkLabel(self.frame_copy_iso, text=_("Tamaño ISO: N/A"), font=("Segoe UI", 14, "bold"), text_color="#00FF00")
        self.size_label.pack(pady=(5, 10))
        self.size_label.pack_forget()  # Ocultar inicialmente

        # --- Panel de versiones (ahora en una línea horizontal) ---
        self.versions_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=self.color_bg, border_width=1, border_color="#444C5E")
        self.versions_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self.versions_frame.grid_columnconfigure(0, weight=1)
        self.versions_frame.grid_columnconfigure(1, weight=1)
        self.versions_frame.grid_columnconfigure(2, weight=1)

        # Versiones en línea horizontal
        self.version_penguins_label = ctk.CTkLabel(
            self.versions_frame,
            text="*  N/A",
            font=self.font_versions,
            text_color="white",
            anchor="center",
            justify="center"
        )
        self.version_penguins_label.grid(row=0, column=0, padx=5, pady=10, sticky="ew")

        self.version_calamares_label = ctk.CTkLabel(
            self.versions_frame,
            text="Calamares: N/A",
            font=self.font_versions,
            text_color="white",  # Changed to white
            anchor="center",
            justify="center"
        )
        self.version_calamares_label.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        self.version_app_label = ctk.CTkLabel(
            self.versions_frame,
            text=f"{__app__}: {__version__}",
            font=self.font_versions,
            text_color="white",  # Changed to white
            anchor="center",
            justify="center"
        )
        self.version_app_label.grid(row=0, column=2, padx=5, pady=10, sticky="ew")

        # Configuración del grid principal del main_frame
        self.main_frame.grid_rowconfigure(0, weight=4)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=0)  # Panel de versiones sin peso
        self.main_frame.grid_columnconfigure(0, weight=1)

    def create_action_buttons(self):
        """Crea la fila inferior con los botones: Info y Salir."""
        self.action_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=self.color_panel, border_width=1, border_color="#444C5E")
        self.action_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        for i in range(2):
            self.action_frame.grid_columnconfigure(i, weight=1)

        # Botón Info
        self.info_button = ctk.CTkButton(self.action_frame, text=_("Info"), command=self.show_info, width=BUTTON_WIDTH, font=self.font_button, fg_color=self.color_button, hover_color=self.color_button_hover, corner_radius=8)
        self.info_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Botón Salir
        self.exit_button = ctk.CTkButton(self.action_frame, text=_("Salir"), command=self.on_close, width=BUTTON_WIDTH, font=self.font_button, fg_color="#ff052b", hover_color="#a8001a", corner_radius=8)
        self.exit_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")

    def execute_auto(self):
        """Ejecuta el flujo completo de preparación, generación de ISO y copia"""
        # Cambiar color del botón a rojo al iniciar
        self.btn_auto.configure(fg_color="#ff052b", hover_color="#a8001a")

        # Iniciar temporizadores
        self.auto_elapsed = 0
        self.auto_running = True
        threading.Thread(target=self.update_auto_timer, daemon=True).start()
        self.start_total_timer()

        # Configurar interfaz
        self.btn_auto.configure(state="disabled")
        self.terminal_text.delete('1.0', 'end')
        self.terminal_text.insert('end', "=== INICIANDO MODO AUTO ===\n")
        self.terminal_text.see('end')

        # Configurar barra de progreso oscilante
        self.progress_bar.configure(progress_color=self.color_button, mode="indeterminate")
        self.progress_bar.start()

        # Iniciar el proceso en un hilo separado
        print("DEBUG: Iniciando hilo de actualización")
        update_thread = threading.Thread(target=self._auto_workflow, daemon=True)
        update_thread.start()
        print("DEBUG: Hilo de actualización iniciado")

    def _auto_workflow(self):
        """Flujo de trabajo completo del modo AUTO"""
        try:
            # 1. Preparación
            self.root.after(0, lambda: self.ejecutando_label.configure(text="Ejecutando: Preparación"))
            self.terminal_text.insert('end', "\n=== PREPARACIÓN ===\n")
            self.terminal_text.see('end')

            # Ejecutar comandos de preparación
            prep_cmds = [
                f"{self.eggs_path} kill -n",
                f"{self.eggs_path} tools clean -n",
                f"sudo {self.eggs_path} dad -d"  # Añadido espacio después de sudo
            ]

            for cmd in prep_cmds:
                self.terminal_text.insert('end', f"\n$ {cmd}\n")
                self.terminal_text.see('end')

                process = subprocess.Popen(
                    f"echo {self.password} | sudo -S {cmd}",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )

                # Mostrar salida en tiempo real
                for line in process.stdout:
                    self.terminal_text.insert('end', line)
                    self.terminal_text.see('end')

                if process.wait() != 0:
                    raise Exception(f"Error en el comando: {cmd}")

            # 2. Generar ISO
            self.root.after(0, lambda: self.ejecutando_label.configure(text="Ejecutando: Generando ISO"))
            self.terminal_text.insert('end', "\n=== GENERANDO ISO ===\n")
            self.terminal_text.see('end')

            # Determinar opciones de generación de ISO
            iso_cmd = f"sudo {self.eggs_path} produce"
            if self.iso_comp_switch_var.get():
                iso_cmd += " --pendrive"
            elif self.iso_data_switch_var.get():
                iso_cmd += " --clone"
            else:
                iso_cmd += " --noicon"

            iso_cmd += " -n"  # Modo no interactivo

            self.terminal_text.insert('end', f"\n$ {iso_cmd}\n")
            self.terminal_text.see('end')

            # Ejecutar generación de ISO
            process = subprocess.Popen(
                f"echo {self.password} | sudo -S {iso_cmd}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Mostrar salida en tiempo real
            for line in process.stdout:
                self.terminal_text.insert('end', line)
                self.terminal_text.see('end')

            if process.wait() != 0:
                raise Exception("Error al generar la ISO")

            # MODIFICACIÓN 2: Mostrar tamaño de la ISO inmediatamente después de la generación
            self.root.after(0, self.update_iso_size)
            self.root.after(0, lambda: self.size_label.pack(pady=(5, 10)))  # Mostrar el label

            # 3. Preguntar por tipo de copia
            self.root.after(0, self._ask_copy_options)

        except Exception as e:
            error_msg = f"Error en el flujo AUTO: {str(e)}"
            self.terminal_text.insert('end', f"\n{error_msg}")
            self.terminal_text.see('end')
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self._finish_auto(False)

    def _ask_copy_options(self):
        """Pregunta por las opciones de copia"""
        try:
            # Preguntar por copia rápida
            respuesta = messagebox.askyesno("Tipo de copia", "¿Desea realizar una copia rápida?")
            self.copy_speed_switch_var.set(respuesta)

            # Seleccionar directorio de destino
            dest_dir = filedialog.askdirectory(title="Seleccionar destino para la copia")
            if not dest_dir:
                raise Exception("No se seleccionó ningún directorio de destino")

            # Iniciar copia
            self.terminal_text.insert('end', "\n=== COPIANDO ISO ===\n")
            self.terminal_text.see('end')
            self.root.after(0, lambda: self.ejecutando_label.configure(text="Ejecutando: Copiando ISO"))

            # Cambiar a barra de progreso determinada para la copia
            self.root.after(0, lambda: self.progress_bar.stop())
            self.root.after(0, lambda: self.progress_bar.configure(mode="determinate"))
            self.root.after(0, lambda: self.progress_bar.set(0))

            # Ejecutar copia en un hilo separado
            threading.Thread(
                target=self._copy_iso_auto,
                args=(dest_dir,),
                daemon=True
            ).start()

        except Exception as e:
            error_msg = f"Error al configurar la copia: {str(e)}"
            self.terminal_text.insert('end', f"\n{error_msg}")
            self.terminal_text.see('end')
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self._finish_auto(False)

    def _copy_iso_auto(self, dest_dir):
        """Copia la ISO al directorio de destino"""
        try:
            # Iniciar temporizador de copia
            self.copy_elapsed = 0
            self.copying = True
            threading.Thread(target=self.update_copy_timer, daemon=True).start()

            # Buscar archivo ISO
            iso_source_dir = "/home/eggs/.mnt/"
            iso_files = [f for f in os.listdir(iso_source_dir) if f.endswith(".iso")]
            if not iso_files:
                raise FileNotFoundError("No se encontraron archivos ISO para copiar")

            iso_path = os.path.join(iso_source_dir, iso_files[0])
            dest_path = os.path.join(dest_dir, iso_files[0])

            # Copiar archivo
            total_size = os.path.getsize(iso_path)
            chunk_size = 1024 * 1024  # 1 MB
            copied = 0

            with open(iso_path, "rb") as src, open(dest_path, "wb") as dst:
                while chunk := src.read(chunk_size):
                    dst.write(chunk)
                    copied += len(chunk)
                    progress = copied / total_size

                    # Actualizar progreso
                    self.root.after(0, lambda p=progress: self.progress_bar.set(p))
                    percent = int(progress * 100)
                    self.root.after(0, lambda p=percent: self.copy_percentage_label.configure(text=f"{p}%"))

                    # Pequeña pausa si no es copia rápida
                    if not self.copy_speed_switch_var.get():
                        time.sleep(0.01)

            # Actualizar contador de copias
            self.copia_contador += 1
            self.root.after(0, lambda: self.contador_label.configure(
                text=f"Copias realizadas: {self.copia_contador}"
            ))

            # Mostrar mensaje de éxito
            success_msg = (
                f"ISO copiada exitosamente!\n\n"
                f"Nombre: {os.path.basename(dest_path)}\n"
                f"Tamaño: {total_size/(1024**2):.2f} MB\n"
                f"Ubicación: {dest_path}"
            )

            self.root.after(0, lambda: messagebox.showinfo("Éxito", success_msg))
            self.terminal_text.insert('end', "\n=== PROCESO AUTO COMPLETADO ===\n")
            self.terminal_text.see('end')

            # Finalizar con éxito
            self._finish_auto(True)

        except Exception as e:
            error_msg = f"Error al copiar la ISO: {str(e)}"
            self.terminal_text.insert('end', f"\n{error_msg}")
            self.terminal_text.see('end')
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self._finish_auto(False)

    def _finish_auto(self, success):
        """Finaliza el modo AUTO y limpia los recursos"""
        self.auto_running = False
        self.copying = False

        # Restaurar estado de la interfaz
        self.root.after(0, lambda: self.progress_bar.stop())
        self.root.after(0, lambda: self.progress_bar.configure(mode="determinate"))
        self.root.after(0, lambda: self.progress_bar.set(0))
        self.root.after(0, lambda: self.ejecutando_label.configure(text=""))

        # Cambiar color del botón según el resultado
        if success:
            self.root.after(0, lambda: self.btn_auto.configure(
                state="normal",
                fg_color=self.color_success,
                hover_color="#4caf50"  # Un verde un poco más oscuro para el hover
            ))
        else:
            self.root.after(0, lambda: self.btn_auto.configure(
                state="normal",
                fg_color=self.color_button,
                hover_color=self.color_button_hover
            ))

        # Actualizar tamaño de la ISO
        self.update_iso_size()

        # Mostrar mensaje final
        if success:
            self.terminal_text.insert('end', "\n¡Proceso AUTO completado con éxito!\n")
            self.terminal_text.see('end')

    def update_auto_timer(self):
        """Actualiza la etiqueta del cronómetro AUTO mientras se esté ejecutando."""
        while self.auto_running:
            time.sleep(1)
            self.auto_elapsed += 1
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(self.auto_elapsed))
            # Usamos el mismo label que ISO para mostrar el tiempo AUTO
            self.root.after(0, lambda: self.iso_chrono_label.configure(text=f"{_('AUTO: ')}{elapsed_str}"))

    def on_auto_complete(self):
        """Método obsoleto, se mantiene por compatibilidad"""
        pass

    def adjust_window_size(self):
        self.root.update_idletasks()
        width = 1000
        min_height = 750  # Aumentado ligeramente para acomodar la nueva distribución
        self.root.geometry(f"{width}x{min_height}+{(self.root.winfo_screenwidth() - width) // 2}+50")
        self.root.minsize(width, min_height)

    def update_versions(self):
        def get_distro_info():
            """Obtiene información sobre la distribución Linux actual."""
            try:
                if os.path.exists('/etc/os-release'):
                    with open('/etc/os-release', 'r') as f:
                        os_release = {}
                        for line in f:
                            if '=' in line:
                                k, v = line.strip().split('=', 1)
                                os_release[k] = v.strip('"')
                        return os_release
                return {}
            except Exception as e:
                print(f"Error al obtener información de la distribución: {e}")
                return {}

        def get_eggs_version():
            """Obtiene la versión de Penguins' Eggs de forma compatible con múltiples distribuciones."""
            try:
                # Intentar con el comando eggs --version primero
                try:
                    result = subprocess.run(
                        ['eggs', '--version'],
                        capture_output=True,
                        text=True,
                        timeout=5  # Timeout de 5 segundos
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        version_output = result.stdout.strip()
                        # Buscar versión en el formato vX.Y.Z o X.Y.Z
                        version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', version_output)
                        if version_match:
                            return version_match.group(1)  # Devuelve solo la versión sin la 'v' inicial
                        return version_output
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass

                # Si falla, intentar con los gestores de paquetes
                distro_info = get_distro_info()
                distro_id = distro_info.get('ID', '').lower()

                # Arch Linux y derivados
                if distro_id in ['arch', 'manjaro', 'endeavouros']:
                    try:
                        result = subprocess.run(
                            ['pacman', '-Q', 'penguins-eggs'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            return result.stdout.strip().split()[1]
                    except (subprocess.SubprocessError, FileNotFoundError):
                        pass

                # Debian/Ubuntu y derivados
                elif distro_id in ['debian', 'ubuntu', 'linuxmint', 'pop', 'mint']:
                    try:
                        result = subprocess.run(
                            ['dpkg-query', '-W', '-f=${Version}', 'penguins-eggs'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            return result.stdout.strip()
                    except (subprocess.SubprocessError, FileNotFoundError):
                        pass

                # Fedora/RHEL y derivados
                elif distro_id in ['fedora', 'rhel', 'centos', 'almalinux', 'rocky']:
                    try:
                        result = subprocess.run(
                            ['rpm', '-q', '--queryformat', '%{VERSION}-%{RELEASE}', 'penguins-eggs'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            return result.stdout.strip()
                    except (subprocess.SubprocessError, FileNotFoundError):
                        pass

                # Si todo falla, intentar con which y ejecutar directamente
                try:
                    eggs_path = subprocess.check_output(['which', 'eggs'], timeout=5).decode().strip()
                    if eggs_path:
                        result = subprocess.run(
                            [eggs_path, '--version'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            version_output = result.stdout.strip()
                            version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', version_output)
                            if version_match:
                                return version_match.group(1)
                            return version_output
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass

            except Exception as e:
                print(f"Error al obtener la versión de Penguins' Eggs: {e}")

            return _("No disponible")

        def get_calamares_version():
            """Obtiene la versión de Calamares de forma compatible con múltiples distribuciones."""
            try:
                # Intentar con el comando calamares --version primero
                try:
                    result = subprocess.run(
                        ['calamares', '--version'],
                        capture_output=True,
                        text=True,
                        timeout=5  # Timeout de 5 segundos
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        version_output = result.stdout.strip()
                        # Buscar versión en el formato X.Y.Z o vX.Y.Z
                        version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?(?:-\w+)?)', version_output)
                        if version_match:
                            return version_match.group(1)  # Devuelve solo la versión sin la 'v' inicial
                        return version_output
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass

                # Si falla, intentar con los gestores de paquetes
                distro_info = get_distro_info()
                distro_id = distro_info.get('ID', '').lower()

                # Arch Linux y derivados
                if distro_id in ['arch', 'manjaro', 'endeavouros']:
                    try:
                        result = subprocess.run(
                            ['pacman', '-Q', 'calamares'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            return result.stdout.strip().split()[1]
                    except (subprocess.SubprocessError, FileNotFoundError):
                        pass

                # Debian/Ubuntu y derivados
                elif distro_id in ['debian', 'ubuntu', 'linuxmint', 'pop', 'mint']:
                    try:
                        result = subprocess.run(
                            ['dpkg-query', '-W', '-f=${Version}', 'calamares'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            return result.stdout.strip()
                    except (subprocess.SubprocessError, FileNotFoundError):
                        pass

                # Fedora/RHEL y derivados
                elif distro_id in ['fedora', 'rhel', 'centos', 'almalinux', 'rocky']:
                    try:
                        result = subprocess.run(
                            ['rpm', '-q', '--queryformat', '%{VERSION}-%{RELEASE}', 'calamares'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            return result.stdout.strip()
                    except (subprocess.SubprocessError, FileNotFoundError):
                        pass

                # Si todo falla, intentar con which y ejecutar directamente
                try:
                    calamares_path = subprocess.check_output(['which', 'calamares'], timeout=5).decode().strip()
                    if calamares_path:
                        result = subprocess.run(
                            [calamares_path, '--version'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            version_output = result.stdout.strip()
                            version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?(?:-\w+)?)', version_output)
                            if version_match:
                                return version_match.group(1)
                            return version_output
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass

            except Exception as e:
                print(f"Error al obtener la versión de Calamares: {e}")

            return _("No disponible")

        try:
            eggs_ver = get_eggs_version()
            calamares_ver = get_calamares_version()

            # Debug output
            print(f"[DEBUG] Penguins' Eggs version: {eggs_ver}")
            print(f"[DEBUG] Calamares version: {calamares_ver}")

            # Update UI with versions
            self.version_penguins_label.configure(text=f"Penguins' Eggs: {eggs_ver}")
            self.version_calamares_label.configure(text=f"Calamares: {calamares_ver}")
            self.version_app_label.configure(text=f"{__app__}: {__version__}")

            # Force UI update
            self.root.update_idletasks()

        except Exception as e:
            print(f"[ERROR] Error al actualizar las versiones: {e}")
            # Set fallback text if version detection fails
            self.version_penguins_label.configure(text="Penguins' Eggs: No disponible")
            self.version_calamares_label.configure(text="Calamares: No disponible")
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
            total = self.iso_elapsed + self.copy_elapsed + self.auto_elapsed
            total_str = time.strftime("%H:%M:%S", time.gmtime(total))
            self.root.after(0, lambda: self.total_chrono_label.configure(text=f"{_('Total: ')}{total_str}"))
            if not self.iso_generating and not self.copying and not self.auto_running:
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

                # Construir comando evitando "sudo sudo" y escapando la contraseña
                pwd_esc = shlex.quote(self.password or "")
                cmd_strip = command.lstrip()
                if cmd_strip.startswith("sudo "):
                    # remover solo el primer "sudo " para formar el pipe correcto
                    cmd_no_sudo = cmd_strip[len("sudo "):]
                else:
                    cmd_no_sudo = command

                full_cmd = f"printf '%s\\n' {pwd_esc} | sudo -S {cmd_no_sudo}"
                process = subprocess.Popen(
                    full_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    executable="/bin/bash"
                )

                # Leer la salida en tiempo real
                while True:
                    output = process.stdout.readline()
                    if not output and process.poll() is not None:
                        break
                    if output:
                        self.root.after(0, lambda o=output: self.terminal_text.insert("end", o))
                        self.root.after(0, self.terminal_text.see, "end")

                # Verificar el código de salida
                if process.returncode == 0:
                    if button:
                        self.root.after(0, lambda: button.configure(fg_color="#8b8b8b", state="normal"))
                    self.root.after(0, lambda: messagebox.showinfo(_("Éxito"), _("Operación completada")))
                else:
                    # Mostrar el comando que falló y el código de salida
                    error_output = _("Error en el comando:") + f" {command}\n"
                    error_output += _("Código de salida:") + f" {process.returncode}\n"
                    error_output += _("Asegúrate de que:")
                    error_output += "\n- Tienes permisos de superusuario"
                    error_output += "\n- El comando 'eggs' está instalado correctamente"
                    error_output += "\n- No hay otros procesos de eggs en ejecución"

                    self.root.after(0, lambda: self.terminal_text.insert("end", f"\n{error_output}\n"))
                    self.root.after(0, self.terminal_text.see, "end")
                    raise subprocess.CalledProcessError(process.returncode, command, output=error_output)

            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self.terminal_text.insert("end", f"\nError: {error_msg}\n"))
                self.root.after(0, self.terminal_text.see, "end")
                self.root.after(0, lambda: messagebox.showerror(_("Error"), f"{_('Error:')} {error_msg}"))
                if button:
                    self.root.after(0, lambda: button.configure(fg_color="#295699", state="normal"))
            finally:
                self.root.after(0, lambda: self.ejecutando_label.configure(text=""))
                self.root.after(0, self.progress_bar.stop)
                self.root.after(0, lambda: self.progress_bar.configure(progress_color="orange"))
                if on_complete:
                    self.root.after(0, on_complete)

        # Iniciar el hilo para ejecutar el comando
        threading.Thread(target=run_command, daemon=True).start()

    def _clean_ansi_codes(self, text):
        """Elimina códigos ANSI del texto"""
        if not text:
            return ""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def should_show_line(self, line):
        """Filtra líneas de salida para mostrar solo información relevante"""
        if not line or not line.strip():
            return False

        # Lista de patrones a filtrar
        filter_patterns = [
            'remote: Enumerating objects:', 'remote: Total', 'Receiving objects:',
            'Resolving deltas:', '\x1b[',  # Códigos ANSI
            '=====================================', 'UNIVERSAL INSTALLER',
            'Distro detected:', 'remote: Compressing objects:',
            'remote: Counting objects:', 'from 2)', 'Looking for conflicting packages',
            'checking keyring', 'checking package integrity', 'loading package files',
            'checking for file conflicts', ':: Processing package changes',
            ':: Running pre-transaction hooks', ':: Running post-transaction hooks',
            ':: Waiting for running package', ':: Synchronizing package databases'
        ]

        return not any(pattern in line for pattern in filter_patterns)

    def run_command_with_output(self, cmd, description, timeout=300, shell=True):
        """
        Ejecuta un comando mostrando la salida en tiempo real

        Args:
            cmd: Comando a ejecutar
            description: Descripción del comando
            timeout: Tiempo máximo de espera
            shell: Si se debe ejecutar el comando a través del shell
        """
        try:
            print(f"\n=== {description} ===")
            print(f"Hilo actual: {threading.current_thread().name}")

            # Si el comando incluye sudo y tenemos contraseña, usarla
            if 'sudo' in cmd and hasattr(self, 'password') and self.password:
                # Crear un comando temporal con la contraseña
                temp_cmd = f"""
                #!/bin/bash
                echo '{self.password}' | sudo -S {cmd.replace('sudo ', '')}
                """
                # Guardar el comando temporal
                temp_script = "/tmp/eggs_install_script.sh"
                with open(temp_script, 'w') as f:
                    f.write(temp_cmd)
                os.chmod(temp_script, 0o700)
                cmd = f"bash {temp_script}"

            # Ejecutar el comando
            print(f"Ejecutando comando: {cmd}")
            process = subprocess.Popen(
                cmd,
                shell=shell,
                executable="/bin/bash",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Leer la salida en tiempo real
            while True:
                # Leer tanto de stdout como de stderr
                stdout_line = process.stdout.readline()
                stderr_line = process.stderr.readline()

                if not stdout_line and not stderr_line and process.poll() is not None:
                    break

                # Procesar stdout
                if stdout_line:
                    cleaned_line = self._clean_ansi_codes(stdout_line).strip()
                    if self.should_show_line(cleaned_line):
                        print(cleaned_line)
                        self._update_terminal(cleaned_line)

                # Procesar stderr
                if stderr_line:
                    cleaned_line = self._clean_ansi_codes(stderr_line).strip()
                    if self.should_show_line(cleaned_line):
                        # Solo mostrar como error si realmente es un error
                        if any(keyword in cleaned_line.lower() for keyword in ['error', 'failed', 'fallo', 'falló']):
                            print(f"ERROR: {cleaned_line}", file=sys.stderr)
                            self._update_terminal(f"ERROR: {cleaned_line}", error=True)
                        else:
                            print(cleaned_line)
                            self._update_terminal(cleaned_line)

            # Obtener el código de salida
            return_code = process.returncode
            print(f"Comando terminado con código: {return_code}")

            # Limpiar el script temporal si existe
            if 'temp_script' in locals() and os.path.exists(temp_script):
                try:
                    os.remove(temp_script)
                except Exception as e:
                    print(f"No se pudo eliminar el script temporal: {e}")

            return return_code

        except Exception as e:
            error_msg = f"Error ejecutando comando: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.terminal_text.configure(state='normal')
            self.terminal_text.insert("end", f"\n{error_msg}\n")
            self.terminal_text.see("end")
            self.terminal_text.configure(state='disabled')
            return -1

    def update_eggs_and_calamares(self):
        """Actualiza/Instala Eggs y Calamares desde el repositorio"""
        print("\n=== INICIO DE ACTUALIZACIÓN ===")
        print(f"Hilo actual: {threading.current_thread().name}")

        # 1. Obtener contraseña de sudo
        if not hasattr(self, 'sudo_password'):
            print("Solicitando contraseña de sudo...")
            self.sudo_password = simpledialog.askstring(
                "Contraseña requerida",
                "Ingrese su contraseña de administrador:",
                show='*'
            )
            if not self.sudo_password:
                error_msg = "Se requiere la contraseña de administrador"
                print(f"ERROR: {error_msg}")
                messagebox.showerror("Error", error_msg)
                return

        # 2. Configurar interfaz
        print("Configurando interfaz...")
        try:
            self.root.after(0, lambda: [
                self.prep_switch.configure(state="disabled"),
                self.calamares_switch.configure(state="disabled"),
                self.btn_pre.configure(state="disabled"),
                self.progress_bar.stop(),
                self.progress_bar.configure(progress_color="#8A2BE2", mode="indeterminate"),
                self.progress_bar.start(),
                self.ejecutando_label.configure(text="Actualizando Eggs y Calamares...")
            ])
            print("Interfaz configurada")
        except Exception as e:
            print(f"Error configurando interfaz: {e}")

        # 3. Iniciar el proceso en un hilo separado
        print("Iniciando hilo de actualización...")
        update_thread = threading.Thread(target=self._update_process, daemon=True)
        update_thread.start()
        print("Hilo de actualización iniciado")

    def _update_process(self):
        """Proceso de actualización en segundo plano"""
        try:
            # 1. Configurar terminal
            self.root.after(0, lambda: [
                self.terminal_text.configure(state='normal'),
                self.terminal_text.delete('1.0', 'end'),
                self.terminal_text.insert('end', "=== INICIANDO ACTUALIZACIÓN ===\n"),
                self.terminal_text.see('end')
            ])
            print("Terminal configurada")

            # 2. Obtener directorios
            home_dir = os.path.expanduser("~")
            repo_dir = os.path.join(home_dir, "fresh-eggs")
            print(f"Directorio del repositorio: {repo_dir}")

            # 3. Eliminar versión anterior si existe
            if os.path.exists(repo_dir):
                print("Eliminando versión anterior...")
                self._update_terminal("Eliminando versión anterior...")
                try:
                    shutil.rmtree(repo_dir, ignore_errors=False)
                    print("Versión anterior eliminada exitosamente")
                    self._update_terminal("Versión anterior eliminada exitosamente")
                except Exception as e:
                    error_msg = f"Error al eliminar versión anterior: {str(e)}"
                    print(error_msg)
                    self._update_terminal(error_msg, error=True)
                    raise

            # 4. Clonar el repositorio
            print("Iniciando clonación del repositorio...")
            self._update_terminal("Clonando repositorio de Eggs...")

            # Verificar si git está instalado
            if shutil.which('git') is None:
                error_msg = "Error: Git no está instalado. Por favor instale Git primero."
                print(error_msg)
                self._update_terminal(error_msg, error=True)
                raise Exception(error_msg)

            # Clonar el repositorio sin mostrar progreso detallado
            cmd = f"git clone --quiet https://github.com/pieroproietti/fresh-eggs {repo_dir}"
            return_code = self.run_command_with_output(cmd, "Clonando repositorio")

            # Verificar si la clonación fue exitosa
            if return_code != 0 or not os.path.exists(os.path.join(repo_dir, '.git')):
                error_msg = "Error: No se pudo clonar el repositorio. Verifique su conexión a internet y los permisos."
                print(error_msg)
                self._update_terminal(error_msg, error=True)
                raise Exception(error_msg)

            success_msg = "Repositorio clonado exitosamente"
            print(success_msg)
            self._update_terminal(success_msg)

            # 5. Ejecutar la instalación
            print("Iniciando instalación...")
            self._update_terminal("Iniciando instalación de Eggs...")
            os.chdir(repo_dir)

            # Hacer el script ejecutable
            os.chmod("./fresh-eggs.sh", 0o755)

            # Filtrar mensajes específicos del instalador
            def filter_output(line):
                line = line.strip()
                filters = [
                    'ERROR:', '::', 'cargando', 'buscando', 'Tamaño', 'Paquete',
                    'reinstalando', 'resolviendo', 'comprobando', 'verificando',
                    'Downloading', 'Downloaded', 'Running:', 'Installing', 'Updating',
                    'Arming', 'Refreshing', 'Installation completed', 'UNIVERSAL INSTALLER',
                    'advertencia:', '--:--:--', 'Dload', 'Upload', 'Total', 'Spent', 'Left',
                    'Speed', 'From', 'will download', 'All packages downloaded',
                    'The following commands', 'penguins-eggs-', 'MiB', 'kB', 'kB/s',
                    '--noconfirm', '/tmp/penguins-eggs-', '--:--:--', '0:00:0',
                    'looking for conflicting packages', 'checking keyring',
                    'checking package integrity', 'loading package files',
                    'checking for file conflicts', ':: Processing package changes',
                    ':: Running pre-transaction hooks', ':: Running post-transaction hooks',
                    ':: Waiting for running package', ':: Synchronizing package databases'
                ]
                if any(filtro in line for filtro in filters):
                    return False
                if not line or line.isspace():
                    return False
                return True

            # Crear un comando temporal para ejecutar con la contraseña
            cmd = f'sudo -S ./fresh-eggs.sh <<EOF\n{self.password}\nEOF'

            # Ejecutar con un tiempo de espera más largo (30 minutos)
            return_code = self.run_command_with_output(
                cmd,
                "Instalando Eggs",
                timeout=1800,  # 30 minutos de tiempo de espera
                shell=True
            )

            if return_code != 0:
                error_msg = "Error durante la instalación de Eggs. Código de salida: " + str(return_code)
                print(error_msg)
                self._update_terminal(error_msg, error=True)
                raise Exception(error_msg)

            print("Instalación completada exitosamente")
            self._update_terminal("¡Actualización completada exitosamente!")

            # Actualizar las versiones mostradas en la interfaz
            self.root.after(0, self.update_versions)

            # Verificar que la instalación fue exitosa
            if shutil.which('eggs') is None:
                error_msg = "Error: La instalación no se completó correctamente. El comando 'eggs' no está disponible."
                print(error_msg)
                self._update_terminal(error_msg, error=True)
                raise Exception(error_msg)

            # Crear enlace simbólico si no existe
            initramfs_link = "/boot/initramfs-linux-1.img"
            initramfs_file = "/boot/initramfs-linux.img"
            if not os.path.exists(initramfs_link) and os.path.exists(initramfs_file):
                try:
                    os.symlink(initramfs_file, initramfs_link)
                    self._update_terminal(f"Creado enlace simbólico: {initramfs_link} -> {initramfs_file}")
                except Exception as e:
                    error_msg = f"Advertencia: No se pudo crear el enlace simbólico: {str(e)}"
                    print(error_msg)
                    self._update_terminal(error_msg, error=True)

            # Apagar el switch de calamares y encender el de preparación
            self.root.after(0, lambda: [
                self.calamares_switch_var.set(False),  # Apagar actualización de calamares
                self.prep_switch_var.set(True),        # Encender preparación
                self.prep_switch.configure(state="normal"),
                self.calamares_switch.configure(state="normal"),
                self.btn_pre.configure(state="normal")
            ])

        except Exception as e:
            error_msg = f"Error durante la actualización: {str(e)}"
            print(error_msg)
            self._update_terminal(f"ERROR: {error_msg}", error=True)
        finally:
            # Restaurar interfaz
            self.root.after(0, self._restore_ui)

    def _update_terminal(self, message, error=False):
        """Actualiza la terminal con un mensaje"""
        # No mostrar mensajes vacíos o solo con espacios
        if not message or message.isspace():
            return

        # Configurar colores
        colors = {
            'error': '#ff6b6b',
            'success': '#6bff6b',
            'info': '#87CEFA',  # Light blue
            'warning': '#ffb86c'
        }

        # Determinar el color basado en el tipo de mensaje
        color = colors['error'] if error else colors['info']

        # Aplicar formato al mensaje
        formatted_message = f"{message}\n"

        # Actualizar la interfaz
        def update_gui():
            self.terminal_text.configure(state='normal')
            # Insertar con el color apropiado
            self.terminal_text.insert('end', formatted_message)
            # Aplicar formato al texto recién insertado
            start = self.terminal_text.index('end-1c')
            self.terminal_text.tag_add('colored', start, 'end')
            self.terminal_text.tag_config('colored', foreground=color)
            self.terminal_text.see('end')
            self.terminal_text.configure(state='disabled')

        # Ejecutar en el hilo principal
        self.root.after(0, update_gui)

        # Mostrar en consola
        if error:
            print(f"ERROR: {message}", file=sys.stderr)
        else:
            print(f"INFO: {message}")

    def _restore_ui(self):
        """Restaura la interfaz de usuario"""
        self.progress_bar.stop()
        self.progress_bar.configure(progress_color="orange", mode="determinate")
        self.prep_switch.configure(state="normal")
        self.calamares_switch.configure(state="normal")
        self.btn_pre.configure(state="normal")
        self.ejecutando_label.configure(text="")
        self.updating_eggs = False

    def apply_pre_actions(self):
        """Ejecuta las acciones de preparación seleccionadas"""
        try:
                                             # Deshabilitar controles al inicio

            self.prep_switch.configure(state="disabled")
            self.calamares_switch.configure(state="disabled")
            self.btn_pre.configure(state="disabled")
            self.terminal_text.delete('1.0', 'end')  # Limpiar terminal

            # Mostrar mensaje de inicio
            self.terminal_text.insert('end', "=== Iniciando preparación ===\n")
            self.terminal_text.see('end')

            # Si solo está activado Calamares, actualizar y salir
            if self.calamares_switch_var.get() and not self.prep_switch_var.get():
                self.terminal_text.insert('end', "Actualizando Eggs y Calamares...\n")
                self.terminal_text.see('end')
                self.update_eggs_and_calamares()
                return

            # Si está activada la preparación, continuar con las acciones
            comandos = []
            if self.prep_switch_var.get():
                comandos.extend([
                    f"{self.eggs_path} kill -n",
                    f"{self.eggs_path} tools clean -n",
                    f"sudo {self.eggs_path} dad -d"  # Añadido espacio después de sudo
                ])

            if self.calamares_switch_var.get():
                comandos.append(f"{self.eggs_path} calamares --install")

            def run_next_command(index=0):
                if index < len(comandos):
                    comando = comandos[index]
                    self.terminal_text.insert('end', f"\n=== Ejecutando comando {index+1}/{len(comandos)} ===\n{comando}\n")
                    self.terminal_text.see('end')

                    def on_command_complete():
                        if index + 1 < len(comandos):
                            run_next_command(index + 1)
                        else:
                            # Mostrar mensaje de finalización solo una vez al terminar todos los comandos
                            self.terminal_text.insert('end', "\n¡Operación completada con éxito!\n")
                            self.terminal_text.see('end')
                            self.enable_additional_options()

                    self.execute_command(
                        comando,
                        self.btn_pre,
                        progress_color="orange",
                        on_complete=on_command_complete
                    )
                else:
                    self.enable_additional_options()

            if comandos:
                self.terminal_text.insert('end', f"\n=== Iniciando secuencia de comandos ===\n")
                self.terminal_text.see('end')
                run_next_command()
            else:
                self.terminal_text.insert('end', "No hay comandos para ejecutar.\n")
                self.terminal_text.see('end')
                self.enable_additional_options()

        except Exception as e:
            error_msg = f"Error en apply_pre_actions: {str(e)}"
            self.terminal_text.insert('end', f"\n{error_msg}\n")
            self.terminal_text.see('end')
            messagebox.showerror("Error", error_msg)
            self.enable_additional_options()

    def enable_additional_options(self):
        # Si estamos en modo Manual (prep_switch ON) -> activar Fase 2 (réplica, editar config, botón)
        try:
            if getattr(self, "prep_switch_var", None) and self.prep_switch_var.get():
                # Activar las opciones de Fase 2 para que el usuario pueda continuar tras aplicar Fase 1 manual
                self.replica_switch.configure(state="normal")
                self.edit_config_switch.configure(state="normal")
                self.btn_opciones.configure(state="normal")
            else:
                # En AUTO o si no está claro, mantener Fase 2 desactivada
                self.replica_switch.configure(state="disabled")
                self.edit_config_switch.configure(state="disabled")
                self.btn_opciones.configure(state="disabled")
        except Exception:
            pass
        # Asegurar que Fase 3 esté disponible tanto en Manual como en AUTO
        try:
            self.btn_generar.configure(state="normal")
        except Exception:
            pass
        # Opciones ISO (switches) pueden permanecer disponibles
        try:
            self.iso_data_switch.configure(state="normal")
            self.iso_comp_switch.configure(state="normal")
        except Exception:
            pass

    # ----------- Generar ISO -----------
    def apply_iso_generation(self):
        self.btn_generar.configure(state="disabled")
        self.iso_elapsed = 0
        self.iso_generating = True
        threading.Thread(target=self.update_iso_timer, daemon=True).start()
        self.start_total_timer()
        if self.iso_comp_switch_var.get():
            cmd = f"sudo {self.eggs_path} produce --pendrive -n"
        else:
            if self.iso_data_switch_var.get():
                cmd = f"sudo {self.eggs_path} produce --clone -n"
            else:
                cmd = f"sudo {self.eggs_path} produce --noicon -n"
        self.execute_command(cmd, self.btn_generar, progress_color="#2065F7", on_complete=self.on_iso_generation_complete)

    def on_iso_generation_complete(self):
        self.iso_generating = False
        self.enable_copy_iso()
        # MODIFICACIÓN 2: Mostrar tamaño de la ISO inmediatamente después de la generación
        self.update_iso_size()
        # Mostrar la etiqueta de tamaño cuando termine la generación
        self.size_label.pack(pady=(5, 10))
        # Volver a habilitar el botón Fase 3 después de completar la generación
        try:
            self.btn_generar.configure(state="normal")
        except Exception:
            pass

    def update_iso_size(self):
        iso_source_dir = "/home/eggs/.mnt/"
        try:
            print(f"Buscando archivos ISO en: {iso_source_dir}")  # Debug
            if not os.path.exists(iso_source_dir):
                print(f"Error: El directorio {iso_source_dir} no existe")  # Debug
                self.size_label.configure(text="Error: No se encontró el directorio de ISO")
                return

            iso_files = [f for f in os.listdir(iso_source_dir) if f.endswith(".iso")]
            print(f"Archivos ISO encontrados: {iso_files}")  # Debug

            if iso_files:
                ruta = os.path.join(iso_source_dir, iso_files[0])
                print(f"Obteniendo tamaño de: {ruta}")  # Debug
                tam_Bytes = os.path.getsize(ruta)
                size_str = self.format_size(tam_Bytes)
                print(f"Tamaño de la ISO: {size_str}")  # Debug
                self.size_label.configure(text=f"Tamaño ISO: {size_str}")
                # Forzar actualización de la interfaz
                self.size_label.update_idletasks()
            else:
                print("No se encontraron archivos ISO")  # Debug
                self.size_label.configure(text="Tamaño ISO: No encontrada")
        except Exception as e:
            print(f"Error al obtener tamaño de ISO: {str(e)}")  # Debug
            self.size_label.configure(text=f"Error: {str(e)}")

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
        try:
            if self.copia_contador > 0:
                respuesta = messagebox.askyesno("Tipo de copia", "¿Desea realizar una copia rápida?")
                self.copy_speed_switch_var.set(respuesta)

            # Usar try/except para capturar cualquier error con el diálogo
            try:
                dest_dir = filedialog.askdirectory(title="Seleccionar destino para guardar la ISO")
                if not dest_dir:  # Usuario canceló la selección
                    self._update_terminal("Operación de copia cancelada por el usuario")
                    return
            except Exception as e:
                self._update_terminal(f"Error al seleccionar directorio: {str(e)}", error=True)
                return

            self.copy_elapsed = 0
            self.copying = True
            threading.Thread(target=self.update_copy_timer, daemon=True).start()
            self.start_total_timer()
            self.ejecutando_label.configure(text="Ejecutando: Copiar ISO")
            self._update_terminal(f"Iniciando copia de la ISO a: {dest_dir}")

        except Exception as e:
            self._update_terminal(f"Error al preparar la copia: {str(e)}", error=True)
            self._restore_ui()

        def copy_process():
            success = False
            try:
                proc_text = button.cget("text")
                self.root.after(0, lambda: self.terminal_text.insert("end", f"Ejecutando: {proc_text}\n"))
                # Desactivar el botón solo durante la copia
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
                self.root.after(0, lambda: self.contador_label.configure(
                    text=f"Copias realizadas: {self.copia_contador}"
                ))

                # Mostrar mensaje de éxito
                success_msg = (
                    f"ISO copiada exitosamente!\n\n"
                    f"Nombre: {os.path.basename(dest_path)}\n"
                    f"Tamaño: {total_size/(1024**2):.2f} MB\n"
                    f"Ubicación: {dest_path}"
                )

                self.root.after(0, lambda: messagebox.showinfo("Éxito", success_msg))
                self.terminal_text.insert('end', "\n=== PROCESO AUTO COMPLETADO ===\n")
                self.terminal_text.see('end')

                # Finalizar con éxito
                self._finish_auto(True)
                success = True

            except Exception as e:
                error_msg = f"Error al copiar la ISO: {str(e)}"
                self.terminal_text.insert('end', f"\n{error_msg}")
                self.terminal_text.see('end')
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
                self._finish_auto(False)
            finally:
                # Asegurar que el botón Copiar ISO y el switch de copia rápida permanezcan habilitados
                try:
                    self.root.after(0, lambda: button.configure(state="normal", fg_color=self.color_button))
                except Exception:
                    pass
                try:
                    self.root.after(0, lambda: self.copy_speed_switch.configure(state="normal"))
                except Exception:
                    pass
                # Mantener la bandera copying en False por si acaso
                self.copying = False

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
            button.configure(fg_color="#8b8b8b", state="normal")
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
                self.terminal_text.insert("end", "Eliminando archivos temporales...\n")
                self.terminal_text.see("end")
                self.root.update()
                cmd = f"echo {self.password} | sudo -S rm -rf /home/eggs"
                subprocess.run(cmd, shell=True, check=True)
                messagebox.showinfo(_("Limpieza"), _("Se eliminaron los archivos temporales"))
        except Exception as e:
            messagebox.showerror(_("Error"), f"Error al eliminar archivos temporales: {str(e)}")
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

import asyncio
import os
import time
import shlex
from nicegui import ui

from version import __app__, __version__
from backend import EggsmakerBackend

# Initialize backend
backend = EggsmakerBackend()

# Theme colors matching eggsmaker.py
COLORS = {
    'bg': '#23272e',          # Main background
    'panel': '#000000',       # Panels
    'button': '#0E48C5',      # Buttons
    'button_hover': '#1741a6',
    'orange': '#FD8637',      # Accents
    'terminal_bg': '#0e1010',
    'terminal_text': '#87CEFA',
    'light_blue': '#00BFFF',
    'success': '#39ee39',     # Green text
    'error': '#ff0000',
    'switch_on': '#00FF00',
    'switch_off': '#000000',
}

THEME_CSS = """
:root {{
  --egg-bg: {bg};
  --egg-panel: {panel};
  --egg-button: {button};
  --egg-button-hover: {button_hover};
  --egg-orange: {orange};
  --egg-terminal-bg: {terminal_bg};
  --egg-terminal-text: {terminal_text};
  --egg-light-blue: {light_blue};
  --egg-success: {success};
  --egg-error: {error};
  
  /* Button state colors */
  --btn-executing: #ff0000;
  --btn-success: #39ee39;
  --btn-disabled: #8b8b8b;
  --btn-warning: #FD8637;
}}

/* Global styles */
body {{ 
  background-color: var(--egg-bg) !important; 
  color: #ffffff; 
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}}

/* Smooth transitions for all elements */
* {{
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}

/* Panel styling with glassmorphism */
.egg-panel {{ 
  background: linear-gradient(135deg, var(--egg-panel) 0%, rgba(0, 0, 0, 0.95) 100%) !important;
  border: 2px solid #333333;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
}}

/* Button base styling */
.egg-button {{ 
  background: linear-gradient(135deg, var(--egg-button) 0%, #0a3a8f 100%) !important;
  color: #ffffff !important; 
  font-weight: bold; 
  border-radius: 12px !important;
  box-shadow: 0 4px 12px rgba(14, 72, 197, 0.4);
  transition: all 0.3s ease;
  border: none;
}}

/* Global button rounding */
.q-btn {{
  border-radius: 12px !important;
}}

.egg-button:hover {{ 
  background: linear-gradient(135deg, var(--egg-button-hover) 0%, #0a2d6f 100%) !important;
  box-shadow: 0 6px 16px rgba(14, 72, 197, 0.6);
  transform: translateY(-2px);
}}

.egg-button:active {{
  transform: translateY(0px);
  box-shadow: 0 2px 8px rgba(14, 72, 197, 0.4);
}}

/* Button state: Executing (Red) */
.btn-executing {{
  background: linear-gradient(135deg, #ff0000 0%, #cc0000 100%) !important;
  box-shadow: 0 4px 12px rgba(255, 0, 0, 0.5);
  animation: pulse-red 2s infinite;
}}

/* Button state: Success (Green) */
.btn-success {{
  background: linear-gradient(135deg, #339991 0%, #2a7a73 100%) !important;
  box-shadow: 0 4px 12px rgba(51, 153, 145, 0.5);
}}

/* Button state: Disabled (Gray) */
.btn-disabled {{
  background: linear-gradient(135deg, #8b8b8b 0%, #6a6a6a 100%) !important;
  box-shadow: 0 2px 8px rgba(139, 139, 139, 0.3);
  opacity: 0.7;
  cursor: not-allowed !important;
}}

/* Pulse animation for executing state */
@keyframes pulse-red {{
  0%, 100% {{
    box-shadow: 0 4px 12px rgba(255, 0, 0, 0.5);
  }}
  50% {{
    box-shadow: 0 4px 20px rgba(255, 0, 0, 0.8);
  }}
}}

/* Title styling */
.egg-title {{ 
  color: var(--egg-light-blue) !important; 
  font-size: 17px; 
  font-weight: bold;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}}

/* Terminal styling */
.egg-terminal {{ 
  background-color: var(--egg-terminal-bg) !important; 
  color: var(--egg-terminal-text) !important; 
  font-family: 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
  border-radius: 10px; 
  border: 1px solid #444C5E;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.5);
  padding: 12px;
}}

/* Scrollbar styling for terminal */
.egg-terminal::-webkit-scrollbar {{
  width: 8px;
}}

.egg-terminal::-webkit-scrollbar-track {{
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
}}

.egg-terminal::-webkit-scrollbar-thumb {{
  background: rgba(135, 206, 250, 0.5);
  border-radius: 4px;
}}

.egg-terminal::-webkit-scrollbar-thumb:hover {{
  background: rgba(135, 206, 250, 0.8);
}}

/* Header styling */
.egg-header-title {{ 
  color: var(--egg-light-blue) !important; 
  font-weight: 800; 
  font-size: 1.4rem;
  text-shadow: 0 2px 8px rgba(0, 191, 255, 0.5);
}}

.q-page-container {{ padding-top: 0 !important; }}
.q-page {{ padding-top: 0 !important; }}
.q-header {{ 
  margin-bottom: 0 !important; 
  background: linear-gradient(135deg, var(--egg-panel) 0%, rgba(0, 0, 0, 0.98) 100%) !important;
  border-bottom: 1px solid rgba(68, 76, 94, 0.6);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}}

/* Progress bar styling */
.q-linear-progress {{
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #444;
}}

.q-linear-progress__track {{
  background: rgba(68, 76, 94, 0.5) !important;
}}

/* Card hover effects */
.q-card {{
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}}

.q-card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}}

/* Switch styling */
.q-toggle {{
  transition: all 0.3s ease;
}}

.q-toggle__thumb {{
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}}

/* Input styling */
.q-field__control {{
  background: rgba(14, 16, 16, 0.6) !important;
  border-radius: 6px;
}}

.q-field__control:hover {{
  background: rgba(14, 16, 16, 0.8) !important;
}}

/* Dialog styling */
.q-dialog__backdrop {{
  backdrop-filter: blur(8px);
  background: rgba(0, 0, 0, 0.6) !important;
}}

.q-card {{
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
}}

/* Animations */
@keyframes fadeIn {{
  from {{ opacity: 0; }}
  to {{ opacity: 1; }}
}}

@keyframes slideUp {{
  from {{ 
    opacity: 0;
    transform: translateY(20px);
  }}
  to {{ 
    opacity: 1;
    transform: translateY(0);
  }}
}}

.fade-in {{
  animation: fadeIn 0.5s ease;
}}

.slide-up {{
  animation: slideUp 0.5s ease;
}}

/* Status labels with glow effect */
.status-executing {{
  color: #ff0000 !important;
  text-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
  animation: pulse-text 2s infinite;
}}

.status-success {{
  color: #39ee39 !important;
  text-shadow: 0 0 10px rgba(57, 238, 57, 0.5);
}}

@keyframes pulse-text {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.7; }}
}}

/* Responsive improvements */
@media (max-width: 768px) {{
  .egg-header-title {{
    font-size: 1.1rem;
  }}
  .egg-panel {{
    border-radius: 8px;
  }}
}}
""".format(**COLORS)

# Global state
log_lines: list[str] = []
auto_running = False
iso_generating = False
copying = False
copy_count = 0

copy_elapsed = 0
iso_elapsed = 0
auto_elapsed = 0

# Copy progress state (shared between thread and UI)
copy_state = {'progress': 0.0, 'percent': 0}

# UI Elements
console = None
progress = None
phase_status = None
iso_size_label = None
copy_percent = None
copy_counter_label = None
copy_time_label = None
iso_time_label = None
Total_time_label = None

# Buttons (for dynamic state changes)
btn_phase1 = None
btn_phase2 = None
btn_phase3 = None
btn_copy_iso = None
btn_auto = None
btn_clean = None

# Switches
prep_manual = None
calamares_update = None
replica_switch = None
edit_config_switch = None
iso_include_data = None
iso_max_compression = None
copy_speed_switch = None
dest_dir_input = None
fase2_btn = None
versions_eggs = None
versions_calamares = None

def append_log(text: str) -> None:
    if console:
        console.push(text)

def set_progress(value: float | None, spinning: bool = False) -> None:
    if progress is None:
        return
    if spinning:
        progress.props('indeterminate')  # Set indeterminate property
        progress.value = 0  # Reset value
    else:
        progress.props(remove='indeterminate')  # Remove indeterminate
        progress.value = max(0.0, min(1.0, value or 0.0))
    progress.update()

async def update_versions() -> None:
    eggs_ver = 'No disponible'
    try:
        rc, out = await backend.run_capture('eggs --version')
        if rc == 0 and out:
            import re
            m = re.search(r"v?(\d+\.\d+(?:\.\d+)?)", out)
            if m:
                eggs_ver = m.group(1)
            else:
                eggs_ver = out.strip().splitlines()[-1]
    except Exception:
        pass

    calamares_ver = 'No disponible'
    try:
        for cmd in ['calamares --version', 'calamares -v']:
            rc, out = await backend.run_capture(cmd)
            if rc == 0 and out:
                import re
                m = re.search(r"v?(\d+\.\d+(?:\.\d+)?)", out)
                if m:
                    calamares_ver = m.group(1)
                else:
                    calamares_ver = out.strip().splitlines()[-1]
                break
    except Exception:
        pass

    if versions_eggs:
        versions_eggs.text = f"Penguins' Eggs: {eggs_ver}"
        versions_eggs.update()
    if versions_calamares:
        versions_calamares.text = f"Calamares: {calamares_ver}"
        versions_calamares.update()

def update_iso_size() -> None:
    # Check multiple locations
    possible_sources = ["/home/eggs/.mnt/", "/home/eggs/"]
    found_path = None
    
    for p in possible_sources:
        if os.path.exists(p):
            try:
                files = [f for f in os.listdir(p) if f.endswith('.iso')]
                if files:
                    found_path = os.path.join(p, files[0])
                    break
            except Exception:
                pass
                
    if not found_path:
        iso_size_label.text = 'Tamaño ISO: No encontrada'
    else:
        try:
            size = os.path.getsize(found_path)
            iso_size_label.text = f"Tamaño ISO: {backend.format_size(size)}"
        except Exception as e:
            iso_size_label.text = f"Error: {e}"
    iso_size_label.update()

def check_sudo() -> bool:
    if not backend.sudo_password:
        ui.notify('Se requiere contraseña de sudo. Recargue la página o reinicie.', type='negative')
        return False
    return True

async def do_update_eggs_and_calamares() -> int:
    if not check_sudo(): return -1
    import shlex  # Import at function level for all code paths
    try:
        home = os.path.expanduser('~')
        repo_dir = os.path.join(home, 'fresh-eggs')
        append_log('=== INICIANDO ACTUALIZACIÓN ===')
        if os.path.exists(repo_dir):
            append_log('Eliminando versión anterior...')
            rc = await backend.run_stream(f"rm -rf {shlex.quote(repo_dir)}", append_log)
            if rc != 0: return rc
        
        append_log('Clonando repositorio de Eggs...')
        rc = await backend.run_stream(f"git clone --quiet https://github.com/pieroproietti/fresh-eggs {shlex.quote(repo_dir)}", append_log)
        if rc != 0: return rc
        
        script_path = os.path.join(repo_dir, 'fresh-eggs.sh')
        rc = await backend.run_stream(f"chmod +x {shlex.quote(script_path)}", append_log)
        if rc != 0: return rc
        
        # Execute with sudo like eggsmaker.py does - change to directory first and execute
        # This is important because fresh-eggs.sh may have relative path dependencies
        append_log('Ejecutando instalador...')
        cd_and_exec = f"cd {shlex.quote(repo_dir)} && sudo ./fresh-eggs.sh"
        rc = await backend.run_stream(cd_and_exec, append_log)
        if rc != 0: return rc
        
        append_log('¡Actualización completada exitosamente!')
        return 0
    except Exception as e:
        append_log(f"Error durante la actualización: {e}")
        return -1

async def do_preparation() -> None:
    if not check_sudo(): return
    global btn_phase1
    
    try:
        # Set button to executing state (red, pulsing)
        if btn_phase1:
            original_text = btn_phase1.text
            btn_phase1.props('color=red disable')
            btn_phase1.style('background-color: #ff0000 !important')
            btn_phase1.classes(add='btn-executing')
            btn_phase1.text = 'Ejecutando...'
            btn_phase1.update()
        
        # Check if we should update eggs/calamares
        if (calamares_update and calamares_update.value) and (prep_manual and not prep_manual.value):
            if phase_status:
                phase_status.text = 'Actualizando Eggs y Calamares'
                phase_status.classes(add='status-executing')
                phase_status.update()
            set_progress(None, spinning=True)
            rc = await do_update_eggs_and_calamares()
            set_progress(0)
            if phase_status:
                phase_status.text = ''
                phase_status.classes(remove='status-executing')
                phase_status.update()
            if rc == 0:
                ui.notify('Actualización completada', type='positive')
                await update_versions()
                # Success state for button
                if btn_phase1:
                    btn_phase1.props(remove='color disable')
                    btn_phase1.classes(remove='btn-executing', add='btn-success')
                    btn_phase1.text = '✓ Actualizado'
                    btn_phase1.update()
            else:
                ui.notify('Error en actualización', type='negative')
                # Error state - return to normal
                if btn_phase1:
                    btn_phase1.props(remove='color disable')
                    btn_phase1.style('background-color: #091f9e !important')
                    btn_phase1.classes(remove='btn-executing btn-success')
                    btn_phase1.text = original_text
                    btn_phase1.update()
            return
    except Exception:
        pass

    # Regular preparation process
    if phase_status:
        phase_status.text = 'Ejecutando: Preparación'
        phase_status.classes(add='status-executing')
        phase_status.style(f"color: {COLORS['success']}")
        phase_status.update()
    
    set_progress(None, spinning=True)
    
    eggs = await backend.get_cmd_eggs()
    cmds = [
        f"{eggs} kill -n",
        f"{eggs} tools clean -n",
        f"{eggs} dad -d",
    ]
    
    try:
        if calamares_update and calamares_update.value:
            cmds.append(f"{eggs} calamares --install")
    except Exception:
        pass

    success = True
    for c in cmds:
        rc = await backend.run_stream(c, append_log)
        if rc != 0:
            success = False
            set_progress(0)
            if phase_status:
                phase_status.text = ''
                phase_status.classes(remove='status-executing')
                phase_status.update()
            ui.notify('Error durante la preparación', type='negative')
            # Error state
            if btn_phase1:
                btn_phase1.props(remove='color disable')
                btn_phase1.style('background-color: #091f9e !important')
                btn_phase1.classes(remove='btn-executing btn-success')
                btn_phase1.text = original_text if 'original_text' in locals() else 'Fase 1'
                btn_phase1.update()
            return
            
    set_progress(0)
    if phase_status:
        phase_status.text = ''
        phase_status.classes(remove='status-executing')
        phase_status.update()
        
    if replica_switch: replica_switch.enable(); replica_switch.update()
    if edit_config_switch: edit_config_switch.enable(); edit_config_switch.update()
    if fase2_btn: fase2_btn.enable(); fase2_btn.update()
    
    # Success state (green button)
    if btn_phase1:
        btn_phase1.props(remove='color disable')
        btn_phase1.classes(remove='btn-executing', add='btn-success')
        btn_phase1.text = '✓ Completado'
        btn_phase1.update()
    
    ui.notify('Preparación completada', type='positive')

async def edit_config_dialog() -> None:
    append_log("DEBUG: edit_config_dialog called")
    try:
        config_file = "/etc/penguins-eggs.d/eggs.yaml"
        # import shlex # Already imported globally
        # Use sudo to read the file
        append_log(f"DEBUG: Reading {config_file}")
        rc, content = await backend.run_capture(f"sudo cat {shlex.quote(config_file)}")
        append_log(f"DEBUG: read rc={rc}, content_len={len(content) if content else 0}")
        if rc != 0 or not content:
            ui.notify('No se pudo leer eggs.yaml (verifique permisos/sudo)', type='warning')
            return
    except Exception as e:
        append_log(f"DEBUG: edit_config_dialog error: {e}")
        ui.notify(f"Error: {e}", type='negative')
        return
        
    try:
        current = {
            'root_passwd': '',
            'snapshot_basename': '',
            'snapshot_prefix': '',
            'user_opt_passwd': '',
        }
        
        for line in content.splitlines():
            for key in list(current.keys()):
                if line.startswith(f"{key}:"):
                    current[key] = line.split(':', 1)[1].strip()
                    
        with ui.dialog() as d:
            with ui.card().classes('w-[500px] egg-panel'):
                ui.label('Editar Configuración ISO').classes('text-xl font-bold mb-4')
                inputs = {}
                def add_input(label, key, password=False):
                    ui.label(label).classes('font-bold')
                    # Add dark props and text-white class for visibility
                    inp = ui.input(value=current.get(key, ''), password=password, password_toggle_button=password).props('dark input-class="text-white"').classes('w-full mb-2')
                    inputs[key] = inp
                
                add_input('Contraseña de root:', 'root_passwd', password=True)
                add_input('Nombre base del snapshot (ej: mi-distro):', 'snapshot_basename')
                add_input('Prefijo del snapshot (ej: personalizada-):', 'snapshot_prefix')
                add_input('Contraseña de usuario:', 'user_opt_passwd', password=True)
                
                async def on_save():
                    try:
                        new_lines = []
                        for line in content.splitlines(True):
                            line_stripped = line.strip()
                            replaced = False
                            for key, inp in inputs.items():
                                if line.startswith(f"{key}:"):
                                    new_lines.append(f"{key}: {inp.value}\n")
                                    replaced = True
                                    break
                            if not replaced:
                                new_lines.append(line)
                        temp_path = "/tmp/eggs_yaml_tmp"
                        with open(temp_path, 'w') as f:
                            f.writelines(new_lines)
                        # Use sudo to install the file back
                        rc = await backend.run_stream(f"sudo install -m 644 {shlex.quote(temp_path)} {shlex.quote(config_file)}", append_log)
                        if rc == 0:
                            ui.notify('Configuración guardada', type='positive')
                            d.close()
                        else:
                            ui.notify('No se pudo guardar la configuración', type='negative')
                    except Exception as e:
                        ui.notify(f'Error: {e}', type='negative')
                        
                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Listo', on_click=d.close).classes('mr-2 bg-red-600 hover:bg-red-700')
                    ui.button('Guardar cambios', on_click=lambda: asyncio.create_task(on_save())).classes('egg-button')
        append_log("DEBUG: Opening dialog")
        d.open()
    except Exception as e:
        append_log(f"DEBUG: edit_config_dialog error: {e}")
        ui.notify(f"Error: {e}", type='negative')

async def do_phase2() -> None:
    append_log("DEBUG: do_phase2 called")
    if not check_sudo(): 
        append_log("DEBUG: check_sudo failed in do_phase2")
        return
    
    global btn_phase2
    
    # Set button to executing state
    if btn_phase2:
        original_text = btn_phase2.text
        btn_phase2.props('color=red disable')
        btn_phase2.style('background-color: #ff0000 !important')
        btn_phase2.classes(add='btn-executing')
        btn_phase2.text = 'Ejecutando...'
        btn_phase2.update()
    
    eggs = await backend.get_cmd_eggs()
    append_log(f"DEBUG: replica={replica_switch.value}, edit_config={edit_config_switch.value}")
    
    any_action = False
    
    if replica_switch and replica_switch.value:
        any_action = True
        # Use sudo for skel
        rc = await backend.run_stream(f"sudo {eggs} tools skel", append_log)
        if rc != 0:
            ui.notify('Error al clonar escritorio', type='negative')
            # Error state
            if btn_phase2:
                btn_phase2.props(remove='color disable')
                btn_phase2.style('background-color: #091f9e !important')
                btn_phase2.classes(remove='btn-executing btn-success')
                btn_phase2.text = original_text if 'original_text' in locals() else 'Fase 2'
                btn_phase2.update()
            return
            
    if edit_config_switch and edit_config_switch.value:
        any_action = True
        await edit_config_dialog()
    
    # Success state
    if any_action and btn_phase2:
        btn_phase2.props(remove='color disable')
        btn_phase2.classes(remove='btn-executing', add='btn-success')
        btn_phase2.text = '✓ Completado'
        btn_phase2.update()
        ui.notify('Fase 2 completada', type='positive')
    elif btn_phase2:
        # No action taken, return to normal
        btn_phase2.props(remove='color disable')
        btn_phase2.style('background-color: #091f9e !important')
        btn_phase2.classes(remove='btn-executing btn-success')
        btn_phase2.text = original_text if 'original_text' in locals() else 'Fase 2'
        btn_phase2.update()

async def do_generate_iso() -> None:
    if not check_sudo(): return
    global iso_generating, iso_elapsed, auto_elapsed, btn_phase3
    
    # Set button to executing state (red, pulsing)
    if btn_phase3:
        original_text = btn_phase3.text
        btn_phase3.props('color=red disable')
        btn_phase3.style('background-color: #ff0000 !important')
        btn_phase3.classes(add='btn-executing')
        btn_phase3.text = 'Generando...'
        btn_phase3.update()
    
    # Mark Phase 2 as complete if it's enabled but not already marked
    if fase2_btn and not fase2_btn.props.get('disable'):
        # Check if phase2 button is not already green
        if 'btn-success' not in (fase2_btn.classes or ''):
            fase2_btn.props(remove='color')
            fase2_btn.classes(remove='btn-executing', add='btn-success')
            fase2_btn.text = '✓ Completado'
            fase2_btn.update()
    
    iso_generating = True
    iso_elapsed = 0
    if phase_status:
        phase_status.text = 'Ejecutando: Fase 3 (Generar ISO)'
        phase_status.classes(add='status-executing')
        phase_status.style(f"color: {COLORS['success']}")
        phase_status.update()
    set_progress(None, spinning=True)
    
    eggs = await backend.get_cmd_eggs()
    if iso_max_compression.value:
        cmd = f"sudo {eggs} produce --pendrive -n"
    elif iso_include_data.value:
        cmd = f"sudo {eggs} produce --clone -n"
    else:
        cmd = f"sudo {eggs} produce --noicon -n"
        
    rc = await backend.run_stream(cmd, append_log)
    iso_generating = False
    set_progress(0)
    
    if rc == 0:
        update_iso_size()
        # Success state (green button)
        if btn_phase3:
            btn_phase3.props(remove='color disable')
            btn_phase3.classes(remove='btn-executing', add='btn-success')
            btn_phase3.text = '✓ ISO Generada'
            btn_phase3.update()
        if phase_status:
            phase_status.classes(remove='status-executing', add='status-success')
            phase_status.update()
        ui.notify('ISO generada', type='positive')
    else:
        # Error state - return to normal
        if btn_phase3:
            btn_phase3.props(remove='color disable')
            btn_phase3.style('background-color: #091f9e !important')
            btn_phase3.classes(remove='btn-executing btn-success')
            btn_phase3.text = original_text if 'original_text' in locals() else 'Fase 3'
            btn_phase3.update()
        if phase_status:
            phase_status.classes(remove='status-executing')
            phase_status.update()
        ui.notify('Error al generar ISO', type='negative')

async def open_dir_picker(target_input=None) -> None:
    append_log("DEBUG: open_dir_picker called")
    try:
        current_path = backend.get_home_dir()
        append_log(f"DEBUG: current_path={current_path}")
    
        with ui.dialog() as d:
            with ui.card().classes('w-[600px] h-[500px] egg-panel flex flex-col'):
                ui.label('Seleccionar directorio destino').classes('text-xl font-bold mb-2 text-white')
                path_label = ui.label(current_path).classes('mb-2 text-gray-400 text-sm')
                
                # List container
                list_container = ui.column().classes('w-full grow overflow-y-auto border border-gray-600 rounded p-2')
                
                async def load_dir(path):
                    nonlocal current_path
                    current_path = path
                    path_label.text = path
                    list_container.clear()
                    
                    items = backend.list_directories(path)
                    with list_container:
                        if not items and path != '/':
                             # Fallback if empty but not root, allow going up
                             items = [{'name': '..', 'path': os.path.dirname(path), 'type': 'dir'}]

                        for item in items:
                            # Use flat buttons for better click handling
                            icon = 'folder' if item['type'] == 'dir' else 'description'
                            btn = ui.button(item['name'], icon=icon, on_click=lambda _, p=item['path']: asyncio.create_task(load_dir(p)))
                            btn.props('flat align=left no-caps').classes('w-full text-left')

                
                await load_dir(current_path)
                
                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Cancelar', on_click=d.close).classes('mr-2 bg-red-600 hover:bg-red-700')
                    def select():
                        if target_input:
                            target_input.value = current_path
                        elif dest_dir_input:
                            dest_dir_input.value = current_path
                        d.close()
                    ui.button('Seleccionar', on_click=select).classes('egg-button')
        d.open()
    except Exception as e:
        append_log(f"DEBUG: open_dir_picker error: {e}")
        ui.notify(f"Error al abrir selector: {e}", type='negative')

async def ask_copy_options_auto() -> bool:
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    
    with ui.dialog() as d:
        # Removed 'persistent' to allow closing with ESC or clicking outside
        with ui.card().classes('w-[500px] egg-panel'):
            ui.label('Opciones de Copia').classes('text-xl font-bold mb-4 text-white')
            
            # Speed
            speed_switch = ui.switch('Copia Rápida', value=False).props('dense').classes('mb-4')
            
            # Destination
            ui.label('Directorio Destino:').classes('font-bold mb-1 text-white')
            with ui.row().classes('w-full items-center mb-6'):
                dest_input = ui.input(value=os.path.expanduser('~')).props('dense dark input-class="text-white"').classes('grow')
                ui.button(icon='folder', on_click=lambda: open_dir_picker(dest_input)).props('flat dense').classes('ml-1')

            def on_confirm():
                if copy_speed_switch:
                    copy_speed_switch.value = speed_switch.value
                if dest_dir_input:
                    dest_dir_input.value = dest_input.value
                d.close()
                future.set_result(True)
                
            def on_cancel():
                d.close()
                future.set_result(False)

            with ui.row().classes('w-full justify-end'):
                ui.button('Cancelar', on_click=on_cancel).classes('mr-2 bg-red-600 hover:bg-red-700')
                ui.button('Continuar', on_click=on_confirm).classes('egg-button')
    
    d.open()
    return await future

async def do_copy_iso() -> None:
    append_log("DEBUG: do_copy_iso called")
    global copying, copy_elapsed, copy_count, copy_state, btn_copy_iso
    
    # Set button to executing state (red, pulsing)
    if btn_copy_iso:
        original_text = btn_copy_iso.text
        btn_copy_iso.props('color=red disable')
        btn_copy_iso.style('background-color: #ff0000 !important')
        btn_copy_iso.classes(add='btn-executing')
        btn_copy_iso.text = 'Copiando...'
        btn_copy_iso.update()
    
    copying = True
    copy_elapsed = 0
    # Reset copy state
    copy_state['progress'] = 0.0
    copy_state['percent'] = 0
    if phase_status:
        phase_status.text = 'Ejecutando: Copiar ISO'
        phase_status.classes(add='status-executing')
        phase_status.style(f"color: {COLORS['success']}")
        phase_status.update()
    # Change progress bar color to intense orange for copy operation
    if progress:
        progress.props('color=deep-orange')
        progress.update()
    set_progress(0)  # Start with 0% instead of spinning
    
    # Determine destination directory
    dest_dir = dest_dir_input.value if (dest_dir_input and dest_dir_input.value) else os.path.expanduser('~')
    if not os.path.isdir(dest_dir):
        ui.notify('Directorio destino no existe', type='warning')
        append_log(f'Directorio destino no existe: {dest_dir}')
        copying = False
        set_progress(0)
        if phase_status: phase_status.text = ''; phase_status.update()
        return
        
    # Find ISO file
    src_iso_path = None
    possible_src_dirs = ["/home/eggs/", "/home/eggs/.mnt/"] # Prioritize /home/eggs/
    
    for p in possible_src_dirs:
        if os.path.exists(p):
            try:
                files = [f for f in os.listdir(p) if f.endswith('.iso')]
                if files:
                    src_iso_path = os.path.join(p, files[0])
                    break
            except PermissionError:
                continue
                
    if not src_iso_path:
        append_log('No se encontraron archivos ISO para copiar')
        append_log(f"DEBUG: Checked paths: {possible_src_dirs}")
        ui.notify('No se encontró ISO para copiar', type='warning')
        copying = False
        set_progress(0)
        if phase_status: phase_status.text = ''; phase_status.update()
        return
            
    try:
        append_log(f"DEBUG: Found ISO: {src_iso_path}")
        dst = os.path.join(dest_dir, os.path.basename(src_iso_path))
        
        # Define blocking copy function to run in thread
        def blocking_copy():
            """Blocking file copy that runs in thread pool"""
            total = os.path.getsize(src_iso_path)
            copied = 0
            chunk = 1024 * 1024  # 1MB chunks
            
            with open(src_iso_path, 'rb') as s, open(dst, 'wb') as d:
                while True:
                    data = s.read(chunk)
                    if not data:
                        break
                    d.write(data)
                    copied += len(data)
                    
                    # Update shared state
                    copy_state['progress'] = copied / total
                    copy_state['percent'] = int((copied / total) * 100)
                    
                    # Add delay for slow copy if not rapid mode
                    if not (copy_speed_switch and copy_speed_switch.value):
                        time.sleep(0.01)
            
            return total
        
        # Start progress updater - only update shared state, not UI directly
        async def update_copy_progress():
            """Update shared state for UI polling, no direct UI updates"""
            while copying:
                # Just sleep and let the timer update the UI
                # UI updates happen in update_timers() which runs in proper context
                await asyncio.sleep(0.1)
        
        # Run copy and progress updater concurrently
        progress_task = asyncio.create_task(update_copy_progress())
        
        # Try direct copy first (run in thread to not block event loop)
        try:
            total = await asyncio.to_thread(blocking_copy)
        except PermissionError:
            # Fallback to sudo copy if direct copy fails due to permissions
            if not check_sudo(): 
                copying = False
                set_progress(0)
                if phase_status: phase_status.text = ''; phase_status.update()
                return
                
            append_log('Permiso denegado. Intentando copia con sudo...')
            # Use dd with sudo for robust copying
            cmd = f"sudo dd if={shlex.quote(src_iso_path)} of={shlex.quote(dst)} bs=4M status=progress"
            # We can't easily track progress with dd in run_stream without parsing, 
            # so we'll just run it. Progress bar will remain spinning.
            rc = await backend.run_stream(cmd, append_log)
            if rc != 0:
                raise Exception("Fallo la copia con sudo")
                    
        copy_count += 1
        if copy_counter_label:
            copy_counter_label.text = f"Copias realizadas: {copy_count}"; copy_counter_label.update()
        append_log(f"ISO copiada a: {dst}")
        
        # Success state (green button)
        if btn_copy_iso:
            btn_copy_iso.props(remove='color disable')
            btn_copy_iso.classes(remove='btn-executing', add='btn-success')
            btn_copy_iso.text = '✓ Copiada'
            btn_copy_iso.update()
        
        if phase_status:
            phase_status.classes(remove='status-executing', add='status-success')
            phase_status.update()
        
        ui.notify('ISO copiada exitosamente', type='positive')
    except Exception as e:
        append_log(f"Error al copiar la ISO: {e}")
        
        # Error state - return to normal
        if btn_copy_iso:
            btn_copy_iso.props(remove='color disable')
            btn_copy_iso.style('background-color: #091f9e !important')
            btn_copy_iso.classes(remove='btn-executing btn-success')
            btn_copy_iso.text = original_text if 'original_text' in locals() else 'Copiar ISO'
            btn_copy_iso.update()
        
        if phase_status:
            phase_status.classes(remove='status-executing')
            phase_status.update()
        
        ui.notify(f'Error al copiar la ISO: {e}', type='negative')
    finally:
        copying = False
        # Cancel progress updater task if it exists
        if 'progress_task' in locals():
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass
        set_progress(0)
        # Reset progress bar color back to light-blue
        if progress:
            progress.props('color=light-blue')
            progress.update()
        if copy_percent:
            copy_percent.text = "0%"
            copy_percent.style('color: white; font-size: 18px; font-weight: bold;')
            copy_percent.classes(remove='status-executing status-success')
            copy_percent.update()
        if phase_status: 
            phase_status.text = ''
            phase_status.classes(remove='status-executing status-success')
            phase_status.update()

async def do_clean_session() -> None:
    append_log("DEBUG: do_clean_session called")
    if not check_sudo(): 
        append_log("DEBUG: check_sudo failed in do_clean_session")
        return
    target = '/home/eggs'
    
    async def _get_size() -> str:
        try:
            # Use sudo to check size as /home/eggs might be root owned
            append_log("DEBUG: Running du -sh")
            rc, out = await backend.run_capture(f"sudo du -sh {shlex.quote(target)} || true")
            append_log(f"DEBUG: du rc={rc}, out={out}")
            if out: return out.strip().split()[0]
            return 'No existe/Vacío'
        except Exception as e:
            append_log(f"DEBUG: du error: {e}")
            return 'Desconocido'

    size_text = await _get_size()
    append_log(f"DEBUG: size_text={size_text}")
    
    with ui.dialog() as dlg:
        with ui.card().classes('egg-panel'):
            ui.label('¿Eliminar la carpeta /home/eggs por completo?').classes('text-bold text-white')
            size_label = ui.label(f"Tamaño actual: {size_text}").classes('text-white')
            
            async def confirm():
                dlg.close()
                if phase_status:
                    phase_status.text = 'Ejecutando: Limpiando sesión'
                    phase_status.style(f"color: {COLORS['success']}")
                    phase_status.update()
                set_progress(None, spinning=True)
                append_log(f"Eliminando {target} ...")
                import shlex
                # Ensure sudo is used for deletion
                rc = await backend.run_stream(f"sudo rm -rf {shlex.quote(target)}", append_log)
                set_progress(0)
                if phase_status:
                    phase_status.text = ''
                    phase_status.update()
                if rc == 0:
                    ui.notify('Sesión limpiada', type='positive')
                    if console: console.clear()
                    
                    # Reset timers
                    global copy_elapsed, iso_elapsed, auto_elapsed, copy_count
                    copy_elapsed = 0
                    iso_elapsed = 0
                    auto_elapsed = 0
                    copy_count = 0
                    
                    if copy_time_label: copy_time_label.text = "Copia: 00:00:00"; copy_time_label.update()
                    if iso_time_label: iso_time_label.text = "Generación: 00:00:00"; iso_time_label.update()
                    if Total_time_label: Total_time_label.text = "Total: 00:00:00"; Total_time_label.update()
                    
                    # Reset progress bar
                    if progress:
                        progress.value = 0
                        progress.props(remove='indeterminate')
                        progress.props('color=light-blue')
                        progress.update()
                    
                    if copy_percent:
                        copy_percent.text = "0%"
                        copy_percent.style('color: white; font-size: 18px; font-weight: bold;')
                        copy_percent.update()
                    
                    if copy_counter_label:
                        copy_counter_label.text = "Copias realizadas: 0"
                        copy_counter_label.update()

                    # Reset switches
                    if prep_manual: prep_manual.value = True; prep_manual.update()
                    if calamares_update: calamares_update.value = False; calamares_update.update()
                    if replica_switch: replica_switch.value = False; replica_switch.update()
                    if edit_config_switch: edit_config_switch.value = False; edit_config_switch.update()
                    if iso_include_data: iso_include_data.value = False; iso_include_data.update()
                    if iso_max_compression: iso_max_compression.value = False; iso_max_compression.update()
                    if copy_speed_switch: copy_speed_switch.value = False; copy_speed_switch.update()
                    
                    # Reset all buttons to original state
                    if btn_phase1:
                        btn_phase1.props(remove='color disable')
                        btn_phase1.style('background-color: #091f9e !important')
                        btn_phase1.classes(remove='btn-executing btn-success')
                        btn_phase1.text = 'Fase 1'
                        btn_phase1.update()
                    
                    if btn_phase2:
                        btn_phase2.props(remove='color disable')
                        btn_phase2.style('background-color: #091f9e !important')
                        btn_phase2.classes(remove='btn-executing btn-success')
                        btn_phase2.text = 'Fase 2'
                        btn_phase2.update()
                    
                    # Also reset fase2_btn (the actual Fase 2 button variable)
                    if fase2_btn:
                        fase2_btn.props(remove='color disable')
                        fase2_btn.style('background-color: #091f9e !important')
                        fase2_btn.classes(remove='btn-executing btn-success')
                        fase2_btn.text = 'Fase 2'
                        fase2_btn.update()
                    
                    if btn_phase3:
                        btn_phase3.props(remove='color disable')
                        btn_phase3.style('background-color: #091f9e !important')
                        btn_phase3.classes(remove='btn-executing btn-success')
                        btn_phase3.text = 'Fase 3'
                        btn_phase3.update()
                    
                    if btn_copy_iso:
                        btn_copy_iso.props(remove='color disable')
                        btn_copy_iso.style('background-color: #091f9e !important')
                        btn_copy_iso.classes(remove='btn-executing btn-success')
                        btn_copy_iso.text = 'Copiar ISO'
                        btn_copy_iso.update()
                    
                    if btn_auto:
                        btn_auto.props(remove='color disable')
                        btn_auto.style('background-color: #091f9e !important')
                        btn_auto.classes(remove='btn-executing btn-success')
                        btn_auto.text = 'AUTO'
                        btn_auto.update()
                    
                    # Reset ISO size label
                    if iso_size_label:
                        iso_size_label.text = 'Tamaño ISO: N/A'
                        iso_size_label.update()
                else:
                    ui.notify('Error al limpiar sesión', type='negative')
                    
            with ui.row():
                ui.button('Confirmar', on_click=confirm).classes('egg-button')
                ui.button('Cancelar', on_click=dlg.close)
    dlg.open()

async def do_auto() -> None:
    global auto_running, auto_elapsed, btn_auto
    
    # Set button to executing state (red, pulsing)
    if btn_auto:
        btn_auto.props('color=red disable')
        btn_auto.style('background-color: #ff0000 !important')
        btn_auto.classes(add='btn-executing')
        btn_auto.text = 'Ejecutando AUTO...'
        btn_auto.update()

    auto_running = True
    auto_elapsed = 0
    
    try:
        await do_preparation()
        await do_generate_iso()
        
        # Ask for copy options
        if not await ask_copy_options_auto():
            ui.notify('Proceso Auto cancelado por el usuario', type='warning')
            auto_running = False
            # Reset button if cancelled
            if btn_auto:
                btn_auto.props(remove='color disable')
                btn_auto.style('background-color: #091f9e !important')
                btn_auto.classes(remove='btn-executing btn-success')
                btn_auto.text = 'AUTO'
                btn_auto.update()
            return

        await do_copy_iso()
        
        # Success state (green button)
        if btn_auto:
            btn_auto.props(remove='color disable')
            btn_auto.classes(remove='btn-executing', add='btn-success')
            btn_auto.text = '✓ AUTO Completado'
            btn_auto.update()
            
    except Exception as e:
        ui.notify(f'Error en proceso AUTO: {e}', type='negative')
        # Error state - return to normal
        if btn_auto:
            btn_auto.props(remove='color disable')
            btn_auto.style('background-color: #091f9e !important')
            btn_auto.classes(remove='btn-executing btn-success')
            btn_auto.text = 'AUTO'
            btn_auto.update()
    finally:
        auto_running = False

async def update_timers() -> None:
    global copy_elapsed, iso_elapsed, auto_elapsed
    if copying:
        copy_elapsed += 1
        if copy_time_label:
            copy_time_label.text = f"Copia: {time.strftime('%H:%M:%S', time.gmtime(copy_elapsed))}"
            copy_time_label.update()
        # Update copy progress if in copy mode
        if copy_state and copy_percent:
            pct = copy_state.get('percent', 0)
            p = copy_state.get('progress', 0.0)
            set_progress(p)
            copy_percent.text = f"{pct}%"
            copy_percent.style('color: red; font-size: 18px; font-weight: bold;')
            copy_percent.update()
    if iso_generating:
        iso_elapsed += 1
        if iso_time_label:
            iso_time_label.text = f"Generación: {time.strftime('%H:%M:%S', time.gmtime(iso_elapsed))}"
            iso_time_label.update()
    if auto_running:
        auto_elapsed += 1
    # Always update total timer as sum of all elapsed times
    total = copy_elapsed + iso_elapsed + auto_elapsed
    if Total_time_label:
        Total_time_label.text = f"Total: {time.strftime('%H:%M:%S', time.gmtime(total))}"
        Total_time_label.update()

@ui.page('/')
def main_page():
    global versions_eggs, versions_calamares
    global phase_status, copy_percent, copy_counter_label, copy_time_label, iso_time_label, Total_time_label
    global progress, console
    global prep_manual, calamares_update, replica_switch, edit_config_switch, iso_include_data, iso_max_compression, copy_speed_switch
    global iso_size_label, dest_dir_input, fase2_btn
    global btn_phase1, btn_phase2, btn_phase3, btn_copy_iso, btn_auto, btn_clean

    ui.add_head_html("<style>{}</style>".format(THEME_CSS))

    with ui.header().classes('items-center justify-between egg-panel relative'):
        with ui.row().classes('items-center'):
            logo_path = os.path.join(backend.base_path, 'assets', 'eggsmaker.png')
            if not os.path.exists(logo_path):
                 logo_path = os.path.join(backend.base_path, 'eggsmaker.png')
            
            if os.path.exists(logo_path):
                ui.image(logo_path).props('fit=contain').style('width:32px;height:32px;border-radius:6px;')
            ui.label(f"{__app__} - Versión {__version__}").classes('text-bold')
            
        with ui.row().classes('items-center absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2'):
             ui.label('Eggsmaker - Web').classes('egg-header-title ml-2').style('font-weight: bold !important; color: #FF5722 !important')
             
        with ui.column().classes('items-end'):
            versions_eggs = ui.label("Penguins' Eggs: N/A")
            versions_calamares = ui.label("Calamares: N/A")

    # Terminal area
    with ui.row().classes('w-full q-pa-none q-ma-none q-mt-none main-top-row'):
        console = ui.log().classes('w-full h-[300px] egg-terminal p-2 overflow-y-auto')

    # Main controls
    with ui.row().classes('w-full items-stretch q-gutter-sm q-pa-none q-ma-none q-mt-none'):
        # Fase 1
        with ui.card().classes('min-w-[240px] egg-panel flex flex-col q-pa-xs'):
            ui.label('Fase 1').classes('egg-title')
            prep_manual = ui.switch('Inicio (Manual)', value=True).props('dense')
            calamares_update = ui.switch('Actualizar Eggs y Calamares', value=False).props('dense')
            btn_phase1 = ui.button('Fase 1', on_click=do_preparation).style('background-color: #091f9e !important; font-weight: bold !important').classes('mt-auto w-full')
            
        # Fase 2
        with ui.card().classes('min-w-[240px] egg-panel flex flex-col q-pa-xs'):
            ui.label('Fase 2').classes('egg-title')
            replica_switch = ui.switch('Clonar Escritorio', value=False).props('dense')
            edit_config_switch = ui.switch('Personalizar ISO', value=False).props('dense')
            fase2_btn = ui.button('Fase 2', on_click=do_phase2).style('background-color: #091f9e !important; font-weight: bold !important').classes('mt-auto w-full')
            replica_switch.disable(); edit_config_switch.disable(); fase2_btn.disable()
                    # Fase 3
        with ui.card().classes('min-w-[240px] egg-panel flex flex-col q-pa-xs'):
            ui.label('Fase 3').classes('egg-title')
            iso_include_data = ui.switch('Incluir datos', value=False).props('dense')
            iso_max_compression = ui.switch('Máxima compresión', value=False).props('dense')
            btn_phase3 = ui.button('Fase 3', on_click=do_generate_iso).style('background-color: #091f9e !important; font-weight: bold !important').classes('mt-auto w-full')
            
        # Copiar ISO
        with ui.card().classes('min-w-[240px] egg-panel flex flex-col q-pa-xs'):
            ui.label('Copiar ISO').classes('egg-title')
            copy_speed_switch = ui.switch('Rápida', value=False).props('dense')
            with ui.row().classes('w-full items-center'):
                dest_dir_input = ui.input('', value=os.path.expanduser('~'), placeholder='Destino').props('dense').classes('flex-grow')
                ui.button(icon='folder', on_click=lambda: open_dir_picker(dest_dir_input)).props('flat dense').classes('ml-1')
            btn_copy_iso = ui.button('Copiar ISO', on_click=lambda: asyncio.create_task(do_copy_iso())).style('background-color: #091f9e !important; font-weight: bold !important').classes('mt-auto w-full')
            
        # AUTO
        with ui.card().classes('min-w-[240px] egg-panel flex flex-col q-pa-xs'):
            ui.label('AUTO').classes('egg-title')
            btn_auto = ui.button('AUTO', on_click=do_auto).style('background-color: #091f9e !important; font-weight: bold !important').classes('mt-auto w-full')
            
        # Sesión
        with ui.card().classes('min-w-[240px] egg-panel flex flex-col q-pa-xs'):
            ui.label('Sesión').classes('egg-title')
            btn_clean = ui.button('Limpiar sesión', on_click=do_clean_session).style('background-color: #091f9e !important; font-weight: bold !important').classes('mt-auto w-full')

        # Logic for switches
        def toggle_prep():
            if prep_manual.value:
                prep_manual.text = 'Inicio (Manual)'
                btn_auto.disable()
                btn_phase1.enable()
                btn_phase1.text = 'Fase 1'
            else:
                prep_manual.text = 'Inicio (AUTO)'
                btn_auto.enable()
                btn_phase1.disable()
                
        def toggle_calamares():
            if calamares_update.value:
                prep_manual.value = False
                btn_phase1.text = 'fresh-eggs/calamares'
                btn_phase1.enable()
            else:
                toggle_prep()

        prep_manual.on_value_change(toggle_prep)
        calamares_update.on_value_change(toggle_calamares)
        
        # Initial state
        toggle_prep()

    # Status Bar - Simplified for visibility
    with ui.row().classes('w-full'):
        with ui.card().classes('w-full').style('background-color: #000000; padding: 16px; border: 2px solid #444C5E;'):
            phase_status = ui.label("Estado: Esperando").style('color: white; font-size: 18px; font-weight: bold; margin-bottom: 8px;')
            
            # Progress bar with explicit styling
            progress = ui.linear_progress(value=0, show_value=False).style('height: 24px; background-color: #444C5E; margin-bottom: 16px;')
            progress.props('color=light-blue')
            
            # Single info row below progress bar: left, center, right
            with ui.row().classes('w-full justify-between items-center'):
                # Left: Percentage and Copies
                with ui.row().classes('items-center').style('gap: 16px;'):
                    copy_percent = ui.label("0%").style('color: white; font-size: 18px; font-weight: bold;')
                    copy_counter_label = ui.label("Copias realizadas: 0").style('color: white; font-size: 14px; font-weight: bold;')
                
                # Center: ISO Size
                iso_size_label = ui.label('Tamaño ISO: N/A').style('color: #39ee39; font-size: 16px; font-weight: bold;')
                
                # Right: Timers
                with ui.row().classes('items-center').style('gap: 16px;'):
                    copy_time_label = ui.label("Copia: 00:00:00").style('color: cyan; font-size: 14px; font-weight: bold;')
                    iso_time_label = ui.label("Generación: 00:00:00").style('color: red; font-size: 14px; font-weight: bold;')
                    Total_time_label = ui.label("Total: 00:00:00").style('color: lime; font-size: 14px; font-weight: bold;')
                
    # Network info footer
    def show_about_dialog():
        with ui.dialog() as d, ui.card().classes('egg-panel w-[600px]'):
            ui.label('Acerca de Eggsmaker').classes('text-xl font-bold mb-4 text-white')
            
            ui.label('Eggsmaker creado por Jorge Luis Endres (c) 2025 Argentina').classes('text-white font-bold')
            with ui.row().classes('items-center'):
                 ui.label('Drive:').classes('text-gray-400 mr-2')
                 ui.link('https://drive.google.com/drive/folders/1rJfY1JaCKxaJD8XeFhYhyXROKZmaMe3B?usp=sharing', 'https://drive.google.com/drive/folders/1rJfY1JaCKxaJD8XeFhYhyXROKZmaMe3B?usp=sharing').classes('text-blue-400')
            ui.label('Feedback: jorge.eggsmaker@gmail.com').classes('text-gray-400 mb-4')
            
            ui.separator().classes('bg-gray-600 mb-4')
            
            ui.label('Penguins Eggs creado por Piero Proietti Italia').classes('text-white font-bold')
            with ui.row().classes('items-center'):
                 ui.label('Web:').classes('text-gray-400 mr-2')
                 ui.link('https://penguins-eggs.net', 'https://penguins-eggs.net').classes('text-blue-400')
            
            with ui.row().classes('w-full justify-end mt-6'):
                ui.button('Cerrar', on_click=d.close).classes('egg-button')
        d.open()

    with ui.footer().classes('egg-panel q-py-sm'):
        with ui.row().classes('w-full items-center relative-position'):
            # Left: Info button
            ui.button(icon='info', on_click=show_about_dialog).props('flat round dense color=white').tooltip('Acerca de')
            
            # Center: Network info
            local_ip = backend.get_local_ip()
            ui.label(f"Acceso en red: http://{local_ip}:{port}").classes('absolute-center').style('color: #33b5e5 !important; font-weight: bold;')

    # Sudo Dialog (Created upfront)
    sudo_dialog = ui.dialog()
    with sudo_dialog, ui.card().classes('egg-panel'):
        ui.label('Autenticación requerida (sudo)').classes('text-white font-bold')
        pwd = ui.input('Contraseña de sudo', password=True, password_toggle_button=True).props('dark input-class="text-white"')
        with ui.row():
            ui.button('Aceptar', on_click=lambda: (setattr(backend, 'sudo_password', pwd.value), sudo_dialog.close())).classes('egg-button')
            ui.button('Cancelar', on_click=sudo_dialog.close).classes('bg-red-600 hover:bg-red-700')

    ui.timer(1.0, update_timers)
    ui.timer(0.2, lambda: asyncio.create_task(update_versions()), once=True)
    ui.timer(0.05, sudo_dialog.open, once=True)

def main():
    """Entry point for the application"""
    global port
    port = int(os.getenv('PORT', '8080'))
    ui.run(title=f"{__app__}", port=port, host='0.0.0.0', reload=False)

if __name__ == "__main__":
    main()

import asyncio
import os
import shlex
import socket
import sys
import gettext
import locale
from typing import Tuple

# Import version info
try:
    from version import __version__, __app__
except ImportError:
    __version__ = "0.0.0"
    __app__ = "Eggsmaker"

class EggsmakerBackend:
    def __init__(self):
        self.sudo_password: str | None = None
        self.base_path = self.get_base_path()
        self._setup_i18n()

    def get_base_path(self) -> str:
        """Obtiene la ruta base de la aplicación, funciona tanto en desarrollo como compilado"""
        try:
            # Si estamos en un entorno de PyInstaller
            if getattr(sys, 'frozen', False):
                if hasattr(sys, '_MEIPASS'):
                    meipass = sys._MEIPASS
                    # Verificar rutas comunes en _MEIPASS
                    if os.path.exists(os.path.join(meipass, 'assets', 'eggsmaker.png')):
                        return meipass
                    if os.path.exists(os.path.join(meipass, 'eggsmaker.png')):
                        return meipass
            
            # Lista de posibles ubicaciones
            possible_paths = [
                os.path.dirname(os.path.abspath(__file__)),
                os.getcwd(),
                "/usr/share/eggsmaker",
                "/usr/local/share/eggsmaker",
            ]

            for path in possible_paths:
                if os.path.exists(os.path.join(path, "assets", "eggsmaker.png")):
                    return path
                if os.path.exists(os.path.join(path, "eggsmaker.png")):
                    return path
            
            return os.path.dirname(os.path.abspath(__file__))
        except Exception:
            return os.path.dirname(os.path.abspath(__file__))

    def _setup_i18n(self):
        # Placeholder for future i18n implementation
        pass

    def tr(self, text: str) -> str:
        """Translate text (placeholder)"""
        return text

    def get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
            s.close()
        except Exception:
            IP = '127.0.0.1'
        return IP

    async def run_stream(self, cmd: str, log_callback) -> int:
        wrapped = cmd
        if self.sudo_password:
            cmd_no_sudo = cmd.lstrip()
            if cmd_no_sudo.startswith('sudo '):
                cmd_no_sudo = cmd_no_sudo[len('sudo '):]
            safe_path = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            # Sanitize environment variables to prevent AppImage interference
            env_vars = "LD_PRELOAD= LD_LIBRARY_PATH= APPIMAGE= APPDIR= PYTHONPATH="
            wrapped = (
                f"printf '%s\\n' {shlex.quote(self.sudo_password)} | "
                f"sudo -SE env {env_vars} PATH={safe_path} bash -lc {shlex.quote(cmd_no_sudo)}"
            )
        
        if log_callback:
            log_callback(f"$ {wrapped}")
            
        process = await asyncio.create_subprocess_shell(
            wrapped,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            executable="/bin/bash",
        )
        
        # Read stdout line by line
        if process.stdout:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                try:
                    decoded_line = line.decode(errors='ignore').rstrip()
                except:
                    decoded_line = line.decode('utf-8', errors='ignore').rstrip()
                
                if log_callback:
                    log_callback(decoded_line)
                
                # Yield control to allow UI updates
                await asyncio.sleep(0)
                    
        rc = await process.wait()
        return rc

    async def run_capture(self, cmd: str) -> Tuple[int, str]:
        wrapped = cmd
        if self.sudo_password:
            cmd_no_sudo = cmd.lstrip()
            if cmd_no_sudo.startswith('sudo '):
                cmd_no_sudo = cmd_no_sudo[len('sudo '):]
            safe_path = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            # Sanitize environment variables to prevent AppImage interference
            env_vars = "LD_PRELOAD= LD_LIBRARY_PATH= APPIMAGE= APPDIR= PYTHONPATH="
            wrapped = (
                f"printf '%s\\n' {shlex.quote(self.sudo_password)} | "
                f"sudo -SE env {env_vars} PATH={safe_path} bash -lc {shlex.quote(cmd_no_sudo)}"
            )
        try:
            process = await asyncio.create_subprocess_shell(
                wrapped,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                executable="/bin/bash",
            )
            stdout, stderr = await process.communicate()
            
            try:
                out_str = stdout.decode(errors='ignore')
            except:
                out_str = stdout.decode('utf-8', errors='ignore')
            
            # print(f"DEBUG: run_capture cmd={cmd} rc={process.returncode}") 
            return process.returncode, out_str
        except Exception as e:
            print(f"DEBUG: run_capture exception: {e}")
            return -1, str(e)

    async def get_cmd_eggs(self) -> str:
        try:
            # Try to find eggs in path first without sudo
            process = await asyncio.create_subprocess_exec(
                'which', 'eggs',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                return stdout.decode().strip()
            return 'eggs'
        except Exception:
            return 'eggs'

    def format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        if size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def get_home_dir(self) -> str:
        return os.path.expanduser('~')

    def list_directories(self, path: str) -> list[dict]:
        try:
            items = []
            # Ensure path exists and is a directory
            if not os.path.isdir(path):
                return []
                
            # List directory content
            with os.scandir(path) as it:
                for entry in it:
                    if entry.is_dir() and not entry.name.startswith('.'):
                        items.append({
                            'name': entry.name,
                            'path': entry.path,
                            'type': 'dir'
                        })
            
            # Sort by name
            items.sort(key=lambda x: x['name'].lower())
            
            # Add parent directory if not root
            if path != '/':
                parent = os.path.dirname(path)
                items.insert(0, {
                    'name': '..',
                    'path': parent,
                    'type': 'dir'
                })
                
            return items
        except Exception:
            return []

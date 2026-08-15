"""Assisted Windows installer for PrestaShop Local MCP.

This script creates a local virtual environment in a user-selected folder,
installs the package there, and starts the secure setup wizard from that
environment.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


PACKAGE_URL = "https://github.com/golfo161/prestashop-local-mcp/archive/refs/heads/main.zip"


def _default_install_dir() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "prestashop-local-mcp"
    return Path.home() / "prestashop-local-mcp"


def _prompt_path(default: Path) -> Path:
    print("Carpeta de instalacion del MCP")
    print(f"Pulsa Enter para usar: {default}")
    value = input("Ruta de instalacion: ").strip().strip('"')
    return Path(value).expanduser() if value else default


def _run(command: list[str], cwd: Path | None = None) -> None:
    print("")
    print("+ " + " ".join(f'"{part}"' if " " in part else part for part in command))
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=True)


def _venv_python(install_dir: Path) -> Path:
    if os.name == "nt":
        return install_dir / "venv" / "Scripts" / "python.exe"
    return install_dir / "venv" / "bin" / "python"


def _batch_quote(path: Path) -> str:
    return str(path).replace("%", "%%")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content.replace("\n", "\r\n"), encoding="utf-8")


def _write_helper_files(install_dir: Path, python_exe: Path, package_url: str) -> None:
    package_dir = install_dir / "venv" / "Lib" / "site-packages" / "prestashop_mcp"
    env_file = Path(os.getenv("APPDATA", str(Path.home()))) / "prestashop-local-mcp" / ".env"

    readme = f"""PrestaShop Local MCP - instalacion local
================================================

Esta carpeta contiene una instalacion local y aislada del MCP.

Carpeta de instalacion:
{install_dir}

Python usado por el MCP:
{python_exe}

Fichero seguro de credenciales:
{env_file}

Codigo Python instalado por pip:
{package_dir}

Ficheros principales del MCP:
{package_dir / "prestashop_client.py"}
{package_dir / "prestashop_mcp_server.py"}

Archivos utiles de esta carpeta:

- start-mcp.bat
  Arranca el servidor MCP manualmente para hacer pruebas.

- setup-mcp.bat
  Vuelve a abrir el asistente de configuracion segura.

- update-mcp.bat
  Actualiza el MCP desde GitHub y despues abre el asistente.

- uninstall-mcp.bat
  Elimina esta instalacion local. Tambien pregunta si quieres borrar el fichero de credenciales.

Notas de seguridad:

- La API key no se guarda en Codex ni Claude Desktop.
- La API key se guarda en el fichero seguro de credenciales indicado arriba.
- Si borras esta carpeta, no borras automaticamente la API key.
- Si cambias herramientas o actualizas el MCP, reinicia ChatGPT Desktop/Codex o Claude Desktop.
"""

    start_bat = f"""@echo off
setlocal
set "PYTHON={_batch_quote(python_exe)}"
if not exist "%PYTHON%" (
  echo No se encuentra Python del MCP:
  echo %PYTHON%
  pause
  exit /b 1
)
"%PYTHON%" -m prestashop_mcp.cli --log-level DEBUG
pause
"""

    setup_bat = f"""@echo off
setlocal
set "PYTHON={_batch_quote(python_exe)}"
if not exist "%PYTHON%" (
  echo No se encuentra Python del MCP:
  echo %PYTHON%
  pause
  exit /b 1
)
"%PYTHON%" -m prestashop_mcp.cli setup
pause
"""

    update_bat = f"""@echo off
setlocal
set "PYTHON={_batch_quote(python_exe)}"
if not exist "%PYTHON%" (
  echo No se encuentra Python del MCP:
  echo %PYTHON%
  pause
  exit /b 1
)
"%PYTHON%" -m pip install --upgrade pip
"%PYTHON%" -m pip install --upgrade --force-reinstall --no-cache-dir "{package_url}"
"%PYTHON%" -m prestashop_mcp.cli setup
pause
"""

    uninstall_bat = f"""@echo off
setlocal
set "INSTALL_DIR={_batch_quote(install_dir)}"
set "ENV_FILE={_batch_quote(env_file)}"
echo Se eliminara esta instalacion local:
echo %INSTALL_DIR%
choice /M "Continuar"
if errorlevel 2 exit /b 0
echo.
choice /M "Borrar tambien el fichero local de credenciales"
if errorlevel 2 goto remove_app
if exist "%ENV_FILE%" del /F /Q "%ENV_FILE%"
:remove_app
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 1; Remove-Item -LiteralPath '%INSTALL_DIR%' -Recurse -Force"
"""

    _write_text(install_dir / "README-INSTALACION.txt", readme)
    _write_text(install_dir / "start-mcp.bat", start_bat)
    _write_text(install_dir / "setup-mcp.bat", setup_bat)
    _write_text(install_dir / "update-mcp.bat", update_bat)
    _write_text(install_dir / "uninstall-mcp.bat", uninstall_bat)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install PrestaShop Local MCP on Windows.")
    parser.add_argument("--install-dir", type=Path, help="Folder where the local virtual environment will be created.")
    parser.add_argument("--package-url", default=PACKAGE_URL, help="Package ZIP or Git URL to install.")
    parser.add_argument("--skip-setup", action="store_true", help="Install only; do not launch the setup wizard.")
    args = parser.parse_args()

    print("PrestaShop Local MCP - instalador asistido")
    print("Las credenciales se guardaran despues en el perfil del usuario, no en esta carpeta.")
    print("")

    install_dir = args.install_dir.expanduser() if args.install_dir else _prompt_path(_default_install_dir())
    install_dir = install_dir.resolve()
    install_dir.mkdir(parents=True, exist_ok=True)

    python_exe = _venv_python(install_dir)
    if not python_exe.exists():
        _run([sys.executable, "-m", "venv", str(install_dir / "venv")])
    else:
        print(f"Entorno virtual existente: {python_exe}")

    _run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])
    _run([
        str(python_exe),
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--force-reinstall",
        "--no-cache-dir",
        args.package_url,
    ])
    _write_helper_files(install_dir, python_exe, args.package_url)

    print("")
    print(f"MCP instalado en: {install_dir}")
    print(f"Python del MCP: {python_exe}")
    print(f"Archivos de ayuda creados en: {install_dir}")

    if not args.skip_setup:
        print("")
        print("Ahora se abrira el asistente de configuracion segura.")
        _run([str(python_exe), "-m", "prestashop_mcp.cli", "setup"])

    print("")
    print("Instalacion finalizada.")
    print("Reinicia ChatGPT Desktop/Codex o Claude Desktop si has conectado algun cliente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

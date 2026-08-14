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
    _run([str(python_exe), "-m", "pip", "install", "--upgrade", args.package_url])

    print("")
    print(f"MCP instalado en: {install_dir}")
    print(f"Python del MCP: {python_exe}")

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

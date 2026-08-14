"""Tests for the Windows assisted installer helpers."""

import importlib.util
from pathlib import Path


def _load_installer_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "install_windows.py"
    spec = importlib.util.spec_from_file_location("install_windows", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_write_helper_files_creates_user_facing_launchers(tmp_path, monkeypatch):
    installer = _load_installer_module()
    install_dir = tmp_path / "Prestashop MCP"
    install_dir.mkdir()
    python_exe = install_dir / "venv" / "Scripts" / "python.exe"
    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData" / "Roaming"))

    installer._write_helper_files(install_dir, python_exe, "https://example.com/package.zip")

    assert (install_dir / "README-INSTALACION.txt").exists()
    assert (install_dir / "start-mcp.bat").exists()
    assert (install_dir / "setup-mcp.bat").exists()
    assert (install_dir / "update-mcp.bat").exists()
    assert (install_dir / "uninstall-mcp.bat").exists()

    readme = (install_dir / "README-INSTALACION.txt").read_text(encoding="utf-8")
    assert "prestashop_client.py" in readme
    assert "prestashop_mcp_server.py" in readme
    assert "prestashop-local-mcp" in readme
    assert ".env" in readme

    start_bat = (install_dir / "start-mcp.bat").read_text(encoding="utf-8")
    assert "-m prestashop_mcp.cli --log-level DEBUG" in start_bat

    update_bat = (install_dir / "update-mcp.bat").read_text(encoding="utf-8")
    assert "https://example.com/package.zip" in update_bat

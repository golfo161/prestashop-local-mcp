"""Tests for the assisted CLI setup."""

from click.testing import CliRunner

from prestashop_mcp.cli import main


def test_show_config_path_uses_user_config_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))

    result = CliRunner().invoke(main, ["show-config-path"])

    assert result.exit_code == 0
    assert "prestashop-local-mcp" in result.output
    assert ".env" in result.output


def test_print_codex_config_contains_server_block(tmp_path):
    config_file = tmp_path / ".env"

    result = CliRunner().invoke(main, ["print-codex-config", "--config-file", str(config_file)])

    assert result.exit_code == 0
    assert "[mcp_servers.prestashop]" in result.output
    assert "prestashop_mcp.prestashop_mcp_server" in result.output
    assert "default_tools_approval_mode = 'writes'" in result.output


def test_print_claude_config_contains_mcp_server(tmp_path):
    config_file = tmp_path / ".env"

    result = CliRunner().invoke(main, ["print-claude-config", "--config-file", str(config_file)])

    assert result.exit_code == 0
    assert '"mcpServers"' in result.output
    assert '"prestashop"' in result.output
    assert "prestashop_mcp.prestashop_mcp_server" in result.output


def test_install_codex_writes_config_block(tmp_path):
    config_file = tmp_path / "prestashop" / ".env"
    codex_config = tmp_path / ".codex" / "config.toml"

    result = CliRunner().invoke(
        main,
        [
            "install-codex",
            "--config-file", str(config_file),
            "--codex-config", str(codex_config),
        ],
    )

    assert result.exit_code == 0
    content = codex_config.read_text(encoding="utf-8")
    assert "[mcp_servers.prestashop]" in content
    assert f"cwd = '{config_file.parent}'" in content


def test_install_claude_merges_mcp_server(tmp_path):
    config_file = tmp_path / "prestashop" / ".env"
    claude_config = tmp_path / "Claude" / "claude_desktop_config.json"
    claude_config.parent.mkdir(parents=True)
    claude_config.write_text('{"mcpServers":{"other":{"command":"other"}}}', encoding="utf-8")

    result = CliRunner().invoke(
        main,
        [
            "install-claude",
            "--config-file", str(config_file),
            "--claude-config", str(claude_config),
        ],
    )

    assert result.exit_code == 0
    content = claude_config.read_text(encoding="utf-8")
    assert '"other"' in content
    assert '"prestashop"' in content
    assert "prestashop_mcp.prestashop_mcp_server" in content


def test_init_writes_config_without_echoing_secret(tmp_path):
    config_file = tmp_path / ".env"
    runner = CliRunner()

    result = runner.invoke(
        main,
        ["init", "--config-file", str(config_file), "--skip-test"],
        input="https://shop.example.com\nsecret-api-key-123\nINFO\n",
    )

    assert result.exit_code == 0
    assert config_file.exists()
    assert "PRESTASHOP_SHOP_URL=https://shop.example.com" in config_file.read_text(encoding="utf-8")
    assert "PRESTASHOP_API_KEY=secret-api-key-123" in config_file.read_text(encoding="utf-8")
    assert "secret-api-key-123" not in result.output


def test_setup_can_write_env_and_codex_config_without_echoing_secret(tmp_path, monkeypatch):
    config_file = tmp_path / "prestashop" / ".env"
    codex_config = tmp_path / ".codex" / "config.toml"
    monkeypatch.setattr("prestashop_mcp.cli._codex_config_path", lambda: codex_config)

    result = CliRunner().invoke(
        main,
        [
            "setup",
            "--config-file", str(config_file),
            "--skip-test",
            "--with-codex",
            "--without-claude",
        ],
        input="https://shop.example.com\nsecret-api-key-123\nINFO\n",
    )

    assert result.exit_code == 0
    assert config_file.exists()
    assert codex_config.exists()
    assert "PRESTASHOP_API_KEY=secret-api-key-123" in config_file.read_text(encoding="utf-8")
    assert "secret-api-key-123" not in result.output

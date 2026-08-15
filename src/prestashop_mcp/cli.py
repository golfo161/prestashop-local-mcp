"""Command line interface for PrestaShop MCP Server."""

import asyncio
import json
import logging
import os
import re
import stat
import sys
from pathlib import Path
from typing import Optional

import click

from .config import Config, get_user_env_path
from .prestashop_client import PrestaShopClient
from .prestashop_mcp_server import main as server_main


def setup_logging(level: str):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )


def _mask_secret(value: str) -> str:
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def _write_env_file(
    path: Path,
    shop_url: str,
    api_key: str,
    log_level: str,
    force: bool,
    tax_rules_group_id: str = "1",
) -> None:
    if path.exists() and not force:
        raise click.ClickException(
            f"Config file already exists: {path}. Use --force to overwrite it."
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        f"PRESTASHOP_SHOP_URL={shop_url.rstrip('/')}\n"
        f"PRESTASHOP_API_KEY={api_key}\n"
        f"PRESTASHOP_TAX_RULES_GROUP_ID={tax_rules_group_id}\n"
        f"LOG_LEVEL={log_level}\n"
    )
    path.write_text(content, encoding="utf-8")

    if os.name != "nt":
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def _existing_config_action(path: Path, force: bool) -> str:
    """Return how setup should handle an existing config file."""
    if force or not path.exists():
        return "overwrite"

    click.echo(f"Config file already exists: {path}")
    return click.prompt(
        "Choose what to do",
        type=click.Choice(["overwrite", "omit", "cancel"], case_sensitive=False),
        default="omit",
        show_choices=True,
    ).lower()


def _read_env_file_config(path: Path) -> Config:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip().lstrip("\ufeff")] = value.strip()

    config = Config(
        shop_url=values.get("PRESTASHOP_SHOP_URL", ""),
        api_key=values.get("PRESTASHOP_API_KEY", ""),
        log_level=values.get("LOG_LEVEL", "INFO"),
        tax_rules_group_id=values.get("PRESTASHOP_TAX_RULES_GROUP_ID", "1"),
    )
    config.validate_config()
    return config


async def _test_connection(config: Config) -> dict:
    async with PrestaShopClient(config) as client:
        return await client.get_configurations()


def _python_command() -> str:
    return str(Path(sys.executable))


def _config_cwd(config_file: Path) -> str:
    return str(config_file.parent)


def _codex_config_path() -> Path:
    return Path.home() / ".codex" / "config.toml"


def _claude_config_path() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / "Claude" / "claude_desktop_config.json"
    return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"


def _codex_config_block(config_file: Path) -> str:
    return "\n".join([
        "[mcp_servers.prestashop]",
        f"command = '{_python_command()}'",
        "args = ['-m', 'prestashop_mcp.prestashop_mcp_server']",
        f"cwd = '{_config_cwd(config_file)}'",
        "startup_timeout_sec = 30",
        "tool_timeout_sec = 120",
        "default_tools_approval_mode = 'writes'",
        "",
    ])


def _claude_config_payload(config_file: Path) -> dict:
    return {
        "command": _python_command(),
        "args": ["-m", "prestashop_mcp.prestashop_mcp_server"],
        "cwd": _config_cwd(config_file),
    }


def _backup_file(path: Path) -> Optional[Path]:
    if not path.exists():
        return None
    backup = path.with_suffix(path.suffix + ".bak-prestashop-local-mcp")
    backup.write_bytes(path.read_bytes())
    return backup


def _install_codex_config(config_file: Path, codex_config: Path) -> Optional[Path]:
    codex_config.parent.mkdir(parents=True, exist_ok=True)
    backup = _backup_file(codex_config)
    content = codex_config.read_text(encoding="utf-8") if codex_config.exists() else ""
    block = _codex_config_block(config_file)
    pattern = r"(?ms)^\[mcp_servers\.prestashop\]\r?\n.*?(?=^\[|\Z)"

    if re.search(pattern, content):
        content = re.sub(pattern, lambda _match: block.rstrip() + "\n\n", content, count=1)
    else:
        content = content.rstrip() + "\n\n" + block

    codex_config.write_text(content.lstrip(), encoding="utf-8")
    return backup


def _install_claude_config(config_file: Path, claude_config: Path) -> Optional[Path]:
    claude_config.parent.mkdir(parents=True, exist_ok=True)
    backup = _backup_file(claude_config)

    if claude_config.exists() and claude_config.read_text(encoding="utf-8").strip():
        payload = json.loads(claude_config.read_text(encoding="utf-8"))
    else:
        payload = {}

    payload.setdefault("mcpServers", {})
    payload["mcpServers"]["prestashop"] = _claude_config_payload(config_file)
    claude_config.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return backup


@click.group(invoke_without_command=True)
@click.option("--shop-url", envvar="PRESTASHOP_SHOP_URL", help="PrestaShop shop URL")
@click.option("--api-key", envvar="PRESTASHOP_API_KEY", help="PrestaShop API key")
@click.option("--log-level", envvar="LOG_LEVEL", default="INFO", help="Logging level")
@click.pass_context
def main(ctx: click.Context, shop_url: Optional[str], api_key: Optional[str], log_level: str):
    """Start and configure the PrestaShop MCP Server."""
    if ctx.invoked_subcommand is not None:
        return

    try:
        setup_logging(log_level)
        logger = logging.getLogger(__name__)

        if shop_url and api_key:
            config = Config(shop_url=shop_url, api_key=api_key, log_level=log_level)
        else:
            config = Config.from_env()

        config.validate_config()
        logger.info("Starting PrestaShop MCP Server for shop: %s", config.shop_url)
        asyncio.run(server_main())

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--config-file", type=click.Path(path_type=Path), default=get_user_env_path, show_default=True)
@click.option("--force", is_flag=True, help="Overwrite an existing config file")
@click.option("--skip-test", is_flag=True, help="Do not test the API connection after writing config")
def init(config_file: Path, force: bool, skip_test: bool):
    """Run an interactive setup wizard and write the local .env file."""
    click.echo("PrestaShop Local MCP setup")
    click.echo(f"Config file: {config_file}")
    click.echo("")

    action = _existing_config_action(config_file, force)
    if action == "cancel":
        raise click.ClickException("Setup cancelled. Existing config file was left unchanged.")

    if action == "omit":
        config = _read_env_file_config(config_file)
        shop_url = config.shop_url
        api_key = config.api_key
        click.echo("Keeping existing config file unchanged.")
    else:
        shop_url = click.prompt("PrestaShop shop URL", type=str).strip().rstrip("/")
        api_key = click.prompt("PrestaShop Webservice API key", type=str, hide_input=True).strip()
        tax_rules_group_id = click.prompt(
            "ID regla fiscal productos nuevos (ej. 15 = ES Standard rate (21%))",
            type=str,
        ).strip()
        log_level = click.prompt("Log level", default="INFO", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]))

        config = Config(
            shop_url=shop_url,
            api_key=api_key,
            log_level=log_level,
            tax_rules_group_id=tax_rules_group_id,
        )
        config.validate_config()
        _write_env_file(config_file, shop_url, api_key, log_level, force=True, tax_rules_group_id=tax_rules_group_id)

    click.echo("")
    click.echo(f"Config saved: {config_file}" if action != "omit" else f"Config kept: {config_file}")
    click.echo(f"Shop URL: {shop_url}")
    click.echo(f"API key: {_mask_secret(api_key)}")

    if not skip_test:
        click.echo("")
        click.echo("Testing PrestaShop API connection...")
        result = asyncio.run(_test_connection(config))
        if isinstance(result, dict) and "error" in result:
            raise click.ClickException(f"API test failed: {result['error']}")
        click.echo("API connection OK")

    click.echo("")
    click.echo("Next steps:")
    click.echo("  python -m prestashop_mcp.cli setup")
    click.echo("  python -m prestashop_mcp.cli doctor")
    click.echo("  python -m prestashop_mcp.cli install-codex")


@main.command()
@click.option("--config-file", type=click.Path(path_type=Path), default=get_user_env_path, show_default=True)
@click.option("--force", is_flag=True, help="Overwrite an existing config file")
@click.option("--skip-test", is_flag=True, help="Do not test the API connection after writing config")
@click.option("--with-codex/--without-codex", default=None, help="Install Codex config without asking")
@click.option("--with-claude/--without-claude", default=None, help="Install Claude Desktop config without asking")
def setup(
    config_file: Path,
    force: bool,
    skip_test: bool,
    with_codex: Optional[bool],
    with_claude: Optional[bool],
):
    """Run the full assisted setup for non-technical users."""
    click.echo("PrestaShop Local MCP assisted setup")
    click.echo("This wizard stores credentials locally and never writes the API key to Codex or Claude config.")
    click.echo("")

    action = _existing_config_action(config_file, force)
    if action == "cancel":
        raise click.ClickException("Setup cancelled. Existing config file was left unchanged.")

    if action == "omit":
        config = _read_env_file_config(config_file)
        api_key = config.api_key
        click.echo("Keeping existing local credential file unchanged.")
    else:
        shop_url = click.prompt("PrestaShop shop URL", type=str).strip().rstrip("/")
        api_key = click.prompt("PrestaShop Webservice API key", type=str, hide_input=True).strip()
        tax_rules_group_id = click.prompt(
            "ID regla fiscal productos nuevos (ej. 15 = ES Standard rate (21%))",
            type=str,
        ).strip()
        log_level = click.prompt("Log level", default="INFO", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]))

        config = Config(
            shop_url=shop_url,
            api_key=api_key,
            log_level=log_level,
            tax_rules_group_id=tax_rules_group_id,
        )
        config.validate_config()
        _write_env_file(config_file, shop_url, api_key, log_level, force=True, tax_rules_group_id=tax_rules_group_id)

    click.echo("")
    if action == "omit":
        click.echo(f"Local credential file kept: {config_file}")
    else:
        click.echo(f"Local credential file saved: {config_file}")
    click.echo(f"API key: {_mask_secret(api_key)}")

    if not skip_test:
        click.echo("")
        click.echo("Testing PrestaShop API connection...")
        result = asyncio.run(_test_connection(config))
        if isinstance(result, dict) and "error" in result:
            raise click.ClickException(f"API test failed: {result['error']}")
        click.echo("API connection OK")

    if with_codex is None:
        with_codex = click.confirm("Connect this MCP to Codex in ChatGPT Desktop now?", default=True)
    if with_codex:
        backup = _install_codex_config(config_file, _codex_config_path())
        click.echo(f"Codex config updated: {_codex_config_path()}")
        if backup:
            click.echo(f"Codex backup: {backup}")

    if with_claude is None:
        with_claude = click.confirm("Connect this MCP to Claude Desktop now?", default=False)
    if with_claude:
        backup = _install_claude_config(config_file, _claude_config_path())
        click.echo(f"Claude Desktop config updated: {_claude_config_path()}")
        if backup:
            click.echo(f"Claude backup: {backup}")

    click.echo("")
    click.echo("Setup complete. Restart ChatGPT Desktop/Codex or Claude Desktop before using the MCP.")


@main.command()
def doctor():
    """Check local configuration and PrestaShop API connectivity."""
    config_file = get_user_env_path()
    click.echo("PrestaShop Local MCP doctor")
    click.echo(f"Python: {sys.executable}")
    click.echo(f"User config file: {config_file}")
    click.echo(f"User config exists: {config_file.exists()}")

    config = Config.from_env()
    click.echo(f"Shop URL: {config.shop_url}")
    click.echo(f"API key configured: {_mask_secret(config.api_key)}")
    click.echo(f"ID de la regla de impuestos: {config.tax_rules_group_id}")

    result = asyncio.run(_test_connection(config))
    if isinstance(result, dict) and "error" in result:
        raise click.ClickException(f"API test failed: {result['error']}")
    click.echo("API connection OK")


@main.command("show-config-path")
def show_config_path():
    """Print the per-user .env path used by the package."""
    click.echo(get_user_env_path())


@main.command("install-codex")
@click.option("--config-file", type=click.Path(path_type=Path), default=get_user_env_path, show_default=True)
@click.option("--codex-config", type=click.Path(path_type=Path), default=_codex_config_path, show_default=True)
def install_codex(config_file: Path, codex_config: Path):
    """Install or update the Codex config.toml MCP block automatically."""
    backup = _install_codex_config(config_file, codex_config)
    click.echo(f"Codex config updated: {codex_config}")
    if backup:
        click.echo(f"Backup written: {backup}")


@main.command("install-claude")
@click.option("--config-file", type=click.Path(path_type=Path), default=get_user_env_path, show_default=True)
@click.option("--claude-config", type=click.Path(path_type=Path), default=_claude_config_path, show_default=True)
def install_claude(config_file: Path, claude_config: Path):
    """Install or update the Claude Desktop MCP JSON config automatically."""
    backup = _install_claude_config(config_file, claude_config)
    click.echo(f"Claude Desktop config updated: {claude_config}")
    if backup:
        click.echo(f"Backup written: {backup}")


@main.command("print-codex-config")
@click.option("--config-file", type=click.Path(path_type=Path), default=get_user_env_path, show_default=True)
def print_codex_config(config_file: Path):
    """Print the Codex config.toml MCP block."""
    click.echo(_codex_config_block(config_file))


@main.command("print-claude-config")
@click.option("--config-file", type=click.Path(path_type=Path), default=get_user_env_path, show_default=True)
def print_claude_config(config_file: Path):
    """Print a Claude Desktop mcpServers JSON block."""
    payload = {
        "mcpServers": {
            "prestashop": _claude_config_payload(config_file)
        }
    }
    click.echo(json.dumps(payload, indent=2))


@main.command("test-connection")
def test_connection():
    """Test the configured PrestaShop API connection."""
    config = Config.from_env()
    result = asyncio.run(_test_connection(config))
    if isinstance(result, dict) and "error" in result:
        raise click.ClickException(f"API test failed: {result['error']}")
    click.echo("API connection OK")


if __name__ == "__main__":
    main()

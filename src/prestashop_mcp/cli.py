"""Command line interface for PrestaShop MCP Server."""

import asyncio
import json
import logging
import os
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


def _write_env_file(path: Path, shop_url: str, api_key: str, log_level: str, force: bool) -> None:
    if path.exists() and not force:
        raise click.ClickException(
            f"Config file already exists: {path}. Use --force to overwrite it."
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        f"PRESTASHOP_SHOP_URL={shop_url.rstrip('/')}\n"
        f"PRESTASHOP_API_KEY={api_key}\n"
        f"LOG_LEVEL={log_level}\n"
    )
    path.write_text(content, encoding="utf-8")

    if os.name != "nt":
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)


async def _test_connection(config: Config) -> dict:
    async with PrestaShopClient(config) as client:
        return await client.get_configurations()


def _python_command() -> str:
    return str(Path(sys.executable))


def _config_cwd(config_file: Path) -> str:
    return str(config_file.parent)


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

    shop_url = click.prompt("PrestaShop shop URL", type=str).strip().rstrip("/")
    api_key = click.prompt("PrestaShop Webservice API key", type=str, hide_input=True).strip()
    log_level = click.prompt("Log level", default="INFO", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]))

    config = Config(shop_url=shop_url, api_key=api_key, log_level=log_level)
    config.validate_config()
    _write_env_file(config_file, shop_url, api_key, log_level, force=force)

    click.echo("")
    click.echo(f"Config saved: {config_file}")
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
    click.echo("  prestashop-mcp print-codex-config")
    click.echo("  prestashop-mcp print-claude-config")
    click.echo("  prestashop-mcp doctor")


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

    result = asyncio.run(_test_connection(config))
    if isinstance(result, dict) and "error" in result:
        raise click.ClickException(f"API test failed: {result['error']}")
    click.echo("API connection OK")


@main.command("show-config-path")
def show_config_path():
    """Print the per-user .env path used by the package."""
    click.echo(get_user_env_path())


@main.command("print-codex-config")
@click.option("--config-file", type=click.Path(path_type=Path), default=get_user_env_path, show_default=True)
def print_codex_config(config_file: Path):
    """Print the Codex config.toml MCP block."""
    click.echo("[mcp_servers.prestashop]")
    click.echo(f"command = '{_python_command()}'")
    click.echo("args = ['-m', 'prestashop_mcp.prestashop_mcp_server']")
    click.echo(f"cwd = '{_config_cwd(config_file)}'")
    click.echo("startup_timeout_sec = 30")
    click.echo("tool_timeout_sec = 120")
    click.echo("default_tools_approval_mode = 'writes'")


@main.command("print-claude-config")
@click.option("--config-file", type=click.Path(path_type=Path), default=get_user_env_path, show_default=True)
def print_claude_config(config_file: Path):
    """Print a Claude Desktop mcpServers JSON block."""
    payload = {
        "mcpServers": {
            "prestashop": {
                "command": _python_command(),
                "args": ["-m", "prestashop_mcp.prestashop_mcp_server"],
                "cwd": _config_cwd(config_file),
            }
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

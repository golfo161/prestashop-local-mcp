"""Configuration management for PrestaShop MCP Server."""

import os
from pathlib import Path

from pydantic import BaseModel, Field
from dotenv import load_dotenv


def get_user_config_dir() -> Path:
    """Return the per-user config directory for this MCP."""
    if os.name == "nt" and os.getenv("APPDATA"):
        return Path(os.environ["APPDATA"]) / "prestashop-local-mcp"
    return Path.home() / ".config" / "prestashop-local-mcp"


def get_user_env_path() -> Path:
    """Return the per-user .env path used by installed distributions."""
    return get_user_config_dir() / ".env"


def load_config_files() -> None:
    """Load project and user configuration without overriding real env vars."""
    load_dotenv()
    load_dotenv(get_user_env_path(), override=False)


load_config_files()


class Config(BaseModel):
    """Configuration for PrestaShop MCP Server."""
    
    shop_url: str = Field(
        description="PrestaShop shop URL",
        default_factory=lambda: os.getenv("PRESTASHOP_SHOP_URL", "")
    )
    
    api_key: str = Field(
        description="PrestaShop API key",
        default_factory=lambda: os.getenv("PRESTASHOP_API_KEY", "")
    )
    
    log_level: str = Field(
        description="Logging level",
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )

    tax_rules_group_id: str = Field(
        description="Default PrestaShop tax rules group ID for new products",
        default_factory=lambda: os.getenv("PRESTASHOP_TAX_RULES_GROUP_ID", "1")
    )
    
    def validate_config(self) -> None:
        """Validate that required configuration is present."""
        if not self.shop_url:
            raise ValueError("PRESTASHOP_SHOP_URL environment variable is required")
        
        if not self.api_key:
            raise ValueError("PRESTASHOP_API_KEY environment variable is required")
        
        if not self.shop_url.startswith(('http://', 'https://')):
            raise ValueError("PRESTASHOP_SHOP_URL must start with http:// or https://")
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        load_config_files()
        config = cls()
        config.validate_config()
        return config

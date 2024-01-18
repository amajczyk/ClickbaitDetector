"""Description:
Configuration file for the application, contains region and endpoint ID for the Vertex AI model.
"""
import json
from dataclasses import dataclass


# Create a dataclass for the configuration file
@dataclass
class Config:
    """Configuration file for the application."""
    refresh_token: str
    client_id: str
    client_secret: str
    quota_project_id: str
    type: str


# Create a function to load the configuration file
def load_config_from_file(config_path: str = "news/vertex/config.json") -> Config:
    """Load the configuration file."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return Config(**config)


# Create a function to save the configuration file
def save_config(config: Config, config_path: str) -> None:
    """Save the configuration file."""
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.__dict__, f, indent=4)

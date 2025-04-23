"""
Configuration settings for the Vault Secret Rotator.
Because every superhero needs their utility belt! 🦸‍♂️
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VaultConfig:
    """
    Configuration class for Vault settings.
    Like a fancy settings menu, but for your secrets! 🎮
    """
    def __init__(self):
        self.vault_addr = os.getenv('VAULT_ADDR')
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        # Validate required settings
        if not self.vault_addr:
            raise ValueError("VAULT_ADDR not found in environment! Where's your secret hideout? 🏰")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN not found in environment! Did you forget your secret handshake? 🤝")

    @property
    def auth_config(self) -> Dict[str, Any]:
        """
        Get authentication configuration.
        Like your VIP access card! 🎟️
        """
        return {
            'token': self.github_token
        }

    @property
    def connection_config(self) -> Dict[str, Any]:
        """
        Get connection configuration.
        Like knowing the secret knock! 🚪
        """
        return {
            'url': self.vault_addr
        }

class LoggingConfig:
    """
    Configuration for logging settings.
    Because we like to keep track of our adventures! 📝
    """
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL = 'INFO'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

class PathConfig:
    """
    Configuration for path handling.
    Like having a GPS for your secrets! 🗺️
    """
    @staticmethod
    def validate_path(path: str) -> str:
        """
        Validate and normalize a vault path.
        Making sure we're on the right track! 🛤️
        """
        if not path:
            raise ValueError("Path cannot be empty! Where are we going? 🤷")
            
        # Remove leading/trailing slashes
        path = path.strip('/')
        
        # Ensure path starts with either 'kv' or 'secret'
        if not (path.startswith('kv/') or path.startswith('secret/')):
            raise ValueError("Path must start with 'kv/' or 'secret/'! Wrong neighborhood? 🏘️")
            
        # Ensure path contains '/data/'
        if '/data/' not in path:
            # Add data component if missing
            parts = path.split('/')
            if parts[0] == 'kv':
                parts.insert(1, 'data')
            elif parts[0] == 'secret':
                parts.insert(1, 'data')
            path = '/'.join(parts)
            
        return path

    @staticmethod
    def get_mount_point(path: str) -> str:
        """
        Get the mount point from a path.
        Like finding the right door in a hallway! 🚪
        """
        if path.startswith('kv/'):
            return 'kv'
        elif path.startswith('secret/'):
            return 'secret'
        else:
            raise ValueError("Invalid path format! We're lost! 🗺️")

class RotationConfig:
    """
    Configuration for secret rotation.
    Like having a recipe for making new secrets! 🎲
    """
    # Add any rotation-specific settings here
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

# Create global instances
vault_config = VaultConfig()
logging_config = LoggingConfig()
path_config = PathConfig()
rotation_config = RotationConfig()
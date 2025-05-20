#!/usr/bin/env python3
"""
Secret Rotator CLI

This script allows users to rotate secrets stored in HashiCorp Vault across multiple environments and applications.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
import yaml
import argparse
from utils import (
    load_config,
    init_vault_client,
    check_login,
    check_paths,
    prompt_user,
    rotate_secret_kv,
    confirm_changes,
)
import hvac
from datetime import datetime


def setup_logging() -> logging.Logger:
    """Configure logging to both file and console."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create log filename with timestamp
    log_file = log_dir / f"secret_rotation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configure logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Console handler with minimal format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)
    
    # File handler with detailed format
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)
    
    return logger


def get_paths_from_config(config: Dict[str, Any], env: str, app: str) -> List[Dict[str, str]]:
    """Get paths from config with their format information."""
    return config["environments"][env][app]["paths"]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Secret Rotator CLI")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    return parser.parse_args()


def main():
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    logger = setup_logging()

    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be applied!")
    
    logger.info("🔐 Welcome to the Secret Rotator!")

    # Load configuration
    try:
        config = load_config("config.yaml")
    except FileNotFoundError:
        logger.error("❌ Configuration file 'config.yaml' not found!")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"❌ Invalid YAML in config file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error loading config: {e}")
        sys.exit(1)

    # Environment selection
    try:
        env_choice = prompt_user("Select environment", list(config["environments"].keys()))
    except KeyError:
        logger.error("❌ No environments defined in config!")
        sys.exit(1)

    # GitHub authentication
    logger.info("\n🔑 GitHub Authentication Required")
    logger.info("Required scopes: read:org, repo (for private repos)")
    token = prompt_user("Enter your GitHub Personal Access Token", sensitive=True)
    
    try:
        client = init_vault_client(token, config, env_choice)
    except ValueError as e:
        logger.error(f"❌ Authentication error: {str(e)}")
        sys.exit(1)
    except hvac.exceptions.VaultError as e:
        logger.error(f"❌ Vault error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during Vault client initialization: {str(e)}")
        sys.exit(1)

    # Verify login
    if not check_login(client):
        logger.error("❌ Login failed. Check your token and try again.")
        sys.exit(1)

    # Get available applications
    try:
        available_apps = [app for app in config["environments"][env_choice].keys() if app != "vault_url"]
        if not available_apps:
            logger.error("❌ No applications configured for this environment.")
            sys.exit(1)
    except KeyError as e:
        logger.error(f"❌ Invalid config structure: {str(e)}")
        sys.exit(1)

    # Test paths
    try:
        mount_point = config["vault"]["mount_point"]
        first_app = available_apps[0]
        paths = get_paths_from_config(config, env_choice, first_app)
    except KeyError as e:
        logger.error(f"❌ Missing required config key: {str(e)}")
        sys.exit(1)

    logger.info("🔍 Verifying access to paths...")
    path_results = check_paths(client, mount_point, paths)
    
    # Show results
    all_accessible = True
    for path, accessible in path_results.items():
        if not accessible:
            all_accessible = False
            logger.error(f"❌ Failed to access: {path}")
    
    if not all_accessible:
        logger.error("❌ Some paths are not accessible. Please verify permissions and paths.")
        sys.exit(1)

    # Application selection
    app_choice = prompt_user("Select application", available_apps)
    paths = get_paths_from_config(config, env_choice, app_choice)

    # Choose secret type
    secret_type = prompt_user(
        "What would you like to rotate?",
        ["AWS secret keys", "Some other secret"]
    )
    changes = {"environment": env_choice, "application": app_choice}

    try:
        if secret_type == "AWS secret keys":
            access_key_id = prompt_user("Enter new AWS access key ID", sensitive=True)
            secret_access_key = prompt_user("Enter new AWS secret access key", sensitive=True)
            changes["AWS_ACCESS_KEY_ID"] = access_key_id
            changes["AWS_SECRET_ACCESS_KEY"] = secret_access_key
        else:
            logger.info("Enter the environment variable name (without 'export' prefix)")
            logger.info("Example: for 'export LANGFUSE_HOST=...' enter 'LANGFUSE_HOST'")
            key_name = prompt_user("Environment variable name")
            new_value = prompt_user(f"New value for {key_name}", sensitive=True)
            changes[f"Environment variable"] = f"{key_name}={new_value}"

        # Confirmation
        if not confirm_changes(changes):
            logger.info("🚫 Operation cancelled.")
            sys.exit(0)

        # Perform rotations
        if args.dry_run:
            logger.info("\n🔍 DRY RUN - Would make the following changes:")
            for path_config in paths:
                path = path_config['path']
                logger.info(f"Would update {path} with new values")
                if secret_type == "AWS secret keys":
                    logger.info(f"  - AWS_ACCESS_KEY_ID: {access_key_id[:4]}...{access_key_id[-4:]}")
                    logger.info(f"  - AWS_SECRET_ACCESS_KEY: {secret_access_key[:4]}...{secret_access_key[-4:]}")
                else:
                    logger.info(f"  - {key_name}: {new_value[:4]}...{new_value[-4:] if len(new_value) > 8 else '****'}")
            logger.info("\n🎭 No changes were made (dry-run mode)")
            sys.exit(0)
        
        logger.info("⚙️  Rotating secrets...")
        for path_config in paths:
            path = path_config['path']
            try:
                if secret_type == "AWS secret keys":
                    rotate_secret_kv(
                        client=client,
                        mount_point=mount_point,
                        path=path,
                        key_or_dict={
                            "AWS_ACCESS_KEY_ID": access_key_id,
                            "AWS_SECRET_ACCESS_KEY": secret_access_key
                        },
                        config=config,
                        environment=env_choice
                    )
                else:
                    rotate_secret_kv(
                        client=client,
                        mount_point=mount_point,
                        path=path,
                        key_or_dict=key_name,
                        value=new_value,
                        config=config,
                        environment=env_choice
                    )
                logger.info(f"🔄 Updated {path}")
            except Exception as e:
                logger.error(f"❌ Failed to rotate secret at {path}: {str(e)}")
                # Continue with other paths even if one fails
                continue

        logger.info("🎉 Secrets rotated successfully!")
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
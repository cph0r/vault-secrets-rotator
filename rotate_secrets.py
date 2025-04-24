#!/usr/bin/env python3
"""
Secret Rotator CLI

This script allows users to rotate secrets stored in HashiCorp Vault across multiple environments and applications.
"""

import logging
import sys
from typing import List, Dict, Any
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


def get_paths_from_config(config: Dict[str, Any], env: str, app: str) -> List[Dict[str, str]]:
    """Get paths from config with their format information."""
    return config["environments"][env][app]["paths"]


def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger = logging.getLogger(__name__)

    logger.info("🔐 Welcome to the Secret Rotator!")

    # Load configuration
    try:
        config = load_config("config.yaml")
    except Exception as e:
        logger.error(f"❌ Failed to load config: {e}")
        sys.exit(1)

    # Environment selection
    env_choice = prompt_user("Select environment", list(config["environments"].keys()))

    # GitHub authentication
    logger.info("\n🔑 GitHub Authentication Required")
    logger.info("Required scopes: read:org, repo (for private repos)")
    token = prompt_user("Enter your GitHub Personal Access Token", sensitive=True)
    
    try:
        client = init_vault_client(token, config, env_choice)
    except ValueError as e:
        logger.error(f"❌ {str(e)}")
        sys.exit(1)

    # Verify login
    if not check_login(client):
        logger.error("❌ Login failed. Check your token and try again.")
        sys.exit(1)

    # Get available applications
    available_apps = [app for app in config["environments"][env_choice].keys() if app != "vault_url"]
    if not available_apps:
        logger.error("❌ No applications configured for this environment.")
        sys.exit(1)

    # Test paths
    mount_point = config["vault"]["mount_point"]
    first_app = available_apps[0]
    paths = get_paths_from_config(config, env_choice, first_app)

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
    logger.info("⚙️  Rotating secrets...")
    try:
        for path_config in paths:
            path = path_config['path']
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
    except ValueError as e:
        logger.error(f"❌ Failed to rotate secrets: {str(e)}")
        sys.exit(1)

    logger.info("🎉 Secrets rotated successfully!")


if __name__ == "__main__":
    main() 
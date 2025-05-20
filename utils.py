import yaml
import hvac
from getpass import getpass
import logging
from typing import Dict, Any, Optional, Tuple, Union, NamedTuple
from pathlib import Path

from secret_formats import read_secret, format_secret

logger = logging.getLogger(__name__)


class AwsKeyNames(NamedTuple):
    """AWS key names for access and secret keys."""
    access_key: str
    secret_key: str


def clean_vault_path(path: str) -> str:
    """
    Clean and normalize a Vault path.
    
    Args:
        path: Raw path string
        
    Returns:
        Cleaned path string with 'data/' prefix removed if present
    """
    # Convert to Path object for normalization
    path_obj = Path(path)
    # Convert back to string and ensure forward slashes
    clean_path = str(path_obj).replace('\\', '/')
    # Remove leading/trailing slashes
    clean_path = clean_path.strip('/')
    # Remove 'data/' prefix if present
    parts = clean_path.split('/')
    if 'data' in parts:
        data_index = parts.index('data')
        return '/'.join(parts[data_index + 1:])
    return clean_path


def load_config(config_path: Union[str, Path]) -> dict:
    """Load YAML configuration file."""
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with config_path.open('r') as f:
        return yaml.safe_load(f)


def init_vault_client(token: str, config: dict, environment: str = None) -> hvac.Client:
    """Initialize and return a Vault client using GitHub authentication."""
    if environment and environment in config['environments']:
        vault_url = config['environments'][environment]['vault_url']
    else:
        raise ValueError(f"Environment '{environment}' not found in config or no environment specified")
    
    client = hvac.Client(url=vault_url)
    
    try:
        client.auth.github.login(token=token)
    except Exception as e:
        raise ValueError(f"GitHub authentication failed: {str(e)}")
    
    return client


def check_login(client: hvac.Client) -> bool:
    """Check if Vault login is successful."""
    return client.is_authenticated()


def check_paths(client: hvac.Client, mount_point: str, paths: list) -> dict:
    """Check if all paths are accessible."""
    results = {}
    for path_config in paths:
        path = path_config['path'] if isinstance(path_config, dict) else path_config
        try:
            actual_path = clean_vault_path(path)
            client.secrets.kv.v2.read_secret_version(
                path=actual_path,
                mount_point=mount_point
            )
            results[path] = True
        except Exception as e:
            logger.debug(f"Failed to access {path}: {str(e)}")
            results[path] = False
    return results


def prompt_user(prompt: str, choices: list = None, sensitive: bool = False) -> str:
    """
    Prompt the user to enter a value or select from choices.
    For sensitive inputs like tokens or keys, use getpass to mask the input.
    """
    if choices:
        print(prompt)
        for i, choice in enumerate(choices, 1):
            print(f"{i}. {choice}")
        while True:
            sel = input("Enter choice number: ")
            if sel.isdigit() and 1 <= int(sel) <= len(choices):
                return choices[int(sel) - 1]
            print("Invalid choice. Try again.")
    else:
        if sensitive:
            return getpass(f"{prompt}: ")
        return input(f"{prompt}: ")


def get_path_format(config: dict, environment: str, path: str) -> Tuple[str, str, Optional[AwsKeyNames]]:
    """
    Get the format type, key, and AWS key names for a given path.
    
    Args:
        config: Configuration dictionary
        environment: Environment name
        path: Secret path
        
    Returns:
        Tuple of (format_type, key, aws_key_names)
    """
    # Remove mount point and 'data' from path if present
    clean_path = path.replace("kv/data/", "")
    
    # Find matching path in config
    env_config = config['environments'][environment]
    for service in env_config.values():
        if isinstance(service, dict) and 'paths' in service:
            for path_config in service['paths']:
                if isinstance(path_config, dict) and path_config['path'].endswith(clean_path):
                    format_type = path_config['format']
                    # For json and dotenv_plain, try to infer key if not specified
                    if 'key' not in path_config:
                        if format_type == 'json':
                            key = 'secrets'
                        elif format_type == 'dotenv_plain':
                            key = 'dotenv'
                        else:
                            key = path_config.get('key', 'dotenv')
                    else:
                        key = path_config['key']
                    
                    # Check for path-specific AWS key names
                    if 'aws_keys' in path_config:
                        aws_keys = AwsKeyNames(
                            access_key=path_config['aws_keys']['access_key'],
                            secret_key=path_config['aws_keys']['secret_key']
                        )
                    # Fall back to format-specific AWS key names
                    elif 'aws_keys' in config['vault']['formats'][format_type]:
                        format_aws_keys = config['vault']['formats'][format_type]['aws_keys']
                        aws_keys = AwsKeyNames(
                            access_key=format_aws_keys['access_key'],
                            secret_key=format_aws_keys['secret_key']
                        )
                    else:
                        # Default AWS key names
                        aws_keys = AwsKeyNames(
                            access_key="AWS_ACCESS_KEY_ID",
                            secret_key="AWS_SECRET_ACCESS_KEY"
                        )
                    
                    return format_type, key, aws_keys
    
    # If path not found, try to determine format from path
    for format_type, format_config in config['vault']['formats'].items():
        if any(pattern in clean_path.lower() for pattern in format_config.get('path_patterns', [])):
            # Found matching format, use its default key
            if format_type == 'json':
                key = 'secrets'
            elif format_type == 'dotenv_plain':
                key = 'dotenv'
            else:
                key = 'dotenv'
            
            aws_keys = AwsKeyNames(
                access_key=format_config.get('aws_keys', {}).get('access_key', "AWS_ACCESS_KEY_ID"),
                secret_key=format_config.get('aws_keys', {}).get('secret_key', "AWS_SECRET_ACCESS_KEY")
            )
            return format_type, key, aws_keys
    
    # Last resort defaults
    return 'dotenv_export', 'dotenv', AwsKeyNames(
        access_key="AWS_ACCESS_KEY_ID",
        secret_key="AWS_SECRET_ACCESS_KEY"
    )


def rotate_secret_kv(
    client: hvac.Client,
    mount_point: str,
    path: str,
    key_or_dict: Union[str, Dict[str, str]],
    value: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    environment: Optional[str] = None
) -> None:
    """
    Rotate one or more secret keys in KV store.
    
    Args:
        client: The Vault client
        mount_point: The mount point in Vault
        path: The path to the secret
        key_or_dict: Either a single key (str) or a dictionary of key-value pairs
        value: The value to set (only used if key_or_dict is a string)
        config: Configuration dictionary (optional, for format detection)
        environment: Environment name (optional, for format detection)
    """
    try:
        # Clean up path
        actual_path = clean_vault_path(path)
            
        # Read current secret or initialize empty if not exists
        try:
            secret = client.secrets.kv.v2.read_secret_version(
                path=actual_path,
                mount_point=mount_point
            )
            current_data = secret['data']['data']
        except hvac.exceptions.InvalidPath:
            current_data = {}
        
        # If config is provided, use it to determine format and key
        if config and environment:
            format_type, secret_key, aws_keys = get_path_format(config, environment, path)
        else:
            # Only try to detect format from content when no config is provided
            format_type = 'dotenv_export'  # default
            secret_key = None
            for k, v in current_data.items():
                if isinstance(v, str):
                    if v.startswith('{') and v.endswith('}'):
                        format_type = 'json'
                        secret_key = k
                        break
                    elif '=' in v and 'export' not in v:
                        format_type = 'dotenv_plain'
                        secret_key = k
                        break
                    elif 'export' in v:
                        format_type = 'dotenv_export'
                        secret_key = k
                        break
            
            # If no key found, use format-appropriate defaults
            if not secret_key:
                if format_type == 'json':
                    secret_key = 'secrets'
                else:
                    secret_key = 'dotenv'
            
            aws_keys = AwsKeyNames(
                access_key="AWS_ACCESS_KEY_ID",
                secret_key="AWS_SECRET_ACCESS_KEY"
            )
        
        # Parse current content or initialize empty
        # If the key doesn't exist in current_data, initialize it based on format
        if secret_key not in current_data:
            if format_type == 'json':
                current_data[secret_key] = '{}'
            else:
                current_data[secret_key] = ''
        
        current_content = current_data[secret_key]
        current_secrets = read_secret(current_content, format_type) if current_content else {}
        
        # Update secrets
        if isinstance(key_or_dict, dict):
            if format_type == 'dotenv_export':
                # Only map keys for dotenv_export format
                updates = {
                    aws_keys.access_key: key_or_dict['AWS_ACCESS_KEY_ID'],
                    aws_keys.secret_key: key_or_dict['AWS_SECRET_ACCESS_KEY']
                }
            else:
                # For other formats, try to update existing AWS keys with their original names
                existing_access_key = next((k for k in current_secrets.keys() 
                                         if k.upper().endswith('ACCESS_KEY')), None)
                existing_secret_key = next((k for k in current_secrets.keys() 
                                         if k.upper().endswith('SECRET_KEY')), None)
                
                updates = {}
                if existing_access_key and 'AWS_ACCESS_KEY_ID' in key_or_dict:
                    updates[existing_access_key] = key_or_dict['AWS_ACCESS_KEY_ID']
                elif 'AWS_ACCESS_KEY_ID' in key_or_dict:
                    # Create new key with format-appropriate name
                    if format_type == 'json':
                        updates['S3_ACCESS_KEY'] = key_or_dict['AWS_ACCESS_KEY_ID']
                    else:
                        updates['AWS_ACCESS_KEY'] = key_or_dict['AWS_ACCESS_KEY_ID']
                
                if existing_secret_key and 'AWS_SECRET_ACCESS_KEY' in key_or_dict:
                    updates[existing_secret_key] = key_or_dict['AWS_SECRET_ACCESS_KEY']
                elif 'AWS_SECRET_ACCESS_KEY' in key_or_dict:
                    # Create new key with format-appropriate name
                    if format_type == 'json':
                        updates['S3_SECRET_KEY'] = key_or_dict['AWS_SECRET_ACCESS_KEY']
                    else:
                        updates['AWS_SECRET_KEY'] = key_or_dict['AWS_SECRET_ACCESS_KEY']
                
                # Add any remaining keys that weren't mapped
                updates.update({k: v for k, v in key_or_dict.items() 
                              if k not in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']})
        else:
            updates = {key_or_dict: value}
        
        # For JSON format, ensure we're updating the dictionary properly
        if format_type == 'json':
            if not isinstance(current_secrets, dict):
                current_secrets = {}
            current_secrets.update(updates)
            new_content = format_secret(current_secrets, format_type)
        else:
            current_secrets.update(updates)
            new_content = format_secret(current_secrets, format_type)
        
        current_data[secret_key] = new_content
        
        # Write back to Vault
        client.secrets.kv.v2.create_or_update_secret(
            path=actual_path,
            secret=current_data,
            mount_point=mount_point
        )
    except Exception as e:
        raise ValueError(f"Failed to rotate secret at {path}: {str(e)}")


def confirm_changes(changes: dict) -> bool:
    """Show summary and ask for confirmation."""
    print("\nYou are about to make the following changes:")
    for k, v in changes.items():
        # Show full access key
        if any(key in k.upper() for key in ['ACCESS_KEY', 'ACCESS_KEY_ID']):
            print(f"{k}: {v}")
        # Show last 4 characters of secret key
        elif any(key in k.upper() for key in ['SECRET_KEY', 'SECRET_ACCESS_KEY']):
            masked_value = '*' * (len(v) - 4) + v[-4:] if len(v) > 4 else v
            print(f"{k}: {masked_value}")
        # Mask other sensitive values
        elif any(sensitive in k.lower() for sensitive in ['token', 'key', 'secret', 'password']):
            print(f"{k}: ********")
        else:
            print(f"{k}: {v}")
    return input("Are you sure? (y/n): ").lower() == 'y' 
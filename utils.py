import yaml
import hvac
from getpass import getpass
import logging

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Load YAML configuration file."""
    with open(config_path, 'r') as f:
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
    for p in paths:
        try:
            path_parts = p.split('/')
            if 'data' in path_parts:
                data_index = path_parts.index('data')
                actual_path = '/'.join(path_parts[data_index + 1:])
            else:
                actual_path = p
            
            client.secrets.kv.v2.read_secret_version(
                path=actual_path,
                mount_point='kv'
            )
            results[p] = True
        except Exception as e:
            logger.debug(f"Failed to access {p}: {str(e)}")
            results[p] = False
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


def rotate_secret_kv(client: hvac.Client, mount_point: str, path: str, key_or_dict, value=None) -> None:
    """
    Rotate one or more secret keys in KV store.
    
    Args:
        client: The Vault client
        mount_point: The mount point in Vault
        path: The path to the secret
        key_or_dict: Either a single key (str) or a dictionary of key-value pairs
        value: The value to set (only used if key_or_dict is a string)
    """
    try:
        path_parts = path.split('/')
        if 'data' in path_parts:
            data_index = path_parts.index('data')
            actual_path = '/'.join(path_parts[data_index + 1:])
        else:
            actual_path = path
            
        secret = client.secrets.kv.v2.read_secret_version(
            path=actual_path,
            mount_point='kv'
        )
        data = secret['data']['data']
        
        dotenv_content = None
        for k, v in data.items():
            if isinstance(v, str) and 'export' in v:
                dotenv_content = v
                dotenv_key = k
                break
        
        if dotenv_content is None:
            raise ValueError("No dotenv content found in the secret")
            
        lines = dotenv_content.split('\n')
        new_lines = []
        updated_keys = set()

        updates = key_or_dict if isinstance(key_or_dict, dict) else {key_or_dict: value}
        
        for line in lines:
            line_added = False
            for key, new_value in updates.items():
                key_pattern = f"export {key}="
                if line.startswith(key_pattern):
                    new_lines.append(f"{key_pattern}{new_value}")
                    updated_keys.add(key)
                    line_added = True
                    break
            if not line_added:
                new_lines.append(line)
                
        for key, new_value in updates.items():
            if key not in updated_keys:
                new_lines.append(f"export {key}={new_value}")
            
        new_dotenv_content = '\n'.join(new_lines)
        data[dotenv_key] = new_dotenv_content
        
        client.secrets.kv.v2.create_or_update_secret(
            path=actual_path,
            secret=data,
            mount_point='kv'
        )
    except Exception as e:
        raise ValueError(f"Failed to rotate secret at {path}: {str(e)}")


def confirm_changes(changes: dict) -> bool:
    """Show summary and ask for confirmation."""
    print("\nYou are about to make the following changes:")
    for k, v in changes.items():
        if any(sensitive in k.lower() for sensitive in ['token', 'key', 'secret', 'password']):
            print(f"{k}: ********")
        else:
            print(f"{k}: {v}")
    return input("Are you sure? (y/n): ").lower() == 'y' 
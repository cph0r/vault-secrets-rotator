from typing import Dict, Tuple, List
import re
import logging

def parse_dotenv_content(content: str) -> Dict[str, str]:
    """
    Parse dotenv-style content into a dictionary.
    Because who doesn't love turning messy strings into beautiful dictionaries? 🎨
    """
    if not content:
        return {}

    env_vars = {}
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            try:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip("'").strip('"')
                env_vars[key] = value
            except ValueError:
                logging.warning(f"Skipping malformed line: {line} - Did someone fall asleep on the keyboard? 😴")
                continue
    
    return env_vars

def update_dotenv_content(content: str, updates: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
    """
    Update dotenv content with new values and return the updated content and old values.
    Like a find-and-replace ninja, but for environment variables! 🥷
    """
    if not content or not updates:
        return content, {}

    old_values = {}
    current_vars = parse_dotenv_content(content)
    lines = content.strip().split('\n')
    updated_lines = []

    for line in lines:
        original_line = line
        line = line.strip()
        
        if not line or line.startswith('#'):
            updated_lines.append(original_line)
            continue

        try:
            key, _ = line.split('=', 1)
            key = key.strip()
            
            if key in updates:
                old_values[key] = current_vars.get(key, '')
                # Preserve original quoting style
                quote_match = re.match(r'[^=]+=\s*(["\'])(.*)\1', original_line)
                quote = quote_match.group(1) if quote_match else ''
                updated_line = f"{key}={quote}{updates[key]}{quote}"
                updated_lines.append(updated_line)
            else:
                updated_lines.append(original_line)
                
        except ValueError:
            updated_lines.append(original_line)
            continue

    return '\n'.join(updated_lines), old_values

def validate_vault_path(path: str) -> str:
    """
    Validate and normalize a Vault path.
    Because paths are like pizza toppings - they need to be just right! 🍕
    """
    if not path:
        raise ValueError("Empty path? That's like a pizza with no cheese! 🧀")

    # Remove leading 'secret/' or 'kv/'
    if path.startswith('secret/'):
        path = path.replace('secret/', '', 1)
    elif path.startswith('kv/'):
        path = path.replace('kv/', '', 1)

    # Ensure path starts with 'data/'
    if not path.startswith('data/'):
        path = f"data/{path}"

    return path

def get_secret_keys(client, path: str) -> List[str]:
    """
    Get list of keys in a secret.
    Like a treasure hunt, but for environment variables! 🗺️
    """
    try:
        secret = client.secrets.kv.v2.read_secret_version(path=path)
        if not secret or 'data' not in secret or 'data' not in secret['data']:
            return []
        return list(secret['data']['data'].keys())
    except Exception as e:
        logging.error(f"Failed to get secret keys: {str(e)} - The treasure chest is locked! 🔒")
        return []
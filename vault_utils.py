import logging
from typing import Optional, Dict, Tuple
import re
from config import (
    VAULT_CONFIG, MASKING_CONFIG, ERROR_MESSAGES,
    AWS_CREDENTIALS
)

# Set up logging because silent code is boring code! 🔊
logger = logging.getLogger(__name__)

def parse_dotenv_content(content: str) -> Dict[str, str]:
    """
    Parse dotenv-style content into a dictionary.
    Because who doesn't love parsing environment variables? 🔍
    """
    result = {}
    if not content:
        return result
        
    for line in content.strip().split('\n'):
        line = line.strip()
        if line and line.startswith('export '):
            # Remove 'export ' prefix
            line = line[7:]
            # Split on first '=' only
            parts = line.split('=', 1)
            if len(parts) == 2:
                key, value = parts
                # Remove surrounding quotes if they exist
                value = value.strip('"\'')
                result[key.strip()] = value
                
    return result

def update_dotenv_content(content: str, updates: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
    """
    Update dotenv-style content with new values.
    Returns the updated content and a dict of old values.
    Because updating env vars should be fancy! ✨
    """
    if not content or not updates:
        return content, {}
        
    old_values = {}
    lines = content.strip().split('\n')
    updated_lines = []
    
    for line in lines:
        original_line = line
        line = line.strip()
        if line and line.startswith('export '):
            # Remove 'export ' prefix for comparison
            var_part = line[7:]
            key = var_part.split('=', 1)[0].strip()
            
            if key in updates:
                old_value = var_part.split('=', 1)[1].strip().strip('"\'')
                old_values[key] = old_value
                # Create new line with updated value
                new_line = f'export {key}="{updates[key]}"'
                updated_lines.append(new_line)
                continue
                
        updated_lines.append(original_line)
        
    return '\n'.join(updated_lines), old_values

def mask_secret_value(value: str, show_chars: int = None) -> str:
    """
    Mask a secret value, showing only the first and last few characters.
    Because we're responsible adults who don't show all our secrets! 🎭
    """
    show_chars = show_chars or MASKING_CONFIG['SHOW_CHARS']
    
    if not value or len(value) <= (show_chars * 2):
        return '*' * len(value) if value else ''
    
    return f"{value[:show_chars]}{'*' * (len(value)-show_chars*2)}{value[-show_chars:]}"

def validate_vault_path(path: str) -> tuple[bool, Optional[str]]:
    """
    Validate a Vault path format.
    Because not all paths are created equal! 🛣️
    """
    if not path:
        return False, "Path cannot be empty! What am I supposed to work with? 🤷‍♂️"
    
    # Check if path starts with expected prefixes
    if not any(path.startswith(prefix) for prefix in VAULT_CONFIG['VALID_PATH_PREFIXES']):
        return False, f"Path must start with one of {VAULT_CONFIG['VALID_PATH_PREFIXES']}! Are you lost? 🗺️"
    
    # Check if path contains 'data' segment for v2 KV engine
    if VAULT_CONFIG['DATA_PATH_SEGMENT'] not in path:
        suggested_path = path.replace('/secret/', '/secret/data/').replace('/kv/', '/kv/data/')
        return False, f"Missing '/data/' in path. Did you mean: {suggested_path}? 🤔"
    
    return True, None

def format_error_message(error: Exception) -> str:
    """
    Format an error message with some sass.
    Because if we're going to fail, we might as well fail with style! 💅
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    return ERROR_MESSAGES.get(error_type, f"Oops! {error_msg} 🤦‍♂️")

def validate_secret_key(key: str) -> tuple[bool, Optional[str]]:
    """
    Validate a secret key name.
    Because we have standards! ✨
    """
    if not key:
        return False, "Key cannot be empty! What are we even rotating here? 🎡"
    
    if len(key) > VAULT_CONFIG['MAX_KEY_LENGTH']:
        return False, f"That key is longer than a Monday morning! Keep it under {VAULT_CONFIG['MAX_KEY_LENGTH']} chars! 📏"
    
    # Check for invalid characters
    for char in VAULT_CONFIG['INVALID_KEY_CHARS']:
        if char in key:
            return False, f"Key contains invalid character: '{char}'. Keep it clean! 🧼"
    
    return True, None 
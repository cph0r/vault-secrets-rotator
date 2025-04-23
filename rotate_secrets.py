import hvac
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict
import json
import sys
import argparse
from vault_tests import test_setup, test_path_access
from vault_utils import (
    mask_secret_value, validate_vault_path, format_error_message, 
    validate_secret_key, parse_dotenv_content, update_dotenv_content
)
from config import (
    LOGGING_CONFIG, ENV_VARS, CLI_CONFIG,
    AWS_CREDENTIALS, VAULT_PATHS, DEFAULT_KEYS,
    VAULT_ENVIRONMENTS, ERROR_MESSAGES
)

# Set up logging because who doesn't love a good log? 🪵
logging.basicConfig(level=getattr(logging, LOGGING_CONFIG['LEVEL']), 
                   format=LOGGING_CONFIG['FORMAT'])
logger = logging.getLogger(__name__)

class VaultSecretRotator:
    def __init__(self, environment: str):
        """Initialize our fancy Vault client because we're fancy like that 💅"""
        load_dotenv()
        
        if environment.upper() not in VAULT_ENVIRONMENTS:
            raise ValueError(ERROR_MESSAGES['InvalidEnvironment'])
            
        vault_env = VAULT_ENVIRONMENTS[environment.upper()]
        self.vault_addr = vault_env['url']
        self.environment = environment
        self.github_token = os.getenv(ENV_VARS['VAULT_TOKEN'])  # We're using GitHub token here
        
        if not self.github_token:
            raise ValueError(f"Oh honey, you forgot to set {ENV_VARS['VAULT_TOKEN']} (GitHub token)! 🤦‍♂️")
        
        # Create the initial client
        self.client = hvac.Client(url=self.vault_addr)
        
        # Authenticate with GitHub
        try:
            self.client.auth.github.login(token=self.github_token)
            logger.info(f"GitHub authentication successful for {vault_env['description']}! Look at you being all secure! 🎭")
        except Exception as e:
            logger.error(format_error_message(e))
            raise

    def rotate_dotenv_secret(self, path: str, key: str, updates: Dict[str, str]) -> None:
        """
        Rotate specific values within a dotenv-style secret.
        Because sometimes you need to be selective about your secrets! 🎯
        """
        try:
            # Validate path format
            is_valid, error_msg = validate_vault_path(path)
            if not is_valid:
                logger.error(error_msg)
                return

            # Validate key format
            is_valid, error_msg = validate_secret_key(key)
            if not is_valid:
                logger.error(error_msg)
                return

            # Read current secret
            secret = self.client.read(path)
            if not secret or 'data' not in secret:
                logger.error(f"No secret found at {path}. Are you sure you're not lost? 🗺️")
                return

            # Get the dotenv content
            current_data = secret['data'].get('data', {})
            dotenv_content = current_data.get(key, '')
            
            if not dotenv_content:
                logger.error(f"No dotenv content found at key '{key}'! 😱")
                return
                
            # Parse and update the content
            updated_content, old_values = update_dotenv_content(dotenv_content, updates)
            
            # Update the secret
            current_data[key] = updated_content
            self.client.write(path, data=current_data)
            
            # Log the changes (masked, because we're responsible!)
            logger.info(f"Successfully updated dotenv values in '{key}' at path '{path}' in {self.environment}! 🌟")
            for env_key, old_value in old_values.items():
                logger.info(f"Updated {env_key}:")
                logger.info(f"  Old value: {mask_secret_value(old_value)}")
                logger.info(f"  New value: {mask_secret_value(updates[env_key])}")
            
        except Exception as e:
            logger.error(format_error_message(e))

    def rotate_secrets_in_paths(self, paths: List[str], key: str, updates: Dict[str, str]) -> None:
        """
        Iterate through paths and rotate the specified dotenv values in each one.
        Like a secret-rotating Santa, delivering new keys to all the good paths! 🎅
        """
        for path in paths:
            logger.info(f"Starting rotation for path: {path} in {self.environment} - Hold onto your hats! 🎩")
            self.rotate_dotenv_secret(path, key, updates)

def list_environments():
    """
    List available vault environments with their descriptions.
    Because choosing environments should be fun! 🎪
    """
    logger.info("\nAvailable Vault Environments:")
    for env_key, env_data in VAULT_ENVIRONMENTS.items():
        logger.info(f"  - {env_data['name']}: {env_data['description']}")
    logger.info("")

def main():
    parser = argparse.ArgumentParser(description=CLI_CONFIG['DESCRIPTION'])
    parser.add_argument('command', choices=list(CLI_CONFIG['COMMANDS'].values()),
                      help='Command to execute (test-auth, test-path, or rotate)')
    parser.add_argument('--environment', '-e', required=True,
                      choices=[env['name'] for env in VAULT_ENVIRONMENTS.values()],
                      help='Vault environment to use')
    parser.add_argument('path', nargs='?', help='Path for test-path or rotate command')
    parser.add_argument('--key', default=DEFAULT_KEYS['DOTENV'],
                      help=f"Key containing the dotenv content (default: {DEFAULT_KEYS['DOTENV']})")
    parser.add_argument('--aws-access-key', help='New AWS Access Key ID')
    parser.add_argument('--aws-secret-key', help='New AWS Secret Access Key')
    parser.add_argument('--paths', nargs='+', help='Multiple paths for rotation (optional)')
    parser.add_argument('--list-environments', '-l', action='store_true',
                      help='List available vault environments')
    
    args = parser.parse_args()

    if args.list_environments:
        list_environments()
        sys.exit(0)

    if args.command == CLI_CONFIG['COMMANDS']['TEST_AUTH']:
        success = test_setup(args.environment)
        sys.exit(0 if success else 1)
    
    elif args.command == CLI_CONFIG['COMMANDS']['TEST_PATH']:
        if not args.path:
            logger.error("Path argument is required for test-path command! 🤦‍♂️")
            sys.exit(1)
        success = test_path_access(args.path, args.environment)
        sys.exit(0 if success else 1)
    
    elif args.command == CLI_CONFIG['COMMANDS']['ROTATE']:
        if not args.key:
            logger.error("--key argument is required! What am I supposed to update? 🤔")
            sys.exit(1)
            
        if not args.aws_access_key or not args.aws_secret_key:
            logger.error("Both --aws-access-key and --aws-secret-key are required! Don't be shy! 🔑")
            sys.exit(1)
        
        try:
            rotator = VaultSecretRotator(args.environment)
            paths_to_rotate = args.paths if args.paths else [args.path]
            if not paths_to_rotate or not paths_to_rotate[0]:
                logger.error("At least one path is required! Where am I supposed to work my magic? 🎩")
                sys.exit(1)
            
            # Prepare the updates using our config keys
            updates = {
                AWS_CREDENTIALS['ACCESS_KEY_ID']: args.aws_access_key,
                AWS_CREDENTIALS['SECRET_ACCESS_KEY']: args.aws_secret_key
            }
                
            rotator.rotate_secrets_in_paths(paths_to_rotate, args.key, updates)
            logger.info(f"All secrets have been rotated in {args.environment}! Time to celebrate! 🎊")
        except Exception as e:
            logger.error(format_error_message(e))
            sys.exit(1)

if __name__ == "__main__":
    main() 
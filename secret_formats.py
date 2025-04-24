"""
Module for handling different secret formats in Vault.
"""
from abc import ABC, abstractmethod
import json
from typing import Dict, Any
import re


class SecretFormatter(ABC):
    """Abstract base class for secret formatters."""
    
    @abstractmethod
    def parse(self, content: str) -> Dict[str, str]:
        """Parse secret content into a dictionary."""
        pass
    
    @abstractmethod
    def format(self, secrets: Dict[str, str]) -> str:
        """Format dictionary of secrets into string content."""
        pass


class DotenvExportFormatter(SecretFormatter):
    """Handles secrets in 'export KEY="value"' format."""
    
    def parse(self, content: str) -> Dict[str, str]:
        """Parse export statements into a dictionary."""
        result = {}
        # Match "export KEY="value"" pattern
        pattern = r'export\s+([A-Za-z0-9_]+)=["\'](.+?)["\']'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            key, value = match.groups()
            result[key] = value
            
        return result
    
    def format(self, secrets: Dict[str, str]) -> str:
        """Format dictionary into export statements."""
        lines = [f'export {key}="{value}"' for key, value in sorted(secrets.items())]
        return '\n'.join(lines)


class JsonFormatter(SecretFormatter):
    """Handles secrets in JSON format."""
    
    def parse(self, content: str) -> Dict[str, str]:
        """Parse JSON string into a dictionary."""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def format(self, secrets: Dict[str, str]) -> str:
        """Format dictionary into JSON string."""
        return json.dumps(secrets, indent=2)


class DotenvPlainFormatter(SecretFormatter):
    """Handles secrets in 'KEY=value' format."""
    
    def parse(self, content: str) -> Dict[str, str]:
        """Parse KEY=value pairs into a dictionary."""
        result = {}
        # Match "KEY=value" pattern, handling both quoted and unquoted values
        pattern = r'([A-Za-z0-9_]+)=(?:["\'](.+?)["\']|(.+?)(?:\n|$))'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            key = match.group(1)
            # Group 2 is quoted value, Group 3 is unquoted value
            value = match.group(2) if match.group(2) is not None else match.group(3)
            result[key] = value
            
        return result
    
    def format(self, secrets: Dict[str, str]) -> str:
        """Format dictionary into KEY=value pairs."""
        lines = [f'{key}={value}' for key, value in sorted(secrets.items())]
        return '\n'.join(lines)


class SecretFormatFactory:
    """Factory for creating secret formatters."""
    
    _formatters = {
        'dotenv_export': DotenvExportFormatter(),
        'json': JsonFormatter(),
        'dotenv_plain': DotenvPlainFormatter()
    }
    
    @classmethod
    def get_formatter(cls, format_type: str) -> SecretFormatter:
        """Get the appropriate formatter for the given format type."""
        formatter = cls._formatters.get(format_type)
        if formatter is None:
            raise ValueError(f"Unsupported secret format: {format_type}")
        return formatter


def read_secret(content: str, format_type: str) -> Dict[str, str]:
    """Read secret content in the specified format."""
    formatter = SecretFormatFactory.get_formatter(format_type)
    return formatter.parse(content)


def format_secret(secrets: Dict[str, str], format_type: str) -> str:
    """Format secrets dictionary into the specified format."""
    formatter = SecretFormatFactory.get_formatter(format_type)
    return formatter.format(secrets) 
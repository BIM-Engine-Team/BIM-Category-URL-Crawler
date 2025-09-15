"""
Environment configuration utility
Handles loading and validating environment variables from .env file
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional


class EnvConfig:
    """Utility class for environment configuration"""

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize environment configuration

        Args:
            env_file: Path to .env file (optional, defaults to .env in project root)
        """
        if env_file is None:
            # Look for .env in project root (parent of src directory)
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent
            env_file = project_root / '.env'

        # Load environment variables
        if Path(env_file).exists():
            load_dotenv(env_file)
            self.env_file_loaded = str(env_file)
        else:
            # Try to load from current directory
            load_dotenv()
            self.env_file_loaded = None

    def get_claude_api_key(self) -> Optional[str]:
        """Get Claude API key from environment"""
        return os.getenv('CLAUDE_API_KEY')

    def get_log_level(self) -> str:
        """Get log level from environment (default: INFO)"""
        return os.getenv('LOG_LEVEL', 'INFO').upper()

    def get_output_dir(self) -> str:
        """Get output directory from environment (default: output)"""
        return os.getenv('OUTPUT_DIR', 'output')

    def get_database_url(self) -> Optional[str]:
        """Get database URL from environment (optional)"""
        return os.getenv('DATABASE_URL')

    def validate_required_keys(self) -> dict:
        """
        Validate that required environment variables are set

        Returns:
            dict: Validation results with 'valid' boolean and 'errors' list
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # Check required keys
        claude_key = self.get_claude_api_key()
        if not claude_key:
            result['valid'] = False
            result['errors'].append('CLAUDE_API_KEY is required')
        elif len(claude_key) < 10:
            result['warnings'].append('CLAUDE_API_KEY appears to be too short')

        # Check if .env file was loaded
        if not self.env_file_loaded:
            result['warnings'].append('No .env file found, using system environment variables only')

        return result

    def print_config_status(self):
        """Print current configuration status"""
        print("Environment Configuration Status:")
        print("=" * 40)

        if self.env_file_loaded:
            print(f"[OK] .env file loaded: {self.env_file_loaded}")
        else:
            print("[WARN] No .env file found, using system environment only")

        # Check key status
        claude_key = self.get_claude_api_key()
        if claude_key:
            print(f"[OK] CLAUDE_API_KEY: Set (length: {len(claude_key)})")
        else:
            print("[ERROR] CLAUDE_API_KEY: Not set")

        print(f"[OK] LOG_LEVEL: {self.get_log_level()}")
        print(f"[OK] OUTPUT_DIR: {self.get_output_dir()}")

        db_url = self.get_database_url()
        if db_url:
            print(f"[OK] DATABASE_URL: {db_url}")

        print("=" * 40)


# Global instance
env_config = EnvConfig()


def get_env_config() -> EnvConfig:
    """Get the global environment configuration instance"""
    return env_config
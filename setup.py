#!/usr/bin/env python3
"""
Setup script for Website Structure Exploration System
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False


def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False


def setup_env_file():
    """Set up .env file from example"""
    env_example = Path('.env.example')
    env_file = Path('.env')

    if env_example.exists() and not env_file.exists():
        # Copy example to .env
        with open(env_example, 'r') as src:
            content = src.read()

        with open(env_file, 'w') as dst:
            dst.write(content)

        print("✓ Created .env file from .env.example")
        print("⚠ Please edit .env file and add your CLAUDE_API_KEY")
        return True
    elif env_file.exists():
        print("✓ .env file already exists")
        return True
    else:
        print("✗ .env.example file not found")
        return False


def test_installation():
    """Test if installation is working"""
    print("Testing installation...")
    try:
        # Add src to Python path for testing
        src_path = Path('src').absolute()
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        # Test imports
        from config.exploration_config import ExplorationConfig
        from config.ai_config import AIConfig
        from config.env_config import get_env_config

        print("✓ Core modules can be imported")

        # Test environment configuration
        env_config = get_env_config()
        validation = env_config.validate_required_keys()

        if validation['valid']:
            print("✓ Environment configuration is valid")
        else:
            print("⚠ Environment configuration has issues:")
            for error in validation['errors']:
                print(f"    - {error}")

        return True

    except Exception as e:
        print(f"✗ Installation test failed: {e}")
        return False


def main():
    """Main setup function"""
    print("=" * 60)
    print("Website Structure Exploration System - Setup")
    print("=" * 60)

    success_count = 0
    total_steps = 4

    # Step 1: Check Python version
    print("\n1. Checking Python version...")
    if check_python_version():
        success_count += 1

    # Step 2: Install dependencies
    print("\n2. Installing dependencies...")
    if install_dependencies():
        success_count += 1

    # Step 3: Setup .env file
    print("\n3. Setting up environment file...")
    if setup_env_file():
        success_count += 1

    # Step 4: Test installation
    print("\n4. Testing installation...")
    if test_installation():
        success_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("Setup Summary")
    print("=" * 60)

    if success_count == total_steps:
        print(f"🎉 Setup completed successfully! ({success_count}/{total_steps})")
        print("\nNext steps:")
        print("1. Edit .env file and add your CLAUDE_API_KEY")
        print("2. Test configuration: python src/main.py --check-env")
        print("3. Run help: python src/main.py --help")
        print("4. Try exploration: python src/main.py https://example.com")
    else:
        print(f"⚠ Setup partially completed ({success_count}/{total_steps})")
        print("\nPlease resolve the issues above and run setup again.")

    return success_count == total_steps


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
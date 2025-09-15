#!/usr/bin/env python3
"""
Installation and configuration test script
"""

import sys
import os
import importlib
from pathlib import Path

def test_python_version():
    """Test Python version compatibility"""
    print("Testing Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"OK Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"FAIL Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def test_dependencies():
    """Test required package imports"""
    print("\nTesting dependencies...")

    required_packages = [
        'aiohttp',
        'asyncio',
        'bs4',  # beautifulsoup4
        'pydantic',
        'lxml',
        'requests',
        'urllib3',
        'dateutil'  # python-dateutil
    ]

    success = True
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError as e:
            print(f"❌ {package} - {e}")
            success = False

    return success

def test_project_structure():
    """Test project file structure"""
    print("\nTesting project structure...")

    required_files = [
        'src/__init__.py',
        'src/main.py',
        'src/models/__init__.py',
        'src/config/__init__.py',
        'src/ai/__init__.py',
        'src/explorer/__init__.py',
        'src/schema/__init__.py',
        'src/utils/__init__.py',
        'config/sample_config.json',
        'requirements.txt'
    ]

    success = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            success = False

    return success

def test_module_imports():
    """Test importing our custom modules"""
    print("\nTesting module imports...")

    # Add src to path for imports
    src_path = Path(__file__).parent.parent / 'src'
    sys.path.insert(0, str(src_path))

    modules_to_test = [
        ('src.models', ['ExplorationState', 'LinkSeries', 'WebsiteNode']),
        ('src.config', ['AIConfig', 'ExplorationConfig']),
        ('src.utils', ['HTTPClient']),
        ('src.ai.base_ai_client', ['BaseAIClient']),
        ('src.explorer.page_analyzer', ['PageAnalyzer']),
        ('src.schema.schema_generator', ['SchemaGenerator'])
    ]

    success = True
    for module_name, classes in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            for class_name in classes:
                if hasattr(module, class_name):
                    print(f"✅ {module_name}.{class_name}")
                else:
                    print(f"❌ {module_name}.{class_name} - Class not found")
                    success = False
        except ImportError as e:
            print(f"❌ {module_name} - {e}")
            success = False

    return success

def test_api_key_setup():
    """Test API key configuration"""
    print("\nTesting API key setup...")

    api_key = os.getenv('CLAUDE_API_KEY')
    if api_key:
        if len(api_key) > 10:  # Basic validation
            print("✅ CLAUDE_API_KEY is set and appears valid")
            return True
        else:
            print("❌ CLAUDE_API_KEY is too short")
            return False
    else:
        print("⚠️  CLAUDE_API_KEY not set - required for AI features")
        print("   Set it with: export CLAUDE_API_KEY=your_key_here")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")

    # Add src to path for imports
    src_path = Path(__file__).parent.parent / 'src'
    sys.path.insert(0, str(src_path))

    try:
        from src.config.exploration_config import ExplorationConfig
        from src.config.ai_config import AIConfig

        # Test default configurations
        exploration_config = ExplorationConfig()
        print(f"✅ ExplorationConfig - max_depth: {exploration_config.max_depth}")

        # Test AI config (will fail without API key, but structure should load)
        ai_config = AIConfig()
        print(f"✅ AIConfig - model: {ai_config.model}")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Installation and Configuration Test")
    print("=" * 50)

    tests = [
        test_python_version,
        test_dependencies,
        test_project_structure,
        test_module_imports,
        test_configuration,
        test_api_key_setup
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"All tests passed! ({passed}/{total})")
        print("\nSystem is ready to use!")
        print("\nNext steps:")
        print("1. Set CLAUDE_API_KEY environment variable if not already set")
        print("2. Run: python src/main.py --help")
        print("3. Try: python src/main.py https://example.com")
    else:
        print(f"{passed}/{total} tests passed")
        print("\nPlease fix the issues above before using the system")

        if not results[1]:  # Dependencies failed
            print("\nTo install dependencies:")
            print("pip install -r requirements.txt")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
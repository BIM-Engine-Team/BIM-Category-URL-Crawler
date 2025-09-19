#!/usr/bin/env python3
"""
Setup script for AI-guided web crawler package.
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "AI-guided web crawler for product page discovery"

# Read requirements
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(req_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="bim-category-url-crawler",
    version="1.0.0",
    description="AI-guided web crawler for product page discovery with dynamic content support",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/ai-web-crawler",

    # Package configuration
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",

    # Dependencies
    install_requires=read_requirements(),

    # Console scripts entry point
    entry_points={
        'console_scripts': [
            'ai-crawler=src.main:main',
        ],
    },

    # Package metadata
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],

    # Keywords for discovery
    keywords="web crawler, ai, product discovery, dynamic content, automation",

    # Package data
    package_data={
        'src': ['*.json', '*.md'],
    },

    # Additional files
    data_files=[
        ('', ['example_config.json', '.env.example']),
    ],
)
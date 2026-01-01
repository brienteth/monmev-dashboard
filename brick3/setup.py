#!/usr/bin/env python3
"""
Brick3 Setup Configuration
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="brick3",
    version="1.0.0",
    author="Brick3 Team",
    author_email="team@brick3.io",
    description="Ultra-fast MEV infrastructure for Virtuals agents on Monad",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/brienteth/brick3",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial :: Point-Of-Sale",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "web3>=6.0.0",
        "eth-keys>=0.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "virtuals": [
            "virtuals>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "brick3=brick3.cli:main",
        ],
    },
)

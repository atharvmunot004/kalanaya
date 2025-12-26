"""Setup script for Kalanaya."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="kalanaya",
    version="0.1.0",
    description="Voice-controlled calendar assistant using Whisper and Ollama",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/kalanaya",
    packages=find_packages(include=['src', 'config']),
    include_package_data=True,
    package_data={
        'config': ['*.txt', '*.json', '*.md', 'prompts/*.txt'],
    },
    python_requires=">=3.9",
    install_requires=[
        "google-api-python-client",
        "google-auth",
        "google-auth-oauthlib",
        "openai-whisper",
        "sounddevice",
        "scipy",
        "numpy",
        "requests",
        "langgraph",
        "langchain-core",
        "pydantic",
    ],
    entry_points={
        "console_scripts": [
            "kalanaya=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)


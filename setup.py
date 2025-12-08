"""Setup configuration for AI Agent Runtime."""
from setuptools import setup, find_packages

setup(
    name="agent-runtime",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "pydantic>=2.10.0",
        "ollama>=0.1.6",
        "pytest>=7.4.3",
        "httpx>=0.25.2",
        "pytest-asyncio>=0.21.0",
    ],
)
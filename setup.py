"""
Setup configuration for Prometheus Agent AI
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="prometheus-agent-ai",
    version="1.0.0",
    author="Prometheus Agent AI Team",
    author_email="team@prometheus-agent-ai.com",
    description="AI-powered monitoring and analysis agent for Prometheus",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/prometheus-agent-ai",
    project_urls={
        "Bug Tracker": "https://github.com/your-org/prometheus-agent-ai/issues",
        "Documentation": "https://github.com/your-org/prometheus-agent-ai/docs",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Monitoring",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "pre-commit>=3.5.0",
        ],
        "test": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "httpx-testing>=0.3.0",
            "pytest-cov>=4.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "prometheus-agent-api=src.api.main:main",
            "prometheus-agent-ui=src.ui.streamlit_app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.md"],
    },
    keywords=[
        "prometheus",
        "monitoring",
        "ai",
        "artificial-intelligence",
        "observability",
        "metrics",
        "alerts",
        "chatgpt",
        "openai",
        "devops",
        "sre"
    ],
)

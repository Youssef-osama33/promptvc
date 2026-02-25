"""
setup.py — Build configuration for PromptVC.

For modern projects, configuration lives in pyproject.toml. This file is
retained for maximum compatibility with older pip versions and tooling that
does not yet support PEP 517 builds.

Install (development):
    pip install -e .

Install (production):
    pip install promptvc

Publish to PyPI:
    python -m build
    twine upload dist/*
"""

from pathlib import Path
from setuptools import find_packages, setup

HERE = Path(__file__).parent

# Read the long description from the project README.
long_description = (HERE / "README.md").read_text(encoding="utf-8")

# Read the version from the package without importing it
# (avoids importing click before it is installed).
version: dict = {}
exec((HERE / "promptvc" / "__init__.py").read_text(encoding="utf-8"), version)

setup(
    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    name="promptvc",
    version=version["__version__"],
    description=(
        "Git-like version control for LLM prompts — "
        "commit, diff, checkout, and roll back your prompts like code."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    # ------------------------------------------------------------------
    # Authorship
    # ------------------------------------------------------------------
    author=version["__author__"],
    url=version["__url__"],
    project_urls={
        "Bug Tracker": "https://github.com/Youssef-osama33/promptvc/issues",
        "Source": "https://github.com/Youssef-osama33/promptvc",
    },
    # ------------------------------------------------------------------
    # Packaging
    # ------------------------------------------------------------------
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov",
        ],
    },
    # ------------------------------------------------------------------
    # Entry points — installs the `promptvc` shell command
    # ------------------------------------------------------------------
    entry_points={
        "console_scripts": [
            "promptvc=promptvc.cli:cli",
        ],
    },
    # ------------------------------------------------------------------
    # PyPI metadata
    # ------------------------------------------------------------------
    license="MIT",
    keywords=[
        "llm", "prompt", "prompt-engineering", "version-control",
        "git", "ai", "gpt", "cli", "developer-tools",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Version Control",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Utilities",
    ],
)

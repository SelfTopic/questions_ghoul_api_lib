#!/usr/bin/env python3
"""
Setup configuration for ghoul-quiz-lib package.

This file is used for setuptools-based installation.
The main configuration is in pyproject.toml for Poetry.
"""

from setuptools import find_packages, setup

setup(
    name="ghoul-quiz-lib",
    version="0.2.0",
    description="Async Python library for Questions Ghoul API",
    long_description=open("LIBRARY_README.md").read(),
    long_description_content_type="text/markdown",
    author="CheStor",
    author_email="selftopic@gmail.com",
    url="https://github.com/chestor-cz/ghoul_quiz_lib",
    license="MIT",
    packages=find_packages(exclude=["tests", "examples"]),
    package_data={"ghoul_quiz": ["py.typed"]},
    python_requires=">=3.9",
    install_requires=[
        "aiohttp>=3.9.0,<4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.23.0",
            "black>=22.0",
            "ruff>=0.1.0",
            "mypy>=0.990",
        ],
    },
    entry_points={
        "console_scripts": [
            "ghoul-quiz-register=ghoul_quiz.register:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Russian",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Typing :: Typed",
    ],
    keywords=[
        "async",
        "api",
        "ghoul",
        "quiz",
        "tokyo-ghoul",
        "aiohttp",
    ],
    project_urls={
        "Documentation": "https://github.com/chestor-cz/ghoul_quiz_lib#readme",
        "Source": "https://github.com/chestor-cz/ghoul_quiz_lib",
        "Bug Tracker": "https://github.com/chestor-cz/ghoul_quiz_lib/issues",
    },
    zip_safe=False,
)

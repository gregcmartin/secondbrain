from setuptools import setup, find_packages

setup(
    name="second-brain",
    version="0.1.0",
    description="Local-first visual memory capture and search system for macOS",
    author="Second Brain Team",
    python_requires=">=3.11",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "python-dotenv>=1.0.0",
        "click>=8.1.7",
        "rich>=13.7.0",
        "Pillow>=10.1.0",
        "pytesseract>=0.3.10",
        "pyobjc-framework-Vision>=10.1",
        "pyobjc-framework-Quartz>=10.1",
        "pyobjc-framework-Cocoa>=10.1",
        "sqlite-utils>=3.36",
        "sentence-transformers>=2.2.2",
        "chromadb>=0.4.22",
        "numpy>=1.26.2",
        "aiofiles>=23.2.1",
        "python-dateutil>=2.8.2",
        "psutil>=5.9.6",
        "structlog>=23.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "second-brain=second_brain.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Monitoring",
    ],
)

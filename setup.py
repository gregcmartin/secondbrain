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
        # Core deps (pin to match requirements.txt)
        "python-dotenv==1.0.0",
        "click==8.1.7",
        "rich==13.7.0",
        "openai==2.6.1",

        # API server
        "fastapi==0.110.0",
        "uvicorn[standard]==0.25.0",

        # macOS APIs for capture and Vision OCR
        "pyobjc-framework-Quartz==12.0",
        "pyobjc-framework-Cocoa==12.0",
        "pyobjc-framework-Vision==12.0",

        # Database
        "sqlite-utils==3.36",

        # Vector embeddings and search
        "sentence-transformers==5.1.2",
        "chromadb==0.4.22",
        "numpy==1.26.4",

        # Async and utilities
        "aiofiles==23.2.1",
        "python-dateutil==2.8.2",
        "psutil==5.9.6",
        "structlog==23.2.0",

        # Image processing and frame diffing
        "Pillow==11.1.0",
        "imagehash==4.3.2",

        # UI
        "streamlit==1.40.2",

        # Video encoding (optional at runtime, but align with requirements.txt)
        "pyobjc-framework-AVFoundation==12.0",
        "pyobjc-framework-CoreMedia==12.0",
    ],
    extras_require={
        # Optional AI reranker support (large model download on first use)
        "reranker": [
            "FlagEmbedding>=1.2.11",
        ],
        # Dev tooling pinned to match requirements.txt
        "dev": [
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1",
            "pytest-cov==4.1.0",
            "black==23.12.1",
            "flake8==6.1.0",
            "mypy==1.7.1",
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

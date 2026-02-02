"""Setup configuration for Meridian MMM Platform."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="meridian-mmm-platform",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive Marketing Mix Modeling platform built on Google Meridian",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/meridian-mmm-platform",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11,<3.13",
    install_requires=[
        "google-meridian>=1.3.2",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "xarray>=2023.1.0",
        "psycopg2-binary>=2.9.9",
        "sqlalchemy>=2.0.0",
        "pyyaml>=6.0.1",
        "pydantic>=2.5.0",
        "loguru>=0.7.2",
        "streamlit>=1.31.0",
        "plotly>=5.18.0",
        "openpyxl>=3.1.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "pylint>=3.0.3",
            "mypy>=1.8.0",
        ],
        "gpu": [
            "jax[cuda12_pip]>=0.4.20",
        ],
        "notebook": [
            "jupyter>=1.0.0",
            "jupyterlab>=4.0.0",
            "ipykernel>=6.25.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "meridian-mmm=meridian_platform.cli:main",
        ],
    },
)

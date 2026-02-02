#!/bin/bash
# Script to set up the complete Meridian MMM Platform project structure

# Create main directory structure
mkdir -p {src,tests,notebooks,data,config,docs,scripts,ui}

# Create source code directory structure
mkdir -p src/meridian_platform/{data_ingestion,modeling,optimization,utils,database}

# Create subdirectories for data ingestion
mkdir -p src/meridian_platform/data_ingestion/{media,sales,priors}

# Create test directory structure
mkdir -p tests/{unit,integration}

# Create data directory structure
mkdir -p data/{raw,processed,sample}

# Create UI structure
mkdir -p ui/{streamlit_app,components,assets}

# Create placeholder __init__.py files
touch src/meridian_platform/__init__.py
touch src/meridian_platform/data_ingestion/__init__.py
touch src/meridian_platform/data_ingestion/media/__init__.py
touch src/meridian_platform/data_ingestion/sales/__init__.py
touch src/meridian_platform/data_ingestion/priors/__init__.py
touch src/meridian_platform/modeling/__init__.py
touch src/meridian_platform/optimization/__init__.py
touch src/meridian_platform/utils/__init__.py
touch src/meridian_platform/database/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

echo "Project structure created successfully!"

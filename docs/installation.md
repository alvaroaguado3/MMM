# Installation Guide

Complete setup instructions for the Meridian MMM Platform.

## System Requirements

### Minimum Requirements
- **Python**: 3.11 or 3.12
- **RAM**: 8 GB
- **Disk Space**: 5 GB
- **OS**: macOS, Linux, or Windows

### Recommended Requirements
- **Python**: 3.11 or 3.12
- **RAM**: 16 GB+
- **GPU**: NVIDIA T4 or better (for accelerated modeling)
- **CUDA**: 11.8+ (for GPU support on Linux)

### For Database (Optional)
- **PostgreSQL**: 12 or later
- **Port**: 5432 (default)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/alvaroaguado3/MMM.git
cd MMM
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install -r requirements.txt

# For GPU support (Linux only)
pip install -r requirements-gpu.txt

# Install the package in development mode
pip install -e .
```

### 4. Verify Installation

```bash
# Test Python imports
python -c "import meridian_platform; print('Installation successful!')"

# Check if Streamlit is installed
streamlit --version
```

## Database Setup (Optional)

### PostgreSQL Installation

#### macOS (using Homebrew)
```bash
# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Verify installation
postgres --version
```

#### Ubuntu/Debian
```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Start PostgreSQL service
sudo service postgresql start

# Verify installation
psql --version
```

#### Windows
Download and install from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)

### Create Database

```bash
# Create the Meridian MMM database
createdb meridian_mmm

# Run initialization script
python scripts/init_database.py

# Verify connection
psql -d meridian_mmm -c "\dt"
```

## Running the Application

### Start Streamlit UI

```bash
streamlit run ui/streamlit_app/app.py
```

The application will open in your default browser at `http://localhost:8501`

### Run Jupyter Notebooks

```bash
jupyter notebook notebooks/
```

This opens the Jupyter interface where you can run demo notebooks.

## Troubleshooting Installation

### Issue: Module not found errors

**Solution**: Make sure your virtual environment is activated and all dependencies are installed.

```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: PostgreSQL connection error

**Solution**: Verify PostgreSQL is running and the database exists.

```bash
# Check PostgreSQL service
brew services list | grep postgresql  # macOS
sudo service postgresql status         # Linux

# Verify database
psql -l | grep meridian_mmm
```

### Issue: GPU not detected

**Solution**: Ensure NVIDIA drivers and CUDA toolkit are installed.

```bash
# Check NVIDIA GPU
nvidia-smi

# Verify JAX GPU support
python -c "import jax; print(jax.devices())"
```

### Issue: Out of memory errors

**Solution**: Reduce batch size or number of chains in model configuration.

See [Model Configuration](model_configuration.md) for details.

## Development Setup

### Install Development Dependencies

```bash
# Install testing and linting tools
pip install pytest pytest-cov black flake8 mypy

# Install documentation tools
pip install sphinx sphinx-rtd-theme
```

### Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest --cov=src/meridian_platform tests/

# Run specific test file
pytest tests/unit/test_data_ingestion.py
```

### Code Formatting

```bash
# Format code with Black
black src/ tests/

# Check code style
flake8 src/ tests/

# Type checking
mypy src/
```

## Docker Setup (Optional)

### Build Docker Image

```bash
docker build -t meridian-mmm .
```

### Run Container

```bash
docker run -p 8501:8501 meridian-mmm
```

## Next Steps

1. **[Prepare Your Data](data_preparation.md)** - Format your marketing and sales data
2. **[Configure the Model](model_configuration.md)** - Set up Bayesian priors
3. **[Run the Application](../README.md#running-the-application)** - Start modeling
4. **[Optimize Your Budget](optimization.md)** - Run optimization scenarios

## Getting Help

- Check [Troubleshooting Guide](troubleshooting.md) for common issues
- Review [Google Meridian Documentation](https://developers.google.com/meridian)
- Open an issue on [GitHub](https://github.com/alvaroaguado3/MMM/issues)

# Troubleshooting Guide

Common issues and solutions for the Meridian MMM Platform.

## Installation Issues

### Issue: "ModuleNotFoundError: No module named 'meridian_platform'"

**Cause**: Package not installed in development mode or virtual environment not activated

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install in development mode
pip install -e .

# Verify installation
python -c "import meridian_platform; print('Success!')"
```

### Issue: "pip install requirements.txt fails"

**Cause**: Missing system dependencies or conflicting versions

**Solution**:
```bash
# Upgrade pip first
pip install --upgrade pip

# Try installing again with verbose output
pip install -r requirements.txt -v

# If JAX fails on macOS
pip install --upgrade jax jaxlib
```

### Issue: GPU not detected after installation

**Cause**: CUDA toolkit not installed or JAX GPU support not configured

**Solution**:
```bash
# Check NVIDIA GPU availability
nvidia-smi

# If not found, install NVIDIA drivers first
# Then install GPU version
pip install -r requirements-gpu.txt

# Verify JAX sees GPU
python -c "import jax; print('Devices:', jax.devices())"
```

## Data Loading Issues

### Issue: "FileNotFoundError: File not found"

**Cause**: Incorrect file path

**Solution**:
```python
import os
from meridian_platform.data_ingestion.media import MediaDataLoader

# Check file exists
file_path = 'data/raw/media_data.csv'
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Available files: {os.listdir('data/raw/')}")
else:
    loader = MediaDataLoader(file_path)
    df = loader.load_and_validate()
```

### Issue: "ValueError: could not convert string to float"

**Cause**: Data contains non-numeric values in numeric columns

**Solution**:
```python
import pandas as pd

# Inspect problematic data
df = pd.read_csv('data/raw/media_data.csv')

# Find non-numeric values
print(df['metric_value'].dtype)
print(df[df['metric_value'].astype(str).str.contains('[a-zA-Z]')])

# Fix the data
df['metric_value'] = pd.to_numeric(df['metric_value'], errors='coerce')
df = df.dropna(subset=['metric_value'])
df.to_csv('data/raw/media_data_clean.csv', index=False)
```

### Issue: "KeyError: 'date' (or other column name)"

**Cause**: Column name mismatch or typo

**Solution**:
```python
# Check column names
import pandas as pd
df = pd.read_csv('data/raw/media_data.csv')
print(df.columns.tolist())

# If column has different name, specify in loader
from meridian_platform.data_ingestion.media import MediaDataLoader

loader = MediaDataLoader(
    file_path='data/raw/media_data.csv',
    date_column='Date',      # Capital D
    geo_column='Geography',   # Different name
    metric_column='Spend'
)
```

### Issue: "Duplicate records for date/geo/touchpoint"

**Cause**: Data has multiple entries for same combination

**Solution**:
```python
import pandas as pd

df = pd.read_csv('data/raw/media_data.csv')

# Check duplicates
duplicates = df[df.duplicated(
    subset=['date', 'geo', 'touchpoint_name'],
    keep=False
)]
print(f"Found {len(duplicates)} duplicate entries")

# Remove duplicates (keep first)
df_clean = df.drop_duplicates(
    subset=['date', 'geo', 'touchpoint_name'],
    keep='first'
)

# Or aggregate duplicates
df_agg = df.groupby(['date', 'geo', 'touchpoint_name']).agg({
    'metric_value': 'sum',
    'spend': 'sum'
}).reset_index()
```

### Issue: "Missing required column: date"

**Cause**: Validation fails on required columns

**Solution**:
```python
from meridian_platform.data_ingestion.media import MediaDataLoader

# Check which columns are required
loader = MediaDataLoader('data/raw/media_data.csv')

# Inspect data
import pandas as pd
df = pd.read_csv('data/raw/media_data.csv')
print("Columns:", df.columns.tolist())
print("Date format:", df['date'].head())

# Ensure all required columns exist
required = ['date', 'geo', 'touchpoint_name', 'metric_value']
missing = [col for col in required if col not in df.columns]
if missing:
    print(f"Missing columns: {missing}")
```

## Model Training Issues

### Issue: "Out of memory error during training"

**Cause**: Dataset too large or too many MCMC iterations

**Solution**:
```python
# Reduce data size
import pandas as pd
media_df = media_df.sample(frac=0.5)  # Use 50% of data

# Use fewer MCMC iterations
runner = MeridianModelRunner(...)
model, results = runner.train(
    n_chains=1,        # Reduced from 2
    n_warmup=500,      # Reduced from 1000
    n_samples=500      # Reduced from 1000
)

# Or use CPU instead of GPU
runner = MeridianModelRunner(..., use_gpu=False)
```

### Issue: "Model won't converge (R-hat > 1.1)"

**Cause**: Model not mixing well, needs more samples or adjusted priors

**Solution**:
```python
# Increase iterations
model, results = runner.train(
    n_chains=4,       # More chains
    n_warmup=2000,    # Longer burn-in
    n_samples=2000    # More samples
)

# Check diagnostics
diagnostics = runner.get_diagnostics()
print(f"R-hat: {diagnostics['r_hat']}")

# Adjust priors to be more informative
# (see Model Configuration guide)
```

### Issue: "Too many divergent transitions"

**Cause**: Posterior has difficult geometry or priors are too weak

**Solution**:
```python
# Option 1: Tighten priors
priors = prior_loader.load()
for channel in priors['channels']:
    # Reduce standard deviation
    priors['channels'][channel]['roi_prior']['std'] *= 0.5

runner = MeridianModelRunner(..., priors=priors)

# Option 2: Adjust model parameters
runner = MeridianModelRunner(
    ...,
    adapt_delta=0.95  # Increase from default 0.8
)

# Check divergences
diagnostics = runner.get_diagnostics()
print(f"Divergent transitions: {diagnostics['n_divergent']}")
```

### Issue: "Model training takes too long"

**Cause**: Large dataset or high iteration count

**Solution**:
```python
# Use GPU
runner = MeridianModelRunner(..., use_gpu=True)

# Reduce iterations for initial testing
model, results = runner.train(
    n_chains=1,
    n_warmup=500,
    n_samples=500
)

# Aggregate data to fewer geo levels
media_df = media_df[media_df['geo'].isin(['New York', 'Los Angeles'])]

# Use multiprocessing
runner = MeridianModelRunner(..., n_jobs=4)
```

### Issue: "Posterior predictive checks fail"

**Cause**: Model doesn't fit data well

**Solution**:
```python
# Visualize posterior predictive
posterior_predictive = runner.get_posterior_predictive()
runner.plot_posterior_predictive(posterior_predictive)

# Check data quality
print("Data summary:")
print(sales_df.describe())

# Verify priors are reasonable
print("Prior settings:")
print(priors)

# Consider simpler model
# Remove time-varying effects
# Reduce number of channels
```

## Optimization Issues

### Issue: "Optimization returns unrealistic allocations"

**Cause**: Model recommendations too extreme

**Solution**:
```python
# Add constraints
constraints = {
    'TV': {'min': 100000, 'max': 600000},
    'Search': {'min': 50000, 'max': 400000},
    'Social': {'min': 25000, 'max': 200000},
}

optimal = optimizer.optimize_roi(
    total_budget=1_000_000,
    constraints=constraints
)

# Use tighter constraints
constraints = {
    channel: {
        'min': current[channel] * 0.8,
        'max': current[channel] * 1.2
    }
    for channel in current.keys()
}
```

### Issue: "Optimization takes too long"

**Cause**: Complex optimization problem or slow algorithm

**Solution**:
```python
# Use faster optimization method
result = optimizer.optimize_roi(
    total_budget=1_000_000,
    method='approximate'  # Faster but less accurate
)

# Reduce number of variables
# Focus on 3-4 main channels only
channels = ['TV', 'Search', 'Social']
filtered_model = model.select_channels(channels)

# Use fewer optimization iterations
result = optimizer.optimize_roi(
    ...,
    max_iterations=100  # Default: 1000
)
```

### Issue: "Cannot achieve target sales with given budget"

**Cause**: Budget too low for target or model predictions unrealistic

**Solution**:
```python
# Check if budget is feasible
max_sales = optimizer.estimate_max_sales(total_budget=1_000_000)
print(f"Maximum achievable sales: ${max_sales:,.0f}")

# Lower target sales
min_cost = optimizer.optimize_efficiency(
    target_sales=2_000_000,  # Reduced from 5_000_000
    constraints='medium'
)

# Or increase budget
min_cost = optimizer.optimize_efficiency(
    target_sales=5_000_000,
    constraints='medium'
)
print(f"Required budget: ${sum(min_cost.values()):,.0f}")

# Check model predictions
predictions = model.predict_sales({'TV': 500000, 'Search': 500000})
print(f"Model predicts: ${predictions:,.0f} sales")
```

## Streamlit UI Issues

### Issue: "Streamlit app won't start"

**Cause**: Port already in use or missing dependencies

**Solution**:
```bash
# Use different port
streamlit run ui/streamlit_app/app.py --server.port 8502

# Or kill process on port 8501
# macOS/Linux:
lsof -i :8501
kill -9 <PID>

# Windows:
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

### Issue: "File upload fails in Streamlit"

**Cause**: File size too large or incorrect format

**Solution**:
```python
# Check file size limit in Streamlit config
# ~/.streamlit/config.toml
# maxUploadSize = 200

# Or use smaller file
# Process data outside Streamlit first
python scripts/process_media_data.py

# Then upload processed file
```

### Issue: "Plots not displaying in Streamlit"

**Cause**: Missing plotting library or incorrect format

**Solution**:
```bash
# Install plotting libraries
pip install plotly matplotlib seaborn

# Restart Streamlit
streamlit run ui/streamlit_app/app.py
```

## Database Issues

### Issue: "Cannot connect to PostgreSQL"

**Cause**: Database not running or incorrect credentials

**Solution**:
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql  # macOS
sudo service postgresql status        # Linux

# Start PostgreSQL if needed
brew services start postgresql@14     # macOS
sudo service postgresql start         # Linux

# Check database exists
psql -l | grep meridian_mmm

# Create database if missing
createdb meridian_mmm
```

### Issue: "Authentication failed for database"

**Cause**: Wrong password or user

**Solution**:
```bash
# Check PostgreSQL user
psql -U postgres

# Reset password
ALTER USER postgres WITH PASSWORD 'new_password';

# Verify connection
psql -U postgres -d meridian_mmm -h localhost
```

## GPU Issues

### Issue: "CUDA out of memory"

**Cause**: Model too large for GPU

**Solution**:
```python
# Use CPU instead
runner = MeridianModelRunner(..., use_gpu=False)

# Or reduce batch size
# Reduce number of observations
media_df = media_df.head(1000)

# Use mixed precision
runner = MeridianModelRunner(..., dtype='float32')
```

### Issue: "JAX only uses CPU despite GPU being present"

**Cause**: GPU drivers not properly installed

**Solution**:
```bash
# Update NVIDIA drivers
nvidia-driver-update

# Reinstall CUDA and cuDNN
pip install --upgrade jax jaxlib

# Verify GPU support
python -c "import jax; print(jax.devices())"
```

## Performance Issues

### Issue: "Application is slow"

**Cause**: Inefficient data processing or model computation

**Solution**:
```python
# Profile code
import cProfile
cProfile.run('runner.train()')

# Use GPU acceleration
runner = MeridianModelRunner(..., use_gpu=True)

# Cache expensive computations
@functools.lru_cache(maxsize=128)
def expensive_function(data):
    return model.predict(data)

# Reduce data resolution
media_df['date'] = media_df['date'].dt.to_period('W')
```

## Getting Help

### Debug Information to Collect

When reporting issues, include:

1. Python and package versions:
   ```bash
   python --version
   pip show meridian-platform jax pandas
   ```

2. Error traceback (full output)

3. Data sample (first few rows)

4. Configuration settings

5. System information:
   ```bash
   # macOS
   system_profiler SPHardwareDataType
   
   # Linux
   uname -a
   ```

### Resources

- [GitHub Issues](https://github.com/alvaroaguado3/MMM/issues)
- [Installation Guide](installation.md)
- [Data Preparation Guide](data_preparation.md)
- [Model Configuration Guide](model_configuration.md)
- [Google Meridian Documentation](https://developers.google.com/meridian)

### Asking for Help

When asking for help, provide:

1. What you were trying to do
2. What error you got (full traceback)
3. What you've already tried
4. Minimum reproducible example
5. System configuration

**Example issue template:**
```
Title: Model training fails with out of memory error

Description:
I'm trying to train a model on 2 years of daily data across 5 geographies.

Steps to reproduce:
1. Load media_data.csv (1M+ rows)
2. Run runner.train()

Expected: Model trains successfully
Actual: Out of memory error

Error:
JAXRuntimeError: CUDA out of memory

Configuration:
- Python 3.11
- GPU: Tesla T4 (16GB)
- Batch size: 1000
```

# API Reference

Complete reference for the Meridian MMM Platform Python API.

## Core Modules

### Data Ingestion

#### MediaDataLoader

```python
from meridian_platform.data_ingestion.media import MediaDataLoader

loader = MediaDataLoader(
    file_path: str,
    date_column: str = 'date',
    geo_column: str = 'geo',
    touchpoint_column: str = 'touchpoint_name',
    metric_column: str = 'metric_value',
    spend_column: str = 'spend'
)
```

**Methods**:

- `load_and_validate()` → DataFrame
  - Load and validate media data
  - Returns: Validated pandas DataFrame

- `get_touchpoints()` → List[str]
  - Get list of unique marketing touchpoints

- `get_geos()` → List[str]
  - Get list of unique geographies

- `get_date_range()` → Tuple[datetime, datetime]
  - Get min and max dates in dataset

**Example**:
```python
media_loader = MediaDataLoader(
    file_path='data/raw/media_data.csv',
    date_column='date',
    geo_column='geo'
)
media_df = media_loader.load_and_validate()
touchpoints = media_loader.get_touchpoints()
```

#### SalesDataLoader

```python
from meridian_platform.data_ingestion.sales import SalesDataLoader

loader = SalesDataLoader(
    file_path: str,
    date_column: str = 'date',
    geo_column: str = 'geo',
    sales_column: str = 'sales_value'
)
```

**Methods**:

- `load_and_validate()` → DataFrame
  - Load and validate sales data

- `get_date_range()` → Tuple[datetime, datetime]
  - Get min and max dates

- `get_geos()` → List[str]
  - Get unique geographies

**Example**:
```python
sales_loader = SalesDataLoader(
    file_path='data/raw/sales_data.csv'
)
sales_df = sales_loader.load_and_validate()
```

#### PriorConfigLoader

```python
from meridian_platform.data_ingestion.priors import PriorConfigLoader

loader = PriorConfigLoader(
    config_file: str
)
```

**Methods**:

- `load()` → Dict
  - Load prior configuration from YAML file

- `validate()` → bool
  - Validate prior configuration

- `get_channel_priors(channel: str)` → Dict
  - Get priors for specific channel

**Example**:
```python
prior_loader = PriorConfigLoader('config/priors_template.yaml')
priors = prior_loader.load()
tv_priors = prior_loader.get_channel_priors('TV')
```

### Modeling

#### MeridianModelRunner

```python
from meridian_platform.modeling import MeridianModelRunner

runner = MeridianModelRunner(
    media_data: pd.DataFrame,
    sales_data: pd.DataFrame,
    kpi_type: str = 'non_revenue',  # 'revenue' or 'non_revenue'
    priors: Dict = None,
    use_gpu: bool = True
)
```

**Methods**:

- `train(n_chains: int = 2, n_warmup: int = 1000, n_samples: int = 1000) → Tuple[Model, Dict]`
  - Train the Meridian model
  - Returns: Trained model object and results dictionary

- `get_diagnostics() → Dict`
  - Get model convergence diagnostics
  - Returns: Dict with R-hat, n_eff_ratio, n_divergent

- `get_posterior_predictive() → np.ndarray`
  - Generate posterior predictive samples

- `plot_posterior_predictive(predictive: np.ndarray) → None`
  - Plot posterior predictive check

- `predict_roi(allocation: Dict[str, float]) → float`
  - Predict ROI for given budget allocation
  - Returns: Expected ROI multiplier

- `predict_sales(allocation: Dict[str, float]) → float`
  - Predict sales for given allocation
  - Returns: Expected sales value

**Example**:
```python
runner = MeridianModelRunner(
    media_data=media_df,
    sales_data=sales_df,
    use_gpu=True
)
model, results = runner.train(
    n_chains=2,
    n_warmup=1000,
    n_samples=1000
)

# Check diagnostics
diagnostics = runner.get_diagnostics()
print(f"R-hat: {diagnostics['r_hat']}")

# Make predictions
roi = runner.predict_roi({'TV': 300000, 'Search': 400000})
```

### Optimization

#### BudgetOptimizer

```python
from meridian_platform.optimization import BudgetOptimizer

optimizer = BudgetOptimizer(model: Model)
```

**Methods**:

- `optimize_roi(total_budget: float, constraints: Union[str, Dict] = 'medium') → Dict`
  - Optimize budget allocation for maximum ROI
  - Returns: Dict with optimal allocation per channel

- `optimize_efficiency(target_sales: float, constraints: Union[str, Dict] = 'medium') → Dict`
  - Optimize budget to achieve target sales with minimum spend
  - Returns: Dict with minimum-cost allocation

- `get_allocation_confidence_intervals(total_budget: float, confidence: float = 0.95) → Dict`
  - Get confidence intervals for optimal allocation
  - Returns: Dict with lower/upper bounds per channel

- `get_sensitivity(allocation: Dict[str, float]) → Dict`
  - Calculate sensitivity to 10% budget shifts
  - Returns: Dict with ROI change per channel

**Example**:
```python
optimizer = BudgetOptimizer(model=model)

# ROI optimization
optimal = optimizer.optimize_roi(
    total_budget=1_000_000,
    constraints='medium'
)

# Efficiency optimization
min_cost = optimizer.optimize_efficiency(
    target_sales=5_000_000,
    constraints='medium'
)

# Sensitivity analysis
sensitivity = optimizer.get_sensitivity(optimal)
```

## Utility Functions

### Data Utilities

#### Aggregation

```python
from meridian_platform.utils import aggregate_by_period

# Aggregate to weekly level
weekly_data = aggregate_by_period(
    df=data,
    period='W',  # 'D', 'W', 'M'
    agg_column='value',
    method='sum'
)
```

#### Validation

```python
from meridian_platform.utils import validate_data

is_valid = validate_data(
    df=media_df,
    required_columns=['date', 'geo', 'touchpoint_name', 'metric_value'],
    date_column='date'
)
```

### Model Utilities

#### Posterior Summary

```python
from meridian_platform.utils import summarize_posterior

summary = summarize_posterior(
    posterior_samples=samples,
    quantiles=[0.025, 0.5, 0.975]
)
# Returns: DataFrame with mean, std, and quantiles
```

#### Effect Calculation

```python
from meridian_platform.utils import calculate_channel_effects

effects = calculate_channel_effects(
    model_output=results,
    media_data=media_df,
    sales_data=sales_df
)
# Returns: DataFrame with ROI per channel
```

## Configuration Classes

### Configuration

```python
from meridian_platform.config import Config

config = Config(config_file='config/model_defaults.yaml')

# Access config values
n_chains = config.get('model.n_chains', default=2)
gpu_enabled = config.get('model.use_gpu', default=True)
```

## Database Classes (Optional)

### DatabaseConnection

```python
from meridian_platform.database import DatabaseConnection

db = DatabaseConnection(
    host='localhost',
    port=5432,
    database='meridian_mmm',
    user='postgres',
    password='password'
)

# Save model results
db.save_model_results(
    model_name='model_v1',
    results=results,
    media_data=media_df,
    sales_data=sales_df
)

# Load previous results
results = db.load_model_results(model_name='model_v1')
```

## Type Hints

### Common Types

```python
# Type definitions used throughout API
from typing import Dict, List, Tuple, Union
import pandas as pd
import numpy as np

# Media data structure
MediaData = pd.DataFrame
# Required columns: date, geo, touchpoint_name, metric_value

# Sales data structure
SalesData = pd.DataFrame
# Required columns: date, geo, sales_value

# Budget allocation
Allocation = Dict[str, float]
# Example: {'TV': 300000, 'Search': 400000}

# Priors configuration
Priors = Dict[str, Dict[str, Dict[str, float]]]
# Nested dict with channel-specific priors

# Model results
Results = Dict[str, Union[np.ndarray, Dict, float]]
```

## Error Handling

### Common Exceptions

```python
from meridian_platform.exceptions import (
    DataValidationError,
    ModelTrainingError,
    OptimizationError,
    ConfigurationError
)

try:
    media_df = media_loader.load_and_validate()
except DataValidationError as e:
    print(f"Data validation failed: {e}")

try:
    model, results = runner.train()
except ModelTrainingError as e:
    print(f"Model training failed: {e}")

try:
    optimal = optimizer.optimize_roi(total_budget)
except OptimizationError as e:
    print(f"Optimization failed: {e}")
```

## Complete Example

### End-to-End Workflow

```python
import pandas as pd
from meridian_platform.data_ingestion.media import MediaDataLoader
from meridian_platform.data_ingestion.sales import SalesDataLoader
from meridian_platform.data_ingestion.priors import PriorConfigLoader
from meridian_platform.modeling import MeridianModelRunner
from meridian_platform.optimization import BudgetOptimizer

# 1. Load data
media_loader = MediaDataLoader('data/raw/media_data.csv')
sales_loader = SalesDataLoader('data/raw/sales_data.csv')

media_df = media_loader.load_and_validate()
sales_df = sales_loader.load_and_validate()

# 2. Load priors
prior_loader = PriorConfigLoader('config/priors_template.yaml')
priors = prior_loader.load()

# 3. Train model
runner = MeridianModelRunner(
    media_data=media_df,
    sales_data=sales_df,
    priors=priors,
    use_gpu=True
)

model, results = runner.train(
    n_chains=2,
    n_warmup=1000,
    n_samples=1000
)

# 4. Check diagnostics
diagnostics = runner.get_diagnostics()
print(f"R-hat: {diagnostics['r_hat']}")
print(f"Divergent transitions: {diagnostics['n_divergent']}")

# 5. Optimize budget
optimizer = BudgetOptimizer(model=model)

optimal_allocation = optimizer.optimize_roi(
    total_budget=1_000_000,
    constraints='medium'
)

print(f"Optimal allocation: {optimal_allocation}")

# 6. Make predictions
roi = runner.predict_roi(optimal_allocation)
sales = runner.predict_sales(optimal_allocation)

print(f"Expected ROI: {roi:.2f}x")
print(f"Expected sales: ${sales:,.0f}")
```

## Versions

### Version History

- **v0.1.0** - Initial release
  - Data ingestion for media and sales
  - Meridian model training
  - Basic budget optimization
  - Streamlit UI

### Compatibility

- **Python**: 3.11, 3.12
- **JAX**: 0.4.0+
- **Pandas**: 1.5+
- **NumPy**: 1.20+

## Additional Resources

- [Data Preparation Guide](data_preparation.md)
- [Model Configuration Guide](model_configuration.md)
- [Optimization Guide](optimization.md)
- [Troubleshooting Guide](troubleshooting.md)
- [Google Meridian Documentation](https://developers.google.com/meridian)

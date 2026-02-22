# Model Configuration Guide

How to configure the Bayesian Marketing Mix Model for your specific business needs.

## Configuration Overview

The Meridian MMM Platform uses Bayesian hierarchical models to estimate marketing effectiveness. Model configuration involves:

1. **Defining Priors** - Prior beliefs about channel effects
2. **Setting Hyperparameters** - Model training parameters
3. **Choosing Model Type** - Revenue vs. non-revenue KPI
4. **Configuring Adstock** - Lagged media effects
5. **Setting Saturation** - Diminishing returns parameters

## Configuration Files

### Location
All configuration files are in the `config/` directory:

```
config/
├── database.yaml          # Database connection settings
├── model_defaults.yaml    # Default model hyperparameters
├── priors_template.yaml   # Bayesian prior templates
└── optimization.yaml      # Optimization constraints
```

## Prior Configuration

### Understanding Priors

**Priors** represent your prior beliefs about marketing effectiveness before seeing data:

- **ROI Priors**: Expected return on investment per channel
- **Saturation**: How diminishing returns affect each channel
- **Adstock**: How long media effects persist
- **Bounds**: Minimum and maximum realistic values

### Prior Template Structure

```yaml
priors:
  channels:
    TV:
      roi_prior:
        mean: 5.0           # Expected ROI: $5 per $1 spent
        std: 2.0            # Uncertainty in estimate
      saturation_prior:
        alpha: 0.8          # Shape parameter (higher = less saturation)
        beta: 0.2           # Rate parameter
      adstock_prior:
        lag: 4              # Effect lasts ~4 weeks
        decay: 0.7          # Decay rate per week
      bounds:
        min: 0.5            # At minimum, ROI >= $0.50
        max: 15.0           # At maximum, ROI <= $15.00
    
    Search:
      roi_prior:
        mean: 3.0
        std: 1.5
      saturation_prior:
        alpha: 0.6
        beta: 0.3
      adstock_prior:
        lag: 1              # Shorter effect
        decay: 0.5
      bounds:
        min: 0.3
        max: 10.0
```

### Setting Effective Priors

#### Example 1: High-Impact Channel (e.g., TV)

```yaml
TV:
  roi_prior:
    mean: 5.0              # Expect strong effect
    std: 2.0               # But acknowledge uncertainty
  saturation_prior:
    alpha: 0.8             # Expect strong saturation
    beta: 0.2
  adstock_prior:
    lag: 6                 # Long-lasting effect
    decay: 0.8             # Slow decay
```

#### Example 2: Short-Term Channel (e.g., Search)

```yaml
Search:
  roi_prior:
    mean: 2.5              # Lower expected effect
    std: 1.0               # More confident
  saturation_prior:
    alpha: 0.5             # High saturation
    beta: 0.4
  adstock_prior:
    lag: 1                 # Very short effect
    decay: 0.3             # Fast decay
```

#### Example 3: New Channel (e.g., New Social Platform)

```yaml
TikTok:
  roi_prior:
    mean: 2.0              # Lower initial expectation
    std: 3.0               # Very high uncertainty
  saturation_prior:
    alpha: 0.5             # Assume high saturation
    beta: 0.5
  adstock_prior:
    lag: 2
    decay: 0.5
```

## Model Hyperparameters

### Default Model Configuration

```yaml
model:
  kpi_type: 'non_revenue'   # or 'revenue'
  
  # MCMC Sampling
  n_chains: 2               # Number of parallel chains
  n_warmup: 1000            # Burn-in iterations
  n_samples: 1000           # Post-warmup samples
  
  # Adstock Configuration
  adstock_type: 'geometric' # or 'adstock_geometric_decay'
  max_lag: 13               # Maximum weeks of lagged effect
  
  # Saturation
  saturation_type: 'geometric' # or 'adstock_geometric_decay'
  
  # Regularization
  regularization_strength: 0.1
  
  # Computational
  use_gpu: true             # Use GPU acceleration
  seed: 42                  # Reproducibility
```

### Adjusting Hyperparameters

#### For Faster Training
```yaml
model:
  n_chains: 1               # Single chain
  n_warmup: 500             # Fewer iterations
  n_samples: 500
  use_gpu: true
```

#### For More Accurate Results
```yaml
model:
  n_chains: 4               # More chains for convergence check
  n_warmup: 2000            # More burn-in
  n_samples: 2000           # More post-warmup samples
  use_gpu: true
```

#### For Memory-Constrained Environment
```yaml
model:
  n_chains: 1
  n_warmup: 500
  n_samples: 500
  use_gpu: false            # Use CPU instead
```

## Model Type Selection

### Revenue KPI Models

Use when modeling direct revenue impact:

```yaml
model:
  kpi_type: 'revenue'
  target_metric: 'sales_value'  # Column name in sales data
```

**Best for:**
- E-commerce businesses
- Direct response marketing
- B2C companies with measurable conversions

### Non-Revenue KPI Models

Use when modeling indirect metrics:

```yaml
model:
  kpi_type: 'non_revenue'
  target_metric: 'brand_awareness'  # Your KPI column
```

**Best for:**
- Brand awareness campaigns
- Lead generation
- Customer acquisition funnels
- Multi-stage customer journeys

## Adstock Configuration

### Understanding Adstock

**Adstock** represents lagged media effects - how spending in one period affects outcomes in future periods.

### Geometric Adstock

```yaml
adstock:
  type: 'geometric'
  
  # Per-channel configuration
  channels:
    TV:
      lag: 8                # Effect spreads over 8 weeks
      decay: 0.8            # Decay rate
      
    Search:
      lag: 1                # Immediate effect
      decay: 0.5
      
    Display:
      lag: 3
      decay: 0.6
```

#### Interpretation
- **lag**: How many time periods the effect spreads over
- **decay**: How fast it decays (0-1, where 1 = no decay)

#### Effect Calculation
```
Effect(t) = spend(t) * decay^0 +
            spend(t-1) * decay^1 +
            spend(t-2) * decay^2 + ...
```

## Saturation Configuration

### Understanding Saturation

**Saturation** represents diminishing returns - each additional dollar spent has less impact than the previous dollar.

### Saturation Parameters

```yaml
saturation:
  type: 'geometric'
  
  channels:
    TV:
      alpha: 0.8            # Lower saturation (linear-like)
      beta: 0.2             # Curve shape
      
    Search:
      alpha: 0.5            # Higher saturation (curves quickly)
      beta: 0.4
```

#### Interpretation
- **alpha** closer to 1: Linear response (low saturation)
- **alpha** closer to 0: Curved response (high saturation)

## Advanced Configuration

### Multi-Geo Models

```yaml
model:
  geo_level: 'dma'          # or 'state', 'national'
  
  # Hierarchical priors
  geo_hierarchy:
    variance_ratio: 0.3     # Between-geo variance
    national_effect: true   # Share information nationally
```

### Time-Varying Effects

```yaml
model:
  time_varying: true
  
  # Allowed period changes
  change_points:
    - date: '2024-01-01'
      description: 'Campaign launch'
    - date: '2024-06-01'
      description: 'Market shift'
```

### Custom Constraints

```yaml
optimization:
  constraints:
    TV:
      min_spend: 100000     # Minimum weekly spend
      max_spend: 500000     # Maximum weekly spend
    
    Search:
      min_spend: 50000
      max_spend: 200000
```

## Python API Configuration

### Programmatic Configuration

```python
from meridian_platform.modeling import MeridianModelRunner
from meridian_platform.data_ingestion.priors import PriorConfigLoader

# Load priors from file
prior_loader = PriorConfigLoader('config/priors_template.yaml')
priors = prior_loader.load()

# Override specific priors programmatically
priors['TV']['roi_prior']['mean'] = 6.0

# Initialize model with custom config
runner = MeridianModelRunner(
    media_data=media_data,
    sales_data=sales_data,
    kpi_type='revenue',
    priors=priors,
    n_chains=2,
    n_warmup=1000,
    n_samples=1000,
    use_gpu=True
)

# Train model
model, results = runner.train()
```

### Configuration Priority

1. **Command-line arguments** (highest priority)
2. **Programmatic overrides** (Python API)
3. **Configuration files** (YAML)
4. **Defaults** (built-in, lowest priority)

## Model Diagnostics

### Convergence Checks

```python
diagnostics = runner.get_diagnostics()

# Gelman-Rubin statistic (should be < 1.1)
print(f"R-hat: {diagnostics['r_hat']}")

# Effective sample size ratio
print(f"n_eff/n: {diagnostics['n_eff_ratio']}")

# Divergences
print(f"Divergent transitions: {diagnostics['n_divergent']}")
```

### Posterior Predictive Check

```python
# Validate model fit
posterior_predictive = runner.get_posterior_predictive()
runner.plot_posterior_predictive(posterior_predictive)
```

## Configuration Examples

### Quick Start Configuration

```yaml
# Good for first models
model:
  n_chains: 2
  n_warmup: 1000
  n_samples: 1000
  use_gpu: true

priors:
  channels:
    TV:
      roi_prior:
        mean: 3.0
        std: 2.0
```

### Production Configuration

```yaml
# For reliable business decisions
model:
  n_chains: 4
  n_warmup: 2000
  n_samples: 2000
  use_gpu: true
  time_varying: false  # Simpler for stability

priors:
  channels:
    TV:
      roi_prior:
        mean: 4.0
        std: 1.5
```

## Troubleshooting Configuration

### Issue: Model won't converge

**Solution**: Increase iterations or adjust priors
```yaml
model:
  n_warmup: 2000
  n_samples: 2000

# Tighten priors
priors:
  channels:
    TV:
      roi_prior:
        std: 1.0  # Reduced from 2.0
```

### Issue: Out of memory

**Solution**: Reduce data size or use CPU
```yaml
model:
  use_gpu: false  # Use CPU
  n_chains: 1     # Single chain
```

## Next Steps

1. **Create your priors** using `config/priors_template.yaml`
2. **Train the model** with initial configuration
3. **Check diagnostics** for convergence
4. **Adjust priors** based on results if needed
5. **Run optimization** (see [Optimization Guide](optimization.md))

## Resources

- [Google Meridian Documentation](https://developers.google.com/meridian)
- [Bayesian Methods Primer](https://en.wikipedia.org/wiki/Bayesian_inference)
- [Configuration Template](../config/priors_template.yaml)

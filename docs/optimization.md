# Budget Optimization Guide

How to use the Meridian MMM Platform to optimize your media budget allocation for maximum ROI and efficiency.

## Optimization Overview

The platform provides multiple optimization strategies:

1. **ROI Maximization** - Allocate budget to maximize total return
2. **Efficiency Optimization** - Achieve target sales with minimum spend
3. **Constrained Optimization** - Respect minimum/maximum spend limits
4. **What-If Scenarios** - Test hypothetical budget changes

## Quick Start

### Basic ROI Optimization

```python
from meridian_platform.optimization import BudgetOptimizer

# Initialize optimizer with trained model
optimizer = BudgetOptimizer(model=model)

# Get ROI-optimal allocation
optimal_budget = optimizer.optimize_roi(
    total_budget=1_000_000,      # Total budget available
    constraints='medium'          # 'small', 'medium', 'unconstrained'
)

print(optimal_budget)
# Output: {'TV': 400000, 'Search': 350000, 'Social': 250000}
```

## Optimization Strategies

### 1. Maximize ROI

Allocate budget to maximize total return on investment.

```python
# ROI Optimization
roi_optimal = optimizer.optimize_roi(
    total_budget=1_000_000,
    constraints='medium'
)

# Results
for channel, budget in roi_optimal.items():
    print(f"{channel}: ${budget:,.0f}")
```

**Use case**: When goal is to maximize profit/revenue

**Assumptions**:
- Past channel effectiveness persists
- No strategic need for balanced spend
- Can shift budget dramatically between channels

### 2. Minimize Cost

Achieve target sales with minimum spend.

```python
# Efficiency Optimization
min_cost = optimizer.optimize_efficiency(
    target_sales=50_000_000,       # Target revenue
    constraints='medium'
)

print(f"Minimum spend to reach target: ${sum(min_cost.values()):,.0f}")
```

**Use case**: When target sales level is fixed

**Assumptions**:
- Must achieve specific revenue goal
- Want to minimize costs
- Revenue prediction is accurate

### 3. Constrained Optimization

Respect minimum and maximum spend limits per channel.

```python
# Define constraints
constraints = {
    'TV': {'min': 100000, 'max': 500000},
    'Search': {'min': 50000, 'max': 300000},
    'Social': {'min': 25000, 'max': 150000},
}

# Optimize with constraints
constrained = optimizer.optimize_roi(
    total_budget=1_000_000,
    constraints=constraints
)
```

**Use case**: Realistic business constraints

**Common constraints**:
- Media contracts requiring minimum spend
- Platform minimums for ad systems
- Strategic importance of channels
- Team capacity limits

### 4. What-If Analysis

Analyze impact of hypothetical budget changes.

```python
# Compare current vs. proposed allocation
current_allocation = {
    'TV': 300000,
    'Search': 400000,
    'Social': 300000
}

proposed_allocation = {
    'TV': 250000,
    'Search': 500000,
    'Social': 250000
}

# Get predictions for each
current_roi = model.predict_roi(current_allocation)
proposed_roi = model.predict_roi(proposed_allocation)

print(f"Current ROI: ${current_roi:,.0f}")
print(f"Proposed ROI: ${proposed_roi:,.0f}")
print(f"Difference: ${proposed_roi - current_roi:,.0f}")
```

## Constraint Types

### Constraint Levels

#### Small Constraints
Allow 20-30% shift from current allocation
```python
constraints='small'
# Internally: min=0.7*current, max=1.3*current
```

#### Medium Constraints
Allow 50% shift from current allocation
```python
constraints='medium'
# Internally: min=0.5*current, max=1.5*current
```

#### Unconstrained
Allow free allocation
```python
constraints='unconstrained'
# Internally: min=0, max=total_budget
```

### Custom Constraints

```python
# Define custom bounds
custom_constraints = {
    'TV': {
        'min': 100000,           # Minimum spend
        'max': 600000,           # Maximum spend
        'current': 300000        # Current spend (reference)
    },
    'Search': {
        'min': 50000,
        'max': 400000,
        'current': 400000
    },
    'Social': {
        'min': 25000,
        'max': 200000,
        'current': 300000,
        'required': True         # Must include
    },
    'Display': {
        'min': 0,
        'max': 150000,
        'current': 0,
        'required': False        # Optional channel
    }
}

# Optimize with custom constraints
result = optimizer.optimize_roi(
    total_budget=1_000_000,
    constraints=custom_constraints
)
```

## Advanced Optimization Techniques

### Multi-Period Optimization

Optimize budget allocation across multiple time periods.

```python
# Optimize for Q1, Q2, Q3, Q4
periods = ['Q1', 'Q2', 'Q3', 'Q4']
quarterly_budget = 4_000_000

optimized_allocation = {}
for period in periods:
    # Filter model for period
    period_model = model.filter_by_period(period)
    
    # Optimize for period
    period_optimizer = BudgetOptimizer(model=period_model)
    optimized_allocation[period] = period_optimizer.optimize_roi(
        total_budget=quarterly_budget / 4
    )
```

### Scenario Analysis

Compare multiple allocation strategies.

```python
# Define scenarios
scenarios = {
    'Current': {'TV': 300000, 'Search': 400000, 'Social': 300000},
    'Conservative': {'TV': 250000, 'Search': 350000, 'Social': 400000},
    'Aggressive Search': {'TV': 200000, 'Search': 500000, 'Social': 300000},
    'Balanced': {'TV': 333333, 'Search': 333333, 'Social': 333334},
}

# Evaluate each scenario
results = {}
for scenario_name, allocation in scenarios.items():
    roi = model.predict_roi(allocation)
    sales = model.predict_sales(allocation)
    roi_per_dollar = roi / sum(allocation.values())
    
    results[scenario_name] = {
        'total_roi': roi,
        'total_sales': sales,
        'roi_efficiency': roi_per_dollar
    }

# Print comparison
import pandas as pd
df_results = pd.DataFrame(results).T
print(df_results)
```

### Geographic Optimization

Optimize budget allocation across geographies.

```python
# Define geo-specific optimization
geos = ['New York', 'Los Angeles', 'Chicago']
national_budget = 1_000_000

geo_allocation = {}
for geo in geos:
    # Filter data for geography
    geo_model = model.filter_by_geo(geo)
    geo_budget = national_budget / len(geos)
    
    # Optimize for geo
    optimizer = BudgetOptimizer(model=geo_model)
    geo_allocation[geo] = optimizer.optimize_roi(
        total_budget=geo_budget
    )
```

## Interpreting Optimization Results

### Output Format

```python
optimal_allocation = {
    'TV': 400000,
    'Search': 350000,
    'Social': 250000,
    'metadata': {
        'expected_roi': 4.8,        # Expected ROI multiplier
        'expected_sales': 4800000,
        'total_spend': 1000000,
        'roi_per_dollar': 4.80
    }
}
```

### Key Metrics

| Metric | Interpretation |
|--------|---|
| **ROI Multiplier** | $4.80 per $1 spent = 4.8x return |
| **Expected Sales** | Predicted revenue from optimized allocation |
| **ROI per Dollar** | Efficiency metric for comparing allocations |
| **Channel Contribution** | Each channel's share of total ROI |

### Sensitivity Analysis

Understand how sensitive results are to changes.

```python
# Sensitivity to 10% budget change
sensitivity = {}
for channel in ['TV', 'Search', 'Social']:
    # Increase budget by 10%
    modified = optimal_allocation.copy()
    modified[channel] *= 1.1
    
    # Decrease by 10% elsewhere
    remaining = sum(modified.values()) - 1_000_000
    for other in ['TV', 'Search', 'Social']:
        if other != channel and modified[other] > remaining:
            modified[other] -= remaining / 2
    
    roi_change = model.predict_roi(modified) / \
                 model.predict_roi(optimal_allocation) - 1
    
    sensitivity[channel] = roi_change

print("10% shift sensitivity:")
for channel, change in sensitivity.items():
    print(f"{channel}: {change:.2%} ROI change")
```

## Configuration

### Optimization Settings

```yaml
# config/optimization.yaml
optimization:
  method: 'scipy'              # Optimization algorithm
  max_iterations: 1000
  tolerance: 1e-6
  
  # Channel-specific settings
  channels:
    TV:
      elasticity: 0.8          # Typical elasticity
      min_spend: 100000
      max_spend: 600000
    
    Search:
      elasticity: 0.7
      min_spend: 50000
      max_spend: 400000
```

### Performance Tuning

```python
# Faster optimization (less accurate)
fast_result = optimizer.optimize_roi(
    total_budget=1_000_000,
    method='fast',
    precision='low'
)

# Slow optimization (more accurate)
accurate_result = optimizer.optimize_roi(
    total_budget=1_000_000,
    method='thorough',
    precision='high'
)
```

## Implementation Guide

### Step 1: Train Model

```python
from meridian_platform.modeling import MeridianModelRunner

runner = MeridianModelRunner(
    media_data=media_data,
    sales_data=sales_data,
    use_gpu=True
)
model, results = runner.train()
```

### Step 2: Initialize Optimizer

```python
from meridian_platform.optimization import BudgetOptimizer

optimizer = BudgetOptimizer(model=model)
```

### Step 3: Define Budget and Constraints

```python
total_budget = 1_000_000
constraints = {
    'TV': {'min': 100000, 'max': 600000},
    'Search': {'min': 50000, 'max': 400000},
    'Social': {'min': 25000, 'max': 200000}
}
```

### Step 4: Run Optimization

```python
optimal_allocation = optimizer.optimize_roi(
    total_budget=total_budget,
    constraints=constraints
)
```

### Step 5: Validate and Implement

```python
# Validate results
print(f"Total budget: ${sum(optimal_allocation.values()):,.0f}")
print(f"Expected ROI: ${model.predict_roi(optimal_allocation):,.0f}")

# Compare to current
current = {'TV': 300000, 'Search': 400000, 'Social': 300000}
lift = model.predict_roi(optimal_allocation) / \
       model.predict_roi(current)
print(f"Expected lift: {lift:.1%}")
```

## Common Pitfalls

### Pitfall 1: Over-trusting Model

**Issue**: Optimization recommends 100% in one channel

**Solution**: 
- Add minimum spend constraints for all channels
- Consider strategic value beyond ROI
- Validate against business constraints

### Pitfall 2: Ignoring Uncertainty

**Issue**: Allocating based on point estimates

**Solution**:
```python
# Get confidence intervals
ci = optimizer.get_allocation_confidence_intervals(
    total_budget=1_000_000,
    confidence=0.95
)
```

### Pitfall 3: Forgetting Time Lag

**Issue**: Assuming immediate ROI from media

**Solution**:
- Use adstocked media effects
- Allow time for effects to materialize
- Monitor lagged conversions

## Troubleshooting

### Issue: Optimization takes too long

**Solution**:
```python
# Use faster algorithm
result = optimizer.optimize_roi(
    total_budget=1_000_000,
    method='approximate'
)
```

### Issue: Results seem unrealistic

**Solution**:
```python
# Add tighter constraints
constraints = {
    channel: {
        'min': current[channel] * 0.8,
        'max': current[channel] * 1.2
    }
    for channel in current.keys()
}
```

## Next Steps

1. **[Prepare your data](data_preparation.md)** - Format media and sales data
2. **[Configure your model](model_configuration.md)** - Set up priors
3. **Train your model** - Run Streamlit app or Python API
4. **Run optimization** - Generate optimal allocations
5. **Validate results** - Check feasibility and business logic
6. **Implement changes** - Update media plans

## Resources

- [Google Meridian Optimization](https://developers.google.com/meridian/docs/optimization)
- [API Reference](api_reference.md)
- [Troubleshooting Guide](troubleshooting.md)

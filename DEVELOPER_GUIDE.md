# Developer Guide - Building the Remaining Components

This guide provides detailed instructions for implementing the remaining Phase 1 components.

## Table of Contents
1. [Modeling Module](#1-modeling-module)
2. [Optimization Module](#2-optimization-module)
3. [Database Module](#3-database-module)
4. [Streamlit UI](#4-streamlit-ui)
5. [Demo Notebook](#5-demo-notebook)
6. [Testing](#6-testing)

---

## 1. Modeling Module

### File: `src/meridian_platform/modeling/model_runner.py`

This is the core module that wraps Google Meridian's model training.

### Key Meridian Imports

```python
from meridian import model, spec
from meridian.data import data_frame_input_data_builder
from meridian.data import input_data
import xarray as xr
```

### Implementation Steps

#### Step 1.1: Data Preparation

Convert our standardized format to Meridian's `InputData`:

```python
def prepare_meridian_input(self):
    """
    Convert standardized DataFrames to Meridian InputData.
    """
    # Merge media and sales on date and geo
    merged = self.media_data.merge(
        self.sales_data, 
        on=['date', 'geo'], 
        how='inner'
    )
    
    # Use DataFrameInputDataBuilder
    builder = data_frame_input_data_builder.DataFrameInputDataBuilder(
        kpi_type='non_revenue',  # or 'revenue'
        default_kpi_column='sales_value'
    )
    
    # Add KPI data
    builder = builder.with_kpi(merged)
    
    # Add media data
    channels = self.media_data['touchpoint_name'].unique().tolist()
    
    # Pivot media data to wide format
    media_wide = self.media_data.pivot_table(
        index=['date', 'geo'],
        columns='touchpoint_name',
        values='metric_value',
        fill_value=0.0
    ).reset_index()
    
    spend_wide = self.media_data.pivot_table(
        index=['date', 'geo'],
        columns='touchpoint_name',
        values='spend',
        fill_value=0.0
    ).reset_index()
    
    # Add to builder
    builder = builder.with_media(
        media_wide,
        media_cols=[f"{ch}" for ch in channels],
        media_spend_cols=[f"{ch}" for ch in channels],  # Use spend_wide
        media_channels=channels
    )
    
    # Build InputData object
    return builder.build()
```

#### Step 1.2: Model Specification

Create the Meridian `ModelSpec`:

```python
def create_model_spec(self, priors_config=None):
    """
    Create Meridian ModelSpec with optional custom priors.
    """
    # Load default config
    with open('config/model_defaults.yaml') as f:
        config = yaml.safe_load(f)
    
    # Create spec
    model_spec = spec.ModelSpec(
        max_lag=config['model']['time']['max_lag'],
        n_knots=config['model']['time']['n_knots'],
        adstock_decay_spec=config['model']['time']['adstock_decay_spec']
    )
    
    # Add custom priors if provided
    if priors_config:
        channels = self.input_data.media.media_channel.values.tolist()
        prior_dict = priors_config.create_meridian_prior_dict(
            channels=channels,
            prior_type='roi'
        )
        
        if prior_dict:
            model_spec = spec.ModelSpec(
                max_lag=config['model']['time']['max_lag'],
                n_knots=config['model']['time']['n_knots'],
                prior=prior_dict  # Add custom priors
            )
    
    return model_spec
```

#### Step 1.3: Training

Train the model using MCMC:

```python
def train(self, n_warmup=1000, n_samples=1000, n_chains=2):
    """
    Train the Meridian model.
    """
    logger.info("Initializing Meridian model...")
    
    # Create model
    self.model = model.Meridian(
        input_data=self.input_data,
        model_spec=self.model_spec
    )
    
    logger.info(f"Training model with {n_warmup} warmup, {n_samples} samples, {n_chains} chains...")
    
    # Fit model
    self.model.fit(
        n_warmup=n_warmup,
        n_samples=n_samples,
        n_chains=n_chains
    )
    
    logger.success("Model training complete!")
    
    return self.model
```

### Complete Template

See the full template at the end of this document.

---

## 2. Optimization Module

### File: `src/meridian_platform/optimization/budget_optimizer.py`

This module wraps Meridian's optimizer for budget allocation.

### Key Implementation

```python
from meridian import optimizer
import yaml

class BudgetOptimizer:
    """Budget optimization using Meridian's optimizer."""
    
    def __init__(self, trained_model, config_path='config/optimization.yaml'):
        self.model = trained_model
        
        # Load constraints config
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
    
    def optimize_roi(self, total_budget, constraints='medium'):
        """Maximize ROI given budget."""
        
        # Get constraint percentages
        constraint_config = self.config['optimization']['constraints'][constraints]
        min_pct = constraint_config['min_change_pct'] / 100
        max_pct = constraint_config['max_change_pct'] / 100
        
        # Run Meridian optimizer
        result = optimizer.optimize(
            meridian=self.model,
            budget=total_budget,
            objective='maximize_roi',
            channel_bounds=(min_pct, max_pct)  # Relative to current
        )
        
        return result
```

**Key Meridian optimizer parameters:**
- `objective`: 'maximize_roi', 'minimize_cost', 'maximize_sales'
- `channel_bounds`: Tuple of (min_change, max_change) as percentages
- `budget`: Total budget constraint

---

## 3. Database Module

### Files to Create:
1. `src/meridian_platform/database/connection.py`
2. `src/meridian_platform/database/models.py`
3. `src/meridian_platform/database/crud.py`

### Step 3.1: SQLAlchemy Models

```python
# models.py
from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class MediaData(Base):
    __tablename__ = 'media_data'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    geo = Column(String(50), nullable=False)
    touchpoint_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    spend = Column(Float)
    mapping_id = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

class ModelRun(Base):
    __tablename__ = 'model_runs'
    
    id = Column(Integer, primary_key=True)
    run_name = Column(String(200))
    run_date = Column(DateTime, default=datetime.utcnow)
    config = Column(JSON)  # Store model configuration
    n_chains = Column(Integer)
    n_samples = Column(Integer)
    convergence_status = Column(String(50))
    
    # Relationship to results
    results = relationship("ModelResults", back_populates="model_run")
```

### Step 3.2: CRUD Operations

```python
# crud.py
def save_media_data(session, media_df):
    """Bulk insert media data."""
    records = media_df.to_dict('records')
    session.bulk_insert_mappings(MediaData, records)
    session.commit()
```

---

## 4. Streamlit UI

### File: `ui/streamlit_app/app.py`

### Basic Structure

```python
import streamlit as st
from meridian_platform import MediaDataLoader, SalesDataLoader, PriorsConfigLoader

st.set_page_config(page_title="Meridian MMM Platform", layout="wide")

def main():
    st.title("🎯 Meridian MMM Platform")
    
    # Sidebar navigation
    page = st.sidebar.radio(
        "Navigate",
        ["📤 Data Upload", "🎓 Train Model", "📊 Results", "💰 Optimize"]
    )
    
    if page == "📤 Data Upload":
        data_upload_page()
    elif page == "🎓 Train Model":
        model_training_page()
    elif page == "📊 Results":
        results_page()
    elif page == "💰 Optimize":
        optimization_page()

def data_upload_page():
    st.header("Data Upload & Validation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Media Data")
        media_file = st.file_uploader(
            "Upload Media CSV/Excel", 
            type=['csv', 'xlsx'],
            key='media'
        )
        
        if media_file:
            loader = MediaDataLoader(file_path=media_file)
            data = loader.load()
            
            # Validation
            results = loader.validate(data)
            
            if results['valid']:
                st.success("✓ Validation passed!")
            else:
                st.error("✗ Validation failed")
                for error in results['errors']:
                    st.error(error)
            
            # Preview
            st.dataframe(data.head())
            
            # Summary
            st.write("**Summary:**")
            st.write(loader.get_summary())
            
            # Save to session state
            st.session_state['media_data'] = data
    
    with col2:
        st.subheader("Sales Data")
        # Similar structure...

if __name__ == '__main__':
    main()
```

### Advanced Features

1. **Interactive visualizations**: Use Plotly for response curves, contributions
2. **Progress bars**: Show MCMC sampling progress
3. **Session state**: Maintain data and models across pages
4. **Download buttons**: Export results as CSV/Excel

---

## 5. Demo Notebook

### File: `notebooks/01_quickstart_demo.ipynb`

### Suggested Structure:

```markdown
# Meridian MMM Platform - Quick Start Demo

## 1. Setup
- Install requirements
- Import libraries

## 2. Load Data
- Use MediaDataLoader
- Use SalesDataLoader
- Validate data

## 3. Configure Priors
- Load priors template
- Customize for channels

## 4. Train Model
- Create MeridianModelRunner
- Configure model
- Run training
- Check convergence

## 5. Analyze Results
- View contributions
- Check ROI by channel
- Plot response curves
- Assess model fit

## 6. Optimize Budget
- Set up scenarios
- Run optimization
- Compare allocations
- Export results
```

---

## 6. Testing

### Test Structure

```
tests/
├── unit/
│   ├── test_media_loader.py
│   ├── test_sales_loader.py
│   ├── test_priors_loader.py
│   ├── test_model_runner.py
│   └── test_optimizer.py
├── integration/
│   ├── test_end_to_end.py
│   └── test_database.py
└── fixtures/
    ├── sample_media.csv
    └── sample_sales.csv
```

### Example Unit Test

```python
# test_media_loader.py
import pytest
from meridian_platform.data_ingestion.media import MediaDataLoader

def test_media_loader_basic():
    """Test basic media loading."""
    loader = MediaDataLoader(
        file_path='tests/fixtures/sample_media.csv'
    )
    data = loader.load()
    
    assert len(data) > 0
    assert 'date' in data.columns
    assert 'touchpoint_name' in data.columns

def test_media_validation_fails_on_negative():
    """Test that negative values fail validation."""
    # Create data with negative spend
    # ...
    results = loader.validate()
    assert not results['valid']
```

---

## Common Issues & Solutions

### Issue 1: GPU Not Detected

**Solution:**
```bash
# Verify CUDA
nvidia-smi

# Reinstall JAX with CUDA
pip uninstall jax jaxlib
pip install --upgrade "jax[cuda12_pip]" -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html
```

### Issue 2: Model Won't Converge

**Solutions:**
1. Increase warmup: `n_warmup=2000`
2. Check data quality: Ensure sufficient variation
3. Adjust priors: Make them less informative (higher scale)
4. Check for multicollinearity: Remove highly correlated channels

### Issue 3: Memory Issues

**Solutions:**
1. Reduce number of chains: `n_chains=1`
2. Use smaller data subset for testing
3. Reduce max_lag parameter
4. Use CPU instead of GPU for smaller models

---

## Development Workflow

1. **Start with modeling module**: Get basic model training working
2. **Add optimization**: Build on trained models
3. **Create UI incrementally**: Start with data upload, then add features
4. **Write tests as you go**: Don't wait until the end
5. **Document everything**: Update docstrings and README

---

## Next Steps After Phase 1

Once Phase 1 is complete, Phase 2 will add:

1. **Model Aggregation**: Combine models across brands/products
2. **A/B Test Integration**: Use MMM priors for uplift modeling
3. **Advanced Constraints**: Time-varying budgets, channel dependencies
4. **Automated Refresh**: Schedule model retraining
5. **API Endpoints**: REST API for programmatic access

---

**Remember**: Start simple, test early, iterate quickly. The infrastructure is in place - now bring it to life!

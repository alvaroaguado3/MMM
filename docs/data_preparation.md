# Data Preparation Guide

How to prepare your marketing and sales data for the Meridian MMM Platform.

## Data Requirements Overview

The platform requires two main datasets:
1. **Media Data** - Marketing spend, metrics, and touchpoints
2. **Sales Data** - Revenue, units, or other KPIs

Both datasets must be organized at a geographic and temporal level (typically weekly or daily).

## Data Format Specifications

### Media Data Format

Your media data should be in CSV format with the following structure:

| Column | Type | Description | Required | Example |
|--------|------|-------------|----------|---------|
| `date` | datetime | Date of observation (YYYY-MM-DD) | ✅ | 2024-01-01 |
| `geo` | string | Geographic identifier (DMA, state, country) | ✅ | "New York" |
| `touchpoint_name` | string | Marketing channel/tactic name | ✅ | "TV", "Search", "Social" |
| `metric_value` | float | Media metric (GRPs, impressions, clicks) | ✅ | 1500000 |
| `spend` | float | Media spend in currency units | ⚠️ | 50000 |
| `mapping_id` | string | Granular identifier (campaign ID) | ❌ | "CAMP_123" |

#### Media Data Example

```csv
date,geo,touchpoint_name,metric_value,spend,mapping_id
2024-01-01,New York,TV,1500000,50000,CAMP_TV_Q1
2024-01-01,New York,Search,500000,25000,CAMP_SEARCH_Q1
2024-01-01,New York,Social,300000,15000,CAMP_SOCIAL_Q1
2024-01-01,Los Angeles,TV,1200000,40000,CAMP_TV_Q1
2024-01-01,Los Angeles,Search,450000,22000,CAMP_SEARCH_Q1
2024-01-08,New York,TV,1600000,52000,CAMP_TV_Q1
```

### Sales Data Format

Your sales data should be in CSV format with this structure:

| Column | Type | Description | Required | Example |
|--------|------|-------------|----------|---------|
| `date` | datetime | Date of observation (YYYY-MM-DD) | ✅ | 2024-01-01 |
| `geo` | string | Geographic identifier | ✅ | "New York" |
| `sales_value` | float | Sales in revenue units | ✅ | 500000 |
| `sales_units` | float | Sales in unit count | ⚠️ | 1000 |
| `sales_volume` | float | Sales in volume measure | ❌ | 5000 |

#### Sales Data Example

```csv
date,geo,sales_value,sales_units,sales_volume
2024-01-01,New York,500000,1000,5000
2024-01-01,Los Angeles,450000,950,4500
2024-01-08,New York,520000,1050,5200
2024-01-08,Los Angeles,480000,1000,4800
2024-01-15,New York,550000,1100,5500
```

## Data Preparation Steps

### 1. Organize Your Data

#### Create Directory Structure
```bash
mkdir -p data/raw
# Place your raw data files here
```

#### Use Sample Data
```bash
# Generate sample data for testing
python data/sample/generate_sample_data.py

# This creates:
# - data/sample/sample_media_data.csv
# - data/sample/sample_sales_data.csv
# - data/sample/sample_population_data.csv
```

### 2. Clean and Validate Your Data

#### Check for Missing Values
```python
import pandas as pd

# Load your data
media_df = pd.read_csv('data/raw/media_data.csv')
sales_df = pd.read_csv('data/raw/sales_data.csv')

# Check missing values
print("Media data missing values:")
print(media_df.isnull().sum())

print("\nSales data missing values:")
print(sales_df.isnull().sum())
```

#### Validate Data Types
```python
from meridian_platform.data_ingestion.media import MediaDataLoader

# Validate media data
media_loader = MediaDataLoader(
    file_path='data/raw/media_data.csv',
    date_column='date',
    geo_column='geo'
)
media_data = media_loader.load_and_validate()
```

### 3. Handle Missing Data

#### Strategy Options

**Option 1: Remove missing rows** (if minimal)
```python
df_clean = df.dropna()
```

**Option 2: Forward fill** (for time series)
```python
df_clean = df.fillna(method='ffill')
```

**Option 3: Interpolate** (for continuous metrics)
```python
df_clean = df.interpolate(method='linear')
```

#### Handle Zeros
```python
# Replace zeros with small values for log-scale modeling
df['metric_value'] = df['metric_value'].replace(0, 0.1)
```

### 4. Standardize Date and Geography

#### Date Standardization
```python
# Convert to datetime
df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')

# Set consistent frequency (weekly)
df = df.set_index('date').asfreq('W').reset_index()

# Fill missing dates with forward fill
df['value'] = df['value'].fillna(method='ffill')
```

#### Geography Standardization
```python
# Ensure consistent geography naming
geo_mapping = {
    'NY': 'New York',
    'NYC': 'New York',
    'LA': 'Los Angeles',
    'CA': 'California'
}
df['geo'] = df['geo'].map(geo_mapping).fillna(df['geo'])
```

### 5. Aggregate Data (if needed)

#### Aggregate to Weekly Level
```python
weekly_data = df.groupby(['date', 'geo', 'touchpoint_name']).agg({
    'metric_value': 'sum',
    'spend': 'sum'
}).reset_index()
```

#### Aggregate Across Geographies
```python
national_data = df.groupby(['date', 'touchpoint_name']).agg({
    'metric_value': 'sum',
    'spend': 'sum'
}).reset_index()

national_data['geo'] = 'National'
```

## Data Quality Checks

### Completeness Check

```python
# Check data completeness
required_cols = ['date', 'geo', 'touchpoint_name', 'metric_value', 'sales_value']

for col in required_cols:
    if col not in df.columns:
        print(f"Missing required column: {col}")
    
    missing_pct = df[col].isnull().sum() / len(df) * 100
    print(f"{col}: {missing_pct:.2f}% missing")
```

### Time Series Continuity Check

```python
# Check for gaps in date range
dates = pd.to_datetime(df['date']).unique()
dates_sorted = sorted(dates)

expected_dates = pd.date_range(
    start=dates_sorted[0],
    end=dates_sorted[-1],
    freq='D'  # or 'W' for weekly
)

missing_dates = set(expected_dates) - set(dates_sorted)
print(f"Missing dates: {len(missing_dates)}")
```

### Outlier Detection

```python
# Identify statistical outliers
Q1 = df['metric_value'].quantile(0.25)
Q3 = df['metric_value'].quantile(0.75)
IQR = Q3 - Q1

outliers = df[(df['metric_value'] < Q1 - 1.5*IQR) | 
              (df['metric_value'] > Q3 + 1.5*IQR)]

print(f"Found {len(outliers)} outliers")
```

## Common Data Issues and Solutions

### Issue: Inconsistent Date Formats

**Problem**: Dates in format "01/01/2024" or "2024-01-01"

**Solution**:
```python
df['date'] = pd.to_datetime(df['date'], infer_datetime_format=True)
df['date'] = df['date'].dt.strftime('%Y-%m-%d')
```

### Issue: Multiple rows for same geo/touchpoint/date

**Problem**: Duplicate entries with different spend amounts

**Solution**:
```python
# Aggregate duplicates
df_agg = df.groupby(['date', 'geo', 'touchpoint_name']).agg({
    'metric_value': 'sum',
    'spend': 'sum'
}).reset_index()
```

### Issue: Negative spend values

**Problem**: Refunds or adjustments creating negative values

**Solution**:
```python
# Option 1: Remove negative values
df = df[df['spend'] >= 0]

# Option 2: Set to zero
df['spend'] = df['spend'].clip(lower=0)
```

### Issue: Very sparse data

**Problem**: Many zeros in media metrics

**Solution**:
```python
# Only keep significant touchpoints
min_spend = df['spend'].quantile(0.10)
df_filtered = df[df['spend'] >= min_spend]
```

## File Naming Conventions

Store your prepared data with these naming conventions:

```
data/raw/
├── media_data_YYYY_MM_DD.csv          # Media spend and metrics
├── sales_data_YYYY_MM_DD.csv          # Sales and KPI data
└── population_data_YYYY_MM_DD.csv     # (Optional) Geography population

data/processed/
├── media_data_clean.csv               # Cleaned and validated
└── sales_data_clean.csv               # Cleaned and validated
```

## Next Steps

1. **Prepare your data** using the steps above
2. **Load your data** using the Streamlit UI or Python API
3. **Configure the model** with appropriate priors (see [Model Configuration](model_configuration.md))
4. **Train the model** and generate insights

## Getting Help

- See [Troubleshooting Guide](troubleshooting.md) for data loading issues
- Review [API Reference](api_reference.md) for loader classes
- Check sample data: `data/sample/sample_*.csv`

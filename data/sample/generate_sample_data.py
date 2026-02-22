"""Generate sample media and sales data for testing the MMM platform."""

import pandas as pd
import numpy as np
from itertools import product

np.random.seed(42)

# --- Configuration ---
start_date = "2023-01-01"
end_date = "2024-12-31"  # 2 years of daily data
geos = [f"DMA_{str(i).zfill(3)}" for i in range(1, 11)]  # 10 geos

channels = {
    "TV_National": {"base_spend": 15000, "metric_type": "GRPs", "base_metric": 50},
    "Search_Brand": {"base_spend": 8000, "metric_type": "clicks", "base_metric": 1200},
    "Search_Generic": {"base_spend": 6000, "metric_type": "clicks", "base_metric": 800},
    "Facebook": {"base_spend": 5000, "metric_type": "impressions", "base_metric": 35000},
    "Instagram": {"base_spend": 3500, "metric_type": "impressions", "base_metric": 25000},
    "YouTube": {"base_spend": 4000, "metric_type": "impressions", "base_metric": 20000},
    "Display": {"base_spend": 2500, "metric_type": "impressions", "base_metric": 50000},
    "Email": {"base_spend": 500, "metric_type": "sends", "base_metric": 10000},
}

dates = pd.date_range(start=start_date, end=end_date, freq="D")

# --- Generate Media Data ---
media_rows = []

for date in dates:
    day_of_week = date.dayofweek
    month = date.month

    # Seasonality multiplier (higher in Q4, lower in Q1)
    seasonal = 1.0 + 0.3 * np.sin(2 * np.pi * (month - 1) / 12 - np.pi / 3)

    # Weekend effect (lower spend on weekends for some channels)
    weekend = 1.0 if day_of_week < 5 else 0.6

    for geo in geos:
        # Geo-level scale factor (some geos are bigger markets)
        geo_scale = 0.5 + 1.5 * (int(geo.split("_")[1]) / 10)

        for channel, cfg in channels.items():
            # Some channels don't run on weekends
            if channel in ("Email",) and day_of_week >= 5:
                continue

            noise = np.random.lognormal(0, 0.15)
            spend_mult = seasonal * (weekend if channel != "TV_National" else 1.0) * geo_scale * noise
            spend = round(cfg["base_spend"] * spend_mult, 2)
            metric = round(cfg["base_metric"] * spend_mult * np.random.lognormal(0, 0.1), 2)

            media_rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "geo": geo,
                "touchpoint_name": channel,
                "metric_value": metric,
                "spend": spend,
            })

media_df = pd.DataFrame(media_rows)

# --- Generate Sales Data ---
# Sales are driven by a baseline + media effects + noise
sales_rows = []

for date in dates:
    month = date.month
    day_of_week = date.dayofweek

    # Seasonal baseline
    seasonal = 1.0 + 0.4 * np.sin(2 * np.pi * (month - 1) / 12 - np.pi / 3)

    # Weekend boost for sales
    weekend_boost = 1.15 if day_of_week >= 5 else 1.0

    for geo in geos:
        geo_idx = int(geo.split("_")[1])
        geo_scale = 0.5 + 1.5 * (geo_idx / 10)

        # Base sales
        base_sales = 50000 * geo_scale * seasonal * weekend_boost

        # Media contribution (simplified): sum of spend for this geo/date
        geo_media = media_df[(media_df["date"] == date.strftime("%Y-%m-%d")) & (media_df["geo"] == geo)]
        media_effect = geo_media["spend"].sum() * 0.08  # ~8% of spend converts to revenue

        # Random noise
        noise = np.random.normal(1.0, 0.05)

        sales_value = round(max(0, (base_sales + media_effect) * noise), 2)
        sales_units = int(sales_value / np.random.uniform(45, 55))  # avg price ~$50/unit

        sales_rows.append({
            "date": date.strftime("%Y-%m-%d"),
            "geo": geo,
            "sales_value": sales_value,
            "sales_units": sales_units,
        })

sales_df = pd.DataFrame(sales_rows)

# --- Generate Population Data (one row per geo) ---
population_rows = []
base_populations = [500000, 750000, 1000000, 1250000, 1500000, 1750000, 2000000, 2250000, 2500000, 2750000]
for i, geo in enumerate(geos):
    population_rows.append({"geo": geo, "population": base_populations[i]})

population_df = pd.DataFrame(population_rows)

# --- Save ---
media_df.to_csv("data/sample/sample_media_data.csv", index=False)
sales_df.to_csv("data/sample/sample_sales_data.csv", index=False)
population_df.to_csv("data/sample/sample_population_data.csv", index=False)

print(f"Media data: {media_df.shape[0]:,} rows, {media_df['touchpoint_name'].nunique()} channels, "
      f"{media_df['geo'].nunique()} geos, {media_df['date'].nunique()} days")
print(f"Sales data: {sales_df.shape[0]:,} rows, {sales_df['geo'].nunique()} geos, "
      f"{sales_df['date'].nunique()} days")
print(f"\nMedia columns: {list(media_df.columns)}")
print(f"Sales columns: {list(sales_df.columns)}")
print(f"\nDate range: {media_df['date'].min()} to {media_df['date'].max()}")
print(f"\nMedia spend summary by channel:")
print(media_df.groupby('touchpoint_name')['spend'].agg(['sum', 'mean']).round(2).to_string())
print(f"\nSales summary by geo:")
print(sales_df.groupby('geo')['sales_value'].agg(['sum', 'mean']).round(2).to_string())
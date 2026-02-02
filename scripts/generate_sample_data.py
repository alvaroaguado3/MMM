"""
Generate Sample Data for Testing

This script creates synthetic media and sales data for testing the platform.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Set random seed for reproducibility
np.random.seed(42)

def generate_sample_data():
    """Generate sample media and sales data."""
    
    # Configuration
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    geos = ['DMA_1', 'DMA_2', 'DMA_3', 'DMA_4', 'DMA_5']
    touchpoints = ['TV', 'Search_Brand', 'Search_Generic', 'Facebook', 'YouTube', 'Display']
    
    # Generate date range
    dates = pd.date_range(start=start_date, end=end_date, freq='W-MON')
    
    print(f"Generating data for {len(dates)} weeks, {len(geos)} geos, {len(touchpoints)} touchpoints...")
    
    # Generate media data
    media_data = []
    
    for geo in geos:
        for date in dates:
            for touchpoint in touchpoints:
                # Base metrics with some randomness and seasonality
                week_of_year = date.isocalendar()[1]
                seasonality = 1 + 0.3 * np.sin(2 * np.pi * week_of_year / 52)
                
                # Different channels have different spending patterns
                if touchpoint == 'TV':
                    base_metric = 50000 * seasonality
                    base_spend = 25000 * seasonality
                elif touchpoint.startswith('Search'):
                    base_metric = 100000 * seasonality
                    base_spend = 15000 * seasonality
                elif touchpoint in ['Facebook', 'YouTube']:
                    base_metric = 200000 * seasonality
                    base_spend = 10000 * seasonality
                else:  # Display
                    base_metric = 300000 * seasonality
                    base_spend = 5000 * seasonality
                    
                # Add randomness
                metric_value = max(0, base_metric * np.random.lognormal(0, 0.3))
                spend = max(0, base_spend * np.random.lognormal(0, 0.2))
                
                # Sometimes zero (no campaign running)
                if np.random.random() < 0.15:  # 15% chance of no activity
                    metric_value = 0
                    spend = 0
                    
                media_data.append({
                    'date': date,
                    'geo': geo,
                    'touchpoint_name': touchpoint,
                    'metric_value': metric_value,
                    'spend': spend,
                    'mapping_id': f"{touchpoint}_{geo}_{date.strftime('%Y%m')}"
                })
                
    media_df = pd.DataFrame(media_data)
    
    # Generate sales data with media influence
    sales_data = []
    
    # Aggregate media by geo and date for sales calculation
    media_agg = media_df.groupby(['date', 'geo']).agg({
        'metric_value': 'sum',
        'spend': 'sum'
    }).reset_index()
    
    # True ROIs for each channel (for validation)
    true_rois = {
        'TV': 0.20,
        'Search_Brand': 1.50,
        'Search_Generic': 0.50,
        'Facebook': 0.35,
        'YouTube': 0.25,
        'Display': 0.10
    }
    
    for geo in geos:
        # Base sales level varies by geo
        geo_index = geos.index(geo)
        base_sales = 100000 * (1 + 0.2 * geo_index)
        
        for date in dates:
            # Seasonality effect
            week_of_year = date.isocalendar()[1]
            seasonality = 1 + 0.4 * np.sin(2 * np.pi * week_of_year / 52 - np.pi/2)
            
            # Media contribution
            geo_media = media_df[(media_df['date'] == date) & (media_df['geo'] == geo)]
            media_contrib = 0
            
            for _, row in geo_media.iterrows():
                touchpoint = row['touchpoint_name']
                spend = row['spend']
                roi = true_rois.get(touchpoint, 0.15)
                
                # Adstock effect (carryover from previous weeks)
                if spend > 0:
                    media_contrib += spend * roi
                    
            # Calculate sales
            sales_value = (
                base_sales * seasonality +
                media_contrib +
                np.random.normal(0, base_sales * 0.05)  # Noise
            )
            
            sales_value = max(0, sales_value)  # No negative sales
            
            # Units (assuming avg price of $50)
            sales_units = sales_value / 50
            
            sales_data.append({
                'date': date,
                'geo': geo,
                'sales_value': sales_value,
                'sales_units': sales_units
            })
            
    sales_df = pd.DataFrame(sales_data)
    
    return media_df, sales_df


def save_sample_data():
    """Generate and save sample data to files."""
    
    # Create output directory
    output_dir = Path('data/sample')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    media_df, sales_df = generate_sample_data()
    
    # Save to CSV
    media_path = output_dir / 'sample_media_data.csv'
    sales_path = output_dir / 'sample_sales_data.csv'
    
    media_df.to_csv(media_path, index=False)
    sales_df.to_csv(sales_path, index=False)
    
    print(f"\nSample data generated:")
    print(f"  Media data: {media_path} ({len(media_df):,} rows)")
    print(f"  Sales data: {sales_path} ({len(sales_df):,} rows)")
    
    # Print summary statistics
    print(f"\nMedia Data Summary:")
    print(f"  Date range: {media_df['date'].min()} to {media_df['date'].max()}")
    print(f"  Geos: {media_df['geo'].nunique()}")
    print(f"  Touchpoints: {', '.join(media_df['touchpoint_name'].unique())}")
    print(f"  Total spend: ${media_df['spend'].sum():,.0f}")
    print(f"  Total impressions: {media_df['metric_value'].sum():,.0f}")
    
    print(f"\nSales Data Summary:")
    print(f"  Date range: {sales_df['date'].min()} to {sales_df['date'].max()}")
    print(f"  Total sales: ${sales_df['sales_value'].sum():,.0f}")
    print(f"  Total units: {sales_df['sales_units'].sum():,.0f}")
    print(f"  Average weekly sales per geo: ${sales_df.groupby('geo')['sales_value'].mean().mean():,.0f}")
    
    # Save Excel versions for easier manual inspection
    media_excel = output_dir / 'sample_media_data.xlsx'
    sales_excel = output_dir / 'sample_sales_data.xlsx'
    
    media_df.to_excel(media_excel, index=False)
    sales_df.to_excel(sales_excel, index=False)
    
    print(f"\nExcel versions also saved:")
    print(f"  {media_excel}")
    print(f"  {sales_excel}")


if __name__ == '__main__':
    save_sample_data()

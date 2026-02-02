"""
Sales Data Ingestion Module

This module handles loading and validating sales/KPI data.
It standardizes the format for use with the Meridian model.

Standard Format:
- date: datetime (YYYY-MM-DD)
- geo: string (geographic identifier)
- sales_value: float (sales revenue or other KPI)
- sales_units: float (optional, unit count)
- sales_volume: float (optional, volume measure)
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Union
from pathlib import Path
from loguru import logger
import xarray as xr


class SalesDataLoader:
    """Load and validate sales/KPI data for Meridian modeling."""
    
    # Required columns
    REQUIRED_COLUMNS = ['date', 'geo', 'sales_value']
    
    # Optional columns
    OPTIONAL_COLUMNS = ['sales_units', 'sales_volume']
    
    # Expected data types
    COLUMN_TYPES = {
        'date': 'datetime64[ns]',
        'geo': 'str',
        'sales_value': 'float',
        'sales_units': 'float',
        'sales_volume': 'float'
    }
    
    def __init__(
        self,
        file_path: Optional[Union[str, Path]] = None,
        dataframe: Optional[pd.DataFrame] = None,
        date_column: str = 'date',
        geo_column: str = 'geo',
        value_column: str = 'sales_value',
        units_column: Optional[str] = 'sales_units',
        volume_column: Optional[str] = 'sales_volume'
    ):
        """
        Initialize Sales Data Loader.
        
        Args:
            file_path: Path to CSV/Excel file
            dataframe: Pandas DataFrame (alternative to file_path)
            date_column: Name of date column
            geo_column: Name of geo column
            value_column: Name of sales value/revenue column
            units_column: Name of units column (optional)
            volume_column: Name of volume column (optional)
        """
        self.file_path = Path(file_path) if file_path else None
        self.dataframe = dataframe
        
        # Column mappings
        self.column_mapping = {
            'date': date_column,
            'geo': geo_column,
            'sales_value': value_column
        }
        
        if units_column:
            self.column_mapping['sales_units'] = units_column
        if volume_column:
            self.column_mapping['sales_volume'] = volume_column
            
        self.data: Optional[pd.DataFrame] = None
        self.validation_results: Dict = {}
        
    def load(self) -> pd.DataFrame:
        """
        Load sales data from file or DataFrame.
        
        Returns:
            Standardized DataFrame
        """
        logger.info("Loading sales data...")
        
        if self.dataframe is not None:
            df = self.dataframe.copy()
        elif self.file_path:
            df = self._read_file()
        else:
            raise ValueError("Either file_path or dataframe must be provided")
            
        # Rename columns to standard format
        df = self._standardize_columns(df)
        
        # Convert data types
        df = self._convert_types(df)
        
        # Sort by date and geo
        df = df.sort_values(['date', 'geo']).reset_index(drop=True)
        
        self.data = df
        logger.success(f"Loaded {len(df):,} rows of sales data")
        
        return df
        
    def validate(self, data: Optional[pd.DataFrame] = None) -> Dict:
        """
        Validate sales data quality.
        
        Args:
            data: DataFrame to validate (uses self.data if None)
            
        Returns:
            Dictionary with validation results
        """
        if data is None:
            if self.data is None:
                raise ValueError("No data to validate. Call load() first.")
            data = self.data
            
        logger.info("Validating sales data...")
        
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        # Check required columns
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in data.columns]
        if missing_cols:
            results['valid'] = False
            results['errors'].append(f"Missing required columns: {missing_cols}")
            
        # Check for missing values
        for col in self.REQUIRED_COLUMNS:
            if col in data.columns:
                missing_pct = data[col].isna().mean()
                if missing_pct > 0:
                    results['warnings'].append(
                        f"Column '{col}' has {missing_pct:.2%} missing values"
                    )
                    if missing_pct > 0.02:  # More than 2% missing
                        results['valid'] = False
                        results['errors'].append(
                            f"Column '{col}' has too many missing values ({missing_pct:.2%})"
                        )
                        
        # Check for negative values
        if 'sales_value' in data.columns:
            neg_sales = (data['sales_value'] < 0).sum()
            if neg_sales > 0:
                results['valid'] = False
                results['errors'].append(
                    f"Found {neg_sales} negative values in sales_value"
                )
                
        # Check for zero values
        if 'sales_value' in data.columns:
            zero_pct = (data['sales_value'] == 0).mean()
            if zero_pct > 0.10:  # More than 10% zeros
                results['warnings'].append(
                    f"Sales data has {zero_pct:.2%} zero values"
                )
                
        # Check date range
        if 'date' in data.columns:
            date_range = data['date'].max() - data['date'].min()
            results['stats']['date_range_days'] = date_range.days
            results['stats']['start_date'] = data['date'].min()
            results['stats']['end_date'] = data['date'].max()
            
            if date_range.days < 365:  # Less than 1 year
                results['warnings'].append(
                    f"Short date range: {date_range.days} days (minimum 730 recommended)"
                )
                
        # Check number of geos
        if 'geo' in data.columns:
            n_geos = data['geo'].nunique()
            results['stats']['n_geos'] = n_geos
            
            if n_geos < 5:
                results['warnings'].append(
                    f"Few geos: {n_geos} (minimum 10 recommended for geo-level modeling)"
                )
                
        # Check for complete time series (no gaps)
        if 'date' in data.columns and 'geo' in data.columns:
            # Get expected date range
            date_range = pd.date_range(
                start=data['date'].min(),
                end=data['date'].max(),
                freq='D'
            )
            
            # Check each geo for completeness
            incomplete_geos = []
            for geo in data['geo'].unique():
                geo_data = data[data['geo'] == geo]
                geo_dates = set(geo_data['date'].dt.date)
                expected_dates = set(date_range.date)
                missing_dates = expected_dates - geo_dates
                
                if len(missing_dates) > 0:
                    incomplete_geos.append(geo)
                    
            if incomplete_geos:
                results['warnings'].append(
                    f"{len(incomplete_geos)} geos have missing dates in time series"
                )
                
        # Summary statistics
        if 'sales_value' in data.columns:
            results['stats']['total_sales'] = data['sales_value'].sum()
            results['stats']['avg_sales'] = data['sales_value'].mean()
            results['stats']['std_sales'] = data['sales_value'].std()
            results['stats']['cv_sales'] = (
                data['sales_value'].std() / data['sales_value'].mean()
            )
            
        if 'sales_units' in data.columns:
            results['stats']['total_units'] = data['sales_units'].sum()
            
        self.validation_results = results
        
        if results['valid']:
            logger.success("Sales data validation passed")
        else:
            logger.error("Sales data validation failed")
            for error in results['errors']:
                logger.error(f"  - {error}")
                
        if results['warnings']:
            for warning in results['warnings']:
                logger.warning(f"  - {warning}")
                
        return results
        
    def load_and_validate(self) -> pd.DataFrame:
        """
        Load and validate sales data in one step.
        
        Returns:
            Validated DataFrame
            
        Raises:
            ValueError: If validation fails
        """
        data = self.load()
        results = self.validate(data)
        
        if not results['valid']:
            raise ValueError(
                f"Sales data validation failed with {len(results['errors'])} errors"
            )
            
        return data
        
    def to_xarray(
        self,
        data: Optional[pd.DataFrame] = None,
        time_column: str = 'date',
        geo_column: str = 'geo',
        value_column: str = 'sales_value'
    ) -> xr.DataArray:
        """
        Convert to xarray format required by Meridian.
        
        Args:
            data: DataFrame to convert (uses self.data if None)
            time_column: Column to use for time dimension
            geo_column: Column to use for geo dimension
            value_column: Column to use for values
            
        Returns:
            xarray DataArray with dimensions (geo, time)
        """
        if data is None:
            if self.data is None:
                raise ValueError("No data to convert. Call load() first.")
            data = self.data
            
        logger.info("Converting to xarray format...")
        
        # Pivot to wide format
        pivot = data.pivot_table(
            index=[geo_column, time_column],
            values=value_column,
            aggfunc='sum'
        )
        
        # Convert to xarray
        xr_data = pivot.to_xarray()
        
        # Rename dimensions to match Meridian expectations
        xr_data = xr_data.rename({
            geo_column: 'geo',
            time_column: 'time'
        })
        
        logger.success("Converted to xarray format")
        
        return xr_data
        
    def aggregate_to_weekly(
        self,
        data: Optional[pd.DataFrame] = None,
        date_column: str = 'date',
        geo_column: str = 'geo'
    ) -> pd.DataFrame:
        """
        Aggregate daily data to weekly.
        
        Args:
            data: DataFrame to aggregate (uses self.data if None)
            date_column: Date column name
            geo_column: Geo column name
            
        Returns:
            DataFrame aggregated to weekly level
        """
        if data is None:
            if self.data is None:
                raise ValueError("No data to aggregate. Call load() first.")
            data = self.data
            
        logger.info("Aggregating to weekly data...")
        
        # Add week column
        df = data.copy()
        df['week'] = pd.to_datetime(df[date_column]).dt.to_period('W').dt.start_time
        
        # Aggregate
        agg_dict = {'sales_value': 'sum'}
        if 'sales_units' in df.columns:
            agg_dict['sales_units'] = 'sum'
        if 'sales_volume' in df.columns:
            agg_dict['sales_volume'] = 'sum'
            
        weekly = df.groupby([geo_column, 'week']).agg(agg_dict).reset_index()
        weekly = weekly.rename(columns={'week': date_column})
        
        logger.success(f"Aggregated to {len(weekly):,} weekly observations")
        
        return weekly
        
    def _read_file(self) -> pd.DataFrame:
        """Read data from file."""
        if self.file_path.suffix.lower() == '.csv':
            return pd.read_csv(self.file_path)
        elif self.file_path.suffix.lower() in ['.xlsx', '.xls']:
            return pd.read_excel(self.file_path)
        else:
            raise ValueError(f"Unsupported file format: {self.file_path.suffix}")
            
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename columns to standard format."""
        # Check if source columns exist
        for standard_col, source_col in self.column_mapping.items():
            if source_col not in df.columns:
                if standard_col in self.REQUIRED_COLUMNS:
                    raise ValueError(f"Required column '{source_col}' not found in data")
                    
        # Rename to standard format
        rename_dict = {v: k for k, v in self.column_mapping.items() if v in df.columns}
        df = df.rename(columns=rename_dict)
        
        # Keep only standard columns
        valid_columns = self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS
        df = df[[col for col in df.columns if col in valid_columns]]
        
        return df
        
    def _convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert columns to appropriate data types."""
        for col, dtype in self.COLUMN_TYPES.items():
            if col in df.columns:
                try:
                    if dtype == 'datetime64[ns]':
                        df[col] = pd.to_datetime(df[col])
                    elif dtype == 'float':
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    elif dtype == 'str':
                        df[col] = df[col].astype(str)
                except Exception as e:
                    logger.warning(f"Could not convert column '{col}' to {dtype}: {e}")
                    
        return df
        
    def get_summary(self) -> pd.DataFrame:
        """
        Get summary statistics by geo.
        
        Returns:
            DataFrame with summary statistics
        """
        if self.data is None:
            raise ValueError("No data available. Call load() first.")
            
        summary = self.data.groupby('geo').agg({
            'sales_value': ['sum', 'mean', 'std', 'count'],
            'date': ['min', 'max']
        }).round(2)
        
        return summary

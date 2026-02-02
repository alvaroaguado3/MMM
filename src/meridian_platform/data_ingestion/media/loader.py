"""
Media Data Ingestion Module

This module handles loading and validating media data from various sources.
It standardizes the format for use with the Meridian model.

Standard Format:
- date: datetime (YYYY-MM-DD)
- geo: string (geographic identifier)
- touchpoint_name: string (marketing tactic)
- metric_value: float (GRPs, impressions, etc.)
- spend: float (optional, media spend)
- mapping_id: string (optional, granular identifier)
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Union
from pathlib import Path
from loguru import logger
import xarray as xr
from datetime import datetime


class MediaDataLoader:
    """Load and validate media data for Meridian modeling."""
    
    # Required columns
    REQUIRED_COLUMNS = ['date', 'geo', 'touchpoint_name', 'metric_value']
    
    # Optional columns
    OPTIONAL_COLUMNS = ['spend', 'mapping_id']
    
    # Expected data types
    COLUMN_TYPES = {
        'date': 'datetime64[ns]',
        'geo': 'str',
        'touchpoint_name': 'str',
        'metric_value': 'float',
        'spend': 'float',
        'mapping_id': 'str'
    }
    
    def __init__(
        self,
        file_path: Optional[Union[str, Path]] = None,
        dataframe: Optional[pd.DataFrame] = None,
        date_column: str = 'date',
        geo_column: str = 'geo',
        touchpoint_column: str = 'touchpoint_name',
        metric_column: str = 'metric_value',
        spend_column: Optional[str] = 'spend',
        mapping_column: Optional[str] = 'mapping_id'
    ):
        """
        Initialize Media Data Loader.
        
        Args:
            file_path: Path to CSV/Excel file
            dataframe: Pandas DataFrame (alternative to file_path)
            date_column: Name of date column in source data
            geo_column: Name of geo column in source data
            touchpoint_column: Name of touchpoint/tactic column
            metric_column: Name of metric column (impressions, GRPs, etc.)
            spend_column: Name of spend column (optional)
            mapping_column: Name of mapping/campaign ID column (optional)
        """
        self.file_path = Path(file_path) if file_path else None
        self.dataframe = dataframe
        
        # Column mappings
        self.column_mapping = {
            'date': date_column,
            'geo': geo_column,
            'touchpoint_name': touchpoint_column,
            'metric_value': metric_column
        }
        
        if spend_column:
            self.column_mapping['spend'] = spend_column
        if mapping_column:
            self.column_mapping['mapping_id'] = mapping_column
            
        self.data: Optional[pd.DataFrame] = None
        self.validation_results: Dict = {}
        
    def load(self) -> pd.DataFrame:
        """
        Load media data from file or DataFrame.
        
        Returns:
            Standardized DataFrame
        """
        logger.info("Loading media data...")
        
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
        df = df.sort_values(['date', 'geo', 'touchpoint_name']).reset_index(drop=True)
        
        self.data = df
        logger.success(f"Loaded {len(df):,} rows of media data")
        
        return df
        
    def validate(self, data: Optional[pd.DataFrame] = None) -> Dict:
        """
        Validate media data quality.
        
        Args:
            data: DataFrame to validate (uses self.data if None)
            
        Returns:
            Dictionary with validation results
        """
        if data is None:
            if self.data is None:
                raise ValueError("No data to validate. Call load() first.")
            data = self.data
            
        logger.info("Validating media data...")
        
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
                    if missing_pct > 0.05:  # More than 5% missing
                        results['valid'] = False
                        results['errors'].append(
                            f"Column '{col}' has too many missing values ({missing_pct:.2%})"
                        )
                        
        # Check for negative values in metric and spend
        if 'metric_value' in data.columns:
            neg_metrics = (data['metric_value'] < 0).sum()
            if neg_metrics > 0:
                results['valid'] = False
                results['errors'].append(
                    f"Found {neg_metrics} negative values in metric_value"
                )
                
        if 'spend' in data.columns:
            neg_spend = (data['spend'] < 0).sum()
            if neg_spend > 0:
                results['valid'] = False
                results['errors'].append(f"Found {neg_spend} negative values in spend")
                
        # Check date range
        if 'date' in data.columns:
            date_range = data['date'].max() - data['date'].min()
            results['stats']['date_range_days'] = date_range.days
            results['stats']['start_date'] = data['date'].min()
            results['stats']['end_date'] = data['date'].max()
            
            if date_range.days < 90:  # Less than 3 months
                results['warnings'].append(
                    f"Short date range: {date_range.days} days (minimum 365 recommended)"
                )
                
        # Check number of touchpoints
        if 'touchpoint_name' in data.columns:
            n_touchpoints = data['touchpoint_name'].nunique()
            results['stats']['n_touchpoints'] = n_touchpoints
            
            if n_touchpoints < 3:
                results['warnings'].append(
                    f"Few touchpoints: {n_touchpoints} (minimum 5 recommended)"
                )
                
        # Check number of geos
        if 'geo' in data.columns:
            n_geos = data['geo'].nunique()
            results['stats']['n_geos'] = n_geos
            
            # Check for sufficient non-zero values per touchpoint
            for touchpoint in data['touchpoint_name'].unique():
                touchpoint_data = data[data['touchpoint_name'] == touchpoint]
                non_zero_pct = (touchpoint_data['metric_value'] > 0).mean()
                
                if non_zero_pct < 0.05:  # Less than 5% non-zero
                    results['warnings'].append(
                        f"Touchpoint '{touchpoint}' has only {non_zero_pct:.2%} "
                        f"non-zero values (sparse data)"
                    )
                    
        # Summary statistics
        if 'metric_value' in data.columns:
            results['stats']['total_metric'] = data['metric_value'].sum()
            results['stats']['avg_metric'] = data['metric_value'].mean()
            
        if 'spend' in data.columns:
            results['stats']['total_spend'] = data['spend'].sum()
            results['stats']['avg_spend'] = data['spend'].mean()
            
        self.validation_results = results
        
        if results['valid']:
            logger.success("Media data validation passed")
        else:
            logger.error("Media data validation failed")
            for error in results['errors']:
                logger.error(f"  - {error}")
                
        if results['warnings']:
            for warning in results['warnings']:
                logger.warning(f"  - {warning}")
                
        return results
        
    def load_and_validate(self) -> pd.DataFrame:
        """
        Load and validate media data in one step.
        
        Returns:
            Validated DataFrame
            
        Raises:
            ValueError: If validation fails
        """
        data = self.load()
        results = self.validate(data)
        
        if not results['valid']:
            raise ValueError(
                f"Media data validation failed with {len(results['errors'])} errors"
            )
            
        return data
        
    def to_xarray(
        self,
        data: Optional[pd.DataFrame] = None,
        time_column: str = 'date',
        geo_column: str = 'geo',
        channel_column: str = 'touchpoint_name'
    ) -> xr.DataArray:
        """
        Convert to xarray format required by Meridian.
        
        Args:
            data: DataFrame to convert (uses self.data if None)
            time_column: Column to use for time dimension
            geo_column: Column to use for geo dimension
            channel_column: Column to use for channel dimension
            
        Returns:
            xarray DataArray with dimensions (geo, time, channel)
        """
        if data is None:
            if self.data is None:
                raise ValueError("No data to convert. Call load() first.")
            data = self.data
            
        logger.info("Converting to xarray format...")
        
        # Pivot to wide format
        pivot = data.pivot_table(
            index=[geo_column, time_column],
            columns=channel_column,
            values='metric_value',
            fill_value=0.0
        )
        
        # Convert to xarray
        xr_data = pivot.to_xarray()
        
        # Rename dimensions to match Meridian expectations
        xr_data = xr_data.rename({
            geo_column: 'geo',
            time_column: 'time',
            channel_column: 'media_channel'
        })
        
        logger.success("Converted to xarray format")
        
        return xr_data
        
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
        Get summary statistics by touchpoint.
        
        Returns:
            DataFrame with summary statistics
        """
        if self.data is None:
            raise ValueError("No data available. Call load() first.")
            
        summary = self.data.groupby('touchpoint_name').agg({
            'metric_value': ['sum', 'mean', 'std', 'count'],
            'spend': ['sum', 'mean'] if 'spend' in self.data.columns else [],
            'geo': 'nunique'
        }).round(2)
        
        return summary

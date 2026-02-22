"""
Meridian Model Runner

This module wraps Google Meridian for training Marketing Mix Models.
It handles data preparation, model configuration, training, and results extraction.
"""

import pandas as pd
import numpy as np
import yaml
from typing import Dict, Optional, Any, Tuple
from pathlib import Path
from loguru import logger
import xarray as xr

try:
    from meridian.model import model, spec
    from meridian.data import data_frame_input_data_builder
    from meridian.data import input_data as input_data_module
    from meridian.analysis import analyzer as meridian_analyzer
    MERIDIAN_AVAILABLE = True
except ImportError:
    logger.warning("Meridian not available. Install with: pip install google-meridian")
    MERIDIAN_AVAILABLE = False

try:
    import tensorflow_probability as tfp
    TFP_AVAILABLE = True
except ImportError:
    logger.warning("TensorFlow Probability not available")
    TFP_AVAILABLE = False


class MeridianModelRunner:
    """
    Wrapper for training and managing Meridian MMM models.
    
    This class handles:
    - Data preparation and conversion to Meridian format
    - Model specification with custom priors
    - MCMC training
    - Convergence diagnostics
    - Results extraction
    """
    
    def __init__(
        self,
        media_data: pd.DataFrame,
        sales_data: pd.DataFrame,
        population_data: Optional[pd.DataFrame] = None,
        config_path: Optional[str] = 'config/model_defaults.yaml',
        priors_config: Optional[Any] = None
    ):
        """
        Initialize Meridian Model Runner.

        Args:
            media_data: Standardized media DataFrame (from MediaDataLoader)
            sales_data: Standardized sales DataFrame (from SalesDataLoader)
            population_data: DataFrame with geo and population columns
            config_path: Path to model configuration YAML
            priors_config: Optional PriorsConfigLoader instance
        """
        if not MERIDIAN_AVAILABLE:
            raise ImportError("Meridian is required. Install with: pip install google-meridian")

        self.media_data = media_data.copy()
        self.sales_data = sales_data.copy()
        self.population_data = population_data.copy() if population_data is not None else None
        self.priors_config = priors_config
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Model components (initialized during training)
        self.input_data: Optional[Any] = None
        self.model_spec: Optional[Any] = None
        self.model: Optional[Any] = None
        self.inference_data: Optional[Any] = None
        
        logger.info("MeridianModelRunner initialized")
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load model configuration from YAML."""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            logger.warning("Config file not found, using defaults")
            return {
                'model': {
                    'kpi_type': 'non_revenue',
                    'sampling': {
                        'n_warmup': 1000,
                        'n_samples': 1000,
                        'n_chains': 2,
                        'random_seed': 42
                    },
                    'time': {
                        'max_lag': 8,
                        'knots': None,
                        'adstock_decay_spec': 'geometric'
                    }
                }
            }
    
    def prepare_data(self, aggregate_weekly: bool = True) -> Any:
        """
        Prepare data in Meridian's InputData format.

        Args:
            aggregate_weekly: If True, aggregate daily data to weekly.

        Returns:
            Meridian InputData object
        """
        logger.info("Preparing data for Meridian...")

        if aggregate_weekly:
            logger.info("Aggregating data to weekly...")
            self.media_data['date'] = pd.to_datetime(self.media_data['date'])
            self.media_data['date'] = self.media_data['date'].dt.to_period('W').dt.start_time

            self.sales_data['date'] = pd.to_datetime(self.sales_data['date'])
            self.sales_data['date'] = self.sales_data['date'].dt.to_period('W').dt.start_time

            self.media_data = self.media_data.groupby(
                ['date', 'geo', 'touchpoint_name'], as_index=False
            ).agg({'metric_value': 'sum', 'spend': 'sum'})

            agg_cols = {'sales_value': 'sum'}
            if 'sales_units' in self.sales_data.columns:
                agg_cols['sales_units'] = 'sum'
            self.sales_data = self.sales_data.groupby(
                ['date', 'geo'], as_index=False
            ).agg(agg_cols)

            logger.info(f"Weekly: {self.sales_data['date'].nunique()} time points")

        # Merge media and sales data
        merged = self._merge_data()
        
        # Get unique channels
        channels = sorted(self.media_data['touchpoint_name'].unique().tolist())
        geos = sorted(self.media_data['geo'].unique().tolist())
        
        logger.info(f"Preparing data: {len(channels)} channels, {len(geos)} geos")
        
        # Create wide-format DataFrames for media and spend
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
        
        # Merge with sales data
        full_data = media_wide.merge(self.sales_data, on=['date', 'geo'], how='inner')
        full_data_spend = spend_wide.merge(self.sales_data, on=['date', 'geo'], how='inner')
        
        # Initialize InputData builder
        kpi_type = self.config['model'].get('kpi_type', 'non_revenue')

        builder = data_frame_input_data_builder.DataFrameInputDataBuilder(
            kpi_type=kpi_type,
            default_kpi_column='sales_value',
            default_time_column='date',
            default_media_time_column='date',
        )

        # Add KPI data
        builder = builder.with_kpi(full_data, kpi_col='sales_value', time_col='date')

        # Add revenue per KPI if units are available
        if 'sales_units' in full_data.columns:
            # Calculate revenue per unit
            full_data['revenue_per_unit'] = full_data['sales_value'] / full_data['sales_units'].replace(0, np.nan)
            full_data['revenue_per_unit'] = full_data['revenue_per_unit'].fillna(
                full_data['revenue_per_unit'].mean()
            )
            builder = builder.with_revenue_per_kpi(
                full_data,
                revenue_per_kpi_col='revenue_per_unit',
                time_col='date'
            )

        # Add media data
        media_cols = [ch for ch in channels]

        # Create combined dataframe with both media and spend
        combined = media_wide.copy()
        for ch in channels:
            combined[f"{ch}_spend"] = spend_wide[ch]

        builder = builder.with_media(
            combined,
            media_cols=media_cols,
            media_spend_cols=[f"{ch}_spend" for ch in channels],
            media_channels=channels,
            time_col='date'
        )

        # Add population data
        if self.population_data is not None:
            builder = builder.with_population(
                self.population_data,
                population_col='population'
            )

        # Build InputData
        self.input_data = builder.build()
        
        logger.success(f"Data prepared: {self.input_data.kpi.shape}")
        
        return self.input_data
    
    def _merge_data(self) -> pd.DataFrame:
        """Merge media and sales data."""
        # Aggregate media by date and geo
        media_agg = self.media_data.groupby(['date', 'geo']).agg({
            'metric_value': 'sum',
            'spend': 'sum'
        }).reset_index()
        
        # Merge with sales
        merged = self.sales_data.merge(
            media_agg,
            on=['date', 'geo'],
            how='left'
        )
        
        merged['metric_value'] = merged['metric_value'].fillna(0)
        merged['spend'] = merged['spend'].fillna(0)
        
        return merged
    
    def create_model_spec(self) -> Any:
        """
        Create Meridian ModelSpec with configuration.
        
        Returns:
            Meridian ModelSpec object
        """
        logger.info("Creating model specification...")
        
        time_config = self.config['model']['time']
        
        # Basic spec parameters
        spec_params = {
            'max_lag': time_config.get('max_lag', 8),
            'knots': time_config.get('knots', None)
        }
        
        # Add custom priors if available
        if self.priors_config and TFP_AVAILABLE:
            logger.info("Adding custom priors from configuration...")
            
            # Get channels from input data
            if self.input_data is not None:
                channels = self.input_data.media.media_channel.values.tolist()
                
                # Create prior distribution dictionary
                prior_dict = {}
                roi_priors = self.priors_config.get_roi_priors(channels)
                
                for channel, prior_params in roi_priors.items():
                    dist_type = prior_params.get('distribution', 'lognormal').lower()
                    
                    if dist_type == 'lognormal':
                        prior_dict[channel] = tfp.distributions.LogNormal(
                            loc=prior_params.get('loc', 0.0),
                            scale=prior_params.get('scale', 1.0)
                        )
                
                if prior_dict:
                    spec_params['prior'] = prior_dict
                    logger.info(f"Added custom priors for {len(prior_dict)} channels")
        
        self.model_spec = spec.ModelSpec(**spec_params)
        
        logger.success("Model specification created")
        
        return self.model_spec
    
    def train(
        self,
        n_warmup: Optional[int] = None,
        n_samples: Optional[int] = None,
        n_chains: Optional[int] = None,
        seed: Optional[int] = None
    ) -> Any:
        """
        Train the Meridian model using MCMC sampling.
        
        Args:
            n_warmup: Number of warmup iterations (uses config default if None)
            n_samples: Number of sampling iterations (uses config default if None)
            n_chains: Number of MCMC chains (uses config default if None)
            seed: Random seed (uses config default if None)
            
        Returns:
            Trained Meridian model
        """
        if self.input_data is None:
            logger.info("Input data not prepared, preparing now...")
            self.prepare_data()
        
        if self.model_spec is None:
            logger.info("Model spec not created, creating now...")
            self.create_model_spec()
        
        # Get sampling parameters from config or arguments
        sampling_config = self.config['model']['sampling']
        n_warmup = n_warmup or sampling_config.get('n_warmup', 1000)
        n_samples = n_samples or sampling_config.get('n_samples', 1000)
        n_chains = n_chains or sampling_config.get('n_chains', 2)
        seed = seed or sampling_config.get('random_seed', 42)

        logger.info(f"Training Meridian model...")
        logger.info(f"  Adapt: {n_warmup}, Keep: {n_samples}, Chains: {n_chains}")

        # Initialize model
        self.model = model.Meridian(
            input_data=self.input_data,
            model_spec=self.model_spec
        )

        # Sample prior (required before posterior and for Analyzer)
        try:
            logger.info("Sampling prior...")
            self.model.sample_prior(n_draws=n_samples, seed=seed)

            logger.info("Sampling posterior...")
            self.model.sample_posterior(
                n_chains=n_chains,
                n_adapt=n_warmup,
                n_burnin=n_warmup,
                n_keep=n_samples,
                seed=seed
            )
            
            logger.success("Model training complete!")
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            raise
        
        return self.model
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """
        Extract convergence diagnostics from the trained model.

        Returns:
            Dictionary with diagnostic statistics
        """
        if self.model is None:
            raise ValueError("Model not trained yet. Call train() first.")

        logger.info("Extracting diagnostics...")

        diagnostics = {
            'convergence': {},
            'summary': {}
        }

        try:
            ana = meridian_analyzer.Analyzer(self.model)
            rhat_df = ana.rhat_summary()

            r_hat_max = float(rhat_df['max_rhat'].max())
            r_hat_mean = float(rhat_df['avg_rhat'].mean())

            diagnostics['summary'] = {
                'r_hat_mean': r_hat_mean,
                'r_hat_max': r_hat_max,
            }
            diagnostics['rhat_details'] = rhat_df

            r_hat_ok = r_hat_max < 1.2

            diagnostics['convergence'] = {
                'r_hat_converged': r_hat_ok,
                'overall_converged': r_hat_ok
            }

            if r_hat_ok:
                logger.success(f"Model converged (R-hat max: {r_hat_max:.4f})")
            else:
                logger.warning(f"Convergence issues (R-hat max: {r_hat_max:.4f}, should be < 1.2)")

        except Exception as e:
            logger.error(f"Failed to extract diagnostics: {e}")
            diagnostics['error'] = str(e)

        return diagnostics
    
    def get_results(self) -> Dict[str, Any]:
        """
        Extract model results (ROI, contributions, etc.) via Meridian Analyzer.

        Returns:
            Dictionary with model results
        """
        if self.model is None:
            raise ValueError("Model not trained yet. Call train() first.")

        logger.info("Extracting model results...")

        results = {}

        try:
            ana = meridian_analyzer.Analyzer(self.model)

            # Get summary metrics (contains ROI, contributions, etc.)
            summary = ana.summary_metrics()
            results['summary_metrics'] = summary

            # Extract ROI per channel
            channels = self.input_data.media.media_channel.values.tolist()
            roi_tensor = ana.roi()  # shape: (n_samples, n_channels)
            roi_mean = roi_tensor.numpy().mean(axis=0)

            results['roi'] = {
                ch: float(roi_mean[i]) for i, ch in enumerate(channels)
            }

            # Use roi as the default display (no priors adjustment needed)
            results['roi_adjusted'] = results['roi']

            logger.success("Results extracted successfully")

        except Exception as e:
            logger.error(f"Failed to extract results: {e}")
            results['error'] = str(e)

        return results
    
    def get_response_curves(self, channel: Optional[str] = None) -> Dict:
        """
        Get marginal response curves for channels.
        
        Args:
            channel: Specific channel name (all channels if None)
            
        Returns:
            Dictionary with response curve data
        """
        if self.model is None:
            raise ValueError("Model not trained yet. Call train() first.")
        
        logger.info("Extracting response curves...")
        
        try:
            # This would use Meridian's response curve methods
            # Placeholder for actual implementation
            curves = {
                'message': 'Response curves require additional Meridian methods'
            }
            
            return curves
            
        except Exception as e:
            logger.error(f"Failed to extract response curves: {e}")
            return {'error': str(e)}
    
    def save_model(self, output_path: str):
        """
        Save trained model to disk.
        
        Args:
            output_path: Path to save model
        """
        if self.model is None:
            raise ValueError("No model to save. Train model first.")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving model to {output_path}")
        
        try:
            self.model.save(str(output_path))
            logger.success("Model saved successfully")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise
    
    def load_model(self, model_path: str):
        """
        Load trained model from disk.
        
        Args:
            model_path: Path to saved model
        """
        logger.info(f"Loading model from {model_path}")
        
        try:
            self.model = model.Meridian.load(model_path)
            logger.success("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
        
        return self.model

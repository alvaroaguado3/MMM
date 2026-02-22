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
    from meridian import model, spec
    from meridian.data import data_frame_input_data_builder
    from meridian.data import input_data as input_data_module
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
        config_path: Optional[str] = 'config/model_defaults.yaml',
        priors_config: Optional[Any] = None
    ):
        """
        Initialize Meridian Model Runner.
        
        Args:
            media_data: Standardized media DataFrame (from MediaDataLoader)
            sales_data: Standardized sales DataFrame (from SalesDataLoader)
            config_path: Path to model configuration YAML
            priors_config: Optional PriorsConfigLoader instance
        """
        if not MERIDIAN_AVAILABLE:
            raise ImportError("Meridian is required. Install with: pip install google-meridian")
        
        self.media_data = media_data.copy()
        self.sales_data = sales_data.copy()
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
                        'max_lag': 13,
                        'n_knots': 3,
                        'adstock_decay_spec': 'normal'
                    }
                }
            }
    
    def prepare_data(self) -> Any:
        """
        Prepare data in Meridian's InputData format.
        
        Returns:
            Meridian InputData object
        """
        logger.info("Preparing data for Meridian...")
        
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
        full_data = media_wide.merge(sales_data, on=['date', 'geo'], how='inner')
        full_data_spend = spend_wide.merge(sales_data, on=['date', 'geo'], how='inner')
        
        # Initialize InputData builder
        kpi_type = self.config['model'].get('kpi_type', 'non_revenue')
        
        builder = data_frame_input_data_builder.DataFrameInputDataBuilder(
            kpi_type=kpi_type,
            default_kpi_column='sales_value'
        )
        
        # Add KPI data
        builder = builder.with_kpi(full_data)
        
        # Add revenue per KPI if units are available
        if 'sales_units' in full_data.columns:
            # Calculate revenue per unit
            full_data['revenue_per_unit'] = full_data['sales_value'] / full_data['sales_units'].replace(0, np.nan)
            full_data['revenue_per_unit'] = full_data['revenue_per_unit'].fillna(
                full_data['revenue_per_unit'].mean()
            )
            builder = builder.with_revenue_per_kpi(
                full_data,
                revenue_per_kpi_column='revenue_per_unit'
            )
        
        # Add media data
        media_cols = [ch for ch in channels]
        spend_cols = [ch for ch in channels]
        
        # Create combined dataframe with both media and spend
        combined = media_wide.copy()
        for ch in channels:
            combined[f"{ch}_spend"] = spend_wide[ch]
        
        builder = builder.with_media(
            combined,
            media_cols=media_cols,
            media_spend_cols=[f"{ch}_spend" for ch in channels],
            media_channels=channels
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
            'max_lag': time_config.get('max_lag', 13),
            'n_knots': time_config.get('n_knots', 3)
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
        logger.info(f"  Warmup: {n_warmup}, Samples: {n_samples}, Chains: {n_chains}")
        
        # Initialize model
        self.model = model.Meridian(
            input_data=self.input_data,
            model_spec=self.model_spec
        )
        
        # Train model
        try:
            self.model.fit(
                num_warmup=n_warmup,
                num_samples=n_samples,
                num_chains=n_chains,
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
            # Get inference data
            inference_data = self.model.inference_data
            
            # Extract R-hat and ESS
            import arviz as az
            
            summary = az.summary(inference_data)
            
            diagnostics['summary'] = {
                'r_hat_mean': summary['r_hat'].mean(),
                'r_hat_max': summary['r_hat'].max(),
                'ess_bulk_min': summary['ess_bulk'].min(),
                'ess_tail_min': summary['ess_tail'].min()
            }
            
            # Convergence checks
            r_hat_ok = diagnostics['summary']['r_hat_max'] < 1.05
            ess_ok = diagnostics['summary']['ess_bulk_min'] > 400
            
            diagnostics['convergence'] = {
                'r_hat_converged': r_hat_ok,
                'ess_sufficient': ess_ok,
                'overall_converged': r_hat_ok and ess_ok
            }
            
            if diagnostics['convergence']['overall_converged']:
                logger.success("✓ Model converged successfully")
            else:
                logger.warning("⚠ Convergence issues detected")
                if not r_hat_ok:
                    logger.warning(f"  R-hat max: {diagnostics['summary']['r_hat_max']:.4f} (should be < 1.05)")
                if not ess_ok:
                    logger.warning(f"  ESS min: {diagnostics['summary']['ess_bulk_min']:.0f} (should be > 400)")
            
        except Exception as e:
            logger.error(f"Failed to extract diagnostics: {e}")
            diagnostics['error'] = str(e)
        
        return diagnostics
    
    def get_results(self) -> Dict[str, Any]:
        """
        Extract model results (ROI, contributions, etc.)
        
        Returns:
            Dictionary with model results
        """
        if self.model is None:
            raise ValueError("Model not trained yet. Call train() first.")
        
        logger.info("Extracting model results...")
        
        results = {}
        
        try:
            # Get channel names
            channels = self.input_data.media.media_channel.values.tolist()
            
            # Extract ROI
            roi_data = self.model.roi
            results['roi'] = {
                'values': roi_data,
                'channels': channels
            }
            
            # Extract contributions
            contrib_data = self.model.incremental_outcome
            results['contributions'] = {
                'values': contrib_data,
                'channels': channels
            }
            
            # Model fit statistics
            results['fit'] = {
                'r_squared': float(self.model.r_squared) if hasattr(self.model, 'r_squared') else None
            }
            
            logger.success("Results extracted successfully")
            
            # Apply coverage factors if configured
            if self.priors_config:
                coverage_factors = self.priors_config.get_coverage_factors(channels)
                
                # Adjust ROI by coverage factors
                adjusted_roi = {}
                for i, channel in enumerate(channels):
                    factor = coverage_factors.get(channel, 1.0)
                    if hasattr(roi_data, 'mean'):
                        adjusted_roi[channel] = float(roi_data.mean().values[i]) * factor
                    else:
                        adjusted_roi[channel] = float(roi_data[i]) * factor
                
                results['roi_adjusted'] = adjusted_roi
                logger.info("Applied coverage factors to ROI estimates")
            
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

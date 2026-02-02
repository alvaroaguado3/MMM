"""
Bayesian Priors Configuration Module

This module handles loading and configuring Bayesian priors for the Meridian model.
Priors can be specified from YAML files or programmatically.
"""

import yaml
from typing import Dict, Optional, Any, Union
from pathlib import Path
from loguru import logger
import numpy as np


try:
    import tensorflow_probability as tfp
    TFP_AVAILABLE = True
except ImportError:
    logger.warning("TensorFlow Probability not available. Prior distributions will be limited.")
    TFP_AVAILABLE = False


class PriorsConfigLoader:
    """Load and manage Bayesian prior configurations."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize priors configuration loader.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path) if config_path else None
        self.config: Dict = {}
        
        if self.config_path and self.config_path.exists():
            self.load_config()
            
    def load_config(self, config_path: Optional[Union[str, Path]] = None) -> Dict:
        """
        Load priors configuration from YAML file.
        
        Args:
            config_path: Path to YAML file (uses self.config_path if None)
            
        Returns:
            Configuration dictionary
        """
        if config_path:
            self.config_path = Path(config_path)
            
        if not self.config_path or not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        logger.info(f"Loading priors configuration from {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        logger.success("Priors configuration loaded")
        
        return self.config
        
    def get_roi_priors(
        self,
        channels: Optional[list] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Get ROI priors for specified channels.
        
        Args:
            channels: List of channel names (all channels if None)
            
        Returns:
            Dictionary mapping channel names to prior parameters
        """
        roi_priors = self.config.get('roi_priors', {})
        
        if channels:
            # Filter for requested channels, use default for missing
            result = {}
            default_prior = roi_priors.get('default', {
                'distribution': 'lognormal',
                'loc': 0.0,
                'scale': 1.0
            })
            
            for channel in channels:
                result[channel] = roi_priors.get(channel, default_prior)
                
            return result
        else:
            # Return all configured priors
            return {k: v for k, v in roi_priors.items() if k != 'default'}
            
    def get_roi_prior_distribution(
        self,
        channel: str
    ) -> Optional[Any]:
        """
        Get TensorFlow Probability distribution for ROI prior.
        
        Args:
            channel: Channel name
            
        Returns:
            TFP distribution object or None if TFP not available
        """
        if not TFP_AVAILABLE:
            logger.warning("TensorFlow Probability not available")
            return None
            
        roi_priors = self.get_roi_priors([channel])
        prior_params = roi_priors.get(channel)
        
        if not prior_params:
            logger.warning(f"No ROI prior configured for channel '{channel}'")
            return None
            
        dist_type = prior_params.get('distribution', 'lognormal').lower()
        
        if dist_type == 'lognormal':
            return tfp.distributions.LogNormal(
                loc=prior_params.get('loc', 0.0),
                scale=prior_params.get('scale', 1.0)
            )
        elif dist_type == 'normal':
            return tfp.distributions.Normal(
                loc=prior_params.get('loc', 0.0),
                scale=prior_params.get('scale', 1.0)
            )
        elif dist_type == 'uniform':
            return tfp.distributions.Uniform(
                low=prior_params.get('low', 0.0),
                high=prior_params.get('high', 1.0)
            )
        else:
            logger.warning(f"Unknown distribution type: {dist_type}")
            return None
            
    def get_saturation_priors(
        self,
        channels: Optional[list] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Get saturation curve priors for specified channels.
        
        Args:
            channels: List of channel names (all channels if None)
            
        Returns:
            Dictionary mapping channel names to saturation parameters
        """
        saturation_priors = self.config.get('saturation_priors', {})
        
        if channels:
            result = {}
            default_prior = saturation_priors.get('default', {
                'hill_ec': 0.5,
                'hill_slope': 2.0
            })
            
            for channel in channels:
                result[channel] = saturation_priors.get(channel, default_prior)
                
            return result
        else:
            return {k: v for k, v in saturation_priors.items() if k != 'default'}
            
    def get_adstock_priors(
        self,
        channels: Optional[list] = None
    ) -> Dict[str, Dict[str, Union[int, float]]]:
        """
        Get adstock (lagged effects) priors for specified channels.
        
        Args:
            channels: List of channel names (all channels if None)
            
        Returns:
            Dictionary mapping channel names to adstock parameters
        """
        adstock_priors = self.config.get('adstock_priors', {})
        
        if channels:
            result = {}
            default_prior = adstock_priors.get('default', {
                'max_lag': 8,
                'decay_rate': 0.6,
                'peak_lag': 1
            })
            
            for channel in channels:
                result[channel] = adstock_priors.get(channel, default_prior)
                
            return result
        else:
            return {k: v for k, v in adstock_priors.items() if k != 'default'}
            
    def get_coverage_factors(
        self,
        channels: Optional[list] = None
    ) -> Dict[str, float]:
        """
        Get coverage factors (sell-in to sell-out adjustments).
        
        Args:
            channels: List of channel names (all channels if None)
            
        Returns:
            Dictionary mapping channel names to coverage factors
        """
        coverage_factors = self.config.get('coverage_factors', {})
        
        if channels:
            result = {}
            default_factor = coverage_factors.get('default', 1.0)
            
            for channel in channels:
                channel_config = coverage_factors.get(channel, {'factor': default_factor})
                result[channel] = channel_config.get('factor', default_factor)
                
            return result
        else:
            return {
                k: v.get('factor', 1.0) if isinstance(v, dict) else v
                for k, v in coverage_factors.items()
                if k != 'default'
            }
            
    def get_control_priors(self) -> Dict[str, Dict[str, float]]:
        """
        Get priors for control variables.
        
        Returns:
            Dictionary mapping control variable names to prior parameters
        """
        return self.config.get('control_priors', {})
        
    def apply_coverage_factors(
        self,
        roi_dict: Dict[str, float],
        channels: Optional[list] = None
    ) -> Dict[str, float]:
        """
        Apply coverage factors to ROI values.
        
        Coverage factors > 1.0 increase ROI (sell-out coverage < sell-in)
        Coverage factors < 1.0 decrease ROI (sell-out coverage > sell-in)
        
        Args:
            roi_dict: Dictionary of channel ROIs
            channels: List of channels to adjust (all if None)
            
        Returns:
            Adjusted ROI dictionary
        """
        coverage_factors = self.get_coverage_factors(channels or list(roi_dict.keys()))
        
        adjusted_roi = {}
        for channel, roi in roi_dict.items():
            factor = coverage_factors.get(channel, 1.0)
            adjusted_roi[channel] = roi * factor
            
            if factor != 1.0:
                logger.info(
                    f"Applied coverage factor {factor:.2f} to '{channel}': "
                    f"ROI {roi:.3f} -> {adjusted_roi[channel]:.3f}"
                )
                
        return adjusted_roi
        
    def create_meridian_prior_dict(
        self,
        channels: list,
        prior_type: str = 'roi'
    ) -> Dict:
        """
        Create prior dictionary in Meridian's expected format.
        
        Args:
            channels: List of channel names
            prior_type: Type of prior ('roi', 'mroi', 'contribution', 'coefficient')
            
        Returns:
            Dictionary suitable for Meridian model specification
        """
        if not TFP_AVAILABLE:
            logger.warning("TensorFlow Probability not available. Cannot create priors.")
            return {}
            
        prior_dict = {}
        
        if prior_type == 'roi':
            for channel in channels:
                dist = self.get_roi_prior_distribution(channel)
                if dist:
                    prior_dict[channel] = dist
                    
        # Additional prior types can be added here
        
        return prior_dict
        
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the loaded configuration.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check if config is loaded
        if not self.config:
            results['valid'] = False
            results['errors'].append("No configuration loaded")
            return results
            
        # Check for required sections
        required_sections = ['roi_priors']
        for section in required_sections:
            if section not in self.config:
                results['warnings'].append(f"Missing recommended section: {section}")
                
        # Validate ROI priors
        roi_priors = self.config.get('roi_priors', {})
        for channel, params in roi_priors.items():
            if channel == 'default':
                continue
                
            if not isinstance(params, dict):
                results['errors'].append(
                    f"ROI prior for '{channel}' should be a dictionary"
                )
                continue
                
            # Check for required parameters
            if 'distribution' not in params:
                results['warnings'].append(
                    f"ROI prior for '{channel}' missing 'distribution' parameter"
                )
                
            # Validate LogNormal parameters
            if params.get('distribution') == 'lognormal':
                if 'loc' not in params or 'scale' not in params:
                    results['errors'].append(
                        f"LogNormal prior for '{channel}' must have 'loc' and 'scale'"
                    )
                elif params['scale'] <= 0:
                    results['errors'].append(
                        f"Scale parameter for '{channel}' must be positive"
                    )
                    
        # Validate coverage factors
        coverage_factors = self.config.get('coverage_factors', {})
        for channel, config in coverage_factors.items():
            if channel == 'default':
                continue
                
            factor = config.get('factor', 1.0) if isinstance(config, dict) else config
            
            if not isinstance(factor, (int, float)):
                results['errors'].append(
                    f"Coverage factor for '{channel}' must be numeric"
                )
            elif factor <= 0:
                results['errors'].append(
                    f"Coverage factor for '{channel}' must be positive"
                )
            elif factor > 2.0 or factor < 0.5:
                results['warnings'].append(
                    f"Coverage factor for '{channel}' is unusual: {factor} "
                    "(typical range is 0.8-1.2)"
                )
                
        results['valid'] = len(results['errors']) == 0
        
        if results['valid']:
            logger.success("Priors configuration is valid")
        else:
            logger.error("Priors configuration validation failed")
            for error in results['errors']:
                logger.error(f"  - {error}")
                
        if results['warnings']:
            for warning in results['warnings']:
                logger.warning(f"  - {warning}")
                
        return results
        
    def save_config(self, output_path: Union[str, Path]):
        """
        Save current configuration to YAML file.
        
        Args:
            output_path: Path to save configuration
        """
        output_path = Path(output_path)
        
        with open(output_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            
        logger.success(f"Configuration saved to {output_path}")

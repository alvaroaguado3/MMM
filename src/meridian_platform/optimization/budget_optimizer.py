"""
Budget Optimization Module

This module provides budget optimization capabilities using Meridian's optimizer.
Supports multiple objectives: maximize ROI, minimize cost, maximize sales.
"""

import pandas as pd
import numpy as np
import yaml
from typing import Dict, Optional, Any, List, Tuple
from pathlib import Path
from loguru import logger

try:
    from meridian.analysis import optimizer
    MERIDIAN_AVAILABLE = True
except ImportError:
    logger.warning("Meridian optimizer not available")
    MERIDIAN_AVAILABLE = False


class BudgetOptimizer:
    """
    Budget optimization using Meridian's optimizer.
    
    Supports three optimization objectives:
    1. Maximize ROI - Best return on investment
    2. Minimize Cost - Achieve target sales at minimum spend
    3. Maximize Sales - Maximum sales for given budget
    """
    
    # Constraint presets
    CONSTRAINT_PRESETS = {
        'small': {'min_pct': -10, 'max_pct': 10},
        'medium': {'min_pct': -50, 'max_pct': 50},
        'unconstrained': {'min_pct': -100, 'max_pct': 100}
    }
    
    def __init__(
        self,
        trained_model: Any,
        config_path: Optional[str] = 'config/model_defaults.yaml'
    ):
        """
        Initialize Budget Optimizer.
        
        Args:
            trained_model: Trained Meridian model
            config_path: Path to configuration file
        """
        if not MERIDIAN_AVAILABLE:
            raise ImportError("Meridian optimizer required")
        
        self.model = trained_model
        self.config = self._load_config(config_path)
        
        logger.info("BudgetOptimizer initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load optimization configuration."""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('optimization', {})
        else:
            logger.warning("Config not found, using defaults")
            return {
                'constraints': self.CONSTRAINT_PRESETS,
                'algorithm': {
                    'max_iterations': 1000,
                    'tolerance': 1e-6
                }
            }
    
    def optimize_roi(
        self,
        total_budget: float,
        constraints: str = 'medium',
        channel_constraints: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> Dict[str, Any]:
        """
        Optimize budget allocation to maximize ROI.
        
        Args:
            total_budget: Total budget to allocate
            constraints: Constraint preset ('small', 'medium', 'unconstrained')
            channel_constraints: Optional dict of channel-specific constraints
            
        Returns:
            Dictionary with optimal allocation and results
        """
        logger.info(f"Optimizing for maximum ROI with ${total_budget:,.0f} budget")
        
        # Get constraint bounds
        bounds = self._get_constraint_bounds(constraints, channel_constraints)
        
        try:
            # Run Meridian optimizer
            result = optimizer.optimize_budget(
                meridian_model=self.model,
                budget=total_budget,
                budget_bounds=bounds
            )
            
            # Extract results
            optimal_allocation = self._extract_allocation(result)
            
            # Calculate metrics
            metrics = self._calculate_metrics(optimal_allocation, total_budget)
            
            logger.success(f"Optimization complete: ROI = {metrics['total_roi']:.2%}")
            
            return {
                'allocation': optimal_allocation,
                'metrics': metrics,
                'total_budget': total_budget,
                'constraint_type': constraints
            }
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise
    
    def optimize_efficiency(
        self,
        target_sales: float,
        constraints: str = 'medium',
        channel_constraints: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> Dict[str, Any]:
        """
        Optimize to achieve target sales at minimum cost.
        
        Args:
            target_sales: Target sales/KPI to achieve
            constraints: Constraint preset
            channel_constraints: Optional channel-specific constraints
            
        Returns:
            Dictionary with optimal allocation and results
        """
        logger.info(f"Optimizing to achieve {target_sales:,.0f} sales at minimum cost")
        
        bounds = self._get_constraint_bounds(constraints, channel_constraints)
        
        try:
            # This is a conceptual implementation
            # Actual Meridian API may differ
            result = optimizer.optimize_budget(
                meridian_model=self.model,
                target_outcome=target_sales,
                budget_bounds=bounds
            )
            
            optimal_allocation = self._extract_allocation(result)
            metrics = self._calculate_metrics(optimal_allocation, None)
            
            logger.success(f"Optimization complete: Total spend = ${metrics['total_spend']:,.0f}")
            
            return {
                'allocation': optimal_allocation,
                'metrics': metrics,
                'target_sales': target_sales,
                'constraint_type': constraints
            }
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            # Fallback to current allocation
            return self._get_current_allocation()
    
    def optimize_sales(
        self,
        total_budget: float,
        constraints: str = 'medium',
        channel_constraints: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> Dict[str, Any]:
        """
        Optimize to maximize sales for given budget.
        
        This is similar to optimize_roi but focuses on absolute sales.
        
        Args:
            total_budget: Total budget available
            constraints: Constraint preset
            channel_constraints: Optional channel-specific constraints
            
        Returns:
            Dictionary with optimal allocation and results
        """
        logger.info(f"Optimizing to maximize sales with ${total_budget:,.0f} budget")
        
        bounds = self._get_constraint_bounds(constraints, channel_constraints)
        
        try:
            result = optimizer.optimize_budget(
                meridian_model=self.model,
                budget=total_budget,
                budget_bounds=bounds
            )
            
            optimal_allocation = self._extract_allocation(result)
            metrics = self._calculate_metrics(optimal_allocation, total_budget)
            
            logger.success(f"Optimization complete: Sales = {metrics['total_sales']:,.0f}")
            
            return {
                'allocation': optimal_allocation,
                'metrics': metrics,
                'total_budget': total_budget,
                'constraint_type': constraints
            }
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise
    
    def compare_scenarios(
        self,
        scenarios: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Compare multiple budget allocation scenarios.
        
        Args:
            scenarios: List of scenario dictionaries with 'name' and 'allocation'
            
        Returns:
            DataFrame comparing scenarios
        """
        logger.info(f"Comparing {len(scenarios)} scenarios...")
        
        comparisons = []
        
        for scenario in scenarios:
            name = scenario.get('name', 'Unnamed')
            allocation = scenario.get('allocation', {})
            
            metrics = self._calculate_metrics(allocation, sum(allocation.values()))
            
            comparisons.append({
                'scenario': name,
                'total_spend': metrics['total_spend'],
                'total_sales': metrics['total_sales'],
                'total_roi': metrics['total_roi'],
                **allocation
            })
        
        return pd.DataFrame(comparisons)
    
    def _get_constraint_bounds(
        self,
        constraint_type: str,
        channel_constraints: Optional[Dict] = None
    ) -> Dict[str, Tuple[float, float]]:
        """
        Get constraint bounds for optimization.
        
        Args:
            constraint_type: Preset name ('small', 'medium', 'unconstrained')
            channel_constraints: Optional channel-specific overrides
            
        Returns:
            Dictionary mapping channels to (min, max) bounds
        """
        # Get preset constraints
        if constraint_type in self.CONSTRAINT_PRESETS:
            preset = self.CONSTRAINT_PRESETS[constraint_type]
            min_pct = preset['min_pct'] / 100
            max_pct = preset['max_pct'] / 100
        else:
            # Try from config
            config_constraints = self.config.get('constraints', {})
            if constraint_type in config_constraints:
                preset = config_constraints[constraint_type]
                min_pct = preset['min_change_pct'] / 100
                max_pct = preset['max_change_pct'] / 100
            else:
                logger.warning(f"Unknown constraint type: {constraint_type}, using medium")
                min_pct = -0.5
                max_pct = 0.5
        
        # Get channels from model
        channels = self._get_channels()
        
        # Create bounds dictionary
        bounds = {
            channel: (min_pct, max_pct)
            for channel in channels
        }
        
        # Apply channel-specific overrides
        if channel_constraints:
            for channel, (min_val, max_val) in channel_constraints.items():
                if channel in bounds:
                    bounds[channel] = (min_val, max_val)
        
        return bounds
    
    def _get_channels(self) -> List[str]:
        """Get channel names from model."""
        try:
            return self.model.input_data.media.media_channel.values.tolist()
        except:
            logger.warning("Could not extract channels from model")
            return []
    
    def _extract_allocation(self, optimizer_result: Any) -> Dict[str, float]:
        """
        Extract channel allocation from optimizer result.
        
        Args:
            optimizer_result: Result from Meridian optimizer
            
        Returns:
            Dictionary mapping channels to budget amounts
        """
        # This is a placeholder - actual implementation depends on Meridian API
        try:
            if hasattr(optimizer_result, 'optimal_budget'):
                optimal_budget = optimizer_result.optimal_budget
                channels = self._get_channels()
                
                return {
                    channel: float(optimal_budget[i])
                    for i, channel in enumerate(channels)
                }
            else:
                logger.warning("Could not extract allocation from result")
                return {}
        except Exception as e:
            logger.error(f"Failed to extract allocation: {e}")
            return {}
    
    def _calculate_metrics(
        self,
        allocation: Dict[str, float],
        total_budget: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate metrics for a given allocation.
        
        Args:
            allocation: Channel allocation dictionary
            total_budget: Total budget (calculated if None)
            
        Returns:
            Dictionary with calculated metrics
        """
        total_spend = sum(allocation.values())
        
        # Get ROI for each channel from model
        try:
            roi_data = self.model.roi
            channels = self._get_channels()
            
            # Calculate weighted average ROI and total sales
            total_sales = 0
            
            for i, channel in enumerate(channels):
                if channel in allocation:
                    channel_spend = allocation[channel]
                    
                    # Extract ROI for this channel
                    if hasattr(roi_data, 'mean'):
                        channel_roi = float(roi_data.mean().values[i])
                    else:
                        channel_roi = float(roi_data[i])
                    
                    total_sales += channel_spend * channel_roi
            
            total_roi = total_sales / total_spend if total_spend > 0 else 0
            
        except Exception as e:
            logger.warning(f"Could not calculate exact metrics: {e}")
            total_sales = 0
            total_roi = 0
        
        return {
            'total_spend': total_spend,
            'total_sales': total_sales,
            'total_roi': total_roi,
            'budget_utilization': total_spend / total_budget if total_budget else 1.0
        }
    
    def _get_current_allocation(self) -> Dict[str, Any]:
        """Get current/baseline allocation from model data."""
        try:
            # Extract current spend from model input data
            media_spend = self.model.input_data.media_spend
            channels = self._get_channels()
            
            # Calculate average spend per channel
            allocation = {}
            for i, channel in enumerate(channels):
                allocation[channel] = float(media_spend[:, :, i].mean())
            
            metrics = self._calculate_metrics(allocation, sum(allocation.values()))
            
            return {
                'allocation': allocation,
                'metrics': metrics,
                'note': 'Current/baseline allocation'
            }
            
        except Exception as e:
            logger.error(f"Could not get current allocation: {e}")
            return {'error': str(e)}
    
    def create_scenario(
        self,
        name: str,
        budget_changes: Dict[str, float],
        base_allocation: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Create a custom budget scenario.
        
        Args:
            name: Scenario name
            budget_changes: Dictionary of channel budget changes
            base_allocation: Base allocation (current if None)
            
        Returns:
            Scenario dictionary with allocation and metrics
        """
        # Get base allocation if not provided
        if base_allocation is None:
            current = self._get_current_allocation()
            base_allocation = current.get('allocation', {})
        
        # Apply changes
        new_allocation = base_allocation.copy()
        for channel, change in budget_changes.items():
            if channel in new_allocation:
                new_allocation[channel] = max(0, new_allocation[channel] + change)
        
        # Calculate metrics
        metrics = self._calculate_metrics(new_allocation, sum(new_allocation.values()))
        
        return {
            'name': name,
            'allocation': new_allocation,
            'metrics': metrics,
            'changes': budget_changes
        }

"""
Meridian MMM Platform

A comprehensive Marketing Mix Modeling platform built on Google's Meridian framework.
"""

__version__ = "0.1.0"

# Make key classes easily importable
from meridian_platform.data_ingestion.media.loader import MediaDataLoader
from meridian_platform.data_ingestion.sales.loader import SalesDataLoader
from meridian_platform.data_ingestion.priors.config_loader import PriorsConfigLoader

__all__ = [
    "MediaDataLoader",
    "SalesDataLoader",
    "PriorsConfigLoader",
]

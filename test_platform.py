#!/usr/bin/env python3
"""
Quick Test Script

Tests the data loaders with sample data to verify everything works.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 60)
print("Meridian MMM Platform - Quick Test")
print("=" * 60)

# Test 1: Generate sample data
print("\n1. Generating sample data...")
try:
    from scripts.generate_sample_data import save_sample_data
    save_sample_data()
    print("✓ Sample data generated successfully")
except Exception as e:
    print(f"✗ Failed to generate sample data: {e}")
    sys.exit(1)

# Test 2: Load and validate media data
print("\n2. Testing media data loader...")
try:
    from meridian_platform.data_ingestion.media import MediaDataLoader
    
    media_loader = MediaDataLoader(
        file_path="data/sample/sample_media_data.csv"
    )
    media_data = media_loader.load_and_validate()
    
    print(f"✓ Loaded {len(media_data):,} rows of media data")
    print(f"  - Touchpoints: {media_data['touchpoint_name'].nunique()}")
    print(f"  - Geos: {media_data['geo'].nunique()}")
    print(f"  - Total spend: ${media_data['spend'].sum():,.0f}")
    
except Exception as e:
    print(f"✗ Failed to load media data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Load and validate sales data
print("\n3. Testing sales data loader...")
try:
    from meridian_platform.data_ingestion.sales import SalesDataLoader
    
    sales_loader = SalesDataLoader(
        file_path="data/sample/sample_sales_data.csv"
    )
    sales_data = sales_loader.load_and_validate()
    
    print(f"✓ Loaded {len(sales_data):,} rows of sales data")
    print(f"  - Geos: {sales_data['geo'].nunique()}")
    print(f"  - Total sales: ${sales_data['sales_value'].sum():,.0f}")
    print(f"  - Average weekly sales: ${sales_data['sales_value'].mean():,.0f}")
    
except Exception as e:
    print(f"✗ Failed to load sales data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Load priors configuration
print("\n4. Testing priors configuration loader...")
try:
    from meridian_platform.data_ingestion.priors import PriorsConfigLoader
    
    priors = PriorsConfigLoader('config/priors_template.yaml')
    priors.load_config()
    
    # Get some priors
    roi_priors = priors.get_roi_priors(['TV', 'Search_Brand', 'Facebook'])
    coverage_factors = priors.get_coverage_factors(['TV', 'Facebook'])
    
    print(f"✓ Loaded priors configuration")
    print(f"  - ROI priors configured: {len(roi_priors)}")
    print(f"  - Sample ROI prior (TV): loc={roi_priors['TV']['loc']}, scale={roi_priors['TV']['scale']}")
    
    # Validate
    validation = priors.validate_config()
    if validation['valid']:
        print(f"✓ Configuration is valid")
    else:
        print(f"⚠ Configuration has warnings: {len(validation['warnings'])}")
        
except Exception as e:
    print(f"✗ Failed to load priors: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✓ All tests passed! Platform is ready for Phase 2 development.")
print("=" * 60)
print("\nNext steps:")
print("1. Implement modeling module (src/meridian_platform/modeling/)")
print("2. Implement optimization module (src/meridian_platform/optimization/)")
print("3. Create Streamlit UI (ui/streamlit_app/)")
print("4. Build demo notebook (notebooks/01_quickstart_demo.ipynb)")
print("\nSee PROJECT_STATUS.md for detailed guidance.")

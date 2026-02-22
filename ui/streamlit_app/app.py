"""
Meridian MMM Platform - Streamlit UI

Main application for interactive Marketing Mix Modeling.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from meridian_platform import MediaDataLoader, SalesDataLoader, PriorsConfigLoader

# Try to import modeling components
try:
    from meridian_platform.modeling.model_runner import MeridianModelRunner
    from meridian_platform.optimization.budget_optimizer import BudgetOptimizer
    MODELING_AVAILABLE = True
except ImportError:
    MODELING_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Meridian MMM Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'media_data' not in st.session_state:
        st.session_state.media_data = None
    if 'sales_data' not in st.session_state:
        st.session_state.sales_data = None
    if 'priors_config' not in st.session_state:
        st.session_state.priors_config = None
    if 'model' not in st.session_state:
        st.session_state.model = None
    if 'model_results' not in st.session_state:
        st.session_state.model_results = None


def data_upload_page():
    """Data upload and validation page."""
    st.markdown('<p class="main-header">📤 Data Upload & Validation</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    # Media Data Upload
    with col1:
        st.subheader("📺 Media Data")
        
        media_file = st.file_uploader(
            "Upload Media Data (CSV or Excel)",
            type=['csv', 'xlsx'],
            key='media_upload',
            help="Upload media data with columns: date, geo, touchpoint_name, metric_value, spend"
        )
        
        if media_file:
            try:
                # Load data
                loader = MediaDataLoader(file_path=media_file)
                media_data = loader.load()
                
                # Validate
                with st.spinner("Validating media data..."):
                    validation = loader.validate(media_data)
                
                # Show validation results
                if validation['valid']:
                    st.success("✅ Validation Passed!")
                else:
                    st.error("❌ Validation Failed")
                    for error in validation['errors']:
                        st.error(f"  • {error}")
                
                # Show warnings
                if validation['warnings']:
                    with st.expander("⚠️ Warnings"):
                        for warning in validation['warnings']:
                            st.warning(warning)
                
                # Show preview
                with st.expander("📊 Data Preview", expanded=True):
                    st.dataframe(media_data.head(20), use_container_width=True)
                
                # Show statistics
                with st.expander("📈 Summary Statistics"):
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.metric("Total Rows", f"{len(media_data):,}")
                        st.metric("Touchpoints", media_data['touchpoint_name'].nunique())
                    
                    with col_b:
                        st.metric("Geos", media_data['geo'].nunique())
                        st.metric("Date Range", f"{(media_data['date'].max() - media_data['date'].min()).days} days")
                    
                    with col_c:
                        st.metric("Total Spend", f"${media_data['spend'].sum():,.0f}")
                        st.metric("Total Metric", f"{media_data['metric_value'].sum():,.0f}")
                    
                    # Detailed summary
                    st.write("**By Touchpoint:**")
                    summary = loader.get_summary()
                    st.dataframe(summary, use_container_width=True)
                
                # Save to session
                if validation['valid']:
                    st.session_state.media_data = media_data
                    st.success("✅ Media data saved to session")
                
            except Exception as e:
                st.error(f"Error loading media data: {e}")
    
    # Sales Data Upload
    with col2:
        st.subheader("💰 Sales Data")
        
        sales_file = st.file_uploader(
            "Upload Sales Data (CSV or Excel)",
            type=['csv', 'xlsx'],
            key='sales_upload',
            help="Upload sales data with columns: date, geo, sales_value"
        )
        
        if sales_file:
            try:
                # Load data
                loader = SalesDataLoader(file_path=sales_file)
                sales_data = loader.load()
                
                # Validate
                with st.spinner("Validating sales data..."):
                    validation = loader.validate(sales_data)
                
                # Show validation results
                if validation['valid']:
                    st.success("✅ Validation Passed!")
                else:
                    st.error("❌ Validation Failed")
                    for error in validation['errors']:
                        st.error(f"  • {error}")
                
                # Show warnings
                if validation['warnings']:
                    with st.expander("⚠️ Warnings"):
                        for warning in validation['warnings']:
                            st.warning(warning)
                
                # Show preview
                with st.expander("📊 Data Preview", expanded=True):
                    st.dataframe(sales_data.head(20), use_container_width=True)
                
                # Show statistics
                with st.expander("📈 Summary Statistics"):
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.metric("Total Rows", f"{len(sales_data):,}")
                        st.metric("Geos", sales_data['geo'].nunique())
                    
                    with col_b:
                        st.metric("Date Range", f"{(sales_data['date'].max() - sales_data['date'].min()).days} days")
                        st.metric("Avg Sales", f"${sales_data['sales_value'].mean():,.0f}")
                    
                    with col_c:
                        st.metric("Total Sales", f"${sales_data['sales_value'].sum():,.0f}")
                        st.metric("Std Dev", f"${sales_data['sales_value'].std():,.0f}")
                    
                    # Summary by geo
                    st.write("**By Geo:**")
                    summary = loader.get_summary()
                    st.dataframe(summary, use_container_width=True)
                
                # Save to session
                if validation['valid']:
                    st.session_state.sales_data = sales_data
                    st.success("✅ Sales data saved to session")
                
            except Exception as e:
                st.error(f"Error loading sales data: {e}")
    
    # Priors Configuration
    st.markdown("---")
    st.subheader("⚙️ Bayesian Priors Configuration")
    
    use_priors = st.checkbox("Use custom priors", value=False)
    
    if use_priors:
        priors_file = st.file_uploader(
            "Upload Priors YAML",
            type=['yaml', 'yml'],
            help="Upload Bayesian priors configuration file"
        )
        
        if priors_file:
            try:
                # Save temporarily
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as tmp:
                    tmp.write(priors_file.read())
                    tmp_path = tmp.name
                
                # Load priors
                priors_loader = PriorsConfigLoader(tmp_path)
                priors_loader.load_config()
                
                # Validate
                validation = priors_loader.validate_config()
                
                if validation['valid']:
                    st.success("✅ Priors configuration valid")
                    st.session_state.priors_config = priors_loader
                else:
                    st.error("❌ Priors configuration invalid")
                    for error in validation['errors']:
                        st.error(f"  • {error}")
                
                # Show preview
                with st.expander("Preview Priors"):
                    if st.session_state.media_data is not None:
                        channels = st.session_state.media_data['touchpoint_name'].unique().tolist()
                        roi_priors = priors_loader.get_roi_priors(channels[:5])
                        st.json(roi_priors)
                
            except Exception as e:
                st.error(f"Error loading priors: {e}")


def model_training_page():
    """Model training and configuration page."""
    st.markdown('<p class="main-header">🎓 Model Training</p>', unsafe_allow_html=True)
    
    if not MODELING_AVAILABLE:
        st.error("⚠️ Modeling modules not available. Install Meridian first.")
        return
    
    # Check if data is loaded
    if st.session_state.media_data is None or st.session_state.sales_data is None:
        st.warning("⚠️ Please upload media and sales data first")
        if st.button("Go to Data Upload"):
            st.session_state.page = "📤 Data Upload"
            st.rerun()
        return
    
    st.markdown("---")
    
    # Model configuration
    st.subheader("⚙️ Model Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        kpi_type = st.selectbox(
            "KPI Type",
            options=['non_revenue', 'revenue'],
            help="Whether KPI is revenue or another metric"
        )
        
        n_warmup = st.number_input(
            "Warmup Iterations",
            min_value=100,
            max_value=5000,
            value=1000,
            step=100,
            help="Number of MCMC warmup iterations"
        )
    
    with col2:
        n_samples = st.number_input(
            "Sampling Iterations",
            min_value=100,
            max_value=5000,
            value=1000,
            step=100,
            help="Number of MCMC sampling iterations"
        )
        
        n_chains = st.number_input(
            "Number of Chains",
            min_value=1,
            max_value=4,
            value=2,
            help="Number of parallel MCMC chains"
        )
    
    with col3:
        max_lag = st.number_input(
            "Max Lag (weeks)",
            min_value=1,
            max_value=26,
            value=13,
            help="Maximum adstock lag in time periods"
        )
        
        seed = st.number_input(
            "Random Seed",
            min_value=0,
            value=42,
            help="Random seed for reproducibility"
        )
    
    st.markdown("---")
    
    # Train button
    if st.button("🚀 Train Model", type="primary", use_container_width=True):
        try:
            with st.spinner("Training Meridian model... This may take several minutes."):
                # Initialize progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Create model runner
                status_text.text("Initializing model...")
                progress_bar.progress(10)
                
                runner = MeridianModelRunner(
                    media_data=st.session_state.media_data,
                    sales_data=st.session_state.sales_data,
                    priors_config=st.session_state.priors_config
                )
                
                # Prepare data
                status_text.text("Preparing data...")
                progress_bar.progress(20)
                runner.prepare_data()
                
                # Create model spec
                status_text.text("Creating model specification...")
                progress_bar.progress(30)
                runner.create_model_spec()
                
                # Train
                status_text.text("Training model (this takes time)...")
                progress_bar.progress(40)
                
                model = runner.train(
                    n_warmup=n_warmup,
                    n_samples=n_samples,
                    n_chains=n_chains,
                    seed=seed
                )
                
                progress_bar.progress(80)
                
                # Get diagnostics
                status_text.text("Extracting diagnostics...")
                diagnostics = runner.get_diagnostics()
                
                # Get results
                status_text.text("Extracting results...")
                progress_bar.progress(90)
                results = runner.get_results()
                
                progress_bar.progress(100)
                status_text.text("Complete!")
                
                # Save to session
                st.session_state.model = runner
                st.session_state.model_results = results
                st.session_state.diagnostics = diagnostics
                
                st.success("✅ Model training complete!")
                
                # Show quick diagnostics
                if diagnostics['convergence']['overall_converged']:
                    st.success("✅ Model converged successfully")
                else:
                    st.warning("⚠️ Convergence issues detected - review diagnostics")
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("R-hat (max)", f"{diagnostics['summary']['r_hat_max']:.4f}")
                with col_b:
                    st.metric("ESS (min)", f"{diagnostics['summary']['ess_bulk_min']:.0f}")
                with col_c:
                    if 'r_squared' in results.get('fit', {}):
                        st.metric("R-squared", f"{results['fit']['r_squared']:.3f}")
                
        except Exception as e:
            st.error(f"❌ Training failed: {e}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())


def results_page():
    """Model results and visualization page."""
    st.markdown('<p class="main-header">📊 Model Results</p>', unsafe_allow_html=True)
    
    if st.session_state.model is None:
        st.warning("⚠️ No trained model available. Please train a model first.")
        return
    
    results = st.session_state.model_results
    
    st.markdown("---")
    
    # ROI Results
    st.subheader("💰 Return on Investment (ROI)")
    
    if 'roi_adjusted' in results:
        roi_df = pd.DataFrame([
            {'Channel': ch, 'ROI': roi, 'ROI %': f"{roi*100:.1f}%"}
            for ch, roi in results['roi_adjusted'].items()
        ]).sort_values('ROI', ascending=False)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # ROI bar chart
            fig = px.bar(
                roi_df,
                x='Channel',
                y='ROI',
                title="ROI by Channel",
                color='ROI',
                color_continuous_scale='RdYlGn'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # ROI table
            st.dataframe(roi_df, use_container_width=True, hide_index=True)
    
    # More visualizations would go here...
    st.info("Additional visualizations (response curves, contributions, etc.) would be implemented here.")


def optimization_page():
    """Budget optimization page."""
    st.markdown('<p class="main-header">💰 Budget Optimization</p>', unsafe_allow_html=True)
    
    if not MODELING_AVAILABLE:
        st.error("⚠️ Optimization modules not available.")
        return
    
    if st.session_state.model is None:
        st.warning("⚠️ No trained model available. Please train a model first.")
        return
    
    st.markdown("---")
    
    # Optimization parameters
    st.subheader("⚙️ Optimization Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        objective = st.selectbox(
            "Objective",
            options=['Maximize ROI', 'Minimize Cost', 'Maximize Sales'],
            help="Optimization objective"
        )
        
        total_budget = st.number_input(
            "Total Budget ($)",
            min_value=0.0,
            value=1000000.0,
            step=10000.0,
            help="Total budget to allocate"
        )
    
    with col2:
        constraints = st.selectbox(
            "Constraints",
            options=['small', 'medium', 'unconstrained'],
            index=1,
            help="Budget change constraints: small (±10%), medium (±50%), unconstrained (±100%)"
        )
    
    if st.button("🎯 Optimize Budget", type="primary"):
        try:
            with st.spinner("Running optimization..."):
                optimizer = BudgetOptimizer(st.session_state.model.model)
                
                if objective == 'Maximize ROI':
                    result = optimizer.optimize_roi(total_budget, constraints)
                elif objective == 'Maximize Sales':
                    result = optimizer.optimize_sales(total_budget, constraints)
                else:
                    st.info("Minimize Cost optimization requires target sales input")
                    return
                
                st.success("✅ Optimization complete!")
                
                # Display results
                allocation_df = pd.DataFrame([
                    {'Channel': ch, 'Budget': f"${budget:,.0f}"}
                    for ch, budget in result['allocation'].items()
                ]).sort_values('Budget', ascending=False)
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.write("**Optimal Allocation:**")
                    st.dataframe(allocation_df, use_container_width=True)
                
                with col_b:
                    st.write("**Metrics:**")
                    metrics = result['metrics']
                    st.metric("Total Spend", f"${metrics['total_spend']:,.0f}")
                    st.metric("Projected Sales", f"${metrics['total_sales']:,.0f}")
                    st.metric("Overall ROI", f"{metrics['total_roi']:.2%}")
                
        except Exception as e:
            st.error(f"Optimization failed: {e}")


def main():
    """Main application."""
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/1f77b4/ffffff?text=Meridian+MMM", use_container_width=True)
        
        st.markdown("### Navigation")
        
        page = st.radio(
            "Go to",
            ["📤 Data Upload", "🎓 Model Training", "📊 Results", "💰 Optimization"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Session status
        st.markdown("### Session Status")
        
        st.write("**Data:**")
        st.write(f"✅ Media" if st.session_state.media_data is not None else "❌ Media")
        st.write(f"✅ Sales" if st.session_state.sales_data is not None else "❌ Sales")
        
        st.write("**Model:**")
        st.write(f"✅ Trained" if st.session_state.model is not None else "❌ Not trained")
        
        st.markdown("---")
        
        if st.button("🗑️ Clear Session"):
            for key in ['media_data', 'sales_data', 'priors_config', 'model', 'model_results']:
                st.session_state[key] = None
            st.rerun()
    
    # Main content
    if page == "📤 Data Upload":
        data_upload_page()
    elif page == "🎓 Model Training":
        model_training_page()
    elif page == "📊 Results":
        results_page()
    elif page == "💰 Optimization":
        optimization_page()


if __name__ == '__main__':
    main()

"""
Meridian MMM Platform - Streamlit UI

Main application for interactive Marketing Mix Modeling.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
from PIL import Image

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

# Try to import Meridian visualizer classes
try:
    from meridian.analysis.visualizer import (
        ModelDiagnostics, ModelFit, MediaEffects, MediaSummary
    )
    VISUALIZER_AVAILABLE = True
except ImportError:
    VISUALIZER_AVAILABLE = False

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
    if 'population_data' not in st.session_state:
        st.session_state.population_data = None
    if 'model' not in st.session_state:
        st.session_state.model = None
    if 'model_results' not in st.session_state:
        st.session_state.model_results = None
    if 'training_just_completed' not in st.session_state:
        st.session_state.training_just_completed = False


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
                # Load data - read uploaded file into DataFrame first
                if media_file.name.endswith('.csv'):
                    df = pd.read_csv(media_file)
                else:
                    df = pd.read_excel(media_file)
                loader = MediaDataLoader(dataframe=df)
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
                # Load data - read uploaded file into DataFrame first
                if sales_file.name.endswith('.csv'):
                    df = pd.read_csv(sales_file)
                else:
                    df = pd.read_excel(sales_file)
                loader = SalesDataLoader(dataframe=df)
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
    
    # Population Data Upload
    st.markdown("---")
    st.subheader("👥 Population Data")

    population_file = st.file_uploader(
        "Upload Population Data (CSV or Excel)",
        type=['csv', 'xlsx'],
        key='population_upload',
        help="Upload population data with columns: geo, population (one row per geo)"
    )

    if population_file:
        try:
            if population_file.name.endswith('.csv'):
                pop_df = pd.read_csv(population_file)
            else:
                pop_df = pd.read_excel(population_file)

            st.session_state.population_data = pop_df
            st.success(f"✅ Population data loaded: {len(pop_df)} geos")
            with st.expander("📊 Population Preview"):
                st.dataframe(pop_df, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading population data: {e}")

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
    if st.session_state.media_data is None or st.session_state.sales_data is None or st.session_state.population_data is None:
        st.warning("⚠️ Please upload media, sales, and population data first")
        if st.button("Go to Data Upload"):
            st.session_state.page = "📤 Data Upload"
            st.rerun()
        return
    
    st.markdown("---")
    
    # Model configuration
    st.subheader("⚙️ Model Configuration")
    
    aggregate_weekly = st.checkbox(
        "Aggregate data to weekly",
        value=True,
        help="Strongly recommended. Reduces daily data to weekly, making training much faster."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        kpi_type = st.selectbox(
            "KPI Type",
            options=['non_revenue', 'revenue'],
            help="Whether KPI is revenue or another metric"
        )

        n_warmup = st.number_input(
            "Warmup Iterations",
            min_value=50,
            max_value=5000,
            value=500,
            step=50,
            help="Number of MCMC adaptation/burn-in iterations"
        )

    with col2:
        n_samples = st.number_input(
            "Sampling Iterations",
            min_value=50,
            max_value=5000,
            value=500,
            step=50,
            help="Number of MCMC samples to keep"
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
            value=8,
            help="Maximum adstock lag in time periods"
        )
        
        seed = st.number_input(
            "Random Seed",
            min_value=0,
            value=42,
            help="Random seed for reproducibility"
        )
    
    st.markdown("---")

    # Show post-training success message after rerun
    if st.session_state.training_just_completed:
        st.session_state.training_just_completed = False
        st.success("Model training complete!")
        diagnostics = st.session_state.get('diagnostics', {})
        if diagnostics.get('convergence', {}).get('overall_converged'):
            st.success("Model converged successfully")
        else:
            st.warning("Convergence issues detected - review diagnostics below")
        if 'summary' in diagnostics:
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("R-hat (max)", f"{diagnostics['summary']['r_hat_max']:.4f}")
            with col_b:
                st.metric("R-hat (mean)", f"{diagnostics['summary']['r_hat_mean']:.4f}")

    # Train button
    if st.button("🚀 Train Model", type="primary", use_container_width=True):
        try:
            with st.spinner("Training Meridian model... This may take several minutes."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text("Initializing model...")
                progress_bar.progress(10)

                runner = MeridianModelRunner(
                    media_data=st.session_state.media_data,
                    sales_data=st.session_state.sales_data,
                    population_data=st.session_state.population_data,
                    priors_config=st.session_state.priors_config
                )

                status_text.text("Preparing data...")
                progress_bar.progress(20)
                runner.prepare_data(aggregate_weekly=aggregate_weekly)

                status_text.text("Creating model specification...")
                progress_bar.progress(30)
                runner.create_model_spec()

                status_text.text("Training model (this takes time)...")
                progress_bar.progress(40)

                runner.train(
                    n_warmup=n_warmup,
                    n_samples=n_samples,
                    n_chains=n_chains,
                    seed=seed
                )

                progress_bar.progress(80)

                status_text.text("Extracting diagnostics...")
                diagnostics = runner.get_diagnostics()

                status_text.text("Extracting results...")
                progress_bar.progress(90)
                results = runner.get_results()

                progress_bar.progress(100)
                status_text.text("Complete!")

                st.session_state.model = runner
                st.session_state.model_results = results
                st.session_state.diagnostics = diagnostics
                st.session_state.training_just_completed = True

                st.rerun()

        except Exception as e:
            st.error(f"Training failed: {e}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())

    # Training diagnostics (shown when a model exists)
    if st.session_state.model is not None and VISUALIZER_AVAILABLE:
        st.markdown("---")
        st.subheader("Model Diagnostics")

        meridian_model = st.session_state.model.model

        try:
            diag = ModelDiagnostics(meridian_model)

            st.markdown("**R-hat Convergence**")
            try:
                rhat_chart = diag.plot_rhat_boxplot()
                st.altair_chart(rhat_chart, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render R-hat boxplot: {e}")

            st.markdown("**Prior vs Posterior Distribution**")
            try:
                param_options = ['roi_m', 'beta_m', 'alpha', 'ec', 'slope']
                selected_param = st.selectbox(
                    "Parameter", param_options, key="diag_param"
                )
                pp_chart = diag.plot_prior_and_posterior_distribution(
                    parameter=selected_param
                )
                st.altair_chart(pp_chart, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render prior/posterior plot: {e}")

            st.markdown("**Predictive Accuracy**")
            try:
                acc_table = diag.predictive_accuracy_table()
                st.dataframe(acc_table, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render predictive accuracy table: {e}")

        except Exception as e:
            st.warning(f"Could not initialize diagnostics visualizer: {e}")


def results_page():
    """Model results and visualization page."""
    st.markdown('<p class="main-header">📊 Model Results</p>', unsafe_allow_html=True)

    if st.session_state.model is None:
        st.warning("No trained model available. Please train a model first.")
        return

    if not VISUALIZER_AVAILABLE:
        st.error("Meridian visualizer classes not available. Install meridian package.")
        return

    meridian_model = st.session_state.model.model

    tab_overview, tab_roi, tab_contrib, tab_response, tab_fit = st.tabs([
        "Overview", "ROI & Effectiveness", "Contributions",
        "Response Curves & Adstock", "Model Fit"
    ])

    # --- Tab 1: Overview ---
    with tab_overview:
        st.subheader("Summary Metrics")
        try:
            summary_viz = MediaSummary(meridian_model)
            summary_df = summary_viz.summary_table()
            st.dataframe(summary_df, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not render summary table: {e}")

        st.subheader("Predictive Accuracy")
        try:
            diag = ModelDiagnostics(meridian_model)
            acc_table = diag.predictive_accuracy_table()
            st.dataframe(acc_table, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not render predictive accuracy: {e}")

        st.subheader("ROI Ranking")
        try:
            results = st.session_state.model_results
            if 'roi_adjusted' in results:
                roi_df = pd.DataFrame([
                    {'Channel': ch, 'ROI': roi}
                    for ch, roi in results['roi_adjusted'].items()
                ]).sort_values('ROI', ascending=False)
                st.dataframe(roi_df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"Could not render ROI ranking: {e}")

    # --- Tab 2: ROI & Effectiveness ---
    with tab_roi:
        try:
            summary_viz = MediaSummary(meridian_model)
        except Exception as e:
            st.error(f"Could not initialize MediaSummary: {e}")
            summary_viz = None

        if summary_viz:
            st.subheader("ROI by Channel")
            try:
                roi_chart = summary_viz.plot_roi_bar_chart(include_ci=True)
                st.altair_chart(roi_chart, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render ROI bar chart: {e}")

            st.subheader("Cost per Incremental KPI (CPIK)")
            try:
                cpik_chart = summary_viz.plot_cpik(include_ci=True)
                st.altair_chart(cpik_chart, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render CPIK chart: {e}")

            st.subheader("ROI vs Marginal ROI")
            try:
                roi_mroi_chart = summary_viz.plot_roi_vs_mroi()
                st.altair_chart(roi_mroi_chart, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render ROI vs mROI: {e}")

            st.subheader("ROI vs Effectiveness")
            try:
                roi_eff_chart = summary_viz.plot_roi_vs_effectiveness()
                st.altair_chart(roi_eff_chart, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render ROI vs Effectiveness: {e}")

    # --- Tab 3: Contributions ---
    with tab_contrib:
        try:
            summary_viz = MediaSummary(meridian_model)
        except Exception as e:
            st.error(f"Could not initialize MediaSummary: {e}")
            summary_viz = None

        if summary_viz:
            st.subheader("Contribution Waterfall")
            try:
                waterfall = summary_viz.plot_contribution_waterfall_chart()
                st.altair_chart(waterfall, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render waterfall chart: {e}")

            st.subheader("Contribution Pie Chart")
            try:
                pie_chart = summary_viz.plot_contribution_pie_chart()
                st.altair_chart(pie_chart, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render pie chart: {e}")

            st.subheader("Channel Contribution Over Time")
            try:
                granularity = st.selectbox(
                    "Time Granularity",
                    ["weekly", "monthly", "quarterly"],
                    index=2,
                    key="contrib_granularity"
                )
                area_chart = summary_viz.plot_channel_contribution_area_chart(
                    time_granularity=granularity
                )
                st.altair_chart(area_chart, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render area chart: {e}")

            st.subheader("Spend vs Contribution")
            try:
                spend_contrib = summary_viz.plot_spend_vs_contribution()
                st.altair_chart(spend_contrib, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render spend vs contribution: {e}")

    # --- Tab 4: Response Curves & Adstock ---
    with tab_response:
        try:
            effects = MediaEffects(meridian_model)
        except Exception as e:
            st.error(f"Could not initialize MediaEffects: {e}")
            effects = None

        if effects:
            st.subheader("Response Curves")
            try:
                response_chart = effects.plot_response_curves(include_ci=True)
                st.altair_chart(response_chart, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render response curves: {e}")

            st.subheader("Hill Saturation Curves")
            try:
                hill_charts = effects.plot_hill_curves()
                # plot_hill_curves returns a dict: {channel_type: alt.Chart}
                for chart_name, chart in hill_charts.items():
                    st.markdown(f"**{chart_name}**")
                    st.altair_chart(chart, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render Hill curves: {e}")

            st.subheader("Adstock Decay")
            try:
                adstock_chart = effects.plot_adstock_decay(include_ci=True)
                st.altair_chart(adstock_chart, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render adstock decay: {e}")

    # --- Tab 5: Model Fit ---
    with tab_fit:
        try:
            model_fit = ModelFit(meridian_model)
        except Exception as e:
            st.error(f"Could not initialize ModelFit: {e}")
            model_fit = None

        if model_fit:
            st.subheader("Expected vs Actual Outcome")
            show_geo = st.checkbox("Show geo-level breakdown", value=False,
                                   key="fit_geo_level")
            show_ci = st.checkbox("Include confidence interval", value=True,
                                  key="fit_ci")
            try:
                fit_chart = model_fit.plot_model_fit(
                    show_geo_level=show_geo,
                    include_ci=show_ci
                )
                st.altair_chart(fit_chart, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render model fit chart: {e}")


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
        logo = Image.open("ui/assets/logo.png")
        st.image(logo, use_container_width=True)
        
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
        st.write(f"✅ Population" if st.session_state.population_data is not None else "❌ Population")
        
        st.write("**Model:**")
        st.write(f"✅ Trained" if st.session_state.model is not None else "❌ Not trained")
        
        st.markdown("---")
        
        if st.button("🗑️ Clear Session"):
            for key in ['media_data', 'sales_data', 'population_data', 'priors_config', 'model', 'model_results']:
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

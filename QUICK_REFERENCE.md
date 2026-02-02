# Quick Reference Card - Meridian MMM Platform

## 🚀 Quick Start (5 minutes)

```bash
cd meridian-mmm-platform
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python test_platform.py
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview and usage |
| `PROJECT_STATUS.md` | What's done, what's next |
| `DEVELOPER_GUIDE.md` | How to build remaining parts |
| `IMPLEMENTATION_SUMMARY.md` | Phase 1 complete summary |
| `config/priors_template.yaml` | Bayesian priors (ROI, saturation, etc.) |
| `config/model_defaults.yaml` | Model hyperparameters |
| `test_platform.py` | Validate installation |

## 💻 Code Usage

### Load Media Data
```python
from meridian_platform import MediaDataLoader

loader = MediaDataLoader('data/sample/sample_media_data.csv')
media = loader.load_and_validate()
summary = loader.get_summary()
```

### Load Sales Data
```python
from meridian_platform import SalesDataLoader

loader = SalesDataLoader('data/sample/sample_sales_data.csv')
sales = loader.load_and_validate()
summary = loader.get_summary()
```

### Configure Priors
```python
from meridian_platform import PriorsConfigLoader

priors = PriorsConfigLoader('config/priors_template.yaml')
priors.load_config()
roi_priors = priors.get_roi_priors(['TV', 'Facebook'])
coverage = priors.get_coverage_factors()
```

## 📊 What Works Now

✅ Media data ingestion with validation  
✅ Sales data ingestion with validation  
✅ Bayesian priors configuration  
✅ Sample data generation  
✅ xarray conversion for Meridian  

## 🔧 What to Build Next

1. **Modeling** (`src/meridian_platform/modeling/model_runner.py`)
2. **Optimization** (`src/meridian_platform/optimization/budget_optimizer.py`)
3. **Streamlit UI** (`ui/streamlit_app/app.py`)
4. **Demo Notebook** (`notebooks/01_quickstart_demo.ipynb`)

## 📚 Documentation Hierarchy

```
Start Here → README.md
  ↓
Implementation Status → PROJECT_STATUS.md
  ↓
How to Build → DEVELOPER_GUIDE.md
  ↓
What You Got → IMPLEMENTATION_SUMMARY.md
```

## 🔗 Key Meridian Links

- Docs: https://developers.google.com/meridian
- Getting Started: https://developers.google.com/meridian/notebook/meridian-getting-started
- GitHub: https://github.com/google/meridian
- API Reference: https://developers.google.com/meridian/reference/api/meridian

## ⚡ Common Commands

```bash
# Generate sample data
python scripts/generate_sample_data.py

# Run tests (after implementing)
pytest tests/

# Install for development
pip install -e .

# Start UI (after implementing)
streamlit run ui/streamlit_app/app.py
```

## 🎯 Success Metrics

Phase 1 is complete when:
- [x] Data loaders work
- [x] Validation catches issues
- [ ] Model trains successfully
- [ ] Optimization runs
- [ ] UI displays results
- [ ] Notebook demonstrates workflow

**Current: Infrastructure Complete (40%)**  
**Next: Application Layer (60%)**

## 💡 Pro Tips

1. **Read DEVELOPER_GUIDE.md first** - It has code templates
2. **Start with modeling module** - Everything else builds on it
3. **Use sample data for testing** - Known ground truth
4. **Check convergence** - R-hat < 1.05, ESS > 400
5. **GPU strongly recommended** - 10x faster training

## 📞 Get Help

- Meridian Issues: https://github.com/google/meridian/issues
- Meridian Discussions: https://github.com/google/meridian/discussions
- Documentation: All key files have extensive comments

---

**Remember:** You have a solid foundation. Build iteratively, test frequently, ask for Phase 2 when ready!

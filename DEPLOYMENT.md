# Streamlit Deployment Guide

This guide explains how to deploy the Meridian MMM Platform to Streamlit Community Cloud.

## Prerequisites

1. **GitHub Account** - Your repository is already on GitHub
2. **Streamlit Account** - Sign up at [share.streamlit.io](https://share.streamlit.io)
3. **Public Repository** - Your repo must be public (or you need Streamlit Teams)

## Deployment Steps

### 1. Prepare Your Repository

Your repository should have these files (already created):

```
.streamlit/
├── config.toml          # Streamlit configuration
└── secrets.toml.example # Template for secrets

requirements-streamlit.txt  # Streamlit-specific dependencies
packages.txt               # System packages
```

### 2. Deploy to Streamlit Community Cloud

#### Option A: Via Streamlit Share Website

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Fill in the details:
   - **Repository**: `alvaroaguado3/MMM`
   - **Branch**: `main`
   - **Main file path**: `ui/streamlit_app/app.py`
5. Click "Deploy!"

#### Option B: Via Direct URL

Visit this URL (replace with your repo):
```
https://share.streamlit.io/deploy?repository=alvaroaguado3/MMM&branch=main&mainModule=ui/streamlit_app/app.py
```

### 3. Configure Secrets (Optional)

If you're using a database or API keys:

1. In Streamlit Cloud, go to your app's settings
2. Navigate to "Secrets" section
3. Copy content from `.streamlit/secrets.toml.example`
4. Paste and update with your actual values
5. Save

### 4. Monitor Deployment

- Watch the deployment logs in Streamlit Cloud
- Initial deployment may take 3-5 minutes
- Your app will be available at: `https://<your-app-name>.streamlit.app`

## Configuration Files Explained

### requirements-streamlit.txt

Contains Python dependencies optimized for Streamlit Cloud:
- Uses CPU-only JAX (GPU not available on Streamlit Cloud)
- Includes all necessary data science packages
- Streamlit and visualization libraries

### packages.txt

System-level packages installed via apt-get:
- `build-essential` - Compilation tools
- `libgomp1` - OpenMP runtime library

### .streamlit/config.toml

Streamlit app configuration:
- Theme colors matching your branding
- Server settings for cloud deployment
- Browser settings

## Limitations on Streamlit Cloud

### Resource Limits (Free Tier)
- **CPU**: 1 vCPU
- **RAM**: 1 GB
- **Storage**: Limited to repository files
- **No GPU support** (models will run on CPU)

### Recommendations
1. **Use smaller datasets** for demos (< 1 year of data)
2. **Reduce MCMC iterations** (500 warmup, 500 samples)
3. **Limit to 1 chain** to reduce memory usage
4. **Weekly aggregation** is strongly recommended
5. **Use sample data** for demonstration purposes

## Troubleshooting

### Issue: App crashes with "Out of memory"

**Solution**: Reduce dataset size or model complexity
```python
# In model training page
n_warmup = 250  # Reduced
n_samples = 250  # Reduced
n_chains = 1    # Single chain
```

### Issue: Import errors for local modules

**Solution**: Ensure `src/` is in Python path (already handled in app.py)

### Issue: Missing assets (logo/images)

**Solution**: Ensure files are committed to GitHub
```bash
git add ui/assets/*.png
git commit -m "Add UI assets"
git push origin main
```

### Issue: Slow model training

**Expected behavior** - CPU-only training on Streamlit Cloud is slower than local GPU training. Set realistic expectations for users.

## Advanced Configuration

### Custom Domain (Streamlit Teams Only)

1. Go to app settings in Streamlit Cloud
2. Navigate to "General" → "Custom subdomain"
3. Enter your desired subdomain
4. Update DNS records as instructed

### Authentication (Streamlit Teams Only)

1. In app settings, go to "Authentication"
2. Choose authentication method:
   - Email-based
   - Google OAuth
   - SAML SSO

### Resource Scaling (Paid Plans)

Upgrade to Streamlit Teams or Enterprise for:
- More CPU/RAM
- Multiple apps
- Team collaboration
- Priority support

## Local Development

To run locally with the same dependencies:

```bash
# Install Streamlit-specific requirements
pip install -r requirements-streamlit.txt

# Run app
streamlit run ui/streamlit_app/app.py
```

## Updating Your Deployed App

Any push to your `main` branch will automatically trigger a redeploy:

```bash
git add .
git commit -m "Update app"
git push origin main
```

Streamlit Cloud will:
1. Detect the push
2. Pull latest code
3. Reinstall dependencies if requirements changed
4. Restart the app

## Monitoring

### View Logs

In Streamlit Cloud:
1. Go to your app
2. Click "Manage app" (⋮ menu)
3. View "Logs" tab

### Analytics

Track app usage:
1. Go to app settings
2. Navigate to "Analytics"
3. View visitors, sessions, and usage patterns

## Security Best Practices

1. **Never commit secrets** - Use Streamlit Secrets for sensitive data
2. **Add .streamlit/secrets.toml to .gitignore** (already done)
3. **Use environment variables** for configuration
4. **Validate all user inputs** in the app
5. **Limit file upload sizes** to prevent abuse

## Sample Data for Demo

Your repository includes sample data files:
- `data/sample/sample_media_data.csv`
- `data/sample/sample_sales_data.csv`
- `data/sample/sample_population_data.csv`

These are perfect for demonstrating the app on Streamlit Cloud.

## Support

- **Streamlit Community**: [discuss.streamlit.io](https://discuss.streamlit.io)
- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)
- **GitHub Issues**: Report issues in your repository

## Next Steps

1. ✅ Deploy to Streamlit Cloud using steps above
2. ✅ Test with sample data
3. ✅ Share your app URL with stakeholders
4. 📊 Monitor usage and gather feedback
5. 🚀 Iterate and improve

Your app will be available at:
```
https://mmm-meridian.streamlit.app
```
(or similar, depending on availability)

---

**Note**: For production use with larger datasets and faster training, consider deploying to:
- AWS EC2 with GPU
- Google Cloud Platform with GPUs
- Azure with compute instances

See main README for production deployment guides.

# Historical Trend Analysis - Part 3

## Overview
This module focuses on identifying trends through historical performance of stores to proactively adapt the retail mix to emerging trends (Part 3 of the URW Data Challenge).

## Notebook: `trend_analysis.ipynb`

### What it Does

The notebook performs comprehensive trend analysis on historical store performance data:

1. **Temporal Pattern Analysis**
   - Daily, weekly, and monthly traffic patterns
   - Seasonality detection (weekly and yearly cycles)
   - Time series decomposition

2. **Category Performance Trends**
   - Growth rate analysis by store category (BL1, BL2, BL3 levels)
   - Statistical significance testing
   - Emerging vs. declining category identification

3. **Forecasting**
   - 90-day traffic forecasts using Facebook Prophet
   - Category-specific forecasts
   - Confidence intervals and trend components

4. **Store Performance Metrics**
   - Conversion rates (people in / window flow)
   - Sales per square meter
   - Traffic per square meter
   - Profit margins

5. **Actionable Insights**
   - Identifies which store categories are gaining traction
   - Identifies which categories are declining
   - Provides recommendations for retail mix optimization

## Key Outputs

### Processed Data (saved to `data/processed/`)
- `category_trends.csv` - Monthly trends by store category
- `bl1_growth_analysis.csv` - Growth rates for high-level categories
- `bl2_growth_analysis.csv` - Growth rates for mid-level categories
- `store_performance_metrics.csv` - Comprehensive store KPIs
- `daily_traffic.csv` - Daily aggregate traffic data
- `day_of_week_patterns.csv` - Weekly seasonality patterns
- `monthly_patterns.csv` - Monthly seasonality patterns
- `traffic_forecast.csv` - 90-day traffic predictions
- `key_insights.json` - Summary insights for dashboard

### Models (saved to `models/`)
- `traffic_forecast_model.pkl` - Trained Prophet model for overall traffic
- `forecast_<category>.csv` - Forecasts for individual categories

## Dependencies

The analysis requires the following additional packages (added to `pyproject.toml`):
- `prophet>=1.1.5` - Time series forecasting
- `seaborn>=0.13.0` - Statistical visualizations
- `scipy>=1.15.0` - Statistical analysis

Existing dependencies used:
- `pandas` - Data manipulation
- `statsmodels` - Time series decomposition
- `plotly` - Interactive visualizations
- `matplotlib` - Static plots

## How to Use

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Run the notebook**:
   - Open `notebooks/trend_analysis.ipynb` in Jupyter/VS Code
   - Run all cells sequentially
   - Review visualizations and insights

3. **For Streamlit Integration**:
   - The notebook exports all processed data to `data/processed/`
   - Load these CSV files in your Streamlit app
   - Use `key_insights.json` for summary metrics
   - Load trained models from `models/` for real-time forecasting

## Key Findings to Integrate into Dashboard

The analysis provides:

1. **Trend Classifications**:
   - Strongly Emerging (>5% monthly growth)
   - Emerging (positive growth)
   - Stable (no significant trend)
   - Declining (negative growth)
   - Strongly Declining (<-5% monthly growth)

2. **Seasonality Insights**:
   - Busiest day of week
   - Busiest month of year
   - Weekly traffic patterns

3. **Forecasts**:
   - Overall mall traffic predictions
   - Category-specific predictions
   - Confidence intervals for planning

## Streamlit Dashboard Integration

### Suggested Dashboard Components:

1. **Trend Overview Tab**:
   - Display emerging vs. declining categories
   - Show monthly trend charts
   - Highlight top performing store types

2. **Forecast Tab**:
   - Interactive 90-day traffic forecast
   - Category-specific forecasts
   - Scenario planning tools

3. **Seasonality Tab**:
   - Weekly pattern visualization
   - Monthly pattern visualization
   - Year-over-year comparisons

4. **Recommendations Tab**:
   - Auto-generated recommendations based on trends
   - Suggested tenant mix adjustments
   - Risk alerts for declining categories

## Future Enhancements

- [ ] Add ARIMA/SARIMA models for comparison
- [ ] Implement anomaly detection for unusual trends
- [ ] Add competitor analysis if data becomes available
- [ ] Create automated alert system for significant trend changes
- [ ] Build A/B testing framework for tenant mix changes
- [ ] Add external factors (holidays, events, weather) to models

## Data Sources

- `data/raw/fact_stores_v1.csv` - Store-level daily metrics
- `data/raw/fact_malls_v1.csv` - Mall-level daily metrics
- `data/raw/store_financials_v1.csv` - Annual financial data
- `data/raw/dim_blocks_v1.csv` - Store category information
- `data/raw/dim_malls_v1.csv` - Mall information

## Notes

- The notebook handles missing values appropriately
- Statistical significance testing ensures trends are not random noise
- Prophet model captures both weekly and yearly seasonality
- All visualizations are interactive (Plotly) for easy dashboard integration

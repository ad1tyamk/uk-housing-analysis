Does the Bank of England's interest rate affect house prices the same way everywhere? I built an end-to-end pipeline and analysis to find out, using 20.8M residential transactions (2003-2025).

FINDING: London, the South East, and the South West see a statistically significant slowdown in price growth (1.1-1.6 percentage points) the year after a 1% rate rise. Northern England shows no significant effect - a national rate acts like a stronger lever in the South.

PIPELINE: Staged 24 years of HM Land Registry Price Paid Data, the ONS postcode lookup (2.7M postcodes), and BoE rate history into DuckDB. Used an ASOF JOIN to attach the exact prevailing rate to each sale by date.

MODEL A - Hedonic pricing + regional index: log(price) modeled against property type, new-build status, tenure, and a region x year fixed effect (matching the UK's official House Price Index methodology, since PPD lacks bedroom/floor-area data). Exponentiated coefficients form a mix-adjusted regional price index. Fit via statsmodels OLS (HC1 robust SEs), 1M-row stratified sample.

MODEL B - Rate sensitivity by region: regressed each region's index growth on the PRIOR year's rate change, region-specific slope. The first version (same-year change) gave the wrong sign - the BoE raises rates BECAUSE the economy is overheating, so same-year regressions pick up reverse causality. Lagging the rate variable surfaced the true pattern.

ENGINEERING: caught a silent bug where ONS uses a placeholder code (not blank) for Wales' region field, mis-bucketing ~1M rows; and a CRS mismatch that left the interactive map blank. Added regression tests for both.

OUTPUT: static + interactive (folium) choropleth maps for a non-technical audience - real percentage-point values per region instead of a gradient, honest "inconclusive" labels for the 7 of 10 regions without significance.

STACK: Python, DuckDB, pandas, statsmodels, geopandas, folium, pytest.

Full code, methodology, and limitations linked below.

# UK House Prices and Bank of England Rate Rises: A Regional Breakdown

A hedonic pricing model and regional house-price index built from 20.8 million UK property
transactions (2003–2025). The question was whether price growth responds to Bank of England
base rate changes the same way everywhere in the country. It doesn't. London and the South
East show a real, statistically significant slowdown in price growth the year after a rate
rise; Northern England shows no such pattern.

![Regional rate sensitivity map](outputs/rate_sensitivity_map.png)

## Key finding

| Region | Price growth slowdown per 1% rate rise (1yr lag) | Statistically significant? |
|---|---|---|
| South East | −1.57 pp | Yes (p = 0.002) |
| London | −1.53 pp | Yes (p < 0.001) |
| South West | −1.09 pp | Yes (p = 0.025) |
| East of England | −1.06 pp | Borderline (p = 0.12) |
| West Midlands, Yorkshire, East Midlands | small, negative | No |
| Wales, North West, North East | ~0 | No |

In practical terms, one national interest rate doesn't land evenly across the country. It has
real bite in the South and almost none in the North. Methodology and caveats below.

## Methodology

**Data.** HM Land Registry's Price Paid Data covers residential sales in England & Wales
(here, 2003–2026), joined to the [ONS National Statistics Postcode Lookup](https://geoportal.statistics.gov.uk/)
for region and the [Bank of England's Bank Rate history](https://www.bankofengland.co.uk/boeapps/database/Bank-Rate.asp)
for the rate in effect on each sale date. Of ~22.6M raw transactions, 20.8M survive cleaning:
standard arm's-length sales only, non-market transfers and known PPD data-entry errors
excluded (see `scripts/build_fact_table.py`). Full dataset docs: [gov.uk](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads).

**Model A, hedonic pricing + regional index.** PPD has no bedroom count or floor area, so, in
line with how the UK's official House Price Index handles the same gap, price is modeled
against property type, new-build status, tenure, and a region-by-year fixed effect:

```
log(price) = β·property_type + β·new_build + β·tenure + γ[region, year] + ε
```

`exp(γ[region, year])` gives a mix-adjusted regional price index: it nets out the effect of,
say, more flats selling in one year than the next, leaving the genuine like-for-like price
movement. Fit on a 1M-row stratified sample (statsmodels OLS, HC1 robust SEs) for
tractability; the result held up under re-sampling.

**Model B, rate sensitivity by region.** Same-year rate changes give the wrong sign here. The
Bank of England raises rates because the economy is already overheating, so a same-year
regression mostly captures that reverse causality rather than any dampening effect. Model B
instead regresses each region's annual index growth (from Model A) on *last* year's rate
change, with a region-specific slope:

```
growth[region, t] = α[region] + β[region]·Δrate[t-1] + ε
```

That one-year lag is standard in monetary-policy-transmission research, and it's the
difference between the same-year version (noise: every coefficient positive, none
significant) and the real, correctly-signed pattern reported above.

**Map.** Static (matplotlib) and interactive (folium) choropleths over ONS ITL1 region
boundaries — `scripts/build_choropleth.py`.

## Limitations

- 3 of 10 regions reach conventional significance (p < 0.05); East of England is borderline
  at p = 0.12. The North/South direction holds up, but exact magnitudes for the
  non-significant regions aren't reliable on their own.
- This is a small-sample time-series result underneath everything else: 21 years of national
  rate data means one crash (2008) and one hiking cycle (2022–23) are carrying most of the
  weight.
- PPD doesn't record bedroom count, floor area, or condition. The hedonic model's R² (0.56)
  is reasonable given that gap, but real variation is left unexplained.

## Repo structure

```
data/
  raw/        HM Land Registry, ONS, and BoE downloads (gitignored, ~4.6GB)
  staging/    DuckDB database + intermediate model outputs (gitignored)
  external/   small reference data: region code lookup, ONS boundary file
scripts/      the full pipeline, run in order (see below)
outputs/      final map deliverables (static PNG + interactive HTML)
```

## Reproducing this

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/download_ppd.py         # ~3-4GB, 24 yearly files
python scripts/download_nspl.py        # ~769MB
python scripts/download_boe_rate.py    # <100KB
python scripts/load_to_duckdb.py       # stages raw CSVs into DuckDB
python scripts/build_fact_table.py     # joins + cleans -> fct_sales
python scripts/fit_hedonic_model.py    # Model A: hedonic model + regional index
python scripts/fit_rate_sensitivity_model.py  # Model B: rate-sensitivity by region
python scripts/build_choropleth.py     # final map
```

## Testing

`tests/test_data_quality.py` checks for the actual bugs found while building this: a
silently-dropped region behind a placeholder ONS code, a coordinate-reference-system mismatch
that left the interactive map blank, and a bound on the cleaned price field. These validate
pipeline output rather than pure functions, so they need the pipeline to have run first:

```bash
pytest tests/ -v
```

## Stack

Python 3.12, DuckDB, pandas, statsmodels, geopandas, folium, pytest.

## Data attribution

Contains HM Land Registry data © Crown copyright and database right 2021, and ONS/OS
geographic data, licensed under the [Open Government Licence v3.0](http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
Bank Rate history from the Bank of England.

## License

MIT for the code (see [LICENSE](LICENSE)). The underlying data has its own licensing — see
"Data attribution" above.

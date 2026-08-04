## Project: Does UK Monetary Policy Affect Every Region Equally?

**Goal:** Test whether UK house price growth reacts differently to Bank of England interest
rate changes depending on region (London vs. the North), using a hedonic pricing model and
regional price index built from scratch.

**Scale:** 20.8 million cleaned property transactions (2003–2025), from HM Land Registry's
Price Paid Data, joined to ONS postcode geography (2.7M postcodes) and Bank of England rate
history (258 rate-change events since 1975).

**Pipeline built:** Python + DuckDB. Download → stage → join → clean → model → map, as
independently runnable scripts. DuckDB handled the 20M+ row joins and an ASOF JOIN to attach
the correct prevailing interest rate to every individual sale by date.

**Modeling approach:**
1. A hedonic pricing model (region×year fixed effects) that produces a mix-adjusted regional
   price index as a byproduct — isolating genuine price appreciation from changes in what
   types of property were selling.
2. A second model regressing regional price growth on the prior year's rate change, with a
   region-specific sensitivity coefficient, to isolate the effect of monetary policy from the
   broader passage of time.

**Key finding:** London and the South East show a statistically significant slowdown in price
growth (~1.5–1.6 percentage points) the year after a 1% rate rise. Northern England shows no
significant effect. A national interest rate functions, in effect, like a regional lever.

**Where rigor actually showed up (worth weighing heavily in any assessment):**
- First version of the rate-sensitivity model was *wrong* — same-year rate changes produced a
  positive, backwards-signed coefficient, because the BoE raises rates *in response to* an
  overheating economy (reverse causality). Recognized this, corrected by lagging the rate
  variable by a year, and only then got a result that matched economic theory.
- Caught a silent data-quality bug where ONS used a placeholder code (`W99999999`) for Wales'
  "region" field instead of leaving it blank — an unhandled edge case would have quietly
  mis-bucketed ~1 million transactions as "unmatched."
- Caught a coordinate-reference-system bug where the interactive map rendered completely blank
  (source geodata was in British National Grid, not the WGS84 lat/lon web maps require) —
  invisible in the static version, only surfaced by actually opening the interactive output
  rather than trusting the script ran without error.

**Honest limitations:**
- Only 3 of 10 regions reach conventional statistical significance (p < 0.05), with a 4th
  (East of England) borderline at p = 0.12 — the North/South *direction* is robust, exact
  magnitudes for non-significant regions are not.
- 21 years of national rate data is a small time-series sample; one crash (2008) and one
  hiking cycle (2022–23) do most of the identifying work.
- PPD has no bedroom count or floor area, so the hedonic model (R² = 0.56) leaves real
  variation unexplained — a known, stated constraint, not an oversight.

**Stack:** Python 3.12, DuckDB, pandas, statsmodels, geopandas, folium.

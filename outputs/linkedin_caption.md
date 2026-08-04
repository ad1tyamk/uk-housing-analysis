Does the Bank of England's interest rate affect house prices the same way everywhere in the UK? I tested it on 20.8 million property transactions (2003-2025) — and the answer is no.

London, the South East, and the South West see a real, statistically significant slowdown in price growth the year after a rate rise (1.1 to 1.6 percentage points). Northern England shows no clear pattern either way — not enough evidence to say it reacts at all.

In real terms: on London's 2025 median price (£530,000), that's ~£8,000 less value gained in a year. South East (£385,000 median): ~£6,200 less. North East (£175,000 median): no measurable effect at all. And "1%" isn't small to begin with — roughly the gap between 2021's near-zero rates and today's, worth ~£2,500/year extra interest on a typical £250,000 mortgage.

A single national rate functions, in practice, like a much stronger lever in the South than in the North.

Here's how I got there:

→ Data: staged 24 years of HM Land Registry Price Paid Data, the ONS postcode-to-region lookup, and Bank of England rate history into DuckDB — joining every one of 20.8M sales to the exact interest rate in effect on that date.

→ Model A: a hedonic pricing model (property type, new-build status, tenure, and a region-by-year fixed effect) that produces a mix-adjusted regional price index as a byproduct — isolating genuine appreciation from shifts in what was selling, the same variable set the UK's official House Price Index uses.

→ Model B, the actual test: regressed each region's price growth on the prior year's interest rate change, with a region-specific slope. My first attempt used the *same-year* rate change and got a backwards result — the Bank of England raises rates *because* the economy is overheating, so same-year regressions pick up reverse causality, not the real dampening effect. Lagging the rate variable by a year is what surfaced the pattern above.

→ Along the way I caught two real bugs worth mentioning: ONS uses a placeholder code (not a blank field) for Wales' region, which was silently mis-bucketing ~1 million transactions until I caught it; and a coordinate-reference-system mismatch that left my interactive map rendering completely blank, invisible in the static version.

→ Output: static and interactive (folium) choropleth maps built for a general audience — actual percentage-point numbers on each region instead of a color gradient to decode, and honest "inconclusive" labeling (not hidden) for the 7 of 10 regions that don't reach statistical significance.

Stack: Python, DuckDB, pandas, statsmodels, geopandas, folium, pytest.

Full code, methodology, limitations, and reproducible pipeline in the repo: github.com/ad1tyamk/uk-housing-analysis

#dataanalysis #python #housing #economics #datascience

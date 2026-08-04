Does the Bank of England's interest rate affect house prices the same way everywhere in the UK? I tested it on 20.8 million property transactions (2003-2025) — and the answer is no.

London, the South East, and the South West see a real, statistically significant slowdown in price growth the year after a rate rise (1.1 to 1.6 percentage points). Northern England shows no clear pattern either way — not enough evidence to say it reacts at all.

In real terms: on London's 2025 median price (£530,000), that's ~£8,000 less value gained in a year. South East (£385,000 median): ~£6,200 less. North East (£175,000 median): no measurable effect at all. And "1%" isn't small to begin with — roughly the gap between 2021's near-zero rates and today's, worth ~£2,500/year extra interest on a typical £250,000 mortgage.

A single national rate functions, in practice, like a much stronger lever in the South than in the North.

I built the whole thing from scratch: a pipeline joining 24 years of HM Land Registry sales data to Bank of England rate history (DuckDB), a hedonic pricing model producing a mix-adjusted regional price index, and a rate-sensitivity model that initially gave me the *wrong* answer — same-year rate changes pick up reverse causality, since the BoE raises rates *because* the economy is overheating. Lagging the rate variable by a year is what surfaced the real pattern above.

Full methodology, the bugs I caught along the way, limitations, and the reproducible pipeline are in the repo: github.com/ad1tyamk/uk-housing-analysis

#dataanalysis #python #housing #economics #datascience

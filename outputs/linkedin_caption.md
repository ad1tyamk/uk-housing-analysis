Does the Bank of England's interest rate affect house prices the same way everywhere in the UK? I built a hedonic pricing model and a regional rate-sensitivity test on 20.8 million property transactions (2003-2025) to find out — and the answer is no.

London, the South East, and the South West see a real, statistically significant slowdown in price growth the year after a rate rise (1.1 to 1.6 percentage points). Northern England shows no clear pattern either way — not enough evidence to say it reacts at all.

How to read the map: the darker the red, the more that region's price growth slows down after a rate rise — in other words, the harder a BoE decision actually bites there. Striped/hatched regions aren't missing data, they're places where the effect wasn't strong enough to confirm either way, shown honestly rather than hidden. Put simply, the map is answering one question — where does a Bank of England rate rise actually change buyer behaviour? — and the answer is: mostly in the South, barely at all in the North.

In real terms: on London's 2025 median price (£530,000), that's ~£8,000 less value gained in a year. South East (£385,000 median): ~£6,200 less. North East (£175,000 median): no measurable effect at all. And "1%" isn't small to begin with — roughly the gap between 2021's near-zero rates and today's, worth ~£2,500/year extra interest on a typical £250,000 mortgage.

Why? London and the South East carry far higher price-to-income ratios and larger mortgage balances, so the same 1-point rate rise hits affordability harder, in both relative and absolute terms. These markets likely also have more leveraged buyers and investment purchases, which tend to be more rate-sensitive than the lower-LTV owner-occupiers common in cheaper regions. I didn't directly test loan-to-value or buyer type here, so this is the likely mechanism, not a proven one — but it lines up with what regional monetary-policy-transmission theory has long suggested: a single national rate doesn't hit a country evenly when housing leverage and price levels differ this much by region. This project is a direct empirical check of that idea using real transaction-level data, not aggregate indices.

I built the whole thing from scratch: a pipeline joining 24 years of HM Land Registry sales data to Bank of England rate history (DuckDB), a hedonic pricing model producing a mix-adjusted regional price index, and a rate-sensitivity model that initially gave me the *wrong* answer — same-year rate changes pick up reverse causality, since the BoE raises rates *because* the economy is overheating. Lagging the rate variable by a year is what surfaced the real pattern above.

Full methodology, the bugs I caught along the way, limitations, and the reproducible pipeline are in the repo: github.com/ad1tyamk/uk-housing-analysis

#dataanalysis #python #housing #economics #datascience

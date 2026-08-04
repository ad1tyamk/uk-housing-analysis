Does the Bank of England's interest rate affect house prices the same way everywhere in the UK? I tested it on 20.8 million property transactions (2003-2025) — and the answer is no.

London, the South East, and the South West see a real slowdown in price growth the year after a rate rise (1.1 to 1.6 percentage points). Northern England shows no clear pattern either way — not enough evidence to say it reacts at all.

A single national interest rate is, in effect, a much stronger lever in the South than in the North.

What this involved:
→ Hedonic pricing model on HM Land Registry's full price-paid dataset, joined to ONS postcode geography and Bank of England rate history
→ A mix-adjusted regional price index (holding property type/tenure/new-build status constant, so it's genuine like-for-like appreciation, not just "more flats sold this year")
→ Catching and fixing a reverse-causality bug along the way — testing same-year rate changes gave the wrong sign, because the BoE raises rates *because* the market is overheating. Using last year's rate change instead is what surfaced the real pattern.

Full methodology, code, and caveats in the repo (link in comments): github.com/ad1tyamk/uk-housing-analysis

#dataanalysis #python #housing #economics

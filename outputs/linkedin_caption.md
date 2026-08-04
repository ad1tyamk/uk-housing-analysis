I spent the past few weeks digging into 20.8 million UK property sales to answer something I kept seeing argued without real data behind it: when the Bank of England raises interest rates, does it slow down house prices everywhere, or just in some places?

Just some places, it turns out. London, the South East, and the South West all show a real slowdown in price growth the year after a rate rise, somewhere between 1.1 and 1.6 percentage points. Northern England barely moves. There isn't enough evidence to say it reacts at all.

In pounds: a London home at the 2025 median price of £530,000 gains roughly £8,000 less in that year. In the South East, around £6,200 less on a £385,000 median. In the North East, essentially nothing changes on a £175,000 median home. None of this is small money either way — a 1-point move in the Bank Rate is close to the entire gap between 2021's near-zero rates and today, and it adds close to £2,500 a year in interest on an average £250,000 mortgage.

Quick guide to the map: darker red means a harder hit in that region. The hatched regions aren't blank spots in the data. They're places where the pattern wasn't strong enough to call confidently, and I labeled them that way rather than pretending otherwise. Read the whole thing together and it's answering one question — where does a rate decision actually change what people will pay for a house? Mostly the South. Barely the North.

My best guess for why: London and the South East carry much higher price-to-income ratios and bigger mortgages, so the same rate move hits affordability harder there, both in relative and absolute terms. Those markets probably also have more highly-leveraged buyers and investment purchases, which react more to financing costs than the lower-LTV owner-occupiers common elsewhere. I haven't tested loan-to-value or buyer type directly, so take this as the likely explanation, not a proven one. It does match existing research on regional monetary policy transmission, and this project is a fairly direct empirical check of that idea using individual transactions rather than aggregate indices.

Building it meant joining 24 years of Land Registry sales data to Bank of England rate history in DuckDB, fitting a hedonic pricing model that produces a mix-adjusted regional index as a byproduct, then testing rate sensitivity by region. My first version of that last model used the same year's rate change and got the sign backwards, since the Bank raises rates because the economy is already overheating, not the reverse. Lagging the variable by a year fixed it.

Code, full methodology, the bugs, and everything worth flagging before anyone relies on this: github.com/ad1tyamk/uk-housing-analysis

#dataanalysis #python #housing #economics #datascience

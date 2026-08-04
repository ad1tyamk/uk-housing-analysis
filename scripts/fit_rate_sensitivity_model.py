from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "staging" / "housing.duckdb"
OUTPUT_DIR = PROJECT_ROOT / "data" / "staging"

LAST_FULL_YEAR = 2025  # 2026 is a partial year, excluded throughout


def annual_avg_bank_rate() -> pd.DataFrame:
    """Time-weighted average Bank Rate per calendar year, via a daily calendar
    ASOF-joined against the sparse rate-change events."""
    con = duckdb.connect(str(DB_PATH))
    df = con.execute(f"""
        WITH calendar AS (
            SELECT unnest(generate_series(
                DATE '2003-01-01', DATE '{LAST_FULL_YEAR}-12-31', INTERVAL 1 DAY
            )) AS day
        ),
        daily_rate AS (
            SELECT c.day, b.bank_rate
            FROM calendar c
            ASOF JOIN stg_boe_rate b ON c.day >= b.date_changed
        )
        SELECT EXTRACT(YEAR FROM day)::INTEGER AS transfer_year, AVG(bank_rate) AS avg_rate
        FROM daily_rate
        GROUP BY 1
        ORDER BY 1
    """).df()
    con.close()
    return df


def main() -> None:
    rate_df = annual_avg_bank_rate()
    rate_df["rate_change"] = rate_df["avg_rate"].diff()
    # Use last year's rate change to predict this year's growth, not the
    # same year's -- same-year rate hikes and price growth are both driven
    # by the same economic boom (the BoE raises rates *because* things are
    # overheating), so a contemporaneous regressor picks up reverse
    # causality instead of the actual dampening effect, which takes time
    # to filter through to buyer behaviour.
    rate_df["rate_change_lag1"] = rate_df["rate_change"].shift(1)

    index_df = pd.read_csv(OUTPUT_DIR / "regional_price_index.csv")
    index_df = index_df[index_df["transfer_year"] <= LAST_FULL_YEAR].copy()

    regions = pd.read_csv(PROJECT_ROOT / "data" / "external" / "regions.csv")
    index_df = index_df.merge(regions, left_on="geo_code", right_on="code", how="left")

    index_df = index_df.sort_values(["geo_code", "transfer_year"])
    index_df["log_growth"] = index_df.groupby("geo_code")["price_index"].transform(
        lambda s: np.log(s).diff()
    )

    panel = index_df.merge(rate_df[["transfer_year", "rate_change_lag1"]], on="transfer_year")
    panel = panel.dropna(subset=["log_growth", "rate_change_lag1"])

    print(f"Panel: {len(panel)} region-year observations "
          f"({panel['name'].nunique()} regions x ~{len(panel) // panel['name'].nunique()} years)")

    formula = "log_growth ~ C(name) - 1 + C(name):rate_change_lag1"
    model = smf.ols(formula, data=panel).fit(cov_type="HC3")
    print(model.summary())

    sensitivity = model.params[model.params.index.str.contains(":rate_change_lag1")]
    pvalues = model.pvalues[model.params.index.str.contains(":rate_change_lag1")]
    result = pd.DataFrame({
        "region": sensitivity.index.str.extract(r"C\(name\)\[(.+)\]:rate_change_lag1")[0].values,
        "sensitivity": sensitivity.values,
        "p_value": pvalues.values,
    }).sort_values("sensitivity")

    print()
    print("Regional sensitivity to LAST YEAR's 1pp rise in BoE base rate (pp change in this year's price growth):")
    print(result.to_string(index=False))

    result.to_csv(OUTPUT_DIR / "rate_sensitivity_by_region.csv", index=False)
    model.save(str(OUTPUT_DIR / "rate_sensitivity_model_b.pickle"))
    print()
    print("Saved: data/staging/rate_sensitivity_by_region.csv")
    print("Saved: data/staging/rate_sensitivity_model_b.pickle")


if __name__ == "__main__":
    main()

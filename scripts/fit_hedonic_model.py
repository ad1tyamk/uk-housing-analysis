from pathlib import Path

import duckdb
import pandas as pd
import statsmodels.formula.api as smf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "staging" / "housing.duckdb"
OUTPUT_DIR = PROJECT_ROOT / "data" / "staging"

SAMPLE_SIZE = 1_000_000
SEED = 42


def load_sample() -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH))
    df = con.execute(f"""
        SELECT
            log_price,
            property_type,
            is_new_build,
            duration,
            geo_code || '_' || transfer_year AS region_year,
            region_name,
            transfer_year
        FROM fct_sales
        WHERE duration != 'U'
          AND region_name != 'Scotland'
        USING SAMPLE {SAMPLE_SIZE} ROWS (reservoir, {SEED})
    """).df()
    con.close()
    return df


def main() -> None:
    print(f"Loading a {SAMPLE_SIZE:,}-row sample...")
    df = load_sample()
    print(f"Sample loaded: {len(df):,} rows")

    # Keep the intercept in the model. This makes every categorical term
    # (including region_year) use standard reduced-rank dummy encoding, so
    # a region-year's price level is always: Intercept + its coefficient
    # (0 for whichever single cell patsy drops as the reference).
    formula = (
        "log_price ~ "
        "C(property_type, Treatment(reference='T')) + "
        "is_new_build + "
        "C(duration, Treatment(reference='F')) + "
        "C(region_year)"
    )

    print("Fitting OLS model...")
    model = smf.ols(formula, data=df).fit(cov_type="HC1")
    print(model.summary())

    # Save the fitted model for reuse (e.g. Model B, or later diagnostics)
    model.save(str(OUTPUT_DIR / "hedonic_model_a.pickle"))

    # Reconstruct a price level for every region_year cell actually present
    # in the data, including the one dropped as the reference category.
    intercept = model.params["Intercept"]
    region_year_coefs = model.params[model.params.index.str.contains("region_year")]
    region_year_coefs.index = region_year_coefs.index.str.extract(r"\[T\.(.+)\]", expand=False)

    all_region_years = sorted(df["region_year"].unique())
    index_df = pd.DataFrame({"region_year": all_region_years})
    index_df["log_level"] = intercept + index_df["region_year"].map(region_year_coefs).fillna(0.0)
    index_df[["geo_code", "transfer_year"]] = index_df["region_year"].str.rsplit("_", n=1, expand=True)
    index_df["transfer_year"] = index_df["transfer_year"].astype(int)
    index_df["level"] = index_df["log_level"].apply(lambda x: 2.718281828 ** x)

    index_df["base_level"] = index_df.groupby("geo_code")["level"].transform("first")
    index_df["price_index"] = 100 * index_df["level"] / index_df["base_level"]

    index_df = index_df.sort_values(["geo_code", "transfer_year"])
    index_df[["geo_code", "transfer_year", "price_index"]].to_csv(
        OUTPUT_DIR / "regional_price_index.csv", index=False
    )

    print()
    print("Saved: data/staging/hedonic_model_a.pickle")
    print("Saved: data/staging/regional_price_index.csv")


if __name__ == "__main__":
    main()

from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "staging" / "housing.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB_PATH))

    con.execute("""
        CREATE OR REPLACE TABLE fct_sales AS
        SELECT
            p.transaction_id,
            p.price,
            LN(p.price) AS log_price,
            p.transfer_date,
            EXTRACT(YEAR FROM p.transfer_date) AS transfer_year,
            p.postcode,
            p.property_type,
            p.is_new_build,
            p.duration,
            p.town_city,
            p.district,
            p.county,
            n.region_code,
            n.country_code,
            -- NSPL uses placeholder codes like 'W99999999' ("not applicable")
            -- for the region field outside England, instead of leaving it blank.
            CASE
                WHEN n.region_code LIKE '%99999999' THEN n.country_code
                ELSE n.region_code
            END AS geo_code,
            r.name AS region_name,
            n.latitude,
            n.longitude,
            b.bank_rate
        FROM stg_ppd p
        JOIN stg_nspl n
            ON p.postcode = n.postcode
        LEFT JOIN ref_regions r
            ON r.code = CASE
                WHEN n.region_code LIKE '%99999999' THEN n.country_code
                ELSE n.region_code
            END
        ASOF JOIN stg_boe_rate b
            ON p.transfer_date >= b.date_changed
        WHERE p.ppd_category = 'A'
          AND p.property_type IN ('D', 'S', 'T', 'F')
          AND p.price BETWEEN 10000 AND 10000000
    """)

    total = con.execute("SELECT COUNT(*) FROM fct_sales").fetchone()[0]
    print(f"fct_sales: {total:,} rows")

    print()
    print("Rows by region:")
    for region, count in con.execute("""
        SELECT region_name, COUNT(*) AS n
        FROM fct_sales
        GROUP BY 1
        ORDER BY 2 DESC
    """).fetchall():
        print(f"  {region or '(unmatched)'}: {count:,}")

    print()
    print("Sample rows:")
    print(con.execute("SELECT * FROM fct_sales USING SAMPLE 3").df())

    con.close()


if __name__ == "__main__":
    main()

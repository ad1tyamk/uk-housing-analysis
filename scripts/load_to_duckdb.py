from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external"
DB_PATH = PROJECT_ROOT / "data" / "staging" / "housing.duckdb"

# Raw PPD files have no header row -- these are HM Land Registry's official
# column definitions, in order.
PPD_COLUMNS = {
    "transaction_id": "VARCHAR",
    "price": "VARCHAR",
    "transfer_date": "VARCHAR",
    "postcode": "VARCHAR",
    "property_type": "VARCHAR",
    "new_build_flag": "VARCHAR",
    "duration": "VARCHAR",
    "paon": "VARCHAR",
    "saon": "VARCHAR",
    "street": "VARCHAR",
    "locality": "VARCHAR",
    "town_city": "VARCHAR",
    "district": "VARCHAR",
    "county": "VARCHAR",
    "ppd_category": "VARCHAR",
    "record_status": "VARCHAR",
}


def load_ppd(con: duckdb.DuckDBPyConnection) -> None:
    columns_sql = ", ".join(f"'{name}': '{dtype}'" for name, dtype in PPD_COLUMNS.items())
    con.execute(f"""
        CREATE OR REPLACE TABLE stg_ppd AS
        SELECT
            transaction_id,
            CAST(price AS INTEGER) AS price,
            CAST(transfer_date AS DATE) AS transfer_date,
            postcode,
            property_type,
            new_build_flag = 'Y' AS is_new_build,
            duration,
            paon,
            saon,
            street,
            locality,
            town_city,
            district,
            county,
            ppd_category,
            record_status
        FROM read_csv(
            '{RAW_DIR}/pp-*.csv',
            header = false,
            columns = {{{columns_sql}}}
        )
    """)


def load_nspl(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(f"""
        CREATE OR REPLACE TABLE stg_nspl AS
        SELECT
            pcds AS postcode,
            ctry25cd AS country_code,
            rgn25cd AS region_code,
            lad25cd AS local_authority_code,
            lat AS latitude,
            long AS longitude
        FROM read_csv_auto('{RAW_DIR}/nspl.csv')
    """)


def load_boe_rate(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(f"""
        CREATE OR REPLACE TABLE stg_boe_rate AS
        SELECT
            strptime(date_changed, '%d %b %y')::DATE AS date_changed,
            bank_rate
        FROM read_csv_auto('{RAW_DIR}/boe_base_rate.csv')
    """)


def load_ref_regions(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(f"""
        CREATE OR REPLACE TABLE ref_regions AS
        SELECT * FROM read_csv_auto('{EXTERNAL_DIR}/regions.csv')
    """)


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))

    load_ppd(con)
    load_nspl(con)
    load_boe_rate(con)
    load_ref_regions(con)

    for table in ["stg_ppd", "stg_nspl", "stg_boe_rate", "ref_regions"]:
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count:,} rows")

    con.close()


if __name__ == "__main__":
    main()

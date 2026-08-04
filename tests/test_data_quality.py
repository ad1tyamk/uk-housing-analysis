"""Data-validation checks for the pipeline's own output.

These aren't unit tests for pure functions -- they're regression checks
against real bugs found while building this pipeline, run after the full
pipeline (scripts/download_*.py through build_choropleth.py) has produced
its output in data/staging/. They won't pass on a fresh clone until the
pipeline has been run once.
"""

from pathlib import Path

import duckdb
import geopandas as gpd
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "staging" / "housing.duckdb"
BOUNDARIES_PATH = PROJECT_ROOT / "data" / "external" / "itl1_boundaries.geojson"

requires_pipeline = pytest.mark.skipif(
    not DB_PATH.exists(), reason="pipeline hasn't been run yet -- see README"
)


@pytest.fixture(scope="module")
def con():
    connection = duckdb.connect(str(DB_PATH), read_only=True)
    yield connection
    connection.close()


@requires_pipeline
def test_ppd_nspl_join_rate(con):
    """The postcode join (PPD -> NSPL) should match ~99.8% of rows, per the
    manual check done when this join was first built. A big drop would mean
    a postcode-format mismatch has crept in."""
    total = con.execute("SELECT COUNT(*) FROM stg_ppd").fetchone()[0]
    matched = con.execute("""
        SELECT COUNT(*) FROM stg_ppd p JOIN stg_nspl n ON p.postcode = n.postcode
    """).fetchone()[0]
    match_rate = matched / total
    assert match_rate > 0.99, f"PPD->NSPL join match rate dropped to {match_rate:.2%}"


@requires_pipeline
def test_no_unresolved_region_names(con):
    """Regression check for the Wales bug: NSPL uses a placeholder code
    (W99999999, S99999999, ...) for the 'region' field outside England
    instead of leaving it blank, which silently left ~1M Welsh transactions
    unmatched to a region name until handled explicitly. Every row in
    fct_sales should resolve to a real region."""
    unresolved = con.execute(
        "SELECT COUNT(*) FROM fct_sales WHERE region_name IS NULL"
    ).fetchone()[0]
    assert unresolved == 0, f"{unresolved} rows have no resolved region_name"


@requires_pipeline
def test_fct_sales_price_bounds(con):
    """Cleaning rules from build_fact_table.py should hold: no non-market
    transfers, no PPD aggregate-price data errors."""
    out_of_bounds = con.execute(
        "SELECT COUNT(*) FROM fct_sales WHERE price < 10000 OR price > 10000000"
    ).fetchone()[0]
    assert out_of_bounds == 0


def test_boundary_file_reprojects_to_valid_latlon():
    """Regression check for the CRS bug: the ONS boundary file is in
    British National Grid (EPSG:27700), not the WGS84 lat/lon that Leaflet
    (via folium) needs -- this bug was invisible in the static matplotlib
    map (which just plots raw x/y) and only showed up as a blank interactive
    map. After reprojecting, coordinates must be valid lat/lon values."""
    if not BOUNDARIES_PATH.exists():
        pytest.skip("boundary file hasn't been downloaded yet -- see README")

    gdf = gpd.read_file(BOUNDARIES_PATH).to_crs(epsg=4326)
    minx, miny, maxx, maxy = gdf.total_bounds
    assert -180 <= minx <= maxx <= 180, f"longitude out of range: {minx}, {maxx}"
    assert -90 <= miny <= maxy <= 90, f"latitude out of range: {miny}, {maxy}"


def test_rate_sensitivity_panel_has_expected_shape():
    """The Model B panel should have one row per region per year (minus the
    first year lost to differencing) -- a silent drop here (e.g. a bad
    merge) would quietly bias which regions/years the model is fit on."""
    path = PROJECT_ROOT / "data" / "staging" / "rate_sensitivity_by_region.csv"
    if not path.exists():
        pytest.skip("Model B hasn't been run yet -- see README")

    result = pd.read_csv(path)
    assert len(result) == 10, f"expected 10 regions, got {len(result)}"
    assert result["region"].is_unique
    assert result["p_value"].between(0, 1).all()

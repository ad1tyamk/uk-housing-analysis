import json
import time
from pathlib import Path

import branca.colormap as cm
import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import requests
from PIL import Image, ImageChops


def trim_whitespace(path: Path, padding: int = 40) -> None:
    """Crop a saved figure to its actual content -- sidesteps matplotlib's
    default-subplot-margin vs equal-aspect interaction, which otherwise
    leaves large, hard-to-predict dead space around map plots."""
    img = Image.open(path).convert("RGB")
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bbox = ImageChops.difference(img, bg).getbbox()
    if bbox:
        left, upper, right, lower = bbox
        left = max(0, left - padding)
        upper = max(0, upper - padding)
        right = min(img.width, right + padding)
        lower = min(img.height, lower + padding)
        img.crop((left, upper, right, lower)).save(path)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external"
STAGING_DIR = PROJECT_ROOT / "data" / "staging"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

BOUNDARIES_URL = (
    "https://open-geography-portalx-ons.hub.arcgis.com/api/download/v1/"
    "items/67ad9f4414934171a08051d408cee70d/geojson?layers=0"
)
BOUNDARIES_PATH = EXTERNAL_DIR / "itl1_boundaries.geojson"

# The ITL1 boundary file's own region labels differ slightly from
# ref_regions.csv (e.g. "East (England)" vs "East of England") -- map
# explicitly rather than fuzzy-matching. Scotland and Northern Ireland are
# intentionally omitted: PPD only covers England & Wales, so we have no
# sensitivity estimate for them and shouldn't imply otherwise on the map.
ITL1_NAME_MAP = {
    "North East (England)": "North East",
    "North West (England)": "North West",
    "Yorkshire and The Humber": "Yorkshire and The Humber",
    "East Midlands (England)": "East Midlands",
    "West Midlands (England)": "West Midlands",
    "East (England)": "East of England",
    "London": "London",
    "South East (England)": "South East",
    "South West (England)": "South West",
    "Wales": "Wales",
}


def download_boundaries() -> None:
    if BOUNDARIES_PATH.exists():
        return
    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)

    # This ArcGIS export endpoint generates the file on demand -- the first
    # request(s) can return a small {"status": "Pending"} JSON placeholder
    # instead of the actual GeoJSON, so poll until it's ready.
    for attempt in range(10):
        response = requests.get(BOUNDARIES_URL)
        response.raise_for_status()
        if response.headers.get("content-type", "").startswith("application/json") and b'"status"' in response.content[:200]:
            print(f"Boundary export still generating, waiting... (attempt {attempt + 1})")
            time.sleep(5)
            continue
        BOUNDARIES_PATH.write_bytes(response.content)
        return

    raise RuntimeError("Boundary file never finished generating after 10 attempts")


def load_data() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(BOUNDARIES_PATH)
    gdf["region_name"] = gdf["ITL125NM"].map(ITL1_NAME_MAP)
    gdf = gdf.dropna(subset=["region_name"]).copy()

    sensitivity = pd.read_csv(STAGING_DIR / "rate_sensitivity_by_region.csv")
    gdf = gdf.merge(sensitivity, left_on="region_name", right_on="region", how="left")
    gdf["significant"] = gdf["p_value"] < 0.05

    # Plain-language numbers for a general audience: percentage points of
    # growth, not a raw regression coefficient, and no p-values in sight.
    gdf["pp_change"] = gdf["sensitivity"] * 100
    gdf["pp_label"] = gdf["pp_change"].map(lambda x: f"{x:+.1f}pp")
    gdf["plain_explainer"] = gdf.apply(
        lambda r: (
            f"{r['region_name']}: after a 1% Bank of England rate rise, "
            f"price growth here slows by about {abs(r['pp_change']):.1f} percentage points "
            f"the following year."
            if r["significant"] and r["pp_change"] < 0
            else
            f"{r['region_name']}: after a 1% Bank of England rate rise, "
            f"price growth here speeds up by about {abs(r['pp_change']):.1f} percentage points "
            f"the following year."
            if r["significant"]
            else
            f"{r['region_name']}: inconclusive -- not enough evidence for a real effect of "
            f"rate rises on prices here, could just be normal year-to-year variation."
        ),
        axis=1,
    )
    return gdf


def build_static_map(gdf: gpd.GeoDataFrame) -> None:
    import matplotlib.patheffects as pe

    bound = gdf["sensitivity"].abs().max()
    text_outline = [pe.withStroke(linewidth=2.5, foreground="white")]

    # Size the figure to the map's ACTUAL DISPLAYED extent (i.e. including
    # the asymmetric xlim padding added below for the London callout) --
    # sizing off the raw geometry bounds instead was the bug: that padding
    # skews the true displayed aspect ratio, so a figure sized for the
    # unpadded ratio ends up taller than the equal-aspect plot needs,
    # leaving dead space top and bottom that bbox_inches='tight' can't
    # remove (it's genuinely inside the axes area, not outer margin).
    minx, miny, maxx, maxy = gdf.total_bounds
    xlim = (minx - 15000, maxx + 90000)  # extra right margin for the London callout
    ylim = (miny - 15000, maxy + 15000)
    map_aspect = (ylim[1] - ylim[0]) / (xlim[1] - xlim[0])

    fig_width = 7.5
    fig, ax = plt.subplots(figsize=(fig_width, fig_width * map_aspect))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    gdf.plot(
        column="sensitivity",
        cmap="RdBu",
        vmin=-bound,
        vmax=bound,
        legend=True,
        edgecolor="white",
        linewidth=0.8,
        ax=ax,
        legend_kwds={
            "label": "How much slower prices grow after a 1% interest rate rise\n(percentage points per year)",
            "format": lambda x, _: f"{x * 100:+.1f}",
            "shrink": 0.6,
        },
    )
    # Mark regions where the pattern isn't statistically reliable with a
    # hatch, rather than hiding them or using an unexplained asterisk --
    # the plain-English caption below spells out what this means.
    insignificant = gdf[~gdf["significant"]]
    if len(insignificant):
        insignificant.plot(ax=ax, facecolor="none", edgecolor="black", hatch="///", linewidth=0.5)

    # London is geographically tiny -- its label can't fit inside its own
    # borders without colliding with South East, so give it a callout
    # instead of a centroid label like everywhere else.
    LABEL_OVERRIDES = {"London": (60000, 15000)}  # (dx, dy) offset from centroid

    for _, row in gdf.iterrows():
        centroid = row.geometry.centroid
        dx, dy = LABEL_OVERRIDES.get(row["region_name"], (0, 0))
        label_xy = (centroid.x + dx, centroid.y + dy)

        if dx or dy:
            ax.plot([centroid.x, label_xy[0]], [centroid.y, label_xy[1]], color="black", linewidth=0.6)

        ax.annotate(
            row["region_name"],
            xy=(label_xy[0], label_xy[1] + 8000),
            ha="center", fontsize=7.5, fontweight="bold", color="black",
            path_effects=text_outline,
        )
        ax.annotate(
            row["pp_label"] if row["significant"] else "inconclusive",
            xy=(label_xy[0], label_xy[1] - 8000),
            ha="center", fontsize=7, color="black",
            path_effects=text_outline,
        )

    ax.set_axis_off()

    # Anchor every text block to the axes' own coordinate system (0-1,
    # extending above/below 0-1 as needed) rather than figure-fraction
    # coordinates (fig.text/fig.suptitle) -- those assume where the axes
    # box sits, and matplotlib's default subplot margins don't actually
    # place it where a naive figure-fraction guess expects, which was
    # the real source of the large gaps in earlier attempts.
    ax.text(
        0.5, 1.14,
        "Do Interest Rate Rises Slow Down House Prices?\nIt Depends Where You Live",
        transform=ax.transAxes, ha="center", fontsize=14, fontweight="bold",
    )
    ax.text(
        0.5, 1.04,
        "London and the South East clearly slow down the year after a rate hike.\n"
        "Northern England shows no such pattern.",
        transform=ax.transAxes, ha="center", fontsize=9.5, color="dimgray",
    )
    ax.text(
        0.5, -0.04,
        "Based on 20.8 million UK home sales (2003–2025), HM Land Registry, matched to Bank of England rate history.\n"
        "Hatched / “inconclusive” regions: not enough evidence for a real pattern here — could just be normal year-to-year ups and downs.",
        transform=ax.transAxes, ha="center", va="top", fontsize=7, color="gray",
    )
    out_path = OUTPUT_DIR / "rate_sensitivity_map.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    trim_whitespace(out_path)
    print("Saved:", out_path)


def build_interactive_map(gdf: gpd.GeoDataFrame) -> None:
    # Leaflet (which folium uses) needs real lat/lon (WGS84). The source
    # file is in British National Grid (EPSG:27700) -- fine for the static
    # matplotlib plot, which just draws raw x/y, but silently invisible on
    # a web map without this reprojection.
    gdf = gdf.to_crs(epsg=4326)

    bound = gdf["pp_change"].abs().max()
    colormap = cm.LinearColormap(
        colors=["#b2182b", "#f7f7f7", "#2166ac"],
        vmin=-bound,
        vmax=bound,
        caption="How much slower prices grow after a 1% interest rate rise (percentage points per year)",
    )

    def style_function(feature: dict) -> dict:
        val = feature["properties"]["pp_change"]
        return {
            "fillColor": colormap(val) if val is not None else "#cccccc",
            "color": "white",
            "weight": 1,
            "fillOpacity": 0.85,
        }

    m = folium.Map(location=[52.9, -1.8], zoom_start=6, tiles="cartodbpositron")
    folium.GeoJson(
        json.loads(gdf.to_json()),
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=["plain_explainer"],
            aliases=[""],
            localize=True,
            style="font-size: 13px; max-width: 260px; white-space: normal;",
        ),
    ).add_to(m)
    colormap.add_to(m)

    m.save(str(OUTPUT_DIR / "rate_sensitivity_map.html"))
    print("Saved:", OUTPUT_DIR / "rate_sensitivity_map.html")


def main() -> None:
    download_boundaries()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    gdf = load_data()
    build_static_map(gdf)
    build_interactive_map(gdf)


if __name__ == "__main__":
    main()

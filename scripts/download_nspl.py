from pathlib import Path

import requests

# ONS republishes NSPL quarterly under a new item ID each time.
# This is the Feb 2026 snapshot -- a static postcode->region lookup is fine
# for this project, so we hardcode it rather than auto-discovering the latest.
NSPL_URL = "https://open-geography-portalx-ons.hub.arcgis.com/api/download/v1/items/419355d8a54741f19025ba97e35da55a/csv?layers=0"

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
NSPL_PATH = RAW_DIR / "nspl.csv"


def download_nspl() -> Path:
    """Download the current NSPL postcode-to-region lookup CSV (~769MB)."""
    if NSPL_PATH.exists():
        return NSPL_PATH

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    response = requests.get(NSPL_URL, stream=True)
    response.raise_for_status()

    with open(NSPL_PATH, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)

    return NSPL_PATH


if __name__ == "__main__":
    download_nspl()

import io
from pathlib import Path

import pandas as pd
import requests

# Requires a browser-like User-Agent -- BoE's bot protection blocks the
# default requests User-Agent and returns a 403.
BOE_URL = "https://www.bankofengland.co.uk/boeapps/database/Bank-Rate.asp"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
BOE_PATH = RAW_DIR / "boe_base_rate.csv"


def download_boe_rate() -> Path:
    """Download and parse the full Bank of England Bank Rate change history."""
    if BOE_PATH.exists():
        return BOE_PATH

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    response = requests.get(BOE_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    # The rate-change table is rendered server-side into the static HTML
    # (id="stats-table") -- no need to run JavaScript to get at it.
    tables = pd.read_html(io.StringIO(response.text), attrs={"id": "stats-table"}, flavor="bs4")
    rate_history = tables[0]
    rate_history.columns = ["date_changed", "bank_rate"]
    rate_history.to_csv(BOE_PATH, index=False)

    return BOE_PATH


if __name__ == "__main__":
    download_boe_rate()

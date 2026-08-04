from pathlib import Path

import requests
from tqdm import tqdm

START_YEAR = 2003
END_YEAR = 2026

PPD_URL_TEMPLATE = "https://price-paid-data.publicdata.landregistry.gov.uk/pp-{year}.csv"

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def download_year(year: int) -> Path:
    """Download one year of PPD data and return the local file path."""
    url = PPD_URL_TEMPLATE.format(year=year)
    file_path = RAW_DIR / f"pp-{year}.csv"
    if file_path.exists():
        return file_path

    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)

    return file_path


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for year in tqdm(range(START_YEAR, END_YEAR + 1), desc="Downloading PPD yearly files"):
        download_year(year)


if __name__ == "__main__":
    main()

from pathlib import Path

# src/config.py -> src -> project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "DATA" / "RAW"
PROCESSED_DIR = PROJECT_ROOT / "DATA" / "PROCESSED"
OUTPUT_DIR = PROJECT_ROOT / "OUTPUTS"

# file name
WARDS_FILE = RAW_DIR / "Wards_ahmd.geojson"
BUILDINGS_FILE = RAW_DIR / "buildings_ahmd.geojson"

from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "DATA" / "PROCESSED"

BUILDINGS_FILE = PROCESSED / "buildings_solar_potential.gpkg"
IRRADIATION_FILE = PROCESSED / "nasa_power_yearly_solar_2021_2025.csv"

PANEL_EFFICIENCY = 0.20
PERFORMANCE_RATIO = 0.75

buildings = gpd.read_file(BUILDINGS_FILE)
irradiation = pd.read_csv(IRRADIATION_FILE)

# Use the 2021 annual irradiation value.
year = 2021
annual_h = float(
    irradiation.loc[
        irradiation["year"] == year,
        "annual_irradiation_kwh_m2"
    ].iloc[0]
)

print(f"Annual irradiation for {year}: {annual_h:.4f} kWh/m²/year")
print("\nIndependent energy formula check for 10 buildings")
print("-" * 90)

sample = buildings.head(10).copy()

for idx, row in sample.iterrows():
    usable_area = row["usable_roof_medium_m2"]

    expected = (
        usable_area
        * annual_h
        * PANEL_EFFICIENCY
        * PERFORMANCE_RATIO
    )

    saved = row["generation_2021_medium_kwh_year"]

    difference = abs(expected - saved)

    passed = np.isclose(
        expected, saved, rtol=1e-6, atol=0.01
    )

    print(
        f"Building {idx}: "
        f"usable area={usable_area:.2f} m² | "
        f"expected={expected:.2f} kWh/year | "
        f"saved={saved:.2f} kWh/year | "
        f"difference={difference:.6f} | "
        f"{'PASS' if passed else 'CHECK'}"
    )

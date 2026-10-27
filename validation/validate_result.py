
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "DATA" / "PROCESSED"

buildings_file = PROCESSED / "buildings_solar_potential.gpkg"
roof_file = PROCESSED / "buildings_with_roof_estimates.gpkg"
ward_file = PROCESSED / "ward_solar_potential.csv"
city_file = PROCESSED / "city_solar_potential_summary.csv"

print("=" * 60)
print("VALIDATION OF AHMEDABAD ROOFTOP SOLAR ESTIMATES")
print("=" * 60)


# --------------------------------------------------
# 2. Check whether expected files exist
# --------------------------------------------------

for file in [buildings_file, roof_file, ward_file, city_file]:
    print(f"{file.name}: {'FOUND' if file.exists() else 'NOT FOUND'}")

if not roof_file.exists() or not ward_file.exists() or not city_file.exists():
    raise FileNotFoundError(
        "A required output file is missing. Check the printed paths."
    )


# --------------------------------------------------
# 3. Check rooftop area calculations
# --------------------------------------------------

roofs = gpd.read_file(roof_file)

print("\n--- ROOFTOP AREA CHECK ---")
print("Number of building records:", len(roofs))

required_area_columns = [
    "roof_area_m2",
    "usable_roof_low_m2",
    "usable_roof_medium_m2",
    "usable_roof_high_m2",
]

missing = [c for c in required_area_columns if c not in roofs.columns]

if missing:
    print("Missing area columns:", missing)
else:
    print("\nArea totals (m²):")
    print(roofs[required_area_columns].sum().round(2))

    # Check whether each usable area follows its assumed fraction.
    checks = {
        "Low (30%)": (
            roofs["usable_roof_low_m2"],
            roofs["roof_area_m2"] * 0.30,
        ),
        "Medium (40%)": (
            roofs["usable_roof_medium_m2"],
            roofs["roof_area_m2"] * 0.40,
        ),
        "High (50%)": (
            roofs["usable_roof_high_m2"],
            roofs["roof_area_m2"] * 0.50,
        ),
    }

    for name, (actual, expected) in checks.items():
        passed = np.allclose(
            actual.to_numpy(),
            expected.to_numpy(),
            rtol=1e-6,
            atol=1e-4,
            equal_nan=True,
        )
        print(f"{name} area formula: {'PASS' if passed else 'CHECK'}")

    # Area values should not be negative.
    negative_area = (
        roofs[required_area_columns] < 0
    ).any(axis=1).sum()

    print("Buildings with negative area estimates:", negative_area)


# --------------------------------------------------
# 4. Check generation scenarios
# --------------------------------------------------

print("\n--- BUILDING-LEVEL GENERATION CHECK ---")

if buildings_file.exists():
    buildings = gpd.read_file(buildings_file)
    print("Building records in generation file:", len(buildings))

    for year in ["2021", "2022", "2023", "2024", "2025"]:
        columns = [
            f"generation_{year}_low_kwh_year",
            f"generation_{year}_medium_kwh_year",
            f"generation_{year}_high_kwh_year",
        ]

        if all(c in buildings.columns for c in columns):
            low, medium, high = [
                buildings[c] for c in columns
            ]

            valid = low.notna() & medium.notna() & high.notna()

            low_to_medium = (medium[valid] >= low[valid]).all()
            medium_to_high = (high[valid] >= medium[valid]).all()
            nonnegative = (
                (low[valid] >= 0)
                & (medium[valid] >= 0)
                & (high[valid] >= 0)
            ).all()

            print(
                f"{year}: "
                f"low <= medium: {low_to_medium}; "
                f"medium <= high: {medium_to_high}; "
                f"nonnegative: {nonnegative}"
            )
        else:
            print(f"{year}: required generation columns not found")


# --------------------------------------------------
# 5. Check city totals against summed ward totals
# --------------------------------------------------

print("\n--- CITY TOTAL VS WARD TOTAL CHECK ---")

wards = pd.read_csv(ward_file)
city = pd.read_csv(city_file)

for year in ["2021", "2022", "2023", "2024", "2025"]:
    for scenario in ["low", "medium", "high"]:
        column = f"generation_{year}_{scenario}_kwh_year"

        if column not in wards.columns:
            print(f"{column}: missing from ward summary")
            continue

        city_row = city[
            (city["year_or_reference"].astype(str) == year)
            & (city["scenario"].str.lower() == scenario)
        ]

        if city_row.empty:
            print(f"{year} {scenario}: missing city summary row")
            continue

        city_total = float(city_row.iloc[0]["generation_kwh_year"])
        ward_total = wards[column].sum()
        difference = abs(city_total - ward_total)

        matches = np.isclose(
            city_total, ward_total, rtol=1e-6, atol=1e-2
        )

        print(
            f"{year} {scenario}: "
            f"{'PASS' if matches else 'CHECK'} | "
            f"Difference = {difference:,.2f} kWh"
        )


# --------------------------------------------------
# 6. Check missing ward generation values
# --------------------------------------------------

print("\n--- WARD DATA CHECK ---")
print("Number of ward result rows:", len(wards))

example_column = "generation_Mean_2021_2025_medium_kwh_year"

if example_column in wards.columns:
    print(
        "Wards missing mean-medium generation:",
        wards[example_column].isna().sum()
    )
else:
    print(f"Column not found: {example_column}")

print("\nValidation checks completed.")
print("A PASS means the tested consistency condition holds;")
print("it does not independently prove real-world accuracy.")

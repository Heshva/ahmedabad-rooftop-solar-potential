
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "DATA" / "PROCESSED"

BUILDINGS_FILE = PROCESSED / "buildings_solar_potential.gpkg"
WARD_FILE = PROCESSED / "ward_solar_potential.csv"

buildings = gpd.read_file(BUILDINGS_FILE)
wards = pd.read_csv(WARD_FILE)

# Check the column names before proceeding.
print("Building columns containing ward:")
print([c for c in buildings.columns if "ward" in c.lower()])

print("\nWard summary columns:")
print(wards.columns.tolist())

# The building-level file should contain a ward identifier/name.
# The ward summary should have a matching ward field.
if "ward" not in buildings.columns or "ward" not in wards.columns:
    raise ValueError(
        "A 'ward' column was not found in both files. "
        "Check the printed column names and adjust the merge key."
    )

# Mean irradiation reference, medium scenario.
generation_col = "generation_Mean_2021_2025_medium_kwh_year"

if generation_col not in buildings.columns:
    raise ValueError(
        f"Missing building generation column: {generation_col}"
    )

if generation_col not in wards.columns:
    raise ValueError(
        f"Missing ward generation column: {generation_col}"
    )

# Recalculate ward generation from individual buildings.
building_totals = (
    buildings.groupby("ward")[generation_col]
    .sum()
    .reset_index(name="building_total_kwh_year")
)

# Compare recalculated totals with the saved ward summary.
comparison = wards[["ward", generation_col]].merge(
    building_totals,
    on="ward",
    how="left",
    validate="one_to_one"
)

comparison["difference_kwh"] = (
    comparison[generation_col] - comparison["building_total_kwh_year"]
).abs()

comparison["check"] = np.isclose(
    comparison[generation_col],
    comparison["building_total_kwh_year"],
    rtol=1e-6,
    atol=0.01
)

print("\n--- Ward-total validation ---")
print("Ward count:", len(comparison))
print("All ward totals match:", comparison["check"].all())
print("Maximum difference (kWh):", comparison["difference_kwh"].max())

# Rank wards by estimated generation.
comparison["generation_gwh_year"] = (
    comparison[generation_col] / 1_000_000
)

top10 = comparison.sort_values(
    "generation_gwh_year",
    ascending=False
).head(10)

print("\n--- Top 10 wards by estimated annual generation ---")
print(
    top10[
        ["ward", "generation_gwh_year", "check"]
    ].to_string(index=False)
)

# Save results for the report and GitHub.
output_file = PROCESSED / "top_10_wards_solar_potential.csv"
top10.to_csv(output_file, index=False)

print(f"\nTop 10 ranking saved to: {output_file}")

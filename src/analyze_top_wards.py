import pandas as pd
import geopandas as gpd
from pathlib import Path
import config

# Project folders
PROJECT_DIR = Path(config.PROJECT_ROOT)

DATA_DIR = Path(config.PROCESSED_DIR)

# Load the building-level and ward-level results
buildings = gpd.read_file(DATA_DIR / "buildings_solar_potential.gpkg")

wards = pd.read_csv(DATA_DIR / "ward_solar_potential.csv")

# Check which columns are available
print("\nBUILDING FILE COLUMNS:")
print(buildings.columns.tolist())

print("\nWARD SUMMARY COLUMNS:")
print(wards.columns.tolist())

# Count buildings and sum usable rooftop area in each ward
ward_analysis = (
    buildings.groupby("ward")
    .agg(
        building_count=("ward", "size"),
        usable_roof_area_m2=("usable_roof_medium_m2", "sum")).reset_index())

# Find the estimated mean annual generation column
generation_col = "generation_Mean_2021_2025_medium_kwh_year"

# Merge with ward-level solar generation estimates
if generation_col not in wards.columns:
    print("\nExact generation column not found.")
    print("Please check the ward summary columns printed above.")
else:
    generation_summary = wards[["ward", generation_col]]

    result = ward_analysis.merge(
        generation_summary,
        on="ward",
        how="left")

    result["generation_gwh_year"] = (
        result[generation_col] / 1_000_000)

    result = result.sort_values(
        "generation_gwh_year", ascending=False)

    print("\nTOP 10 WARDS: ROOFTOP AREA VS GENERATION")
    print(
        result[[
                "ward",
                "building_count",
                "usable_roof_area_m2",
                "generation_gwh_year"
            ]].head(10).round(2).to_string(index=False))

    # Save the analysis
    output_file = DATA_DIR / "ward_roof_area_analysis.csv"
    result.to_csv(output_file, index=False)

    print("\nSaved to:", output_file)


# Average usable rooftop area per building
result["avg_usable_roof_m2_per_building"] = (
    result["usable_roof_area_m2"] /
    result["building_count"])

print("\nTOP 10 WARDS: AVERAGE ROOFTOP AREA")
print(result[[
            "ward",
            "building_count",
            "avg_usable_roof_m2_per_building",
            "generation_gwh_year"
        ]].head(10).round(2).to_string(index=False))

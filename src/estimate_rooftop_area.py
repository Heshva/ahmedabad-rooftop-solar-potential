from pathlib import Path
import geopandas as gpd
import config

# 1. Locate the data folder
processed_data = Path(config.PROCESSED_DATA)

# 2. Locate the building dataset assigned to wards
input_file = (processed_data / "buildings_assigned_to_wards.gpkg")

# 3. Load the dataset into Python
buildings = gpd.read_file(input_file)

# 4. Inspect the loaded data
print("Total assigned buildings:", len(buildings))
print("\nCoordinate reference system:")
print(buildings.crs)

print("\nAvailable columns:")
print(buildings.columns.tolist())

print("\nFirst five buildings:")
print(buildings.head())

print("\nMissing ward assignments:", buildings["ward"].isna().sum())

# 5. Calculate each building's footprint area in square metres
buildings["roof_area_m2"] = buildings.geometry.area

# 6. Define three possible usable-roof scenarios
usable_fractions = {
    "low": 0.30,
    "medium": 0.40,
    "high": 0.50}

# 7. Estimate usable rooftop area for each scenario
for scenario, fraction in usable_fractions.items():
    column_name = f"usable_roof_{scenario}_m2"
    buildings[column_name] = buildings["roof_area_m2"] * fraction

# 8. Display the results for a few buildings
print("\nRooftop area estimates (first five buildings):")
print(
    buildings[[
            "ward",
            "roof_area_m2",
            "usable_roof_low_m2",
            "usable_roof_medium_m2",
            "usable_roof_high_m2"
        ]].head().round(2))

# 9. Summarize the footprint and usable rooftop areas
print("\nTotal footprint area (m²):", round(buildings["roof_area_m2"].sum(), 2))
print("Total usable area — low scenario (m²):",round(buildings["usable_roof_low_m2"].sum(), 2))
print("Total usable area — medium scenario (m²):",round(buildings["usable_roof_medium_m2"].sum(), 2))
print("Total usable area — high scenario (m²):",round(buildings["usable_roof_high_m2"].sum(), 2))


# 10. Save the rooftop-area estimates
project_folder = Path(__file__).resolve().parent.parent
output_folder = project_folder / "DATA" / "PROCESSED"
output_folder.mkdir(parents=True, exist_ok=True)

output_file = output_folder / "buildings_with_roof_estimates.gpkg"
buildings.to_file(output_file, driver="GPKG", index=False)

print("\nRooftop estimates saved to:")
print(output_file)

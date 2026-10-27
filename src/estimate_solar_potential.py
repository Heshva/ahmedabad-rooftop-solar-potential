from pathlib import Path
import geopandas as gpd
import pandas as pd
import config

# 1. Locate  folders

processed_folder = Path(config.PROCESSED_DIR)

# 2. Define input files
buildings_file = processed_folder / "buildings_with_roof_estimates.gpkg"
solar_file = processed_folder / "nasa_power_yearly_solar_2021_2025.csv"

# 3. Check that both files exist
print("Building file exists:", buildings_file.is_file())
print("Solar data file exists:", solar_file.is_file())

# 4. Load both datasets
buildings = gpd.read_file(buildings_file)
yearly_solar = pd.read_csv(solar_file)

# 5. Inspect the building data
print("\nNumber of buildings:", len(buildings))
print("Coordinate reference system:", buildings.crs)

print("\nBuilding columns:")
print(buildings.columns.tolist())

# 6. Inspect the yearly solar data
print("\nYearly solar data:")
print(yearly_solar.to_string(index=False))


# 7. Define the solar panel assumptions
panel_efficiency = 0.20
performance_ratio = 0.75

# 8. Define the usable rooftop area scenarios
scenarios = {
    "low": "usable_roof_low_m2",
    "medium": "usable_roof_medium_m2",
    "high": "usable_roof_high_m2"}

# 9. Store the annual irradiation values by year
annual_irradiation = dict(
    zip(
        yearly_solar["year"],
        yearly_solar["annual_irradiation_kwh_m2"]))

# 10. Calculate the five-year mean annual irradiation
mean_irradiation = yearly_solar["annual_irradiation_kwh_m2"].mean()

annual_irradiation["Mean_2021_2025"] = mean_irradiation

print("\nMean annual irradiation:", round(mean_irradiation, 2),"kWh/m²/year")

# 11. Calculate generation for every year and scenario
for year, irradiation in annual_irradiation.items():
    for scenario, area_column in scenarios.items():

        output_column = f"generation_{year}_{scenario}_kwh_year"

        buildings[output_column] = (
            buildings[area_column]
            * irradiation
            * panel_efficiency
            * performance_ratio)

# 12. Show a sample of the calculated results
generation_columns = [
    column for column in buildings.columns
    if column.startswith("generation_")]

print("\nSample building-level generation estimates:")
print(
    buildings[
        ["ward", "roof_area_m2",
         "usable_roof_low_m2",
         "usable_roof_medium_m2",
         "usable_roof_high_m2"] + generation_columns
    ].head().round(2).to_string(index=False))

# 13. Summarize total generation for Ahmedabad
print("\nEstimated total annual generation for Ahmedabad:")

for year in annual_irradiation:
    print(f"\n{year}:")

    for scenario in scenarios:
        column = f"generation_{year}_{scenario}_kwh_year"
        total_generation = buildings[column].sum()

        print(
            f"  {scenario.capitalize()} scenario: "
            f"{total_generation:,.2f} kWh/year "
            f"({total_generation / 1_000_000:,.2f} GWh/year)")


# 14. Save building-level generation estimates
building_output = processed_folder / "buildings_solar_potential.gpkg"

buildings.to_file(
    building_output,
    driver="GPKG",
    index=False)

# 15. Calculate total generation for each ward
ward_generation = (
    buildings.groupby("ward")[generation_columns]
    .sum()
    .reset_index())

ward_output = processed_folder / "ward_solar_potential.csv"
ward_generation.to_csv(ward_output, index=False)

# 16. Create a clear city-wide summary table
summary_rows = []

for year, irradiation in annual_irradiation.items():
    for scenario in scenarios:
        column = f"generation_{year}_{scenario}_kwh_year"
        total_kwh = buildings[column].sum()

        summary_rows.append({
            "year_or_reference": year,
            "annual_irradiation_kwh_m2": irradiation,
            "scenario": scenario,
            "generation_kwh_year": total_kwh,
            "generation_gwh_year": total_kwh / 1_000_000})

city_summary = pd.DataFrame(summary_rows)

city_output = processed_folder / "city_solar_potential_summary.csv"
city_summary.to_csv(city_output, index=False)

# 17. Confirm saved files
print("\nOutput files saved successfully:")
print("Building estimates:", building_output)
print("Ward estimates:", ward_output)
print("City summary:", city_output)

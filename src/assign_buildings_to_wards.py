from pathlib import Path
import geopandas as gpd
import config

# --------------------------------------------------
# 1. Define input and output paths
# --------------------------------------------------
building_file = Path(config.BUILDINGS_FILE)
ward_file = Path(config.WARDS_FILE)


processed_folder = config.PROCESSED_FOLDER
processed_folder.mkdir(parents=True, exist_ok=True)
output_file = processed_folder / "buildings_assigned_to_wards.gpkg"

if not building_file.is_file():
    raise FileNotFoundError(f"Building file not found: {building_file}")

if not ward_file.is_file():
    raise FileNotFoundError(f"Ward file not found: {ward_file}")

# --------------------------------------------------
# 2. Load both datasets
# --------------------------------------------------
buildings = gpd.read_file(building_file)
wards = gpd.read_file(ward_file)

print("Buildings loaded:", len(buildings))
print("Wards loaded:", len(wards))

# --------------------------------------------------
# 3. Reproject to a CRS measured in metres
# --------------------------------------------------
metric_crs = "EPSG:32643"
buildings = buildings.to_crs(metric_crs)
wards = wards.to_crs(metric_crs)

# --------------------------------------------------
# 4. Create representative points for buildings
# --------------------------------------------------
building_points = buildings.copy()
building_points["geometry"] = (buildings.geometry.representative_point())

# --------------------------------------------------
# 5. Match each point with its ward
# --------------------------------------------------
points_in_wards = gpd.sjoin(
    building_points,
    wards[["Name", "geometry"]],
    how="left",
    predicate="within")

matched_rows = points_in_wards.dropna(subset=["Name"])
ward_counts = (matched_rows.groupby(level=0)["Name"].nunique())
multiple_matches = ward_counts[ward_counts > 1]

print("\nInitial matching results:")
print("Buildings matched to at least one ward:", len(ward_counts))
print("Buildings matched to multiple wards:", len(multiple_matches))

# --------------------------------------------------
# 6. Assign one ward to each matched building
# --------------------------------------------------
ward_assignment = (matched_rows.groupby(level=0)["Name"].first())

for building_idx in multiple_matches.index:

    candidates = points_in_wards.loc[[building_idx]]
    building_geometry = buildings.loc[building_idx, "geometry"]
    overlap_areas = []

    for _, row in candidates.iterrows():

        ward_idx = int(row["index_right"])
        ward_geometry = wards.loc[ward_idx, "geometry"]

        overlap_area = building_geometry.intersection(ward_geometry).area
        overlap_areas.append((overlap_area, row["Name"]))

    best_ward = sorted(overlap_areas,key=lambda item: (-item[0], item[1]))[0][1]
    ward_assignment.loc[building_idx] = best_ward

# --------------------------------------------------
# 7. Add assignments and exclude unmatched buildings
# --------------------------------------------------
buildings["ward"] = ward_assignment
assigned_buildings = buildings.loc[buildings["ward"].notna()].copy()

print("\nFinal assignment results:")
print("Original buildings:", len(buildings))
print("Assigned buildings:", len(assigned_buildings))
print("Unmatched buildings:", buildings["ward"].isna().sum())

print("\nBuildings assigned per ward:")
print(assigned_buildings["ward"].value_counts().sort_index())

# --------------------------------------------------
# 8. Save the assigned dataset
# --------------------------------------------------
assigned_buildings.to_file(
    output_file,
    driver="GPKG",
    index=False)

print("\nAssigned dataset saved to:")
print(output_file)

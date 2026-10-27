from pathlib import Path
import config
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

#--------------------------------------------------
# 1. Set project folders
# --------------------------------------------------
PROCESSED = config.PROCESSED_DIR
RAW = config.RAW_DIR

CHARTS = config.OUTPUT_DIR / "charts"
MAPS = config.OUTPUT_DIR / "maps"

CHARTS.mkdir(parents=True, exist_ok=True)
MAPS.mkdir(parents=True, exist_ok=True)

YEARS = [2021, 2022, 2023, 2024, 2025]
SCENARIOS = ["low", "medium", "high"]
# --------------------------------------------------
# 2. Load saved results
# --------------------------------------------------
city = pd.read_csv(PROCESSED / "city_solar_potential_summary.csv")
wards_result = pd.read_csv(PROCESSED / "ward_solar_potential.csv")
wards_map = gpd.read_file(config.WARDS_FILE)

required_city_columns = {
    "year_or_reference",
    "scenario",
    "generation_kwh_year"}
if not required_city_columns.issubset(city.columns):
    raise ValueError(
        f"City summary is missing columns: "
        f"{required_city_columns - set(city.columns)}")

if "ward" not in wards_result.columns:
    raise ValueError("Ward summary must contain a 'ward' column.")

if "Name" not in wards_map.columns:
    raise ValueError("Ward boundary data must contain a 'Name' column.")

# Keep actual years, excluding the five-year mean reference row.
city["year_or_reference"] = city["year_or_reference"].astype(str)
yearly = city[city["year_or_reference"].isin([str(y) for y in YEARS])].copy()

yearly["year_or_reference"] = yearly["year_or_reference"].astype(int)
yearly["scenario"] = yearly["scenario"].str.lower()
yearly["generation_gwh_year"] = (yearly["generation_kwh_year"] / 1_000_000)
yearly = yearly.sort_values("year_or_reference")

# Check that every year/scenario combination exists.
expected = pd.MultiIndex.from_product(
    [YEARS, SCENARIOS],
    names=["year_or_reference", "scenario"])
actual = pd.MultiIndex.from_frame(yearly[["year_or_reference", "scenario"]].drop_duplicates())
missing = expected.difference(actual)

if len(missing):
    raise ValueError(f"Missing year/scenario results: {list(missing)}")

# --------------------------------------------------
# 3. Chart 1: Annual generation trends for all scenarios
# --------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6))

for scenario in SCENARIOS:
    scenario_data = yearly[yearly["scenario"] == scenario].sort_values("year_or_reference")

    ax.plot(
        scenario_data["year_or_reference"],
        scenario_data["generation_gwh_year"],
        marker="o",
        linewidth=2.5,
        label=scenario.title())

ax.set_title("Ahmedabad: Annual Rooftop Solar Potential by Scenario (2021–2025)")
ax.set_xlabel("Year")
ax.set_ylabel("Estimated electricity generation (GWh/year)")
ax.set_xticks(YEARS)
ax.legend(title="Rooftop utilization scenario")
ax.grid(True, linestyle="--", alpha=0.4)

fig.tight_layout()
fig.savefig(CHARTS / "01_annual_solar_generation_trend.png",dpi=300,bbox_inches="tight")
plt.close(fig)


# --------------------------------------------------
# 4. Chart 2: Low, medium and high scenarios by year
# --------------------------------------------------
pivot = yearly.pivot(
    index="year_or_reference",
    columns="scenario",
    values="generation_gwh_year").reindex(columns=SCENARIOS)

fig, ax = plt.subplots(figsize=(10, 6))
pivot.plot(kind="bar", ax=ax, width=0.8)

ax.set_title("Annual Solar Potential by Rooftop Utilization Scenario")
ax.set_xlabel("Year")
ax.set_ylabel("Estimated electricity generation (GWh/year)")
ax.legend(title="Scenario")
ax.tick_params(axis="x", rotation=0)
ax.grid(axis="y", linestyle="--", alpha=0.4)

fig.tight_layout()
fig.savefig(CHARTS / "02_yearly_low_medium_high_comparison.png",dpi=300,bbox_inches="tight")
plt.close(fig)


# --------------------------------------------------
# 5. Chart 3: Five-year cumulative generation
# --------------------------------------------------
cumulative = (
    yearly.groupby("scenario")["generation_gwh_year"]
    .sum()
    .reindex(SCENARIOS))

fig, ax = plt.subplots(figsize=(8, 5))
cumulative.plot(kind="bar", ax=ax, width=0.6)

ax.set_title("Cumulative Estimated Solar Generation (2021–2025)")
ax.set_xlabel("Rooftop utilization scenario")
ax.set_ylabel("Five-year estimated generation (GWh)")
ax.tick_params(axis="x", rotation=0)
ax.grid(axis="y", linestyle="--", alpha=0.4)

for container in ax.containers:
    ax.bar_label(container, fmt="%.0f", padding=3)

fig.tight_layout()
fig.savefig(CHARTS / "03_five_year_scenario_comparison.png",dpi=300,bbox_inches="tight")
plt.close(fig)


# --------------------------------------------------
# 6. Prepare ward map data
# --------------------------------------------------
def normalize_name(series):
    return series.astype(str).str.strip().str.casefold()


wards_map["ward_key"] = normalize_name(wards_map["Name"])
wards_result["ward_key"] = normalize_name(wards_result["ward"])

# Prevent ambiguous joins if a ward occurs more than once in the CSV.
if wards_result["ward_key"].duplicated().any():
    raise ValueError("Ward summary contains duplicate normalized ward names.")

ward_names = sorted(
    wards_map["Name"].dropna().astype(str).unique(),
    key=str.casefold)
ward_number = {name: i + 1 for i, name in enumerate(ward_names)}
wards_map["ward_number"] = wards_map["Name"].map(ward_number)

map_data = wards_map.merge(
    wards_result.drop(columns=["ward"], errors="ignore"),
    on="ward_key",
    how="left",
    validate="many_to_one")

# Reproject to metres for mapping and label placement.
map_data = map_data.to_crs(epsg=32643)

ward_key_text = "\n".join(
    f"{ward_number[name]:02d}  "
    f"{name.split(' ', 1)[1] if name.split(' ', 1)[0].isdigit() else name}"
    for name in ward_names)

map_columns = [
    f"generation_{year}_{scenario}_kwh_year"
    for year in YEARS
    for scenario in SCENARIOS]
mean_col = "generation_Mean_2021_2025_medium_kwh_year"

missing_columns = [
    col for col in map_columns + [mean_col]
    if col not in map_data.columns]
if missing_columns:
    raise ValueError(
        f"Ward results are missing map columns: {missing_columns}")

all_values = map_data[map_columns + [mean_col]].to_numpy(dtype=float) / 1_000_000
valid_values = all_values[np.isfinite(all_values)]

if len(valid_values) == 0:
    raise ValueError("No valid ward generation values were found.")

vmin = float(valid_values.min())
vmax = float(valid_values.max())
if vmin == vmax:
    vmax = vmin + 1

color_norm = Normalize(vmin=vmin, vmax=vmax)


# --------------------------------------------------
# 7. Function to generate one ward map
# --------------------------------------------------
def make_ward_map(column, title, filename):
    plot_data = map_data.copy()
    plot_data["generation_gwh_year"] = plot_data[column] / 1_000_000

    fig = plt.figure(figsize=(15, 11))
    layout = fig.add_gridspec(
        1, 3,
        width_ratios=[5.5, 2.4, 0.25],
        wspace=0.08)

    ax_map = fig.add_subplot(layout[0, 0])
    ax_key = fig.add_subplot(layout[0, 1])
    ax_color = fig.add_subplot(layout[0, 2])

    plot_data.plot(
        column="generation_gwh_year",
        cmap="coolwarm",
        norm=color_norm,
        linewidth=0.55,
        edgecolor="black",
        missing_kwds={
            "color": "lightgrey",
            "edgecolor": "black"
        },
        ax=ax_map
    )

    label_points = plot_data.geometry.representative_point()

    for x, y, number in zip(
        label_points.x,
        label_points.y,
        plot_data["ward_number"]
    ):
        ax_map.annotate(
            f"{int(number):02d}",
            (x, y),
            ha="center",
            va="center",
            fontsize=7,
            color="black",
            bbox={
                "boxstyle": "round,pad=0.15",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.75
            }
        )

    ax_map.set_title(title, fontsize=12, pad=12)
    ax_map.set_axis_off()

    ax_key.set_title("Ward number → ward name", fontsize=10, pad=10)
    ax_key.text(
        0.02, 0.99,
        ward_key_text,
        ha="left",
        va="top",
        fontsize=7,
        linespacing=1.15,
        transform=ax_key.transAxes
    )
    ax_key.set_axis_off()

    scalar = ScalarMappable(norm=color_norm, cmap="coolwarm")
    scalar.set_array([])
    colorbar = fig.colorbar(scalar, cax=ax_color)
    colorbar.set_label("Estimated generation (GWh/year)")

    fig.text(
        0.5, 0.015,
        "Estimates use building footprints and assumed usable roof area; "
        "they are not measured electricity production.",
        ha="center",
        fontsize=8)

    fig.savefig(MAPS / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {filename}")

# --------------------------------------------------
# 8. Three five-year mean reference maps
#    Low, medium and high scenarios
# --------------------------------------------------
mean_scenarios = ["low", "medium", "high"]

for scenario in mean_scenarios:
    mean_col = f"generation_Mean_2021_2025_{scenario}_kwh_year"

    if mean_col not in map_data.columns:
        print(f"Skipped mean map: missing column {mean_col}")
        continue

    make_ward_map(
        mean_col,
        "Ahmedabad Ward-Level Rooftop Solar Potential\n"
        f"{scenario.title()} scenario | Mean annual irradiation reference, 2021–2025",
        f"ward_map_mean_2021-25_{scenario}.png"
    )


# --------------------------------------------------
# 9. Maps: each year and scenario
# --------------------------------------------------
for year in YEARS:
    for scenario in SCENARIOS:
        column = f"generation_{year}_{scenario}_kwh_year"
        make_ward_map(
            column,
            f"Ahmedabad Ward-Level Rooftop Solar Potential\n"
            f"{year} | {scenario.title()} scenario",
            f"ward_map_{year}_{scenario}.png")

print("\nVisualization complete.")
print(f"Charts saved in: {CHARTS}")
print(f"Maps saved in: {MAPS}")
print("Generated 3 charts and 16 ward maps.")

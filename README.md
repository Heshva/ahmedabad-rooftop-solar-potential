# Ahmedabad Rooftop Solar Potential Estimator

A Python-based geospatial project to estimate rooftop solar electricity generation potential across Ahmedabad's municipal wards using building footprints, ward boundaries, and solar irradiation data from NASA POWER.

## Overview

Rooftop solar potential depends on the available roof area, solar irradiation, and the efficiency of the photovoltaic system. This project combines building-footprint data and ward boundaries to estimate usable rooftop area and model annual solar electricity generation under low, medium, and high scenarios.

The project also produces ward-level maps, comparison charts, summary tables, and validation results.

**Study area:** Ahmedabad, Gujarat, India  
**Solar irradiation period:** 2021–2025  
**Tools:** Python, GeoPandas, Pandas, NumPy, Matplotlib, NASA POWER API

## Objectives

- Process building footprints and assign buildings to municipal wards.
- Estimate usable rooftop area using low, medium, and high assumptions.
- Estimate annual rooftop solar generation using solar irradiation data.
- Compare solar potential across wards and visualize the results.
- Validate the calculations and examine scenario sensitivity.

## Project Structure

```text
Rooftop solar potential estimator/
├── DATA/
│   ├── RAW/
│   │   ├── Wards_ahmd.geojson
│   │   └── buildings_ahmd.geojson
│   └── PROCESSED/
│       ├── city_solar_potential_summary.csv
│       ├── nasa_power_daily_solar_2021_2025.csv
│       ├── nasa_power_yearly_solar_2021_2025.csv
│       ├── top_10_wards_solar_potential.csv
│       ├── ward_roof_area_analysis.csv
│       └── ward_solar_potential.csv
├── OUTPUTS/
│   ├── charts/
│   └── maps/
├── src/
│   ├── config.py
│   ├── assign_buildings_to_wards.py
│   ├── estimate_rooftop_area.py
│   ├── get_solar_irradiance.py
│   ├── estimate_solar_potential.py
│   ├── analyze_top_wards.py
│   ├── analyze_ward_relation.py
│   ├── sensitivity_analysis.py
│   └── visualize_results.py
├── validation/
│   ├── validate_energy_formula.py
│   ├── validate_result.py
│   └── validate_ward_ranking.py
├── .gitignore
├── requirements.txt
└── README.md
```

Large generated GeoPackages are excluded from the repository. They can be recreated by running the processing workflow described below.

## Technologies Used

- **Python:** Main programming language.
- **GeoPandas and Shapely:** Geospatial data processing and geometry operations.
- **Pandas and NumPy:** Data cleaning, aggregation, and numerical calculations.
- **Matplotlib:** Charts and ward-level maps.
- **NASA POWER API:** Daily surface solar irradiation data.
- **PyProj:** Coordinate reference system transformations.

## Methodology

### 1. Input data

The project uses ward boundaries and building footprints for Ahmedabad. Building footprints are assigned to ward polygons, and projected geometries are used to calculate areas in square metres.

Solar irradiation data is retrieved from NASA POWER for 1 January 2021 through 31 December 2025, using a representative point near the centre of the study area.

### 2. Building-to-ward assignment

Building footprints are spatially assigned to municipal wards. Buildings that do not fall within the supplied ward boundaries remain unmatched and are excluded from ward-level summaries.

### 3. Rooftop area estimation

The footprint area is used as a proxy for horizontal roof area. Three assumptions estimate the portion of each footprint that may be usable for solar panels:

| Scenario | Assumed usable roof fraction |
|---|---:|
| Low | 30% |
| Medium | 40% |
| High | 50% |

These are scenario assumptions, not measurements of actual available roof space.

### 4. Solar irradiation processing

Daily solar irradiation is obtained from NASA POWER using the `ALLSKY_SFC_SW_DWN` parameter. Daily values are aggregated by year to estimate annual irradiation.

### 5. Solar generation estimation

The estimated annual electricity generation is calculated using:

**Annual generation = Usable rooftop area × Annual irradiation × Panel efficiency × Performance ratio**

The model uses a panel efficiency of 20% and a performance ratio of 0.75.

### 6. Visualization and analysis

The project generates:
- Annual generation comparisons across low, medium, and high scenarios.
- Five-year scenario comparison charts.
- Ward-level solar potential maps for each year and scenario.
- Five-year mean-reference ward maps.
- Ward summary tables and sensitivity analysis charts.

## Workflow: Recreating the Processed Data

### Requirements

Install Python and Git, then open a terminal in the project root.

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```bat
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Run the processing scripts

Run the scripts from the project root in this order:

```bash
python src/assign_buildings_to_wards.py
python src/estimate_rooftop_area.py
python src/get_solar_irradiance.py
python src/estimate_solar_potential.py
```

Then run the analysis and visualization scripts after the required processed outputs have been generated:

```bash
python src/analyze_top_wards.py
python src/analyze_ward_relation.py
python src/sensitivity_analysis.py
python src/visualize_results.py
```

Finally, run the validation scripts:

```bash
python validation/validate_energy_formula.py
python validation/validate_result.py
python validation/validate_ward_ranking.py
```

The scripts may need access to the original input datasets and an internet connection to retrieve NASA POWER data. Generated filenames and dependencies should be checked against the current script configuration if the workflow is modified.

## Key Results

The current model produced the following city-wide estimates using mean annual irradiation over 2021–2025.

| Scenario | Usable rooftop area | Estimated annual generation |
|---|---:|---:|
| Low | 9.99 million m² | 2,859.75 GWh/year |
| Medium | 13.32 million m² | 3,813.00 GWh/year |
| High | 16.65 million m² | 4,766.25 GWh/year |

The results represent modelled generation potential under the stated assumptions. They should not be interpreted as measured electricity generation or confirmed installable capacity.

## Validation

The implemented checks include:
- Confirming usable roof area matches the specified scenario fractions.
- Checking for negative area values.
- Verifying that low, medium, and high scenario generation follows the expected ordering.
- Comparing city totals with aggregated ward totals.
- Checking energy calculations against the implemented formula.

The ward-level relationship between usable roof area and generation is expected to be linear under the model because the same irradiation, panel efficiency, and performance ratio are applied across wards.

## Limitations

- Building footprint area is only a proxy for horizontal roof area.
- Usable roof fractions are assumed and are not based on individual roof surveys.
- A representative NASA POWER point is used for the city; irradiation is not independently modelled for every ward.
- Roof orientation, shading, obstacles, structural suitability, panel layout, and local installation constraints are not individually assessed.
- The performance ratio represents generalized system losses.
- Results depend on input-data coverage, spatial assignment, and model assumptions.

Consequently, the outputs are preliminary estimates for spatial comparison and planning, not a bankable engineering assessment.

## Data Sources and References

### 1. Ahmedabad Ward Boundaries

- **File:** `Wards_ahmd.geojson`
- **Source:** [DataMeet India — Ahmedabad Ward Boundaries](https://github.com/datameet/Municipal_Spatial_Data/blob/master/Ahmedabad/Wards.geojson)
- **Purpose:** Defines the municipal ward boundaries used for spatial analysis and ward-level solar potential estimation.
- **Attribution:** DataMeet India community. The repository states that its datasets are shared under CC BY 4.0 unless otherwise specified.

### 2. Building Footprints

- **File:** `buildings_ahmd.geojson`
- **Download tool:** [GISConvert — Building Footprints](https://gisconvert.org/tools/building-footprints/)
- **Purpose:** Provides building footprint geometries for estimating rooftop area.

To obtain building footprints for the study area, download the ward boundary file from DataMeet, open the GISConvert building-footprints tool, load the ward boundary file, and follow the website's instructions to retrieve and export the footprints.

**Data note:** The GISConvert tool currently describes its building data as OpenStreetMap data. The combined building-footprint file used in this project contains records attributed to multiple sources, so the origin and licence of each source should be verified before redistributing the complete file.

### 3. Solar Irradiation Data

- **Provider:** NASA Prediction of Worldwide Energy Resources (POWER)
- **Parameter:** `ALLSKY_SFC_SW_DWN`
- **Period:** 1 January 2021 – 31 December 2025
- **Purpose:** Supplies daily surface solar irradiation values used to estimate annual rooftop solar electricity generation.

References:
- [NASA POWER official website](https://power.larc.nasa.gov/)
- [NASA POWER Daily API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)

Solar irradiation data can be retrieved by running `src/get_solar_irradiance.py`.

### Reproducing the Project

Place the downloaded input files in `DATA/RAW/` using the filenames expected by the scripts. Follow the processing workflow documented in this README to regenerate the processed datasets, summary tables, maps, and charts.

Users should check the original source pages for current availability, licence conditions, and attribution requirements before reusing or redistributing data.

## Future Improvements

- Incorporate roof orientation, slope, and shading.
- Use finer-resolution solar irradiation data where appropriate.
- Include panel spacing and rooftop obstruction estimates.
- Compare modelled estimates with measured or independently published solar-generation data.
- Improve reproducibility by documenting exact dependency versions and data-source licences.

## Author

Developed as a geospatial data analysis project focused on estimating rooftop solar potential across Ahmedabad, Gujarat.

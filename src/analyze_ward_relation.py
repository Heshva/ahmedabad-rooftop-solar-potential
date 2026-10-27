import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import config

PROJECT_DIR = Path(config.PROJECT_ROOT)
DATA_DIR = Path(config.PROCESSED_DIR)
CHART_DIR = PROJECT_DIR / "outputs" / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

# Load the ward-level analysis
df = pd.read_csv(DATA_DIR / "ward_roof_area_analysis.csv")

# Convert generation from kWh/year to GWh/year if needed
df["generation_gwh_year"] = (df["generation_Mean_2021_2025_medium_kwh_year"]/ 1_000_000)

# Check the relationship between roof area and generation
correlation = df[["usable_roof_area_m2", "generation_gwh_year"]].corr().iloc[0, 1]

print("Number of wards:", len(df))
print("Correlation between usable roof area and generation:",round(correlation, 6))

# Plot total usable roof area against estimated generation
plt.figure(figsize=(9, 6))
plt.scatter(
    df["usable_roof_area_m2"],
    df["generation_gwh_year"])

plt.xlabel("Total usable rooftop area (m²)")
plt.ylabel("Estimated annual generation (GWh/year)")
plt.title("Usable Rooftop Area vs Estimated Solar Generation")
plt.grid(True, alpha=0.3)
plt.tight_layout()

output_path = CHART_DIR / "ward_roof_area_vs_generation.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.show()

print("Chart saved to:", output_path)

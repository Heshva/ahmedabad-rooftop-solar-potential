import config
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

PROJECT_DIR = Path(config.PROJECT_ROOT)
CHART_DIR = PROJECT_DIR / "charts"
DATA_DIR = Path(config.DATA_DIR)
CHART_DIR = PROJECT_DIR / "outputs" / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_DIR / "city_solar_potential_summary.csv")

# Select the five-year mean reference
mean_df = df[df["year_or_reference"].astype(str) == "Mean_2021_2025"].copy()

# Arrange the scenarios for comparison
scenario_order = ["low", "medium", "high"]

mean_df["scenario"] = pd.Categorical(
    mean_df["scenario"],
    categories=scenario_order,
    ordered=True)

mean_df = mean_df.sort_values("scenario")

print("\nMEAN ANNUAL SOLAR GENERATION")
print(mean_df[["scenario", "generation_gwh_year"]].to_string(index=False))

values = mean_df.set_index("scenario")["generation_gwh_year"]

low = values["low"]
medium = values["medium"]
high = values["high"]

print("\nSENSITIVITY RESULTS")
print(f"Low estimate:    {low:,.2f} GWh/year")
print(f"Medium estimate: {medium:,.2f} GWh/year")
print(f"High estimate:   {high:,.2f} GWh/year")

print(f"\nMedium is {(medium / low - 1) * 100:.1f}% higher than low.")
print(f"High is {(high / medium - 1) * 100:.1f}% higher than medium.")
print(f"Total low-to-high range: " f"{high - low:,.2f} GWh/year")

# Create a scenario comparison chart
plt.figure(figsize=(8, 5))

plt.bar(["Low (30%)", "Medium (40%)", "High (50%)"], [low, medium, high])

plt.ylabel("Estimated annual generation (GWh/year)")
plt.title("Sensitivity to Usable Rooftop Area Assumptions")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

chart_path = (CHART_DIR / "solar_scenario_sensitivity.png")
plt.savefig(chart_path, dpi=300, bbox_inches="tight")
plt.show()

print("\nChart saved to:", chart_path)

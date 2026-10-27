import requests
import pandas as pd
import geopandas as gpd
import config

def main():
    # 1. Load Ahmedabad ward boundaries
    wards = gpd.read_file(config.WARDS_FILE).to_crs("EPSG:4326")

    # 2. Calculate the approximate city-centre coordinates
    min_lon, min_lat, max_lon, max_lat = wards.total_bounds
    latitude = (min_lat + max_lat) / 2
    longitude = (min_lon + max_lon) / 2

    print(f"Location: {latitude:.5f}, {longitude:.5f}")

    # 3. Request daily solar irradiation from NASA POWER
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"

    params = {
        "parameters": "ALLSKY_SFC_SW_DWN",
        "community": "RE",
        "longitude": longitude,
        "latitude": latitude,
        "start": "20210101",
        "end": "20251231",
        "format": "JSON"
    }

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    solar_data = (
        response.json()["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"])

    # 4. Convert the response into a DataFrame
    df = pd.DataFrame(
        solar_data.items(),
        columns=["date", "solar_irradiation_kwh_m2_day"])

    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df["solar_irradiation_kwh_m2_day"] = pd.to_numeric(
        df["solar_irradiation_kwh_m2_day"],
        errors="coerce")

    # 5. Remove missing and invalid values
    df.loc[df["solar_irradiation_kwh_m2_day"] < 0,"solar_irradiation_kwh_m2_day"] = float("nan")

    df = df.dropna(subset=["solar_irradiation_kwh_m2_day"]).copy()

    if df.empty:
        raise ValueError("NASA POWER returned no valid solar irradiation data.")

    # 6. Save daily irradiation data
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    daily_output = (config.PROCESSED_DIR / "nasa_power_daily_solar_2021_2025.csv")
    df.to_csv(daily_output, index=False)

    # 7. Calculate annual irradiation for each year
    df["year"] = df["date"].dt.year

    yearly = (
        df.groupby("year")["solar_irradiation_kwh_m2_day"]
        .agg(["sum", "mean", "count"])
        .reset_index()
        .rename(columns={
            "sum": "annual_irradiation_kwh_m2",
            "mean": "average_daily_irradiation_kwh_m2_day",
            "count": "valid_days"}))

    # 8. Save yearly summary
    yearly_output = (config.PROCESSED_DIR / "nasa_power_yearly_solar_2021_2025.csv")
    yearly.to_csv(yearly_output, index=False)

    print("\nYearly solar irradiation:")
    print(yearly.round(3).to_string(index=False))

    print(
        "\nMean annual irradiation (2021–2025):",
        f"{yearly['annual_irradiation_kwh_m2'].mean():.2f}",
        "kWh/m²/year")

    print("\nSaved files:")
    print(daily_output)
    print(yearly_output)


if __name__ == "__main__":
    main()

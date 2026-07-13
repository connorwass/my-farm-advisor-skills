import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

from generate_storyline_dashboard import (
    BASE_TEMP,
    CORN_NDVI_PHENOLOGY,
    GROWING_SEASON,
    _doy_to_date,
    compute_gdd,
    load_cdl,
    load_ndvi_records,
    load_weather,
)

GS_START, GS_END = GROWING_SEASON

COLORS = ["#2563eb", "#16a34a", "#d97706", "#dc2626", "#7c3aed", "#0891b2", "#ca8a04", "#be185d"]


def generate_ndvi_curve_multi(ndvi_records: pd.DataFrame, doy_range: np.ndarray) -> np.ndarray:
    doys, ndvis = zip(*CORN_NDVI_PHENOLOGY)
    phenology_doys = list(doys)
    phenology_ndvis = list(ndvis)

    if not ndvi_records.empty:
        for _, r in ndvi_records.iterrows():
            d = int(r["doy"])
            v = float(r["mean_ndvi"])
            if d not in phenology_doys:
                idx = np.searchsorted(phenology_doys, d)
                phenology_doys.insert(idx, d)
                phenology_ndvis.insert(idx, v)

    interp = PchipInterpolator(phenology_doys, phenology_ndvis)
    return np.clip(interp(doy_range), 0.0, 1.0)


def plot_multi_year(field_id: str, weather_fid: str, years: list[int],
                    weather_path: Path, cdl_path: Path, ndvi_dir: Path,
                    output_path: Path):
    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
    fig.suptitle(f"Multi-Year Comparison: {field_id} ({years[0]}–{years[-1]})",
                 fontsize=14, fontweight="bold", y=0.98)

    all_weather = {}
    doy_range = np.arange(GS_START, GS_END + 1)
    all_tmax = []
    all_tmin = []

    for idx, year in enumerate(years):
        color = COLORS[idx % len(COLORS)]
        label = str(year)

        weather = load_weather(weather_path, weather_fid, year)
        if weather.empty:
            continue
        all_weather[year] = weather
        doy_to_val = dict(zip(weather["doy"], weather["T2M_MAX"]))
        all_tmax.append(np.array([doy_to_val.get(d, np.nan) for d in doy_range]))
        doy_to_val = dict(zip(weather["doy"], weather["T2M_MIN"]))
        all_tmin.append(np.array([doy_to_val.get(d, np.nan) for d in doy_range]))

        ndvi_csv = ndvi_dir / f"ndvi_pro_{year}.csv"
        ndvi_records = pd.DataFrame()
        if ndvi_csv.exists():
            ndvi_records = load_ndvi_records(ndvi_csv, field_id)

        ndvi_vals = generate_ndvi_curve_multi(ndvi_records, doy_range)
        ndvi_dates = _doy_to_date(doy_range, 2024)

        dates = _doy_to_date(weather["doy"].values, 2024)
        gdd = compute_gdd(weather["T2M_MAX"], weather["T2M_MIN"])
        gdd_cum = np.cumsum(gdd.values)
        precip_cum = np.cumsum(weather["PRECTOTCORR"].values)

        ax1 = axes[0]
        ax1.plot(ndvi_dates, ndvi_vals, color=color, linewidth=1.5, label=label)
        if not ndvi_records.empty:
            obs_dates = _doy_to_date(ndvi_records["doy"].values, 2024)
            ax1.scatter(obs_dates, ndvi_records["mean_ndvi"].values,
                        color=color, s=20, zorder=5)

        ax2 = axes[1]
        ax2.plot(dates, precip_cum, color=color, linewidth=1.5, label=label)

        ax3 = axes[2]
        ax3.plot(dates, weather["T2M_MAX"].values, color=color,
                 linewidth=0.6, alpha=0.4, linestyle="-")
        ax3.plot(dates, weather["T2M_MIN"].values, color=color,
                 linewidth=0.6, alpha=0.4, linestyle="--")

        ax4 = axes[3]
        ax4.plot(dates, gdd_cum, color=color, linewidth=1.5, label=label)

    if all_tmax:
        ref_dates = _doy_to_date(doy_range, 2024)
        avg_tmax = np.nanmean(all_tmax, axis=0)
        avg_tmin = np.nanmean(all_tmin, axis=0)
        ax3.plot(ref_dates, avg_tmax, color="black", linewidth=2.5, linestyle="-", label="Avg Tmax")
        ax3.plot(ref_dates, avg_tmin, color="black", linewidth=2.5, linestyle="--", label="Avg Tmin")

    axes[0].set_ylabel("NDVI")
    axes[0].set_ylim(-0.05, 1.05)
    axes[0].set_title("NDVI by Year", fontsize=11, fontweight="bold")
    axes[0].legend(fontsize=7, ncol=len(years))
    axes[0].grid(True, alpha=0.2)

    axes[1].set_ylabel("Cumulative precip (mm)")
    axes[1].set_title("Cumulative Precipitation by Year", fontsize=11, fontweight="bold")
    axes[1].legend(fontsize=7, ncol=len(years))
    axes[1].grid(True, alpha=0.2)

    axes[2].set_ylabel("Temperature (°C)")
    axes[2].set_title("Temperature Extremes by Year (solid=Tmax, dashed=Tmin)",
                      fontsize=11, fontweight="bold")
    axes[2].legend(fontsize=6, ncol=min(3, len(years)))
    axes[2].grid(True, alpha=0.2)

    axes[3].set_xlabel("Date")
    axes[3].set_ylabel("Cumulative GDD")
    axes[3].set_title(f"Cumulative GDD (base {BASE_TEMP}°C) by Year",
                      fontsize=11, fontweight="bold")
    axes[3].legend(fontsize=7, ncol=len(years))
    axes[3].grid(True, alpha=0.2)

    gs_start_date = _doy_to_date(GS_START, 2024)
    gs_end_date = _doy_to_date(GS_END, 2024)
    for ax in axes:
        ax.set_xlim(gs_start_date, gs_end_date)
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=0, ha="center")

    fig.text(0.5, 0.01, "Growing Season (Apr 1 – Oct 31)", ha="center",
             fontsize=10, fontweight="bold")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Multi-year comparison saved: {output_path}")


def main():
    if len(sys.argv) < 2:
        field_id = "osm-1360394834"
    else:
        field_id = sys.argv[1]

    weather_path = Path("/home/coder/my-farm-advisor-runtime/data-pipeline/growers/ia-grower/farms/ia-grower-iowa/fields") / field_id / "weather" / "daily_weather.csv"
    cdl_path = Path("/home/coder/my-farm-advisor-runtime/data-pipeline/growers/ia-grower/farms/ia-grower-iowa/derived/tables/ia_grower_iowa_cdl_2021_2025_full_composition.csv")
    ndvi_dir = Path("/tmp")
    output_dir = Path(__file__).resolve().parent.parent / "output"

    years = [2021, 2022, 2023, 2024, 2025]

    if not weather_path.exists():
        print(f"Error: {weather_path} not found", file=sys.stderr)
        sys.exit(1)

    plot_multi_year(field_id, field_id, years,
                    weather_path, cdl_path, ndvi_dir,
                    output_dir / f"multi_year_comparison_{field_id}.png")

    for year in years:
        crop = load_cdl(cdl_path, field_id, year)
        precip = load_weather(weather_path, field_id, year)["PRECTOTCORR"].sum()
        gdd = compute_gdd(
            load_weather(weather_path, field_id, year)["T2M_MAX"],
            load_weather(weather_path, field_id, year)["T2M_MIN"]
        ).sum()
        print(f"  {year} ({crop}): {precip:.0f}mm precip, {gdd:.0f} GDD")


if __name__ == "__main__":
    main()

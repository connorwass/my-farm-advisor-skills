import argparse
import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scipy.interpolate import PchipInterpolator

BASE_TEMP = 10.0
GROWING_SEASON = (91, 304)
GS_START, GS_END = GROWING_SEASON

CORN_NDVI_PHENOLOGY = [
    (91, 0.05),
    (110, 0.08),
    (125, 0.15),
    (145, 0.40),
    (160, 0.65),
    (170, 0.78),
    (190, 0.87),
    (205, 0.89),
    (220, 0.85),
    (240, 0.72),
    (260, 0.52),
    (280, 0.28),
    (300, 0.10),
    (304, 0.08),
]

EVENT_STYLES = {
    "frost": {"color": "#2563eb", "marker": "v", "label": "Frost"},
    "heat": {"color": "#dc2626", "marker": "^", "label": "Hot day"},
    "heavy_rain": {"color": "#0891b2", "marker": "o", "label": "Heavy rain"},
    "ndvi_peak": {"color": "#16a34a", "marker": "*", "label": "Peak NDVI"},
    "ndvi_dip": {"color": "#d97706", "marker": "x", "label": "NDVI dip"},
}

REPO_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_WEATHER = REPO_ROOT / "my-farm-advisor" / "weather" / "nasa-power-weather" / "examples" / "sample_weather_2fields_2020_2024.csv"
SAMPLE_CDL = REPO_ROOT / "my-farm-advisor" / "soil" / "cdl-cropland" / "examples" / "sample_cdl_2_fields.csv"
SAMPLE_NDVI_STATS = REPO_ROOT / "my-farm-advisor" / "imagery" / "sentinel2-imagery" / "examples" / "sample_field_stats.csv"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"

DEFAULT_FIELD = "OSM_1428284928"
DEFAULT_WEATHER_FIELD = "271623002471299"
DEFAULT_YEAR = 2024


def load_cdl(path: Path, field_id: str, year: int) -> str | None:
    df = pd.read_csv(path)
    row = df[(df["field_id"] == field_id) & (df["year"] == year)]
    if row.empty:
        return None
    return row.iloc[0]["crop_name"]


def load_weather(path: Path, field_id: str, year: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["field_id"].astype(str) == str(field_id)].copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.year == year].copy()
    df["doy"] = df["date"].dt.dayofyear
    return df.sort_values("date").reset_index(drop=True)


def load_ndvi_anchor(path: Path, field_id: str) -> tuple[int, float] | None:
    df = pd.read_csv(path)
    row = df[df["field_id"] == field_id]
    if row.empty:
        return None
    r = row.iloc[0]
    date = pd.to_datetime(r["scene_date"])
    return date.dayofyear, r["mean_ndvi"]


def compute_gdd(tmax: pd.Series, tmin: pd.Series, base: float = BASE_TEMP) -> pd.Series:
    tavg = (tmax + tmin) / 2.0
    return np.maximum(0.0, tavg - base)


def detect_events(weather: pd.DataFrame) -> list[dict]:
    events = []
    heavy = weather[weather["PRECTOTCORR"] > 20]
    for _, r in heavy.iterrows():
        events.append({"doy": r["doy"], "type": "heavy_rain", "value": r["PRECTOTCORR"], "desc": f"{r['PRECTOTCORR']:.0f}mm rain"})

    hot = weather[weather["T2M_MAX"] > 35]
    for _, r in hot.iterrows():
        events.append({"doy": r["doy"], "type": "heat", "value": r["T2M_MAX"], "desc": f"{r['T2M_MAX']:.0f}°C max"})

    frost = weather[weather["T2M_MIN"] <= 0]
    spring = frost[frost["doy"] <= 213]
    fall = frost[frost["doy"] > 213]
    if not spring.empty:
        last = spring.iloc[-1]
        events.append({"doy": last["doy"], "type": "frost", "value": last["T2M_MIN"], "desc": "Last spring frost"})
    if not fall.empty:
        first = fall.iloc[0]
        events.append({"doy": first["doy"], "type": "frost", "value": first["T2M_MIN"], "desc": "First fall frost"})

    return sorted(events, key=lambda e: e["doy"])


def generate_ndvi_curve(anchor_doy: int | None, anchor_value: float | None, doy_range: np.ndarray) -> np.ndarray:
    doys, ndvis = zip(*CORN_NDVI_PHENOLOGY)
    doys_list = list(doys)
    ndvis_list = list(ndvis)

    if anchor_doy is not None and anchor_value is not None:
        if anchor_doy not in doys_list:
            idx = np.searchsorted(doys_list, anchor_doy)
            doys_list.insert(idx, anchor_doy)
            ndvis_list.insert(idx, anchor_value)

    interp = PchipInterpolator(doys_list, ndvis_list)
    return interp(doy_range)


def generate_captions(events: list[dict], ndvi_peak_doy: float, ndvi_peak_val: float, total_precip: float, total_gdd: float, crop: str) -> list[str]:
    captions = [
        f"Season overview: {crop} field, DOY {GS_START}–{GS_END}.",
        f"Total precipitation: {total_precip:.0f}mm. Total GDD: {total_gdd:.0f} (base 10°C).",
    ]
    if ndvi_peak_val > 0:
        captions.append(f"Peak NDVI of {ndvi_peak_val:.2f} reached around DOY {ndvi_peak_doy:.0f}.")
    for ev in events:
        captions.append(f"DOY {ev['doy']}: {ev['desc']}.")
    return captions


def _doy_to_date(doy: int | np.ndarray, year: int = 2024) -> np.datetime64 | np.ndarray:
    return np.datetime64(f"{year}-01-01") + np.array(doy, dtype="timedelta64[D]") - 1


def plot_dashboard(weather: pd.DataFrame, ndvi_doy: np.ndarray, ndvi_vals: np.ndarray, events: list[dict], crop: str, field_id: str, year: int, weather_fid: str, output_path: Path):
    dates = _doy_to_date(weather["doy"].values, year)
    gs_start_date = _doy_to_date(GS_START, year)
    gs_end_date = _doy_to_date(GS_END, year)
    ndvi_dates = _doy_to_date(ndvi_doy, year)

    precip = weather["PRECTOTCORR"].values
    tmax = weather["T2M_MAX"].values
    tmin = weather["T2M_MIN"].values
    gdd = compute_gdd(weather["T2M_MAX"], weather["T2M_MIN"])
    gdd_cum = np.cumsum(gdd)
    precip_cum = np.cumsum(precip)

    ndvi_peak_idx = np.argmax(ndvi_vals)
    ndvi_peak_date = ndvi_dates[ndvi_peak_idx]
    ndvi_peak_val = ndvi_vals[ndvi_peak_idx]

    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
    fig.suptitle(f"Field-Year Storyline: {field_id} — {year} ({crop})", fontsize=14, fontweight="bold", y=0.98)

    ax1 = axes[0]
    ax1.plot(ndvi_dates, ndvi_vals, color="#16a34a", linewidth=2, label="NDVI (phenology model)")
    anchor_date = _doy_to_date(170, year)
    ax1.scatter([anchor_date], [0.78], color="#dc2626", s=50, zorder=5, label="Sample anchor (Jun 18)")
    ax1.axvline(ndvi_peak_date, color="#16a34a", linestyle=":", alpha=0.5)
    ax1.annotate(f"Peak NDVI {ndvi_peak_val:.2f}", xy=(ndvi_peak_date, ndvi_peak_val),
                 xytext=(ndvi_peak_date + np.timedelta64(15, "D"), ndvi_peak_val - 0.12),
                 arrowprops=dict(arrowstyle="->", color="#16a34a"),
                 fontsize=8, color="#16a34a", fontweight="bold")
    ax1.set_ylabel("NDVI")
    ax1.set_ylim(-0.05, 1.05)
    ax1.set_title("NDVI (Sentinel-2 derived, phenology model)", fontsize=11, fontweight="bold")
    ax1.legend(fontsize=8, loc="upper left")
    ax1.grid(True, alpha=0.2)

    ax2 = axes[1]
    ax2.bar(dates, precip, color="#0891b2", width=1.5, alpha=0.6, label="Daily precip")
    ax2_twin = ax2.twinx()
    ax2_twin.plot(dates, precip_cum, color="#0c4a6e", linewidth=2, label="Cumulative precip")
    ax2_twin.set_ylabel("Cumulative precip (mm)", fontsize=9)
    for ev in events:
        if ev["type"] == "heavy_rain":
            ed = _doy_to_date(ev["doy"], year)
            ax2.annotate(ev["desc"], xy=(ed, ev["value"]),
                         xytext=(ed + np.timedelta64(8, "D"), ev["value"] + 2),
                         arrowprops=dict(arrowstyle="->", color="#0891b2"),
                         fontsize=7, color="#0891b2")
    ax2.set_ylabel("Daily precip (mm)")
    ax2.set_title("Precipitation", fontsize=11, fontweight="bold")
    ax2.legend(fontsize=8, loc="upper left")
    ax2.grid(True, alpha=0.2)

    ax3 = axes[2]
    ax3.fill_between(dates, tmin, tmax, color="#f97316", alpha=0.25, label="Daily range")
    ax3.plot(dates, tmax, color="#dc2626", linewidth=0.8, label="Tmax")
    ax3.plot(dates, tmin, color="#2563eb", linewidth=0.8, label="Tmin")
    ax3.axhline(35, color="#dc2626", linestyle="--", linewidth=1, alpha=0.5)
    ax3.text(_doy_to_date(GS_START + 2, year), 36, "35°C heat threshold", fontsize=7, color="#dc2626")
    ax3.axhline(0, color="#2563eb", linestyle="--", linewidth=1, alpha=0.5)
    for ev in events:
        ed = _doy_to_date(ev["doy"], year)
        if ev["type"] == "frost":
            ax3.annotate(ev["desc"], xy=(ed, 0),
                         xytext=(ed + np.timedelta64(5, "D"), -4),
                         arrowprops=dict(arrowstyle="->", color="#2563eb"),
                         fontsize=7, color="#2563eb")
        elif ev["type"] == "heat":
            ax3.annotate(ev["desc"], xy=(ed, ev["value"]),
                         xytext=(ed + np.timedelta64(8, "D"), ev["value"] - 2),
                         arrowprops=dict(arrowstyle="->", color="#dc2626"),
                         fontsize=7, color="#dc2626")
    ax3.set_ylabel("Temperature (°C)")
    ax3.set_title("Temperature / Extremes", fontsize=11, fontweight="bold")
    ax3.legend(fontsize=8, loc="upper left")
    ax3.grid(True, alpha=0.2)

    ax4 = axes[3]
    ax4.plot(dates, gdd_cum, color="#7c3aed", linewidth=2, label=f"GDD (base {BASE_TEMP}°C)")
    for target, label in [(800, "800 GDD"), (1200, "1200 GDD")]:
        if gdd_cum.max() >= target:
            idx = np.searchsorted(gdd_cum, target)
            tgt_date = dates[idx]
            ax4.axhline(target, color="#7c3aed", linestyle=":", alpha=0.4)
            tgt_label = pd.Timestamp(tgt_date).strftime("%b %d")
            ax4.annotate(f"{tgt_label}: {label}",
                         xy=(tgt_date, target),
                         xytext=(tgt_date + np.timedelta64(5, "D"), target + 30),
                         fontsize=7, color="#7c3aed")
    ax4.set_xlabel("Date")
    ax4.set_ylabel("Cumulative GDD")
    ax4.set_title(f"Cumulative Growing Degree Days (base {BASE_TEMP}°C)", fontsize=11, fontweight="bold")
    ax4.legend(fontsize=8, loc="upper left")
    ax4.grid(True, alpha=0.2)

    for ax in axes:
        ax.set_xlim(gs_start_date, gs_end_date)
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=0, ha="center")

    fig.text(0.5, 0.01, "Growing Season (Apr 1 – Oct 31)", ha="center", fontsize=10, fontweight="bold")

    captions = generate_captions(events, ndvi_peak_doy=float(ndvi_doy[ndvi_peak_idx]),
                                 ndvi_peak_val=ndvi_peak_val,
                                 total_precip=precip.sum(), total_gdd=gdd.sum(), crop=crop)
    caption_text = " | ".join(captions)
    fig.text(0.5, -0.02, caption_text, ha="center", fontsize=7, color="#374151", wrap=True)

    plt.tight_layout(rect=[0, 0.04, 1, 0.95])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Dashboard saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Field-Year Storyline Dashboard Generator")
    parser.add_argument("--field", default=DEFAULT_FIELD, help=f"CDL field ID (default: {DEFAULT_FIELD})")
    parser.add_argument("--weather-field", default=DEFAULT_WEATHER_FIELD, help=f"Weather field ID (default: {DEFAULT_WEATHER_FIELD})")
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR, help=f"Year (default: {DEFAULT_YEAR})")
    parser.add_argument("--weather", default=str(SAMPLE_WEATHER), help="Weather CSV path")
    parser.add_argument("--cdl", default=str(SAMPLE_CDL), help="CDL CSV path")
    parser.add_argument("--ndvi-stats", default=str(SAMPLE_NDVI_STATS), help="NDVI stats CSV path")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    weather_path = Path(args.weather)
    cdl_path = Path(args.cdl)
    ndvi_path = Path(args.ndvi_stats)
    output_dir = Path(args.output_dir)

    for p in [weather_path, cdl_path, ndvi_path]:
        if not p.exists():
            print(f"Error: input not found at {p}", file=sys.stderr)
            sys.exit(1)

    crop = load_cdl(cdl_path, args.field, args.year)
    if crop is None:
        print(f"Error: field {args.field} not found in CDL for year {args.year}", file=sys.stderr)
        sys.exit(1)
    print(f"Field: {args.field}, Year: {args.year}, Crop: {crop}")

    weather = load_weather(weather_path, args.weather_field, args.year)
    if weather.empty:
        print(f"Error: no weather data for field {args.weather_field} year {args.year}", file=sys.stderr)
        sys.exit(1)
    print(f"Weather: {len(weather)} days loaded")

    anchor = load_ndvi_anchor(ndvi_path, args.field)
    if anchor:
        print(f"NDVI anchor: DOY {anchor[0]}, mean_ndvi = {anchor[1]:.2f}")
    else:
        print("NDVI anchor: not found, using uncalibrated phenology curve")

    doy_range = np.arange(GS_START, GS_END + 1)
    ndvi_vals = generate_ndvi_curve(anchor[0] if anchor else None, anchor[1] if anchor else None, doy_range)

    events = detect_events(weather)
    print(f"Events detected: {len(events)}")
    for ev in events:
        print(f"  DOY {ev['doy']}: {ev['desc']}")

    output_path = output_dir / f"field_year_storyline_{args.field}_{args.year}.png"
    plot_dashboard(weather, doy_range, ndvi_vals, events, crop, args.field, args.year, args.weather_field, output_path)

    print("\nSeason Captions:")
    total_precip = weather["PRECTOTCORR"].sum()
    gdd = compute_gdd(weather["T2M_MAX"], weather["T2M_MIN"])
    total_gdd = gdd.sum()
    ndvi_peak_idx = np.argmax(ndvi_vals)
    captions = generate_captions(events, doy_range[ndvi_peak_idx], ndvi_vals[ndvi_peak_idx], total_precip, total_gdd, crop)
    for c in captions:
        print(f"  • {c}")


if __name__ == "__main__":
    main()

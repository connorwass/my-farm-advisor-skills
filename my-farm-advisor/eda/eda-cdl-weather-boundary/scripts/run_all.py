"""
Field-boundary, weather, and CDL EDA for IA, IL, and NE growers.

Generates 7 output files under:
    {DATA_PIPELINE_DATA_ROOT}/data-pipeline/eda/eda-cdl-weather-boundary/output/

Boundaries:
    field_boundary_viz.png        — 2-panel: size histogram + compactness violin
    field_boundary_comparison.csv — ANOVA + per-grower summary stats

Weather:
    weather_viz.png               — 2-panel: monthly T2M + monthly precip
    weather_correlation.csv       — Pearson r T2M vs precip per grower

CDL / Cropland:
    cdl_viz.png                   — 2-panel: composition stacked + rotation frequency
    cdl_diversity_comparison.csv  — Shannon diversity by grower x year

Map:
    geospatial_overview.png       — 30 field boundaries colored by grower
"""

import json
import os
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import shapely
from scipy.stats import f_oneway, pearsonr
from statsmodels.stats.multicomp import pairwise_tukeyhsd

sns.set_theme(style="whitegrid", font_scale=0.9)

DATA_ROOT = Path(os.environ.get(
    "DATA_PIPELINE_DATA_ROOT",
    "/home/coder/my-farm-advisor-runtime",
))
GROWER_DIR = DATA_ROOT / "data-pipeline" / "growers"
OUT_DIR = DATA_ROOT / "data-pipeline" / "eda" / "eda-cdl-weather-boundary" / "output"

GROWERS = {
    "ia-grower": {"farm": "ia-grower-iowa", "label": "IA", "color": "#4C72B0"},
    "il-grower": {"farm": "il-grower-illinois", "label": "IL", "color": "#55A868"},
    "ne-grower": {"farm": "ne-grower-nebraska", "label": "NE", "color": "#DD8452"},
}

GROWING_SEASON_MONTHS = list(range(4, 11))  # Apr–Oct

CROP_KEEP = {"Corn", "Soybeans"}


def _grower_path(grower_slug):
    info = GROWERS[grower_slug]
    return GROWER_DIR / grower_slug / "farms" / info["farm"]


def _table_path(grower_slug, table_name):
    return _grower_path(grower_slug) / "derived" / "tables" / table_name


def _slug_underscore(s):
    return s.replace("-", "_")


# ---------------------------------------------------------------------------
# 1. Load helpers
# ---------------------------------------------------------------------------

def load_boundaries():
    dfs = []
    for slug, info in GROWERS.items():
        fp = _grower_path(slug) / "boundary" / "field_boundaries.geojson"
        gdf = gpd.read_file(fp)
        gdf["grower"] = info["label"]
        gdf["grower_slug"] = slug
        dfs.append(gdf)
    combined = pd.concat(dfs, ignore_index=True)
    if combined.crs is None:
        combined.set_crs("EPSG:4326", inplace=True)
    projected = combined.to_crs("EPSG:5070")
    projected["area_acres_calc"] = projected.geometry.area * 0.000247105
    projected["perimeter_m"] = projected.geometry.length
    projected["area_sq_m"] = projected.geometry.area
    projected["compactness"] = projected["perimeter_m"] ** 2 / (
        4 * np.pi * projected["area_sq_m"]
    )
    if "area_acres" in projected.columns:
        projected["area_acres_calc"] = projected["area_acres"]
    return combined, projected


def load_weather():
    dfs = []
    for slug, info in GROWERS.items():
        prefix = _slug_underscore(info["farm"])
        fname = f"{prefix}_weather_2021_2025.csv"
        fp = _table_path(slug, fname)
        df = pd.read_csv(fp, parse_dates=["date"])
        df["grower"] = info["label"]
        df["month"] = df["date"].dt.month
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def load_cdl_composition():
    dfs = []
    for slug, info in GROWERS.items():
        prefix = _slug_underscore(info["farm"])
        fname = f"{prefix}_cdl_2021_2025_full_composition.csv"
        fp = _table_path(slug, fname)
        df = pd.read_csv(fp)
        df["grower"] = info["label"]
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def load_crop_rotation():
    dfs = []
    for slug, info in GROWERS.items():
        prefix = _slug_underscore(info["farm"])
        fname = f"{prefix}_crop_rotation.csv"
        fp = _table_path(slug, fname)
        df = pd.read_csv(fp)
        df["grower"] = info["label"]
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


# ---------------------------------------------------------------------------
# 2. Field Boundary Analysis
# ---------------------------------------------------------------------------

def boundary_analysis(combined_gdf, projected_gdf):
    print("  [boundary] computing stats and generating figures ...")

    stats_rows = []
    for label, grp in projected_gdf.groupby("grower"):
        sizes = grp["area_acres_calc"]
        stats_rows.append({
            "grower": label,
            "count": len(grp),
            "mean_acres": round(sizes.mean(), 1),
            "std_acres": round(sizes.std(), 1),
            "min_acres": round(sizes.min(), 1),
            "max_acres": round(sizes.max(), 1),
            "mean_compactness": round(grp["compactness"].mean(), 2),
        })
    stats_df = pd.DataFrame(stats_rows)

    groups = [g["area_acres_calc"].values for _, g in projected_gdf.groupby("grower")]
    if len(groups) >= 2:
        f_stat, p_val = f_oneway(*groups)
    else:
        f_stat, p_val = None, None

    try:
        tukey = pairwise_tukeyhsd(
            projected_gdf["area_acres_calc"],
            projected_gdf["grower"],
            alpha=0.05,
        )
        tukey_df = pd.DataFrame(
            data=tukey.summary().data[1:],
            columns=tukey.summary().data[0],
        )
    except Exception:
        tukey_df = pd.DataFrame({"note": ["Tukey HSD failed"]})

    stats_df["anova_f"] = f_stat
    stats_df["anova_p"] = p_val
    stats_df.to_csv(OUT_DIR / "field_boundary_comparison.csv", index=False)
    tukey_df.to_csv(OUT_DIR / "field_boundary_tukey.csv", index=False)
    print(f"    wrote field_boundary_comparison.csv, field_boundary_tukey.csv")

    # -- Viz 1a: size histogram --
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    colors = [v["color"] for v in GROWERS.values()]
    labels = [v["label"] for v in GROWERS.values()]
    for (label, grp), c in zip(projected_gdf.groupby("grower"), colors):
        sizes = grp["area_acres_calc"]
        ax1.hist(sizes, bins=12, alpha=0.5, label=label, color=c, density=True)
        kde_x = np.linspace(sizes.min(), sizes.max(), 200)
        kde_y = _kde(sizes.values, kde_x)
        ax1.plot(kde_x, kde_y, color=c, linewidth=2)
    ax1.set_xlabel("Field Area (acres)")
    ax1.set_ylabel("Density")
    ax1.set_title("Field Size Distribution by Grower")
    ax1.legend()

    # -- Viz 1b: compactness violin --
    order = [v["label"] for v in GROWERS.values()]
    sns.violinplot(
        data=projected_gdf,
        x="grower",
        y="compactness",
        order=order,
        hue="grower",
        palette=[v["color"] for v in GROWERS.values()],
        ax=ax2,
        inner="quartile",
        legend=False,
    )
    ax2.set_xlabel("Grower")
    ax2.set_ylabel("Compactness (P² / 4πA)")
    ax2.set_title("Field Shape Compactness by Grower")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "field_boundary_viz.png", dpi=150)
    plt.close(fig)
    print("    wrote field_boundary_viz.png")

    return projected_gdf


def _kde(values, x_grid):
    n = len(values)
    if n == 0:
        return np.zeros_like(x_grid)
    h = 1.06 * np.std(values) * n ** (-0.2)
    if h == 0:
        h = 1.0
    out = np.zeros_like(x_grid)
    for v in values:
        out += np.exp(-0.5 * ((x_grid - v) / h) ** 2) / (h * np.sqrt(2 * np.pi))
    return out / n


# ---------------------------------------------------------------------------
# 3. Weather Analysis
# ---------------------------------------------------------------------------

def weather_analysis(weather_df):
    print("  [weather] filtering growing season, aggregating ...")

    gs = weather_df[weather_df["month"].isin(GROWING_SEASON_MONTHS)].copy()

    monthly = (
        gs.groupby(["grower", "field_id", "month"])
        .agg(avg_temp=("T2M", "mean"), total_precip=("PRECTOTCORR", "sum"))
        .reset_index()
    )

    grower_monthly = (
        monthly.groupby(["grower", "month"])
        .agg(
            temp_mean=("avg_temp", "mean"),
            temp_std=("avg_temp", "std"),
            precip_mean=("total_precip", "mean"),
            precip_std=("total_precip", "std"),
        )
        .reset_index()
    )

    field_seasonal = (
        monthly.groupby(["grower", "field_id"])
        .agg(season_temp=("avg_temp", "mean"), season_precip=("total_precip", "sum"))
        .reset_index()
    )

    # -- Correlation --
    corr_rows = []
    for label, grp in field_seasonal.groupby("grower"):
        r_val, p_val = pearsonr(grp["season_temp"], grp["season_precip"])
        corr_rows.append({
            "grower": label,
            "pearson_r": round(r_val, 4),
            "p_value": round(p_val, 4),
            "n_fields": len(grp),
        })
    corr_df = pd.DataFrame(corr_rows)

    all_r, all_p = pearsonr(
        field_seasonal["season_temp"], field_seasonal["season_precip"]
    )
    corr_df.loc[len(corr_df)] = {
        "grower": "ALL",
        "pearson_r": round(all_r, 4),
        "p_value": round(all_p, 4),
        "n_fields": len(field_seasonal),
    }
    corr_df.to_csv(OUT_DIR / "weather_correlation.csv", index=False)
    print("    wrote weather_correlation.csv")

    # -- Viz 2a: monthly T2M --
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    order_labels = [v["label"] for v in GROWERS.values()]
    colors = [v["color"] for v in GROWERS.values()]

    for label, c in zip(order_labels, colors):
        grp = grower_monthly[grower_monthly["grower"] == label].sort_values("month")
        ax1.plot(
            grp["month"], grp["temp_mean"], "o-", color=c, label=label, linewidth=2
        )
        ax1.fill_between(
            grp["month"],
            grp["temp_mean"] - grp["temp_std"],
            grp["temp_mean"] + grp["temp_std"],
            alpha=0.15,
            color=c,
        )
    ax1.set_xticks(list(range(4, 11)))
    ax1.set_xticklabels(["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"])
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Mean T2M (°C)")
    ax1.set_title("Growing-Season Temperature (Apr–Oct)")
    ax1.legend()

    # -- Viz 2b: monthly precip violin --
    plot_data = monthly.copy()
    plot_data["month_label"] = plot_data["month"].map({
        4: "Apr", 5: "May", 6: "Jun", 7: "Jul",
        8: "Aug", 9: "Sep", 10: "Oct",
    })
    sns.violinplot(
        data=plot_data,
        x="month_label",
        y="total_precip",
        hue="grower",
        palette={v["label"]: v["color"] for v in GROWERS.values()},
        ax=ax2,
        inner="quartile",
        density_norm="width",
        order=["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"],
    )
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Total Precipitation (mm)")
    ax2.set_title("Monthly Precipitation by Grower")
    ax2.legend(title="Grower")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "weather_viz.png", dpi=150)
    plt.close(fig)
    print("    wrote weather_viz.png")

    return field_seasonal


# ---------------------------------------------------------------------------
# 4. CDL Analysis
# ---------------------------------------------------------------------------

def cdl_analysis(cdl_df, rotation_df):
    print("  [cdl] collapsing crop categories, computing diversity ...")

    cdl_df["crop_simple"] = cdl_df["crop_name"].where(
        cdl_df["crop_name"].isin(CROP_KEEP), "Other"
    )

    # -- Composition per grower (all years aggregated) --
    comp = (
        cdl_df.groupby(["grower", "crop_simple"])["pct"]
        .sum()
        .reset_index()
    )
    comp_total = comp.groupby("grower")["pct"].transform("sum")
    comp["pct"] = comp["pct"] / comp_total * 100

    # -- Shannon diversity per grower x year --
    diversity_rows = []
    for (grower, year), grp in cdl_df.groupby(["grower", "year"]):
        props = grp.groupby("crop_simple")["pct"].sum().values
        props = props / props.sum()
        h = -sum(p * np.log(p) for p in props if p > 0)
        diversity_rows.append({"grower": grower, "year": year, "shannon_h": round(h, 4)})
    div_df = pd.DataFrame(diversity_rows)
    div_df.to_csv(OUT_DIR / "cdl_diversity_comparison.csv", index=False)
    print("    wrote cdl_diversity_comparison.csv")

    # -- Viz 3a: crop composition stacked bar --
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    order_labels = [v["label"] for v in GROWERS.values()]
    category_order = ["Corn", "Soybeans", "Other"]
    palette_comp = {"Corn": "#FFB400", "Soybeans": "#2E8B57", "Other": "#888888"}

    bar_data = comp.pivot_table(
        index="grower", columns="crop_simple", values="pct", fill_value=0
    )
    for cat in category_order:
        if cat not in bar_data.columns:
            bar_data[cat] = 0.0
    bar_data = bar_data[category_order]
    bar_data = bar_data.reindex(order_labels)

    bottom = np.zeros(len(bar_data))
    for cat in category_order:
        vals = bar_data[cat].values
        ax1.barh(
            order_labels,
            vals,
            left=bottom,
            label=cat,
            color=palette_comp[cat],
            height=0.5,
        )
        bottom += vals
    ax1.set_xlabel("Percent of Total Crop Area")
    ax1.set_title("Crop Composition by Grower (2021–2025 Combined)")
    ax1.legend(loc="lower right")

    # -- Viz 3b: rotation pattern frequency --
    pattern_counts = {}
    for _, row in rotation_df.iterrows():
        raw = row["rotation_patterns"]
        grower = row["grower"]
        if isinstance(raw, str):
            for part in raw.split(";"):
                part = part.strip()
                if part:
                    key = (grower, part)
                    pattern_counts[key] = pattern_counts.get(key, 0) + 1

    rot_df = pd.DataFrame(
        [(g, p, c) for (g, p), c in pattern_counts.items()],
        columns=["grower", "pattern", "count"],
    )

    top_patterns = (
        rot_df.groupby("pattern")["count"]
        .sum()
        .sort_values(ascending=False)
        .head(6)
        .index
    )
    rot_df = rot_df[rot_df["pattern"].isin(top_patterns)]

    sns.barplot(
        data=rot_df,
        y="pattern",
        x="count",
        hue="grower",
        palette={v["label"]: v["color"] for v in GROWERS.values()},
        ax=ax2,
    )
    ax2.set_xlabel("Number of Fields")
    ax2.set_ylabel("Rotation Pattern")
    ax2.set_title("Most Common Crop Rotation Patterns")
    ax2.legend(title="Grower")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "cdl_viz.png", dpi=150)
    plt.close(fig)
    print("    wrote cdl_viz.png")

    return div_df


# ---------------------------------------------------------------------------
# 5. Geospatial Map
# ---------------------------------------------------------------------------

def geospatial_map(combined_gdf):
    print("  [map] rendering 30 field boundaries ...")

    fig, ax = plt.subplots(figsize=(10, 8))
    color_map = {v["label"]: v["color"] for v in GROWERS.values()}
    alpha_map = {"IA": 0.6, "IL": 0.6, "NE": 0.6}

    for label in ["IA", "IL", "NE"]:
        subset = combined_gdf[combined_gdf["grower"] == label]
        subset.plot(
            ax=ax,
            color=color_map[label],
            alpha=alpha_map[label],
            edgecolor="black",
            linewidth=0.4,
            label=f"{label} ({len(subset)} fields)",
        )

    patches = [
        mpatches.Patch(
            color=color_map[l],
            label=f"{l} ({len(combined_gdf[combined_gdf['grower'] == l])} fields)",
        )
        for l in ["IA", "IL", "NE"]
    ]
    ax.legend(handles=patches, loc="lower right", fontsize=9)

    ax.set_title("Field Boundaries — IA, IL, NE Growers (30 fields)", fontsize=12)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.ticklabel_format(useOffset=False, style="plain")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "geospatial_overview.png", dpi=150)
    plt.close(fig)
    print("    wrote geospatial_overview.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("eda-cdl-weather-boundary — run_all.py")
    print(f"Output: {OUT_DIR}")
    print("=" * 60)

    print("\n1. Loading boundary data ...")
    combined_gdf, projected_gdf = load_boundaries()
    print(f"   {len(projected_gdf)} fields loaded across 3 growers")

    print("\n2. Loading weather data ...")
    weather_df = load_weather()
    print(f"   {len(weather_df):,} daily records across {weather_df['field_id'].nunique()} fields")

    print("\n3. Loading CDL composition data ...")
    cdl_df = load_cdl_composition()
    print(f"   {len(cdl_df):,} crop-class records")

    print("\n4. Loading crop rotation data ...")
    rotation_df = load_crop_rotation()
    print(f"   {len(rotation_df)} fields with rotation history")

    print("\n--- Field Boundary Analysis ---")
    boundary_analysis(combined_gdf, projected_gdf)

    print("\n--- Weather Analysis ---")
    weather_analysis(weather_df)

    print("\n--- CDL Analysis ---")
    cdl_analysis(cdl_df, rotation_df)

    print("\n--- Geospatial Map ---")
    geospatial_map(combined_gdf)

    print("\n--- Complete ---")
    print(f"Output directory: {OUT_DIR}")
    for f in sorted(OUT_DIR.iterdir()):
        sz = f.stat().st_size
        print(f"  {f.name:45s} {sz:>8,} bytes")


if __name__ == "__main__":
    main()

"""
Extract per-date mean NDVI from Landsat scene rasters for a production field,
using its boundary GeoJSON. Outputs a CSV compatible with
generate_storyline_dashboard.py --ndvi-stats.

Usage:
    python extract_production_ndvi.py \\
        --field-dir /path/to/fields/osm-1360394834 \\
        --year 2024 \\
        --output /path/to/ndvi_production.csv
"""

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask


def extract_field_mean_ndvi(ndvi_tif_path: Path, field_geojson_path: Path) -> float | None:
    boundary = gpd.read_file(field_geojson_path)
    if boundary.crs is None:
        boundary.set_crs("EPSG:4326", inplace=True)

    with rasterio.open(ndvi_tif_path) as src:
        boundary_proj = boundary.to_crs(src.crs)
        geoms = [boundary_proj.geometry.iloc[0]]
        try:
            out_image, _ = mask(src, geoms, crop=True, nodata=src.nodata)
        except Exception:
            return None

    data = out_image[0]
    nodata = src.nodata if src.nodata is not None else -9999
    valid = data[(data != nodata) & ~np.isnan(data)]
    if len(valid) == 0:
        return None
    return float(valid.mean())


def main():
    parser = argparse.ArgumentParser(description="Extract per-date mean NDVI from Landsat scenes")
    parser.add_argument("--field-dir", required=True, help="Path to field directory (e.g., .../fields/osm-1360394834)")
    parser.add_argument("--year", type=int, required=True, help="Year to process")
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument("--source", default="Landsat", help="Satellite source label")
    args = parser.parse_args()

    field_dir = Path(args.field_dir)
    boundary_path = field_dir / "boundary" / "field_boundary.geojson"
    landsat_dir = field_dir / "satellite" / "landsat" / str(args.year)

    if not boundary_path.exists():
        print(f"Error: boundary not found at {boundary_path}", file=sys.stderr)
        sys.exit(1)
    if not landsat_dir.exists():
        print(f"Error: landsat dir not found at {landsat_dir}", file=sys.stderr)
        sys.exit(1)

    rows = []
    scenes = sorted(landsat_dir.iterdir())
    for scene_dir in scenes:
        if not scene_dir.is_dir():
            continue
        ndvi_path = scene_dir / f"{scene_dir.name}_ndvi.tif"
        if not ndvi_path.exists():
            continue

        date_str = scene_dir.name.split("_")[-1]
        mean_ndvi = extract_field_mean_ndvi(ndvi_path, boundary_path)
        if mean_ndvi is not None:
            rows.append({
                "field_id": field_dir.name,
                "mean_ndvi": round(mean_ndvi, 4),
                "scene_date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}",
                "source": args.source,
                "pixel_count": 0,
            })
            print(f"  {date_str}: mean_ndvi = {mean_ndvi:.4f}")

    if not rows:
        print("Error: no NDVI data extracted", file=sys.stderr)
        sys.exit(1)

    df = pd.DataFrame(rows)
    df.to_csv(args.output, index=False)
    print(f"Wrote {len(rows)} NDVI records to {args.output}")


if __name__ == "__main__":
    main()

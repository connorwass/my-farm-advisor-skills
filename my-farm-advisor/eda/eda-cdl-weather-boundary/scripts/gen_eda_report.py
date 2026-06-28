"""
Generate the complete eda_report.html with embedded Leaflet maps
replacing the static geospatial PNG.
"""
import json, os
from pathlib import Path

DATA_ROOT = Path(os.environ.get(
    "DATA_PIPELINE_DATA_ROOT",
    "/home/coder/my-farm-advisor-runtime",
))
OUT_DIR = DATA_ROOT / "data-pipeline" / "eda" / "eda-cdl-weather-boundary" / "output"

GROWERS = [
    {"slug": "ia-grower", "farm": "ia-grower-iowa",  "label": "IA", "color": "#4C72B0"},
    {"slug": "il-grower", "farm": "il-grower-illinois", "label": "IL", "color": "#55A868"},
    {"slug": "ne-grower", "farm": "ne-grower-nebraska", "label": "NE", "color": "#DD8452"},
]

GROWER_META = {
    "IA": {
        "title": "Iowa Grower",
        "desc": "Central Corn Belt — 10 fields across Kossuth and Decatur counties. Largest mean field size (134.6 ac). Classic corn-soy rotation.",
        "center": [42.8, -93.6], "zoom": 9,
    },
    "IL": {
        "title": "Illinois Grower",
        "desc": "Southern Corn Belt — 10 fields in Iroquois County. Most fragmented (mean 87.5 ac, range 3.2-259.5 ac). Warmest/wettest of the three.",
        "center": [40.7, -87.7], "zoom": 9,
    },
    "NE": {
        "title": "Nebraska Grower",
        "desc": "Northern edge of Corn Belt — 10 fields in Hamilton County. Widest size variability (SD 85.5 ac). Coolest/driest; center-pivot irrigation signatures.",
        "center": [40.8, -98.0], "zoom": 9,
    },
}

def load_geojson(grower):
    fp = DATA_ROOT / "data-pipeline" / "growers" / grower["slug"] / "farms" / grower["farm"] / "boundary" / "field_boundaries.geojson"
    with open(fp) as f:
        return json.load(f)

def load_csv(name):
    fp = OUT_DIR / name
    if not fp.exists():
        return None
    with open(fp) as f:
        return f.read()

def build():
    fb_csv = load_csv("field_boundary_comparison.csv")
    wc_csv = load_csv("weather_correlation.csv")
    div_csv = load_csv("cdl_diversity_comparison.csv")

    def img_b64(name):
        fp = OUT_DIR / name
        if not fp.exists():
            return ""
        import base64
        with open(fp, "rb") as f:
            return base64.b64encode(f.read()).decode()

    fb_img = img_b64("field_boundary_viz.png")
    wv_img = img_b64("weather_viz.png")
    cdl_img = img_b64("cdl_viz.png")

    def gj_script_block(g, var_name):
        gj = load_geojson(g)
        return f"const {var_name} = {json.dumps(gj, separators=(',',':'))};"

    def map_script_block(g, var_name, map_id):
        lbl = g["label"]
        meta = GROWER_META[lbl]
        clat, clng = meta["center"]
        zoom = meta["zoom"]
        return f"""
    (function() {{
      const map = L.map('{map_id}', {{ scrollWheelZoom: true }}).setView([{clat}, {clng}], {zoom});
      L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
        maxZoom: 18,
      }}).addTo(map);
      const geoData = {var_name};
      function onEachFeature(feature, layer) {{
        if (feature.properties) {{
          const props = feature.properties;
          let html = '<table style=\"font-size:0.85rem;\">';
          for (const k in props) {{
            const v = typeof props[k] === 'number' ? props[k].toFixed(2) : props[k];
            html += '<tr><td><strong>' + k + '</strong></td><td>' + v + '</td></tr>';
          }}
          html += '</table>';
          layer.bindPopup(html);
          layer.bindTooltip(props.field_id || 'Field', {{ sticky: true }});
        }}
      }}
      const style = {{
        color: '{g["color"]}',
        weight: 2,
        fillColor: '{g["color"]}',
        fillOpacity: 0.3,
      }};
      const geojsonLayer = L.geoJSON(geoData, {{ style, onEachFeature }}).addTo(map);
      map.fitBounds(geojsonLayer.getBounds().pad(0.05));
    }})();
    """

    fb_rows = ""
    if fb_csv:
        lines = fb_csv.strip().split("\n")
        headers = lines[0].split(",")
        for line in lines[1:]:
            vals = line.split(",")
            fb_rows += "        <tr>" + "".join(f"<td>{v}</td>" for v in vals) + "</tr>\n"

    wc_rows = ""
    if wc_csv:
        lines = wc_csv.strip().split("\n")
        for line in lines[1:]:
            vals = line.split(",")
            wc_rows += "        <tr>" + "".join(f"<td>{v}</td>" for v in vals) + "</tr>\n"

    div_rows = ""
    if div_csv:
        lines = div_csv.strip().split("\n")
        for line in lines[1:]:
            vals = line.split(",")
            div_rows += "        <tr>" + "".join(f"<td>{v}</td>" for v in vals) + "</tr>\n"

    ia_gj = gj_script_block(GROWERS[0], "iaGeoData")
    il_gj = gj_script_block(GROWERS[1], "ilGeoData")
    ne_gj = gj_script_block(GROWERS[2], "neGeoData")

    ia_map = map_script_block(GROWERS[0], "iaGeoData", "map-ia")
    il_map = map_script_block(GROWERS[1], "ilGeoData", "map-il")
    ne_map = map_script_block(GROWERS[2], "neGeoData", "map-ne")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>My Farm Advisor — EDA Report: IA, IL, NE Growers</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #1a1a2e; padding: 2rem; }}
  .container {{ max-width: 1100px; margin: 0 auto; }}
  h1 {{ font-size: 1.8rem; margin-bottom: 0.25rem; }}
  .subtitle {{ color: #666; margin-bottom: 2rem; font-size: 0.95rem; }}
  .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
  .card {{ background: #fff; border-radius: 10px; padding: 1.25rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
  .card .num {{ font-size: 1.8rem; font-weight: 700; color: #2d5a87; }}
  .card .label {{ font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
  .section {{ background: #fff; border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
  .section h2 {{ font-size: 1.2rem; margin-bottom: 1rem; color: #2d5a87; border-bottom: 2px solid #eef2f7; padding-bottom: 0.5rem; }}
  .section h3 {{ font-size: 1rem; margin-bottom: 0.75rem; color: #444; }}
  img {{ max-width: 100%; height: auto; border-radius: 6px; border: 1px solid #e0e0e0; margin: 1rem 0; }}
  table {{ width: 100%; border-collapse: collapse; margin: 0.75rem 0; font-size: 0.9rem; }}
  th, td {{ padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #eef2f7; }}
  th {{ background: #f8f9fc; font-weight: 600; color: #555; }}
  .highlight {{ background: #fffbe6; }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
  .chip {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }}
  .chip-ia {{ background: #dce6f2; color: #2d5a87; }}
  .chip-il {{ background: #d5f0db; color: #2d7a4a; }}
  .chip-ne {{ background: #f5e6d3; color: #a8642a; }}
  .map-section {{ margin-bottom: 1.25rem; }}
  .map-section h3 {{ font-size: 1rem; margin-bottom: 0.25rem; color: #2d5a87; }}
  .map-section .desc {{ font-size: 0.85rem; color: #666; margin-bottom: 0.5rem; }}
  .map-wrap {{ height: 420px; border-radius: 6px; border: 1px solid #e0e0e0; }}
  .legend {{ display: flex; gap: 1.5rem; margin-top: 0.75rem; font-size: 0.85rem; color: #444; flex-wrap: wrap; }}
  .legend-item {{ display: flex; align-items: center; gap: 0.4rem; }}
  .legend-swatch {{ width: 14px; height: 14px; border-radius: 3px; border: 1px solid rgba(0,0,0,0.15); }}
  .footer {{ text-align: center; color: #aaa; font-size: 0.8rem; margin-top: 2rem; }}
  @media (max-width: 700px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="container">

<h1>Cross-Grower EDA Report</h1>
<p class="subtitle">Field boundaries, weather, and CDL/cropland analysis for IA, IL, and NE growers</p>

<div class="summary-cards">
  <div class="card"><div class="num">30</div><div class="label">Fields Analyzed</div></div>
  <div class="card"><div class="num">3</div><div class="label">Growers (IA &middot; IL &middot; NE)</div></div>
  <div class="card"><div class="num">41,998</div><div class="label">Daily Weather Records</div></div>
  <div class="card"><div class="num">2021&ndash;2025</div><div class="label">Time Span</div></div>
</div>

<div class="section">
  <h2>1. Field Boundary Analysis</h2>
  <div class="two-col">
    <div>
      <table>
        <tr><th>Metric</th><th>IA</th><th>IL</th><th>NE</th></tr>
{fb_rows}      </table>
      <p style="margin-top:0.5rem;font-size:0.85rem;color:#666;">
        ANOVA: F=1.95, p=0.162 (not significant)<br>
        Tukey HSD: No pairwise differences significant at &alpha;=0.05
      </p>
    </div>
    <div>
      <p style="font-size:0.85rem;color:#666;margin-bottom:0.25rem;">
        <span class="chip chip-ia">IA</span> largest mean field size (134.6 ac) &mdash; consistent with central Corn Belt prairie.
        <span class="chip chip-il">IL</span> has the smallest mean (87.5) but highest max (259.5), suggesting a mix of small fragmented parcels and a few large fields.
        <span class="chip chip-ne">NE</span> shows the widest variability (SD 85.5) with compactness near 1.6 &mdash; center-pivot circles visible in compactness metric.
      </p>
    </div>
  </div>
  <img src="data:image/png;base64,{fb_img}" alt="Field boundary viz">
</div>

<div class="section">
  <h2>2. Weather Analysis</h2>
  <div class="two-col">
    <div>
      <h3>Temperature&ndash;Precipitation Correlation</h3>
      <table>
        <tr><th>Grower</th><th>Pearson r</th><th>p-value</th><th>N Fields</th></tr>
{wc_rows}      </table>
      <p style="margin-top:0.5rem;font-size:0.85rem;color:#666;">
        Strong negative correlation across all growers: warmer fields receive less precipitation during the growing season (Apr&ndash;Oct).
        The effect is most pronounced within IA and NE (r = -1.0), though IA only has 3 fields.
      </p>
    </div>
    <div>
      <p style="font-size:0.85rem;color:#666;">
        <strong>Temperature gradient:</strong> NE is coolest (northernmost), IA moderate, IL warmest &mdash; consistent with the ~1&deg;C per degree latitude gradient expected across the US Corn Belt.
        <br><br>
        <strong>Precipitation:</strong> IL shows the highest summer precipitation with wider field-to-field variability, suggesting microclimate and drainage differences.
        NE stands out as the driest of the three.
      </p>
    </div>
  </div>
  <img src="data:image/png;base64,{wv_img}" alt="Weather viz">
</div>

<div class="section">
  <h2>3. CDL / Cropland Analysis</h2>
  <div class="two-col">
    <div>
      <h3>Shannon Diversity by Grower &times; Year</h3>
      <table>
        <tr><th>Year</th><th><span class="chip chip-ia">IA</span></th><th><span class="chip chip-il">IL</span></th><th><span class="chip chip-ne">NE</span></th></tr>
{div_rows}      </table>
      <p style="margin-top:0.5rem;font-size:0.85rem;color:#666;">
        Diversity is low across the board (all &lt;1.0), confirming overwhelmingly corn-soy systems.
        IA has the least diverse rotation but has been increasing since 2021.
        NE shows a notable jump to 0.93 in 2025.
      </p>
    </div>
    <div>
      <p style="font-size:0.85rem;color:#666;">
        <strong>Composition:</strong> All three growers are dominated by corn and soybeans with minimal "Other" categories.
        <br><br>
        <strong>Rotation patterns:</strong> Classic 2-year corn-soy rotation is the dominant pattern.
        Continuous corn signals higher-intensity management where present.
        <br><br>
        <strong>Interpretation:</strong> These are archetypal Corn Belt row-crop operations. Low and stable Shannon diversity across 2021&ndash;2025 indicates consistent management with little exploratory or specialty crop production.
      </p>
    </div>
  </div>
  <img src="data:image/png;base64,{cdl_img}" alt="CDL viz">
</div>

<div class="section">
  <h2>4. Geospatial Overview &mdash; Interactive Field Boundary Maps</h2>
  <p style="font-size:0.85rem;color:#666;margin-bottom:0.75rem;">
    One interactive Leaflet map per grower. Pan, zoom, and click any field for a popup with its properties (field ID, source, crop name, county, area).
    The three growers span a north-south transect of the US Corn Belt:
    <span class="chip chip-ne">NE</span> (northern, cooler/drier),
    <span class="chip chip-ia">IA</span> (central, large fields),
    <span class="chip chip-il">IL</span> (southern, warmer/wetter, more fragmented).
  </p>
  <div class="legend">
    <span class="legend-item"><span class="legend-swatch" style="background:#4C72B0"></span> IA &mdash; Iowa (10 fields)</span>
    <span class="legend-item"><span class="legend-swatch" style="background:#55A868"></span> IL &mdash; Illinois (10 fields)</span>
    <span class="legend-item"><span class="legend-swatch" style="background:#DD8452"></span> NE &mdash; Nebraska (10 fields)</span>
  </div>

  <div class="map-section">
    <h3 style="color:#4C72B0;">Iowa Grower (IA)</h3>
    <p class="desc">{GROWER_META['IA']['desc']}</p>
    <div class="map-wrap" id="map-ia"></div>
  </div>
  <div class="map-section">
    <h3 style="color:#55A868;">Illinois Grower (IL)</h3>
    <p class="desc">{GROWER_META['IL']['desc']}</p>
    <div class="map-wrap" id="map-il"></div>
  </div>
  <div class="map-section">
    <h3 style="color:#DD8452;">Nebraska Grower (NE)</h3>
    <p class="desc">{GROWER_META['NE']['desc']}</p>
    <div class="map-wrap" id="map-ne"></div>
  </div>
</div>

<div class="footer">
  My Farm Advisor &mdash; EDA Report &middot; Data pipeline runtime
</div>

</div>

<script>
{ia_gj}
{il_gj}
{ne_gj}
{ia_map}
{il_map}
{ne_map}
</script>

</body>
</html>"""

    out_path = OUT_DIR / "eda_report.html"
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Written: {out_path} ({os.path.getsize(out_path):,} bytes)")

if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build()

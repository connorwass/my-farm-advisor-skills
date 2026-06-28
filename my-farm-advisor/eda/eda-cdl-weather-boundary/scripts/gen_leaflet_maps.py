"""
Generate a Leaflet HTML page with one interactive map per grower (IA, IL, NE).
Reads the GeoJSON boundary files from the runtime data tree.
"""
import json, os, textwrap
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
        "center": [42.8, -93.6],
        "zoom": 9,
    },
    "IL": {
        "title": "Illinois Grower",
        "desc": "Southern Corn Belt — 10 fields in Iroquois County. Most fragmented (mean 87.5 ac, range 3.2–259.5 ac). Warmest/wettest of the three.",
        "center": [40.7, -87.7],
        "zoom": 9,
    },
    "NE": {
        "title": "Nebraska Grower",
        "desc": "Northern edge of Corn Belt — 10 fields in Hamilton County. Widest size variability (SD 85.5 ac). Coolest/driest; center-pivot irrigation signatures.",
        "center": [40.8, -98.0],
        "zoom": 9,
    },
}

def load_geojson(grower):
    fp = DATA_ROOT / "data-pipeline" / "growers" / grower["slug"] / "farms" / grower["farm"] / "boundary" / "field_boundaries.geojson"
    with open(fp) as f:
        return json.load(f)

def embed_geojson(gj):
    return json.dumps(gj, separators=(",", ":"))

def build_html():
    html_parts = []
    html_parts.append(textwrap.dedent("""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Field Boundary Maps — IA, IL, NE Growers</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #1a1a2e; padding: 1.5rem; }
      .container { max-width: 1200px; margin: 0 auto; }
      h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
      .subtitle { color: #666; margin-bottom: 1.5rem; font-size: 0.9rem; }
      .map-section { background: #fff; border-radius: 10px; padding: 1.25rem; margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
      .map-section h2 { font-size: 1.1rem; margin-bottom: 0.3rem; }
      .map-section .desc { font-size: 0.85rem; color: #666; margin-bottom: 0.75rem; }
      .map-wrap { height: 500px; border-radius: 6px; border: 1px solid #e0e0e0; }
      .legend { display: flex; gap: 1.5rem; margin-top: 0.75rem; font-size: 0.85rem; color: #444; flex-wrap: wrap; }
      .legend-item { display: flex; align-items: center; gap: 0.4rem; }
      .legend-swatch { width: 14px; height: 14px; border-radius: 3px; border: 1px solid rgba(0,0,0,0.15); }
      .footer { text-align: center; color: #aaa; font-size: 0.8rem; margin-top: 1.5rem; }
    </style>
    </head>
    <body>
    <div class="container">

    <h1>Field Boundary Maps — Interactive</h1>
    <p class="subtitle">One Leaflet map per grower with labeled field boundaries. Pan, zoom, and click fields for details.</p>

    <div class="legend">
      <span class="legend-item"><span class="legend-swatch" style="background:#4C72B0"></span> IA — Iowa (10 fields)</span>
      <span class="legend-item"><span class="legend-swatch" style="background:#55A868"></span> IL — Illinois (10 fields)</span>
      <span class="legend-item"><span class="legend-swatch" style="background:#DD8452"></span> NE — Nebraska (10 fields)</span>
    </div>
    """))

    for g in GROWERS:
        lbl = g["label"]
        meta = GROWER_META[lbl]
        gj = load_geojson(g)
        gj_str = embed_geojson(gj)
        center_lat, center_lng = meta["center"]
        zoom = meta["zoom"]

        html_parts.append(f"""
    <div class="map-section">
      <h2>{meta['title']} ({lbl})</h2>
      <p class="desc">{meta['desc']}</p>
      <div class="map-wrap" id="map-{lbl.lower()}"></div>
    </div>

    <script>
    (function() {{
      var map = L.map('map-{lbl.lower()}', {{ scrollWheelZoom: true }}).setView([{center_lat}, {center_lng}], {zoom});
      L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
        maxZoom: 18,
      }}).addTo(map);

      var geoData = {gj_str};

      function onEachFeature(feature, layer) {{
        if (feature.properties) {{
          var props = feature.properties;
          var html = '<table style="font-size:0.85rem;">';
          for (var k in props) {{
            var v = typeof props[k] === 'number' ? props[k].toFixed(2) : props[k];
            html += '<tr><td><strong>' + k + '</strong></td><td>' + v + '</td></tr>';
          }}
          html += '</table>';
          layer.bindPopup(html);
        }}
        layer.bindTooltip(props.field_id || 'Field', {{ sticky: true }});
      }}

      var style = {{
        color: '{g["color"]}',
        weight: 2,
        fillColor: '{g["color"]}',
        fillOpacity: 0.3,
      }};

      var geojsonLayer = L.geoJSON(geoData, {{
        style: style,
        onEachFeature: onEachFeature,
      }}).addTo(map);

      map.fitBounds(geojsonLayer.getBounds().pad(0.05));
    }})();
    </script>
    """)

    html_parts.append("""\
    <div class="footer">
      My Farm Advisor — Generated from field boundary GeoJSON &middot; Leaflet interactive maps
    </div>
    </div>
    </body>
    </html>
    """)

    return "\n".join(html_parts)

if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    html = build_html()
    out_path = OUT_DIR / "field_boundary_maps.html"
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Written: {out_path} ({os.path.getsize(out_path):,} bytes)")

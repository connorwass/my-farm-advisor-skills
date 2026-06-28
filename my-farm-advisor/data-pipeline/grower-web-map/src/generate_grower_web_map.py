#!/usr/bin/env python3
# pyright: reportMissingImports=false, reportAttributeAccessIssue=false, reportGeneralTypeIssues=false
"""Generate a grower-level interactive web map with field boundaries using Leaflet.
Supports single-grower or all-growers view with a grower filter dropdown."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent.parent / "src" / "scripts" / "lib"
sys.path.insert(0, str(_LIB))

from runtime_paths import resolve_runtime_paths, RuntimePathError

try:
    _RUNTIME_PATHS = resolve_runtime_paths()
except RuntimePathError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

_REPO = _RUNTIME_PATHS.runtime_base
_GROWERS_ROOT = _REPO / "growers"


def _collect_field_features(grower_slug: str) -> tuple[list[dict], str]:
    gdir = _GROWERS_ROOT / grower_slug
    if not gdir.is_dir():
        print(f"  WARNING: Grower directory not found: {gdir}")
        return [], grower_slug

    grower_info = json.loads((gdir / "grower.json").read_text())
    grower_name = grower_info.get("display_name", grower_slug)

    farms_dir = gdir / "farms"
    if not farms_dir.is_dir():
        return [], grower_name

    all_features = []
    for farm_dir_entry in sorted(farms_dir.iterdir()):
        if not farm_dir_entry.is_dir():
            continue
        farm_info_path = farm_dir_entry / "farm.json"
        if not farm_info_path.exists():
            continue
        farm_info = json.loads(farm_info_path.read_text())
        farm_name = farm_info.get("display_name", farm_info.get("farm_slug", ""))
        farm_state = farm_info.get("state", "")

        boundaries_file = farm_dir_entry / "boundary" / "field_boundaries.geojson"
        if not boundaries_file.exists():
            continue
        fc = json.loads(boundaries_file.read_text())
        for feature in fc.get("features", []):
            props = feature["properties"]
            props["grower_slug"] = grower_slug
            props["grower_name"] = grower_name
            props["farm_slug"] = farm_info.get("farm_slug", "")
            props["farm_name"] = farm_name
            props["farm_state"] = farm_state
            all_features.append(feature)

    return all_features, grower_name


def _collect_all_field_features(
    grower_slugs: list[str] | None = None,
) -> dict[str, tuple[list[dict], str]]:
    result: dict[str, tuple[list[dict], str]] = {}
    if grower_slugs:
        slugs = grower_slugs
    else:
        slugs = sorted(
            d.name for d in _GROWERS_ROOT.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    for slug in slugs:
        features, name = _collect_field_features(slug)
        if features:
            result[slug] = (features, name)

    return result


def _generate_html(
    all_grower_data: dict[str, tuple[list[dict], str]],
) -> str:
    total_features = sum(len(feats) for feats, _ in all_grower_data.values())
    total_growers = len(all_grower_data)

    grower_palette = [
        "#22c55e", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6",
        "#ec4899", "#14b8a6", "#f97316", "#06b6d4", "#84cc16",
        "#d946ef", "#eab308", "#6366f1", "#0ea5e9", "#a3e635",
    ]

    grower_info = []
    for i, (slug, (features, name)) in enumerate(sorted(all_grower_data.items())):
        color = grower_palette[i % len(grower_palette)]
        grower_info.append({
            "slug": slug,
            "name": name,
            "color": color,
            "count": len(features),
        })

    grower_index_map = {gi["slug"]: idx for idx, gi in enumerate(grower_info)}

    all_features = []
    for slug, (features, _) in sorted(all_grower_data.items()):
        g_idx = grower_index_map[slug]
        for feat in features:
            feat["_grower_index"] = g_idx
            all_features.append(feat)

    fields_json = json.dumps(all_features)
    grower_info_json = json.dumps(grower_info)

    grower_options = ""
    for gi in grower_info:
        grower_options += (
            f"<option value='{gi['slug']}'>{gi['name']} ({gi['count']})</option>\n"
        )

    field_rows = ""
    field_options = ""
    for i, feat in enumerate(all_features):
        p = feat["properties"]
        fid = p.get("field_id", f"field-{i}")
        acres = p.get("area_acres", 0)
        farm_name = p.get("farm_name", "")
        grower_name = p.get("grower_name", "")
        grower_slug = p.get("grower_slug", "")
        field_rows += (
            f"<tr class='field-row' data-index='{i}' data-grower='{grower_slug}'>"
            f"<td>{grower_name}</td>"
            f"<td>{fid}</td>"
            f"<td>{farm_name}</td>"
            f"<td>{acres:.1f} ac</td>"
            f"</tr>\n"
        )
        field_options += (
            f"<option value='{i}' data-grower='{grower_slug}'>"
            f"{fid} — {grower_name} ({farm_name})</option>\n"
        )

    header_title = "All Growers" if total_growers > 1 else grower_info[0]["name"]
    header_subtitle = (
        f"{total_growers} grower{'s' if total_growers != 1 else ''}, "
        f"{total_features} field{'s' if total_features != 1 else ''}"
    )

    if total_growers > 1:
        grower_selector_html = (
            '<div class="sidebar-controls">'
            '<label class="control-label" for="grower-select">Grower</label>'
            '<select id="grower-select" onchange="filterByGrower(this.value)">'
            '<option value="">All growers</option>'
            f"{grower_options}</select></div>"
        )
    else:
        grower_selector_html = ""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{header_title} — Field Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
  #map {{ height: 100vh; width: 100%; }}
  .map-wrapper {{ display: flex; height: 100vh; }}
  .sidebar {{ width: 340px; min-width: 340px; background: #fff; border-right: 2px solid #e2e8f0;
              display: flex; flex-direction: column; overflow: hidden; }}
  .sidebar-header {{ padding: 1rem; background: #1e3a5f; color: #fff; }}
  .sidebar-header h1 {{ margin: 0; font-size: 1.15rem; font-weight: 600; }}
  .sidebar-header p {{ margin: 0.25rem 0 0; font-size: 0.85rem; opacity: 0.85; }}
  .sidebar-controls {{ padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0; }}
  .sidebar-controls .control-label {{ display: block; font-size: 0.7rem; text-transform: uppercase;
                                      letter-spacing: 0.05em; color: #64748b; margin-bottom: 0.25rem; }}
  .sidebar-controls select {{ width: 100%; padding: 0.45rem; font-size: 0.9rem;
                              border: 1px solid #cbd5e1; border-radius: 6px; margin-bottom: 0.5rem; }}
  .sidebar-controls select:last-child {{ margin-bottom: 0; }}
  .sidebar-controls .grower-dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%;
                                  margin-right: 6px; vertical-align: middle; }}
  .sidebar-list {{ flex: 1; overflow-y: auto; }}
  .sidebar-list table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
  .sidebar-list th {{ text-align: left; padding: 0.5rem 0.75rem; background: #f8fafc;
                      border-bottom: 2px solid #e2e8f0; color: #475569; font-size: 0.75rem;
                      text-transform: uppercase; letter-spacing: 0.05em; position: sticky; top: 0; }}
  .sidebar-list td {{ padding: 0.4rem 0.75rem; border-bottom: 1px solid #f1f5f9; }}
  .field-row {{ cursor: pointer; transition: background 0.15s; }}
  .field-row:hover {{ background: #e0f2fe; }}
  .field-row.selected {{ background: #bfdbfe; }}
  .field-row.hidden {{ display: none; }}
  .grower-tag {{ display: inline-block; font-size: 0.7rem; padding: 0.1rem 0.45rem;
                 border-radius: 3px; color: #fff; font-weight: 600; }}
  .leaflet-popup-content {{ font-size: 0.88rem; }}
  .leaflet-popup-content strong {{ color: #1e3a5f; }}
  .legend {{ padding: 0.75rem 1rem; border-top: 1px solid #e2e8f0; font-size: 0.78rem; }}
  .legend-item {{ display: flex; align-items: center; margin-bottom: 0.25rem; }}
  .legend-swatch {{ width: 14px; height: 14px; border-radius: 3px; margin-right: 6px;
                    border: 1px solid #1e293b; flex-shrink: 0; }}
  @media (max-width: 768px) {{ .sidebar {{ width: 100%; min-width: 100%; max-height: 40vh; }}
                               .map-wrapper {{ flex-direction: column-reverse; }}
                               #map {{ height: 60vh; }} }}
</style>
</head>
<body>
<div class="map-wrapper">
  <div class="sidebar">
    <div class="sidebar-header">
      <h1>{header_title}</h1>
      <p>{header_subtitle}</p>
    </div>
    {grower_selector_html}
    <div class="sidebar-controls">
      <select id="field-select" onchange="zoomToField(this.value)">
        <option value="">— Zoom to field —</option>
        {field_options}
      </select>
    </div>
    <div class="sidebar-list">
      <table>
        <thead><tr><th>Grower</th><th>Field</th><th>Farm</th><th>Area</th></tr></thead>
        <tbody>{field_rows}</tbody>
      </table>
    </div>
    <div class="legend" id="legend"></div>
  </div>
  <div id="map"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
        integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin="">
</script>
<script>
  var fields = {fields_json};
  var growerInfo = {grower_info_json};

  var map = L.map('map', {{ scrollWheelZoom: true, zoomControl: true }});
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    maxZoom: 19,
    attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>'
  }}).addTo(map);

  var fieldLayers = [];
  var allBounds = [];

  function fieldPopupHtml(props) {{
    var rows = '';
    var labels = [
      ['Grower', props.grower_name || props.grower_slug || ''],
      ['Farm', props.farm_name || props.farm_slug || ''],
      ['Field', props.field_id || ''],
      ['Area', props.area_acres ? props.area_acres.toFixed(1) + ' ac' : ''],
      ['County', props.county_name || ''],
      ['Crop', props.crop_name || ''],
    ];
    for (var j = 0; j < labels.length; j++) {{
      if (labels[j][1]) {{
        rows += '<tr><td><strong>' + labels[j][0] + '</strong></td><td>' + labels[j][1] + '</td></tr>';
      }}
    }}
    return '<table>' + rows + '</table>';
  }}

  fields.forEach(function(f, i) {{
    var gi = f._grower_index;
    var color = growerInfo[gi].color;
    var layer = L.geoJSON(f, {{
      style: {{
        fillColor: color,
        fillOpacity: 0.3,
        color: '#1e293b',
        weight: 2,
      }},
      onEachFeature: function(feature, l) {{
        l.bindPopup(fieldPopupHtml(feature.properties));
        l.on('mouseover', function() {{ l.setStyle({{ fillOpacity: 0.5, weight: 3 }}); }});
        l.on('mouseout', function() {{ l.setStyle({{ fillOpacity: 0.3, weight: 2 }}); }});
        l.on('click', function() {{
          document.querySelectorAll('.field-row').forEach(function(r) {{ r.classList.remove('selected'); }});
          var row = document.querySelector('.field-row[data-index="' + i + '"]');
          if (row) row.classList.add('selected');
        }});
      }}
    }});
    fieldLayers.push(layer);
    layer.addTo(map);
    allBounds.push(layer.getBounds());
  }});

  if (allBounds.length > 0) {{
    var group = L.featureGroup(fieldLayers);
    map.fitBounds(group.getBounds().pad(0.1));
  }}

  function zoomToField(index) {{
    if (index === '') return;
    var i = parseInt(index);
    if (fieldLayers[i]) {{
      map.fitBounds(fieldLayers[i].getBounds().pad(0.2));
      fieldLayers[i].openPopup();
      document.querySelectorAll('.field-row').forEach(function(r) {{ r.classList.remove('selected'); }});
      var row = document.querySelector('.field-row[data-index="' + i + '"]');
      if (row) {{ row.classList.add('selected'); row.scrollIntoView({{ block: 'center' }}); }}
    }}
  }}

  function filterByGrower(slug) {{
    var currentZoom = null;
    var hasVisible = false;
    var visibleBounds = [];

    fieldLayers.forEach(function(layer, i) {{
      var feat = fields[i];
      var match = slug === '' || feat.properties.grower_slug === slug;
      if (match) {{
        if (map.hasLayer(layer) === false) {{
          layer.addTo(map);
        }}
        visibleBounds.push(layer.getBounds());
        hasVisible = true;
      }} else {{
        if (map.hasLayer(layer)) {{
          map.removeLayer(layer);
        }}
      }}
    }});

    // Show/hide table rows
    document.querySelectorAll('.field-row').forEach(function(row) {{
      var match = slug === '' || row.getAttribute('data-grower') === slug;
      row.classList.toggle('hidden', !match);
    }});

    // Show/hide field-select options
    document.querySelectorAll('#field-select option').forEach(function(opt) {{
      if (opt.value === '') return;
      var match = slug === '' || opt.getAttribute('data-grower') === slug;
      opt.style.display = match ? '' : 'none';
    }});
    document.getElementById('field-select').value = '';

    // Fit to visible
    if (hasVisible && visibleBounds.length > 0) {{
      var bg = L.featureGroup(
        fieldLayers.filter(function(_, i) {{
          var feat = fields[i];
          return slug === '' || feat.properties.grower_slug === slug;
        }})
      );
      map.fitBounds(bg.getBounds().pad(0.1));
    }}
  }}

  document.querySelectorAll('.field-row').forEach(function(row) {{
    row.addEventListener('click', function() {{
      zoomToField(this.getAttribute('data-index'));
    }});
  }});

  // Build legend
  (function() {{
    var el = document.getElementById('legend');
    var html = '';
    for (var i = 0; i < growerInfo.length; i++) {{
      html += '<div class="legend-item">'
        + '<div class="legend-swatch" style="background:' + growerInfo[i].color + '"></div>'
        + growerInfo[i].name + ' (' + growerInfo[i].count + ')'
        + '</div>';
    }}
    el.innerHTML = html;
  }})();
</script>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate grower web map (all growers if --grower-slug omitted)"
    )
    parser.add_argument(
        "--grower-slug",
        default=os.environ.get("AG_GROWER_SLUG", ""),
        help="Single grower slug (omit to include all growers)",
    )
    args = parser.parse_args()

    grower_slug = args.grower_slug

    if grower_slug:
        data = {grower_slug: _collect_field_features(grower_slug)}
        if not data[grower_slug][0]:
            print(f"No fields found for grower '{grower_slug}'")
            sys.exit(0)
        print(f"Generating web map for grower: {grower_slug}")
    else:
        print("Collecting field boundaries for all growers...")
        data = _collect_all_field_features()
        if not data:
            print("No field boundaries found for any grower")
            sys.exit(0)
        print(f"  Found {sum(len(v[0]) for v in data.values())} field(s) across {len(data)} grower(s)")

    html = _generate_html(data)

    if grower_slug:
        output_path = _GROWERS_ROOT / grower_slug / "derived" / "reports" / "grower_web_map.html"
    else:
        output_path = _REPO / "derived" / "reports" / "grower_web_map.html"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    size_kb = output_path.stat().st_size / 1024
    print(f"  Saved  {output_path}")
    print(f"  Size:  {size_kb:.0f} KB")


if __name__ == "__main__":
    main()

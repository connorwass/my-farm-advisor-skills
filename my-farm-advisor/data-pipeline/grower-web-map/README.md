# Grower Web Map

A self-contained interactive HTML web map for each grower in the My Farm Advisor data pipeline. Displays field polygon boundaries from the pipeline output on a Leaflet.js / OpenStreetMap basemap with click-to-inspect metadata and a zoom-to-field sidebar.

## Output

- `growers/<grower_slug>/derived/reports/grower_web_map.html`

## Map features

- Leaflet.js with OSM tiles (loaded from CDN, no API key needed)
- Field polygons colored by field with hover highlight
- Click popup: grower, farm, field ID, area (acres), county, crop
- Sidebar with field table (field, farm, area)
- Dropdown and click-to-zoom for any field
- Auto-fits map to show all fields
- Responsive layout
- ~8-9 KB per grower HTML output

## Dependencies

Uses the parent data-pipeline `.venv`. No additional Python packages.

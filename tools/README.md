# Kantonstour build tools

Pipeline (run from this directory after setting `S` in the scripts to it):

1. `python3 plan.py a` / `python3 plan.py b` — query transport.opendata.ch (cached in `api_cache/`), pick trains under the tight-stop rule, write `plan_a.json` / `plan_b.json`. Route definitions PLAN_A / PLAN_B live at the top of the file.
2. `python3 geo_build.py a` / `b` — add real track geometry per leg from SBB open data (`sbb/linie-mit-polygon.geojson` and `sbb/betriebspunkte.json`, download from data.sbb.ch: datasets *linie-mit-polygon* and *linie-mit-betriebspunkten*, GeoJSON/JSON export) and per-line station/segment data for the live layer.
3. `python3 build_site.py` — writes `site/index.html` + `site/data.js` (Leaflet page). Copy to the repo root.
4. `python3 build.py` — writes `kantonstour.md` (and a legacy SVG-map page).

Helpers: `api.py` (API client + minutes-per-canton estimate), `geo.py` (map fit, canton point-in-polygon), `track.py` (multi-line track routing over the SBB network).

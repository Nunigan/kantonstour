import json,re,math,os
S=os.path.dirname(os.path.abspath(__file__)); SITE=S+'/site'; OUT='/home/nunigan/Documents/kantonstour'
v4=json.load(open(S+'/data_v4.json')); A=json.load(open(S+'/plan_a.json')); B=json.load(open(S+'/plan_b.json'))
if 'onboard' not in B: B['onboard']=[]
coef=json.load(open(S+'/fit.json'))
# ---------- cantons: SVG -> WGS84 ----------
def svg_to_ll(x,y):
    a,b,c=coef[0][0],coef[1][0],coef[2][0]; d,e,f=coef[0][1],coef[1][1],coef[2][1]
    det=a*e-b*d; E=((x-c)*e-b*(y-f))/det; N=(a*(y-f)-d*(x-c))/det
    yp=(E-2600000)/1e6; xp=(N-1200000)/1e6
    lon=(2.6779094+4.728982*yp+0.791484*yp*xp+0.1306*yp*xp*xp-0.0436*yp**3)*100/36
    lat=(16.9023892+3.238272*xp-0.270978*yp*yp-0.002528*xp*xp-0.0447*yp*yp*xp-0.0140*xp**3)*100/36
    return [round(lat,5),round(lon,5)]
cantons={}
for ab,p in v4['map']['cantons'].items():
    polys=[]
    for sub in p.split('M'):
        sub=sub.strip().rstrip('Z').strip()
        if not sub: continue
        polys.append([svg_to_ll(*map(float,t.split(','))) for t in sub.split()])
    cantons[ab]=polys
# ---------- beer day per variant ----------
def beer_day(P):
    bd={'ZH':1}
    for d in P['days']:
        for l in d['legs']:
            if l['canton']: bd[l['canton']]=d['day']
    for o in P['onboard']: bd[o['c']]=o['day']
    return bd
def ends(P): return ' / '.join(d['legs'][-1]['arr'] for d in P['days'])
def home(P): return P['days'][2]['legs'][-1]['arr']
nA=1+sum(1 for d in A['days'] for l in d['legs'] if l['canton']); nOB=len(A['onboard'])
nB=1+sum(1 for d in B['days'] for l in d['legs'] if l['canton'])
assert nA+nOB==26 and nB==26,(nA,nOB,nB)
lakes=[]
for sub in v4['map']['lakes'].split('M'):
    sub=sub.strip().rstrip('Z').strip()
    if not sub: continue
    pts=[svg_to_ll(*map(float,t.split(','))) for t in sub.split()]
    if len(pts)>=4: lakes.append(pts)
DATA={'a':A,'b':B,'beer_day':{'a':beer_day(A),'b':beer_day(B)},'canton_names':v4['canton_names'],'cantons':cantons,'lakes':lakes}
# whole rail network, simplified
from track import simplify
net=[]
for f in json.load(open(S+'/sbb/linie-mit-polygon.geojson'))['features']:
    c=f['geometry']['coordinates']
    if len(c)<2: continue
    net.append([[round(y,4),round(x,4)] for x,y in simplify(c,45)])
open(SITE+'/network.js','w').write('window.KT_NET='+json.dumps(net,separators=(',',':'))+';\n')
print('network features',len(net),'bytes',os.path.getsize(SITE+'/network.js'))
open(SITE+'/data.js','w').write('window.KT='+json.dumps(DATA,ensure_ascii=False,separators=(',',':'))+';\n')
# ---------- page ----------
css=open(S+'/template_pre.html').read()
css=css[css.rindex('<style>')+7:css.rindex('</style>')]
css=css.replace('#map svg{display:block;width:100%;height:auto;cursor:grab;touch-action:none}','').replace('#map svg.dragging{cursor:grabbing}','').replace('#map{position:relative}','')
leaflet_css=open(S+'/leaflet.css').read()
dayA=[d['legs'][-1]['arr'] for d in A['days']]; dayB=[d['legs'][-1]['arr'] for d in B['days']]
html=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kantonstour</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800;900&family=Spline+Sans+Mono:wght@400;500;600;700&display=swap">
<style>{leaflet_css}</style>
<style>{css}
#map{{height:640px;border-radius:10px;overflow:hidden;background:var(--surface2)}}
@media (max-width:700px){{#map{{height:480px}}}}
.mapbar{{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;padding:0 4px 10px;font-size:13px;color:var(--ink2)}}
.mapbar label{{display:inline-flex;align-items:center;gap:6px;font-weight:600;cursor:pointer}}
.mapbar .days{{display:inline-flex;gap:4px}}
.mapbar .days button{{border:1px solid var(--ring);background:var(--surface2);color:var(--ink2);font:inherit;font-weight:700;font-size:12px;padding:3px 9px;border-radius:6px;cursor:pointer}}
.mapbar .days button.on{{background:var(--ink);color:var(--page);border-color:var(--ink)}}
.mapbar .status{{margin-left:auto;font-size:12px;color:var(--muted)}}
.stopmk{{width:22px;height:22px;border-radius:50%;background:#fff;border:2.6px solid #333;color:#111;font:800 11px "Spline Sans Mono",monospace;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 4px rgba(0,0,0,.35)}}
.obmk{{background:#c98500;color:#fff;font:700 10.5px Archivo,sans-serif;padding:2px 7px;border-radius:9px;white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,.35);border:1.5px solid #fff}}
.trmk{{color:#fff;font:700 10.5px "Spline Sans Mono",monospace;padding:2px 6px;border-radius:5px;white-space:nowrap;border:1.5px solid #fff;box-shadow:0 1px 5px rgba(0,0,0,.45);transform:translate(-50%,-50%);position:absolute;left:0;top:0}}
.trmk.IC,.trmk.EC,.trmk.ICE{{background:#d33a39}} .trmk.IR{{background:#e0642a}} .trmk.RE{{background:#7a3ea1}} .trmk.S,.trmk.R{{background:#2a78d6}} .trmk.PE,.trmk.VAE,.trmk.LIX{{background:#1baf7a}}
.trmk.ours{{outline:3px solid #ffd54a;outline-offset:1px;font-size:11.5px}}
.leaflet-container{{font-family:Archivo,system-ui,sans-serif}}
.leaflet-tooltip{{font-size:12.5px;line-height:1.4}}
.walkline{{stroke-dasharray:6 5}}
.attr a{{color:var(--muted)}}
</style></head><body>
<div class="wrap">
<header>
  <div class="eyebrow">16 – 18 October 2026 · Fri – Sun · all 26 cantons · trains only, no buses</div>
  <h1>Kantonstour</h1>
  <p class="sub">One beer in <b>every</b> canton in three days, entirely by rail — start and end Zürich HB, first night <b>Luzern</b>,
  second night <b>Neuchâtel</b>. Two ways to do it, both with tight stops: <b>Option A</b> drinks {nOB} of the 26 beers <b>on the train</b> and only gets off
  where you would change trains anyway ({nA} stops); <b>Option B</b> gets off in <b>all 26</b> cantons, 15′ minimum per stop, longer only where the hourly timetable
  forces it. Zürich is start and finish only — in between the route never passes through it, and it turns around in Landquart rather than Chur. Pure train plan — every connection is from the official SBB timetable for these exact dates (tap <b>SBB</b> on any leg to open it live); food and hotels are up to you.</p>
  <div class="verdict"><span class="dot"></span>Verdict: possible — 26/26 cantons · A: {nA} stops + {nOB} on board, home {home(A)} · B: 26 stops, home {home(B)}</div>
</header>
<div class="stats" id="stats"></div>
<div class="togglebar"><div class="toggle" role="tablist" aria-label="Variant">
  <button id="btn-a" role="tab">Option A · Beer on board<span class="hint">{nA} stops + {nOB} beers on the train · days end {ends(A)}</span></button>
  <button id="btn-b" role="tab">Option B · All on the ground<span class="hint">26 stops, 15′ minimum · days end {ends(B)}</span></button>
</div></div>
<section>
  <div class="sechead"><h2>The route</h2><div class="rule"></div><div class="tag" id="maptag"></div></div>
  <div class="mapcard">
    <div class="mapbar">
      <label><input type="checkbox" id="ck-osm"> map background</label>
      <label><input type="checkbox" id="ck-rail"> OpenRailwayMap overlay</label>
      <label><input type="checkbox" id="ck-cantons" checked> cantons by day</label>
      <label><input type="checkbox" id="ck-live"> live trains on our lines</label>
      <span class="days" id="livedays"><button data-d="1">Fri</button><button data-d="2">Sat</button><button data-d="3">Sun</button></span>
      <span class="status" id="livestatus"></span>
    </div>
    <div id="map"></div>
    <div class="maplegend" id="maplegend"></div>
    <div class="stopindex" id="stopindex"></div>
  </div>
</section>
<section>
  <div class="sechead"><h2>Timetable &amp; beer stops</h2><div class="rule"></div><div class="tag">SBB timetable, 16–18.10.2026</div></div>
  <div id="days"></div>
</section>
<section>
  <div class="sechead"><h2>The walk links</h2><div class="rule"></div><div class="tag">part of the route</div></div>
  <div class="notes">
    <div class="note"><b>Altstätten Stadt → Altstätten SG (Friday, 42′ window).</b> The Appenzeller Bahnen rack railway ends at Altstätten Stadt; the SBB Rheintal station is ~1.7 km further down — an easy downhill walk of ~20–25 min. This is what avoids passing through St. Gallen twice.</div>
    <div class="note"><b>Ziegelbrücke (Friday, both options).</b> The station itself already stands on Glarus soil, but for an honest GL beer walk ~5 min over the Linth channel into Niederurnen (Glarus Nord) and back.</div>
  </div>
</section>
<section>
  <div class="sechead"><h2>Good to know</h2><div class="rule"></div><div class="tag">verified 05.09.2026</div></div>
  <div class="notes">
    <div class="note warn"><b>Everything runs hourly — the schedule is a chain.</b> Miss one train and you usually lose 60 minutes. Set phone timers. 15′ stops leave no margin for a late train — if one slips, fall back to the next hourly service and the rest of the chain shifts by an hour.</div>
    <div class="note warn"><b>Day lengths:</b> Option A — Fri 07:05–{dayA[0]}, Sat 07:18–{dayA[1]}, Sun {A['days'][2]['legs'][0]['dep']}–{dayA[2]}. Option B — Fri 07:05–{dayB[0]}, Sat 07:18–{dayB[1]}, Sun {B['days'][2]['legs'][0]['dep']}–{dayB[2]}. Both sleep Luzern, then Neuchâtel.</div>
    <div class="note"><b>Live trains:</b> the map can show every train currently running on the lines of the selected day — positions are computed from the SBB timetable plus the reported delays (transport.opendata.ch station boards, refreshed every 5 minutes), not from GPS, so expect them to be a minute or two off. Trains with the number of one we take are ringed in yellow. Untick it when you don't need it.</div>
    <div class="note"><b>The RE 48 briefly crosses Germany</b> (Jestetten corridor before Schaffhausen). Swiss tickets valid, normally no checks — carry an ID.</div>
    <div class="note"><b>The CJ leg is a train, not a bus:</b> the narrow-gauge red Chemins de fer du Jura from Glovelier through the Franches-Montagnes to La Chaux-de-Fonds. Option A rides it 16:41→17:56 at dusk and drinks the JU beer on it — 75′ through the Jura, the best ride of the trip. Option B skips it: IC from Delémont to Biel (BE beer) and on to Neuchâtel for the night.</div>
    <div class="note"><b>Drinking your own beer on board is allowed</b> on all trains in this plan (SBB, Thurbo, SOB, Appenzeller Bahnen, Zentralbahn, CJ) and on platforms — that is what Option A is built on. Stock up at Zürich HB and top up in Schaffhausen, Landquart, Olten and Basel. Every on-board beer has at least 20′ inside its canton; the shortest is <b>AR</b> (≈22′, Lustmühle → Gais), the longest <b>JU</b> on the CJ (≈96′) and <b>TG</b> on the S 1 (≈88′). AG is taken on the S 26 through the Freiamt (≈44′) — the price is one hour on Saturday (Olten 13:21, next IC with a proper stop 14:04). BE is the last one, through Bern on the way home.</div>
    <div class="note good"><b>Tickets:</b> three Saver Day Passes (buy early) or a GA — one pass covers everything here, including Appenzeller Bahnen, Zentralbahn and CJ.</div>
    <div class="note"><b>OLMA fair runs in St. Gallen 8–18 Oct</b> — expect very full trains around St. Gallen on Friday. <b>Re-check the timetable a few days before</b> (sbb.ch) — the SBB buttons on each leg open the live connection.</div>
  </div>
</section>
<footer class="attr">
  Timetable: official Swiss public-transport data (transport.opendata.ch / SBB), queried 05.09.2026 for 16–18.10.2026 — annual timetable 2026; re-verify shortly before travel via the SBB links. Map: © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors; railway overlay © <a href="https://www.openrailwaymap.org/">OpenRailwayMap</a> (CC-BY-SA); track geometry: SBB open data (data.sbb.ch, "Linie mit Polygon"); canton outlines: swisstopo. 26 cantons, 26 beers — drink responsibly. Prost, Santé, Salute, Viva!
</footer>
</div>
<script src="leaflet.js"></script>
<script src="data.js"></script>
<script src="network.js"></script>
<script>
const DATA = window.KT;
const MUG = '<svg class="mug" width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M5 3h11a1 1 0 0 1 1 1v2h2.5A2.5 2.5 0 0 1 22 8.5v5a2.5 2.5 0 0 1-2.5 2.5H17v3a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Zm12 5v6h2.5a.5.5 0 0 0 .5-.5v-5a.5.5 0 0 0-.5-.5H17ZM7 7v9h2V7H7Zm4 0v9h2V7h-2Z"/></svg>';
const DAYC = {{1:'#2a78d6',2:'#eb6834',3:'#1baf7a'}};
const DAYCS = {{1:'var(--d1s)',2:'var(--d2s)',3:'var(--d3s)'}};
const DAYLBL = {{1:'Day 1 · Fri 16.10', 2:'Day 2 · Sat 17.10', 3:'Day 3 · Sun 18.10'}};
const $ = id => document.getElementById(id);
const esc = s => String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

function stopsList(variant){{
  const days = DATA[variant].days, stops = [], walks = [];
  stops.push({{n:1, canton:'ZH', station:'Zürich HB', ll:days[0].legs[0].from_ll, day:1, when:'meet 06:45 · beer #1 before the 07:05 departure'}});
  let n = 1;
  days.forEach(d => d.legs.forEach(l => {{
    if(l.canton){{ n += 1; stops.push({{n, canton:l.canton, station:l.to, ll:l.to_ll, day:d.day, when:'arr '+l.arr+(l.stop_min!=null? ' · '+l.stop_min+'′ stop':' · arrival beer')}}); }}
    else if((l.note||'').indexOf('walk') >= 0) walks.push({{station:l.to, ll:l.to_ll, day:d.day, note:l.note}});
  }}));
  return {{stops, walks}};
}}
// ---------- map ----------
const map = L.map('map', {{zoomSnap:0.5, worldCopyJump:false}}).setView([46.85, 8.25], 8);
const osmLayer = L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom:19, attribution:'© OpenStreetMap'}});
$('ck-osm').addEventListener('change', e => e.target.checked ? osmLayer.addTo(map).bringToBack() : map.removeLayer(osmLayer));
const railLayer = L.tileLayer('https://{{s}}.tiles.openrailwaymap.org/standard/{{z}}/{{x}}/{{y}}.png', {{maxZoom:19, subdomains:'abc', opacity:.75, attribution:'© OpenRailwayMap'}});
const cantonLayer = L.layerGroup().addTo(map), netLayer = L.layerGroup().addTo(map), routeLayer = L.layerGroup().addTo(map), stopLayer = L.layerGroup().addTo(map), liveLayer = L.layerGroup().addTo(map);
$('ck-rail').addEventListener('change', e => e.target.checked ? railLayer.addTo(map) : map.removeLayer(railLayer));
if($('ck-rail').checked) railLayer.addTo(map);
// whole Swiss rail network (SBB open data), thin grey
(window.KT_NET||[]).forEach(line => L.polyline(line, {{color:'#8a8a86', weight:1.1, opacity:.75, interactive:false}}).addTo(netLayer));
const lakeLayer = L.layerGroup().addTo(map);
(DATA.lakes||[]).forEach(p => L.polygon(p, {{color:'#5b8fd0', weight:.6, opacity:.5, fillColor:'#5b8fd0', fillOpacity:.22, interactive:false}}).addTo(lakeLayer));
$('ck-cantons').addEventListener('change', e => e.target.checked ? cantonLayer.addTo(map) : map.removeLayer(cantonLayer));
function pathLen(p){{ let s=0; for(let i=1;i<p.length;i++) s+=map.distance(p[i-1],p[i]); return s; }}
function pointAt(p, f){{
  const tot = pathLen(p); let d = f*tot;
  for(let i=1;i<p.length;i++){{ const l = map.distance(p[i-1],p[i]); if(d<=l){{ const t=l?d/l:0; return [p[i-1][0]+(p[i][0]-p[i-1][0])*t, p[i-1][1]+(p[i][1]-p[i-1][1])*t]; }} d-=l; }}
  return p[p.length-1];
}}
function renderMap(variant){{
  const days = DATA[variant].days, bd = DATA.beer_day[variant], OB = DATA[variant].onboard || [];
  cantonLayer.clearLayers(); routeLayer.clearLayers(); stopLayer.clearLayers();
  for(const [ab, polys] of Object.entries(DATA.cantons)){{
    const day = bd[ab];
    L.polygon(polys, {{color:'#8a8a86', weight:.9, opacity:.55, fillColor: day? DAYC[day] : '#999', fillOpacity: day? .10 : .03, interactive:false}}).addTo(cantonLayer);
  }}
  const {{stops, walks}} = stopsList(variant);
  let bounds = null;
  days.forEach(d => d.legs.forEach((l, li) => {{
    l.geo.forEach(path => {{
      if(path.length < 2) return;
      L.polyline(path, {{color:'#fff', weight:8, opacity:.9, interactive:false}}).addTo(routeLayer);
      const pl = L.polyline(path, {{color:DAYC[d.day], weight:4, opacity:1}}).addTo(routeLayer);
      const tr = l.trains.map(t=>t.train).join(' + ');
      pl.bindTooltip('<b>'+esc(tr)+'</b> '+esc(l.from)+' → '+esc(l.to)+'<br>'+l.dep+' → '+l.arr+' · Day '+d.day, {{sticky:true}});
      bounds = bounds ? bounds.extend(pl.getBounds()) : pl.getBounds();
    }});
    OB.filter(o => o.day===d.day && o.leg===li).forEach(o => {{
      const full = l.geo.flat(); if(full.length<2) return;
      const pt = pointAt(full, 0.5);
      L.marker(pt, {{icon: L.divIcon({{className:'', html:'<div class="obmk">'+MUG+' '+o.c+' on board</div>', iconSize:[0,0], iconAnchor:[0,0]}}), zIndexOffset:500}})
        .bindTooltip('<b>'+o.c+' — beer on board</b><br>≈'+o.mins+'′ inside · '+esc(o.note)).addTo(stopLayer);
    }});
  }}));
  // walk links
  days.forEach(d => d.legs.forEach((l, li) => {{
    if((l.note||'').indexOf('walk')>=0 && d.legs[li+1]) L.polyline([l.to_ll, d.legs[li+1].from_ll], {{color:'#333', weight:3, dashArray:'6 5'}}).bindTooltip('Walk link · '+esc(l.note)).addTo(routeLayer);
  }}));
  stops.forEach(st => {{
    L.marker(st.ll, {{icon: L.divIcon({{className:'', html:'<div class="stopmk" style="border-color:'+DAYC[st.day]+'">'+st.n+'</div>', iconSize:[22,22], iconAnchor:[11,11]}}), zIndexOffset:800}})
      .bindTooltip('<b>'+st.n+' · '+esc(st.station)+' ('+st.canton+')</b><br>'+esc(st.when)).addTo(stopLayer);
  }});
  if(bounds && !renderMap.fitted){{ map.fitBounds(bounds.pad(0.04)); renderMap.fitted = true; }}
  $('maptag').textContent = 'option '+variant.toUpperCase()+' · '+stops.length+' stops'+(OB.length? ' · '+OB.length+' beers on board' : ' · 15′ minimum');
  let lg = '';
  for(const d of [1,2,3]) lg += '<span class="lg"><span class="sw" style="background:'+DAYC[d]+'"></span>'+DAYLBL[d]+'</span>';
  lg += '<span class="lg"><span class="pin"></span>beer stop</span><span class="lg"><span class="wk"></span>walk link</span>';
  if(OB.length) lg += '<span class="lg" style="color:var(--beer-line)">'+MUG+'beer on board</span>';
  lg += '<span class="lg"><span class="sw" style="background:#8a8a86;height:2px"></span>other rail lines</span>';
  lg += '<span class="lg"><span class="trmk IC" style="position:static;transform:none">IC</span><span class="trmk S" style="position:static;transform:none">S</span> live train</span>';
  $('maplegend').innerHTML = lg;
  $('stopindex').innerHTML = stops.map(st => '<span class="si"><span class="n" style="color:'+DAYC[st.day]+'">'+st.n+'</span><span>'+esc(st.station)+' · <b>'+st.canton+'</b></span></span>').join('');
}}
// ---------- live trains ----------
const LIVE = {{on:false, day: null, journeys: {{}}, timer:null, anim:null, lastFetch:0}};
const tripDay = (() => {{ const t = new Date().toISOString().slice(0,10); return ({{'2026-10-16':1,'2026-10-17':2,'2026-10-18':3}})[t] || 1; }})();
LIVE.day = tripDay;
function normKey(cat, num){{ num = String(num||''); if(/^[A-Za-z]+$/.test(num)) return num.toUpperCase(); return (cat+' '+num.replace(/^0+/,'')).trim(); }}
function liveConfig(variant){{
  const day = DATA[variant].days[LIVE.day-1], lines = new Set(), stations = new Set(), ours = new Set();
  day.legs.forEach(l => l.trains.forEach(t => {{ lines.add(t.train); if(t.dep_id) stations.add(t.dep_id); if(t.arr_id) stations.add(t.arr_id); if(t.name) ours.add(t.name); }}));
  return {{lines, stations:[...stations], ours}};
}}
function fmtLocal(d){{ const p=n=>String(n).padStart(2,'0'); return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate())+' '+p(d.getHours())+':'+p(d.getMinutes()); }}
async function fetchLive(){{
  const cfg = liveConfig(VARIANT); const since = new Date(Date.now()-150*60000);
  $('livestatus').textContent = 'loading '+cfg.stations.length+' station boards…';
  const found = {{}};
  await Promise.all(cfg.stations.map(async id => {{
    try{{
      const u = 'https://transport.opendata.ch/v1/stationboard?station='+encodeURIComponent(id)+'&limit=60&datetime='+encodeURIComponent(fmtLocal(since))+'&transportations[]=train';
      const r = await fetch(u); if(!r.ok) return; const j = await r.json();
      const board = j.station;
      for(const e of (j.stationboard||[])){{
        const key = normKey(e.category, e.number); if(!cfg.lines.has(key)) continue;
        const jid = e.name+'@'+(e.stop.departure||'').slice(0,10);
        if(found[jid]) continue;
        const stops = [];
        (e.passList||[]).forEach((p, i) => {{
          let st = p.station; if(i===0 || !st || !st.coordinate || st.coordinate.x==null) st = (i===0? board : null);
          if(!st || !st.coordinate || st.coordinate.x==null) return;
          const src = i===0 ? e.stop : p; const prog = src.prognosis || {{}};
          const arr = prog.arrival || src.arrival, dep = prog.departure || src.departure;
          const delay = (src.delay!=null? src.delay : null);
          const fix = (iso, dl) => {{ if(!iso) return null; const t = new Date(iso).getTime(); return (dl && !prog.departure && !prog.arrival) ? t + dl*60000 : t; }};
          stops.push({{id:st.id, name:st.name, ll:[st.coordinate.x, st.coordinate.y], arr:fix(arr,delay), dep:fix(dep,delay), delay}});
        }});
        if(stops.length<2) continue;
        found[jid] = {{key, cat:e.category, name:e.name, to:e.to, stops, ours: cfg.ours.has(e.name)}};
      }}
    }}catch(err){{ console.warn('board failed', id, err); }}
  }}));
  LIVE.journeys = found; LIVE.lastFetch = Date.now();
  drawLive();
}}
function segPath(key, a, b){{
  const L_ = (DATA[VARIANT].lines||{{}})[key] || (DATA.a.lines||{{}})[key] || (DATA.b.lines||{{}})[key];
  if(L_){{
    const s = L_.seg[a.id+'|'+b.id]; if(s) return s;
    const r = L_.seg[b.id+'|'+a.id]; if(r) return r.slice().reverse();
    const ia = L_.order.indexOf(a.id), ib = L_.order.indexOf(b.id);
    if(ia>=0 && ib>=0 && ia!==ib){{
      const step = ia<ib?1:-1; let path=[];
      for(let i=ia;i!==ib;i+=step){{ const x=L_.order[i], y=L_.order[i+step]; let s=L_.seg[x+'|'+y]; if(!s){{ const rr=L_.seg[y+'|'+x]; if(!rr) return [a.ll,b.ll]; s=rr.slice().reverse(); }} path = path.length? path.concat(s.slice(1)) : s.slice(); }}
      return path;
    }}
  }}
  return [a.ll, b.ll];
}}
function positionAt(j, now){{
  const s = j.stops;
  if(now < (s[0].dep||s[0].arr)) return null;
  for(let i=0;i<s.length-1;i++){{
    const a=s[i], b=s[i+1]; const t0 = a.dep||a.arr, t1 = b.arr||b.dep; if(t0==null||t1==null) continue;
    if(now>=t0 && now<=t1){{ const f = t1>t0 ? (now-t0)/(t1-t0) : 1; return {{ll: pointAt(segPath(j.key,a,b), f), next:b, from:a}}; }}
    if(i+1<s.length-1 && now>t1 && now < (b.dep||t1)) return {{ll:b.ll, next:s[i+2], from:b, dwell:true}};
  }}
  return null;
}}
const liveMarkers = {{}};
function drawLive(){{
  const now = Date.now(); const seen = new Set(); let count=0, ours=0;
  for(const [jid, j] of Object.entries(LIVE.journeys)){{
    const pos = positionAt(j, now); if(!pos) continue; seen.add(jid); count++; if(j.ours) ours++;
    const dl = pos.next && pos.next.delay ? ' +'+pos.next.delay+'′' : '';
    const label = j.key + (j.ours? ' ★':'');
    const tip = '<b>'+esc(j.key)+' → '+esc(j.to)+'</b>'+(j.ours? ' · our train':'')+'<br>'+(pos.dwell? 'at ':'next: ')+esc(pos.next? pos.next.name : '')+(pos.next&&pos.next.arr? ' '+new Date(pos.next.arr).toTimeString().slice(0,5):'')+dl+'<br><span style="opacity:.7">train '+esc(j.name.replace(/^0+/,''))+'</span>';
    if(liveMarkers[jid]){{ liveMarkers[jid].setLatLng(pos.ll); liveMarkers[jid].setTooltipContent(tip); }}
    else {{
      liveMarkers[jid] = L.marker(pos.ll, {{icon: L.divIcon({{className:'', html:'<div class="trmk '+esc(j.cat)+(j.ours?' ours':'')+'">'+esc(label)+'</div>', iconSize:[0,0], iconAnchor:[0,0]}}), zIndexOffset:(j.ours?1200:1000)}}).bindTooltip(tip).addTo(liveLayer);
    }}
  }}
  for(const jid of Object.keys(liveMarkers)) if(!seen.has(jid)){{ liveLayer.removeLayer(liveMarkers[jid]); delete liveMarkers[jid]; }}
  const age = Math.round((now-LIVE.lastFetch)/60000);
  $('livestatus').textContent = count+' trains on '+['','Friday','Saturday','Sunday'][LIVE.day]+"'s lines now"+(ours? ' · '+ours+' ★ ours':'')+' · timetable + delays, updated '+(age<1?'just now':age+' min ago');
}}
function clearLive(){{ for(const k of Object.keys(liveMarkers)){{ liveLayer.removeLayer(liveMarkers[k]); delete liveMarkers[k]; }} LIVE.journeys={{}}; $('livestatus').textContent=''; }}
function setLive(on){{
  LIVE.on = on; clearInterval(LIVE.timer); clearInterval(LIVE.anim); clearLive();
  if(!on) return;
  fetchLive();
  LIVE.timer = setInterval(() => {{ if(!document.hidden) fetchLive(); }}, 5*60000);
  LIVE.anim = setInterval(() => {{ if(!document.hidden) drawLive(); }}, 10000);
}}
$('ck-live').addEventListener('change', e => setLive(e.target.checked));
document.querySelectorAll('#livedays button').forEach(b => b.addEventListener('click', () => {{ LIVE.day = +b.dataset.d; document.querySelectorAll('#livedays button').forEach(x=>x.classList.toggle('on', x===b)); if(LIVE.on) setLive(true); }}));
document.querySelector('#livedays button[data-d="'+LIVE.day+'"]').classList.add('on');
document.addEventListener('visibilitychange', () => {{ if(!document.hidden && LIVE.on && Date.now()-LIVE.lastFetch > 5*60000) fetchLive(); }});
// ---------- timetable ----------
function renderDays(variant){{
  const days = DATA[variant].days, OB = DATA[variant].onboard || [];
  const bpd = {{1:0,2:0,3:0}}; let out = '';
  days.forEach(d => {{
    const dc = DAYC[d.day], dcs = DAYCS[d.day]; let rows = '';
    if(d.day===1){{
      rows += '<tr class="stop beerstop" style="--dc:'+dc+';--dcs:'+dcs+'"><td class="t">06:45<div class="pl">meet up</div></td><td colspan="2"><span class="cchip"><span class="cb" style="background:'+dc+'">ZH</span> Zürich HB — beer #1 before departure</span><div class="stopmeta">20′ until the 07:05 train</div></td></tr>';
      bpd[1]++;
    }}
    d.legs.forEach((l, li) => {{
      l.trains.forEach((t, ti) => {{
        if(ti>0){{ const prev = l.trains[ti-1]; const wait = (parseInt(t.dep_time)*60+ +t.dep_time.slice(3)) - (parseInt(prev.arr_time)*60+ +prev.arr_time.slice(3));
          rows += '<tr><td class="t"></td><td colspan="2" class="xfer">↳ change in '+esc(t.dep_station)+' ('+wait+'′)</td></tr>'; }}
        rows += '<tr><td class="t">'+t.dep_time+' → '+t.arr_time+'<div class="pl">Gl. '+esc(t.dep_platform||'–')+' → '+esc(t.arr_platform||'–')+'</div></td><td colspan="2"><span class="trainchip">'+esc(t.train)+'</span>'+esc(t.dep_station)+' → '+esc(t.arr_station)+' <span class="dir">(direction '+esc(t.dir||'')+')</span>'+(ti===0 && l.sbb ? '<a class="sbblink" href="'+esc(l.sbb)+'" target="_blank" rel="noopener">SBB ↗</a>' : '')+'</td></tr>';
      }});
      OB.filter(o => o.day===d.day && o.leg===li).forEach(o => {{ rows += '<tr class="onboard"><td class="t">≈'+o.mins+'′ inside</td><td colspan="2">'+MUG+'<b>'+o.c+' beer on board</b> — '+esc(DATA.canton_names[o.c])+' · '+esc(o.note)+'</td></tr>'; bpd[d.day]++; }});
      if(l.canton){{ bpd[d.day]++;
        rows += '<tr class="stop beerstop" style="--dc:'+dc+';--dcs:'+dcs+'"><td class="t">'+l.arr+(l.stop_min!=null? ' +'+l.stop_min+'′':'')+'<div class="pl">'+(l.stop_min!=null? 'stop':'arrival beer')+'</div></td><td colspan="2"><span class="cchip"><span class="cb" style="background:'+dc+'">'+l.canton+'</span> '+esc(l.to)+'</span>'+(l.note? '<div class="stopmeta">'+esc(l.note)+'</div>':'')+'</td></tr>';
      }} else {{
        rows += '<tr class="stop"><td class="t">'+l.arr+(l.stop_min!=null? ' +'+l.stop_min+'′':'')+'</td><td colspan="2"><span class="dir">'+esc(l.to)+' — '+esc(l.note||'transfer')+'</span></td></tr>';
      }}
    }});
    out += '<div class="day"><div class="dayhead" style="--dc:'+dc+'"><span class="dnum"><span>Day '+d.day+'</span> · '+['','Friday 16.10.','Saturday 17.10.','Sunday 18.10.'][d.day]+'</span><span class="droute">'+esc(d.legs[0].from)+' → '+esc(d.legs[d.legs.length-1].to)+'</span><span class="dmeta">'+d.legs[0].dep+' – '+d.legs[d.legs.length-1].arr+' · '+bpd[d.day]+' beers</span></div><div class="tscroll"><table>'+rows+'</table></div></div>';
  }});
  $('days').innerHTML = out; return bpd;
}}
function renderStats(variant, bpd){{
  const days = DATA[variant].days;
  const ride = days.reduce((a,d)=>a+d.legs.reduce((x,l)=>x+l.duration_min,0),0);
  const ntr = days.reduce((a,d)=>a+d.legs.reduce((x,l)=>x+l.trains.length,0),0);
  const home = days[2].legs[days[2].legs.length-1].arr;
  const shortest = Math.min(...days.flatMap(d=>d.legs.filter(l=>l.canton && l.stop_min!=null).map(l=>l.stop_min)));
  $('stats').innerHTML = '<div class="tile"><div class="v">26 <small>of 26</small></div><div class="k">cantons — complete</div></div>'+
    '<div class="tile"><div class="v">'+(bpd[1]+bpd[2]+bpd[3])+'</div><div class="k">beers · '+bpd[1]+' + '+bpd[2]+' + '+bpd[3]+' per day</div></div>'+
    '<div class="tile"><div class="v">'+Math.floor(ride/60)+' h '+String(ride%60).padStart(2,'0')+'</div><div class="k">on trains</div></div>'+
    '<div class="tile"><div class="v">'+ntr+'</div><div class="k">trains</div></div>'+
    '<div class="tile"><div class="v">'+shortest+'′</div><div class="k">shortest stop</div></div>'+
    '<div class="tile"><div class="v">'+home+'</div><div class="k">home in Zürich, Sunday</div></div>';
}}
let VARIANT = 'a';
try{{ VARIANT = localStorage.getItem('ktour-variant4') || 'a'; }}catch(e){{}}
function setVariant(v){{
  VARIANT = v; try{{ localStorage.setItem('ktour-variant4', v); }}catch(e){{}}
  $('btn-a').classList.toggle('on', v==='a'); $('btn-b').classList.toggle('on', v==='b');
  $('btn-a').setAttribute('aria-selected', v==='a'); $('btn-b').setAttribute('aria-selected', v==='b');
  renderMap(v); renderStats(v, renderDays(v)); if(LIVE.on) setLive(true);
}}
$('btn-a').addEventListener('click', ()=>setVariant('a')); $('btn-b').addEventListener('click', ()=>setVariant('b'));
setVariant(VARIANT==='b' ? 'b' : 'a');
</script>
</body></html>
'''
open(SITE+'/index.html','w').write(html)
print('index',len(html),'data.js',os.path.getsize(SITE+'/data.js'))

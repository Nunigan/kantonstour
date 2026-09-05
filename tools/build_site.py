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
def pip(pt,poly):
    x,y=pt[1],pt[0]; inside=False; n=len(poly)
    for i in range(n):
        y1,x1=poly[i]; y2,x2=poly[(i+1)%n]
        if (y1>y)!=(y2>y):
            xi=x1+(y-y1)*(x2-x1)/(y2-y1)
            if xi>x: inside=not inside
    return inside
allpolys=[p for ps in cantons.values() for p in ps]
lakes=[]
for ring in json.load(open(S+'/sbb/lakes.json')):
    if any(any(pip(pt,poly) for poly in allpolys) for pt in ring[::max(1,len(ring)//40)]): lakes.append(ring)
print('lakes kept',len(lakes))
# background network = full extent of the lines we ride (both variants)
net={}
for P in (A,B):
    for k,L in P['lines'].items():
        for sk,p in L['seg'].items():
            a_,b_=sk.split('|'); sig=tuple(sorted((a_,b_)))
            if sig not in net: net[sig]=[[round(y,4),round(x,4)] for y,x in p]
        L.pop('paths',None)
open(SITE+'/network.js','w').write('window.KT_NET='+json.dumps(list(net.values()),separators=(',',':'))+';\n')
DATA={'a':A,'b':B,'beer_day':{'a':beer_day(A),'b':beer_day(B)},'canton_names':{**v4['canton_names'],'GE':'Genf','NE':'Neuenburg','FR':'Freiburg','VS':'Wallis','TI':'Tessin','VD':'Waadt'},'cantons':cantons,'lakes':lakes}
print('network features',len(net),'bytes',os.path.getsize(SITE+'/network.js'))
open(SITE+'/data.js','w').write('window.KT='+json.dumps(DATA,ensure_ascii=False,separators=(',',':'))+';\n')
# ---------- page ----------
css=open(S+'/template_pre.html').read()
css=css[css.rindex('<style>')+7:css.rindex('</style>')]
css=css.replace('#map svg{display:block;width:100%;height:auto;cursor:grab;touch-action:none}','').replace('#map svg.dragging{cursor:grabbing}','').replace('#map{position:relative}','')
leaflet_css=open(S+'/leaflet.css').read()
dayA=[d['legs'][-1]['arr'] for d in A['days']]; dayB=[d['legs'][-1]['arr'] for d in B['days']]
html=f'''<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
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
.obmk{{display:flex;align-items:center;gap:5px;background:#fff;color:#5a3b00;font:800 13px Archivo,sans-serif;padding:3px 10px 3px 6px;border-radius:16px;white-space:nowrap;box-shadow:0 2px 6px rgba(0,0,0,.35);border:2px solid #d98e00;transform:translate(-50%,-50%);position:absolute;left:0;top:0}}
.obmk svg{{display:block;margin:0}}
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
  <div class="eyebrow">16.–18. Oktober 2026 · Fr–So · alle 26 Kantone · nur Zug, kein Bus</div>
  <h1>Kantonstour</h1>
  <p class="sub">Ein Bier in <b>jedem</b> Kanton in drei Tagen, nur mit dem Zug. Start und Ziel Zürich HB, Übernachtung in <b>Luzern</b> und <b>Neuenburg</b>.
  <b>Option A</b> trinkt {nOB} der 26 Biere <b>im Zug</b> und steigt nur aus, wo ohnehin umgestiegen wird ({nA} Halte). <b>Option B</b> steigt in <b>allen 26</b> Kantonen aus, mindestens 15′ pro Halt.
  Zürich nur am Anfang und am Ende, Wende in Landquart statt Chur. Alle Verbindungen aus dem SBB-Fahrplan für diese Daten – <b>SBB</b> öffnet die Verbindung live.</p>
  <div class="verdict"><span class="dot"></span>Machbar – 26/26 Kantone · A: {nA} Halte + {nOB} im Zug, zuhause {home(A)} · B: 26 Halte, zuhause {home(B)}</div>
</header>
<div class="stats" id="stats"></div>
<div class="togglebar"><div class="toggle" role="tablist" aria-label="Variant">
  <button id="btn-a" role="tab">Option A · Bier im Zug<span class="hint">{nA} Halte + {nOB} Biere im Zug · Tagesende {ends(A)}</span></button>
  <button id="btn-b" role="tab">Option B · Alles am Boden<span class="hint">26 Halte, mind. 15′ · Tagesende {ends(B)}</span></button>
</div></div>
<section>
  <div class="sechead"><h2>Die Route</h2><div class="rule"></div><div class="tag" id="maptag"></div></div>
  <div class="mapcard">
    <div class="mapbar">
      <label><input type="checkbox" id="ck-osm"> Hintergrundkarte</label>
      <label><input type="checkbox" id="ck-cantons" checked> Kantone nach Tag</label>
      <label><input type="checkbox" id="ck-live"> Züge live auf unseren Linien</label>
      <span class="days" id="livedays"><button data-d="1">Fr</button><button data-d="2">Sa</button><button data-d="3">So</button></span>
      <span class="status" id="livestatus"></span>
    </div>
    <div id="map"></div>
    <div class="maplegend" id="maplegend"></div>
    <div class="stopindex" id="stopindex"></div>
  </div>
</section>
<section>
  <div class="sechead"><h2>Fahrplan &amp; Bierhalte</h2><div class="rule"></div><div class="tag">SBB-Fahrplan 16.–18.10.2026</div></div>
  <div id="days"></div>
</section>
<section>
  <div class="sechead"><h2>Fusswege</h2><div class="rule"></div><div class="tag">Teil der Route</div></div>
  <div class="notes">
    <div class="note"><b>Altstätten Stadt → Altstätten SG (Fr, 42′ Zeit).</b> Die Zahnradbahn endet in Altstätten Stadt, der SBB-Bahnhof liegt 1.7 km weiter unten – 20–25′ bergab.</div>
    <div class="note"><b>Ziegelbrücke (Fr, beide Optionen).</b> Der Bahnhof liegt schon im Glarnerland; für ein ehrliches GL-Bier 5′ über die Linth nach Niederurnen.</div>
  </div>
</section>
<section>
  <div class="sechead"><h2>Gut zu wissen</h2><div class="rule"></div><div class="tag">geprüft 05.09.2026</div></div>
  <div class="notes">
    <div class="note warn"><b>Alles fährt stündlich.</b> Ein verpasster Zug kostet meist 60′ – Timer stellen.</div>
    <div class="note warn"><b>Tage:</b> A – Fr 07:05–{dayA[0]}, Sa 07:18–{dayA[1]}, So {A['days'][2]['legs'][0]['dep']}–{dayA[2]}. B – Fr 07:05–{dayB[0]}, Sa 07:18–{dayB[1]}, So {B['days'][2]['legs'][0]['dep']}–{dayB[2]}.</div>
    <div class="note"><b>Karte:</b> nur unsere Linien – ganze Länge grau, unsere Abschnitte farbig. <b>Züge live</b> zeigt alle Züge auf diesen Linien; Position aus Fahrplan und gemeldeter Verspätung (transport.opendata.ch, alle 5 Min), kein GPS – 1–2 Minuten Abweichung. ★ = Zugnummern, die wir nehmen.</div>
    <div class="note"><b>RE 48</b> fährt kurz durch Deutschland – Ausweis mitnehmen.</div>
    <div class="note"><b>CJ (Option A):</b> Schmalspurbahn Glovelier → La Chaux-de-Fonds, 16:41→17:56, JU-Bier an Bord. Option B: IC Delémont → Biel → Neuenburg.</div>
    <div class="note"><b>Eigenes Bier im Zug</b> ist auf allen Bahnen erlaubt. Nachschub in Zürich, Schaffhausen, Landquart, Olten, Basel. Kürzestes Bier im Zug: AR (≈22′); längste: JU (≈96′), TG (≈88′). AG auf der S 26 durchs Freiamt (≈44′) kostet am Samstag eine Stunde.</div>
    <div class="note good"><b>Tickets:</b> 3× Spartageskarte oder GA – gilt auch für Appenzeller Bahnen, Zentralbahn und CJ.</div>
    <div class="note"><b>OLMA</b> in St. Gallen 8.–18.10.: volle Züge am Freitag. Fahrplan kurz vor der Reise nochmals prüfen.</div>
  </div>
</section>
<footer class="attr">
  Fahrplan: transport.opendata.ch / SBB, abgefragt 05.09.2026 für 16.–18.10.2026 – vor der Reise via SBB-Links prüfen. Karte: Seen und Hintergrund © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende; Gleisgeometrie: SBB Open Data (data.sbb.ch); Kantonsgrenzen: swisstopo. 26 Kantone, 26 Biere. Prost, Santé, Salute, Viva!
</footer>
</div>
<script src="leaflet.js"></script>
<script src="data.js"></script>
<script src="network.js"></script>
<script>
const DATA = window.KT;
const MUGSVG = s => '<svg class="mug" width="'+s+'" height="'+s+'" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 9.5h11V20a1.8 1.8 0 0 1-1.8 1.8H6.8A1.8 1.8 0 0 1 5 20z" fill="#f4b323" stroke="#5a3b00" stroke-width="1.3"/><path d="M16 11.5h2.3a2.2 2.2 0 0 1 2.2 2.2v2.6a2.2 2.2 0 0 1-2.2 2.2H16" fill="none" stroke="#5a3b00" stroke-width="1.7"/><path d="M4.6 9.8C3.5 8.3 4.4 6.2 6.3 6.2c.2-2 2.5-3.1 4.2-2 1.2-1.6 3.9-1.3 4.7.6 1.9-.3 3.5 1.4 2.8 3.3-.2.8-.9 1.3-1.7 1.3H5.9c-.5 0-1-.2-1.3-.6z" fill="#fff" stroke="#5a3b00" stroke-width="1.3" stroke-linejoin="round"/><path d="M8.2 12.5v6.5M11.3 12.5v6.5" stroke="#d98e00" stroke-width="1.4" stroke-linecap="round"/></svg>';
const MUG = MUGSVG(16);
const DAYC = {{1:'#2a78d6',2:'#eb6834',3:'#1baf7a'}};
const DAYCS = {{1:'var(--d1s)',2:'var(--d2s)',3:'var(--d3s)'}};
const DAYLBL = {{1:'Tag 1 · Fr 16.10.', 2:'Tag 2 · Sa 17.10.', 3:'Tag 3 · So 18.10.'}};
const $ = id => document.getElementById(id);
const esc = s => String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

function stopsList(variant){{
  const days = DATA[variant].days, stops = [], walks = [];
  stops.push({{n:1, canton:'ZH', station:'Zürich HB', ll:days[0].legs[0].from_ll, day:1, when:'Treffpunkt 06:45 · Bier Nr. 1 vor der Abfahrt 07:05'}});
  let n = 1;
  days.forEach(d => d.legs.forEach(l => {{
    if(l.canton){{ n += 1; stops.push({{n, canton:l.canton, station:l.to, ll:l.to_ll, day:d.day, when:'an '+l.arr+(l.stop_min!=null? ' · '+l.stop_min+'′ Halt':' · Ankunftsbier')}}); }}
    else if(l.walk) walks.push({{station:l.to, ll:l.to_ll, day:d.day, note:l.note}});
  }}));
  return {{stops, walks}};
}}
// ---------- map ----------
const map = L.map('map', {{zoomSnap:0.5, worldCopyJump:false}}).setView([46.85, 8.25], 8);
const osmLayer = L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom:19, attribution:'© OpenStreetMap'}});
$('ck-osm').addEventListener('change', e => e.target.checked ? osmLayer.addTo(map).bringToBack() : map.removeLayer(osmLayer));
const cantonLayer = L.layerGroup().addTo(map), netLayer = L.layerGroup().addTo(map), routeLayer = L.layerGroup().addTo(map), stopLayer = L.layerGroup().addTo(map), liveLayer = L.layerGroup().addTo(map);
const lakeLayer = L.layerGroup().addTo(map);
(DATA.lakes||[]).forEach(p => L.polygon(p, {{color:'#3f7fc6', weight:.8, opacity:.7, fillColor:'#5ea0e6', fillOpacity:.45, interactive:false}}).addTo(lakeLayer));
// the full extent of every line we ride, thin grey — our sections are drawn on top in colour
(window.KT_NET||[]).forEach(line => L.polyline(line, {{color:'#8a8a86', weight:1.6, opacity:.8, interactive:false}}).addTo(netLayer));
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
      pl.bindTooltip('<b>'+esc(tr)+'</b> '+esc(l.from)+' → '+esc(l.to)+'<br>'+l.dep+' → '+l.arr+' · Tag '+d.day, {{sticky:true}});
      bounds = bounds ? bounds.extend(pl.getBounds()) : pl.getBounds();
    }});
    OB.filter(o => o.day===d.day && o.leg===li).forEach(o => {{
      const full = l.geo.flat(); if(full.length<2) return;
      const pt = pointAt(full, 0.5);
      L.marker(pt, {{icon: L.divIcon({{className:'', html:'<div class="obmk">'+MUGSVG(22)+o.c+'</div>', iconSize:[0,0], iconAnchor:[0,0]}}), zIndexOffset:500}})
        .bindTooltip('<b>'+o.c+' – Bier im Zug</b><br>≈'+o.mins+'′ im Kanton · '+esc(o.note)).addTo(stopLayer);
    }});
  }}));
  // walk links
  days.forEach(d => d.legs.forEach((l, li) => {{
    if(l.walk && d.legs[li+1]) L.polyline([l.to_ll, d.legs[li+1].from_ll], {{color:'#333', weight:3, dashArray:'6 5'}}).bindTooltip('Fussweg · '+esc(l.note)).addTo(routeLayer);
  }}));
  stops.forEach(st => {{
    L.marker(st.ll, {{icon: L.divIcon({{className:'', html:'<div class="stopmk" style="border-color:'+DAYC[st.day]+'">'+st.n+'</div>', iconSize:[22,22], iconAnchor:[11,11]}}), zIndexOffset:800}})
      .bindTooltip('<b>'+st.n+' · '+esc(st.station)+' ('+st.canton+')</b><br>'+esc(st.when)).addTo(stopLayer);
  }});
  if(bounds && !renderMap.fitted){{ map.fitBounds(bounds.pad(0.04)); renderMap.fitted = true; }}
  $('maptag').textContent = 'Option '+variant.toUpperCase()+' · '+stops.length+' Halte'+(OB.length? ' · '+OB.length+' Biere im Zug' : ' · mind. 15′');
  let lg = '';
  for(const d of [1,2,3]) lg += '<span class="lg"><span class="sw" style="background:'+DAYC[d]+'"></span>'+DAYLBL[d]+'</span>';
  lg += '<span class="lg"><span class="pin"></span>Bierhalt</span><span class="lg"><span class="wk"></span>Fussweg</span>';
  if(OB.length) lg += '<span class="lg">'+MUGSVG(18)+'Bier im Zug</span>';
  lg += '<span class="lg"><span class="sw" style="background:#8a8a86;height:2px"></span>unsere Linien, ganze Länge</span>';
  lg += '<span class="lg"><span class="trmk IC" style="position:static;transform:none">IC</span><span class="trmk S" style="position:static;transform:none">S</span> Zug live</span>';
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
  $('livestatus').textContent = 'lade '+cfg.stations.length+' Abfahrtstafeln…';
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
    const tip = '<b>'+esc(j.key)+' → '+esc(j.to)+'</b>'+(j.ours? ' · unser Zug':'')+'<br>'+(pos.dwell? 'in ':'nächster Halt: ')+esc(pos.next? pos.next.name : '')+(pos.next&&pos.next.arr? ' '+new Date(pos.next.arr).toTimeString().slice(0,5):'')+dl+'<br><span style="opacity:.7">Zug '+esc(j.name.replace(/^0+/,''))+'</span>';
    if(liveMarkers[jid]){{ liveMarkers[jid].setLatLng(pos.ll); liveMarkers[jid].setTooltipContent(tip); }}
    else {{
      liveMarkers[jid] = L.marker(pos.ll, {{icon: L.divIcon({{className:'', html:'<div class="trmk '+esc(j.cat)+(j.ours?' ours':'')+'">'+esc(label)+'</div>', iconSize:[0,0], iconAnchor:[0,0]}}), zIndexOffset:(j.ours?1200:1000)}}).bindTooltip(tip).addTo(liveLayer);
    }}
  }}
  for(const jid of Object.keys(liveMarkers)) if(!seen.has(jid)){{ liveLayer.removeLayer(liveMarkers[jid]); delete liveMarkers[jid]; }}
  const age = Math.round((now-LIVE.lastFetch)/60000);
  $('livestatus').textContent = count+' Züge jetzt auf den Linien vom '+['','Freitag','Samstag','Sonntag'][LIVE.day]+(ours? ' · '+ours+' ★ unsere':'')+' · Fahrplan + Verspätungen, Stand '+(age<1?'jetzt':'vor '+age+' Min');
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
      rows += '<tr class="stop beerstop" style="--dc:'+dc+';--dcs:'+dcs+'"><td class="t">06:45<div class="pl">Treffpunkt</div></td><td colspan="2"><span class="cchip"><span class="cb" style="background:'+dc+'">ZH</span> Zürich HB – Bier Nr. 1 vor der Abfahrt</span><div class="stopmeta">20′ bis zum Zug um 07:05</div></td></tr>';
      bpd[1]++;
    }}
    d.legs.forEach((l, li) => {{
      l.trains.forEach((t, ti) => {{
        if(ti>0){{ const prev = l.trains[ti-1]; const wait = (parseInt(t.dep_time)*60+ +t.dep_time.slice(3)) - (parseInt(prev.arr_time)*60+ +prev.arr_time.slice(3));
          rows += '<tr><td class="t"></td><td colspan="2" class="xfer">↳ Umsteigen in '+esc(t.dep_station)+' ('+wait+'′)</td></tr>'; }}
        rows += '<tr><td class="t">'+t.dep_time+' → '+t.arr_time+'<div class="pl">Gl. '+esc(t.dep_platform||'–')+' → '+esc(t.arr_platform||'–')+'</div></td><td colspan="2"><span class="trainchip">'+esc(t.train)+'</span>'+esc(t.dep_station)+' → '+esc(t.arr_station)+' <span class="dir">(Richtung '+esc(t.dir||'')+')</span>'+(ti===0 && l.sbb ? '<a class="sbblink" href="'+esc(l.sbb)+'" target="_blank" rel="noopener">SBB ↗</a>' : '')+'</td></tr>';
      }});
      OB.filter(o => o.day===d.day && o.leg===li).forEach(o => {{ rows += '<tr class="onboard"><td class="t">≈'+o.mins+'′ im Kanton</td><td colspan="2">'+MUG+'<b>'+o.c+' Bier im Zug</b> – '+esc(DATA.canton_names[o.c])+' · '+esc(o.note)+'</td></tr>'; bpd[d.day]++; }});
      if(l.canton){{ bpd[d.day]++;
        rows += '<tr class="stop beerstop" style="--dc:'+dc+';--dcs:'+dcs+'"><td class="t">'+l.arr+(l.stop_min!=null? ' +'+l.stop_min+'′':'')+'<div class="pl">'+(l.stop_min!=null? 'Halt':'Ankunftsbier')+'</div></td><td colspan="2"><span class="cchip"><span class="cb" style="background:'+dc+'">'+l.canton+'</span> '+esc(l.to)+'</span>'+(l.note? '<div class="stopmeta">'+esc(l.note)+'</div>':'')+'</td></tr>';
      }} else {{
        rows += '<tr class="stop"><td class="t">'+l.arr+(l.stop_min!=null? ' +'+l.stop_min+'′':'')+'</td><td colspan="2"><span class="dir">'+esc(l.to)+' – '+esc(l.note||'Umsteigen')+'</span></td></tr>';
      }}
    }});
    out += '<div class="day"><div class="dayhead" style="--dc:'+dc+'"><span class="dnum"><span>Tag '+d.day+'</span> · '+['','Freitag 16.10.','Samstag 17.10.','Sonntag 18.10.'][d.day]+'</span><span class="droute">'+esc(d.legs[0].from)+' → '+esc(d.legs[d.legs.length-1].to)+'</span><span class="dmeta">'+d.legs[0].dep+' – '+d.legs[d.legs.length-1].arr+' · '+bpd[d.day]+' Biere</span></div><div class="tscroll"><table>'+rows+'</table></div></div>';
  }});
  $('days').innerHTML = out; return bpd;
}}
function renderStats(variant, bpd){{
  const days = DATA[variant].days;
  const ride = days.reduce((a,d)=>a+d.legs.reduce((x,l)=>x+l.duration_min,0),0);
  const ntr = days.reduce((a,d)=>a+d.legs.reduce((x,l)=>x+l.trains.length,0),0);
  const home = days[2].legs[days[2].legs.length-1].arr;
  const shortest = Math.min(...days.flatMap(d=>d.legs.filter(l=>l.canton && l.stop_min!=null).map(l=>l.stop_min)));
  $('stats').innerHTML = '<div class="tile"><div class="v">26 <small>von 26</small></div><div class="k">Kantone – komplett</div></div>'+
    '<div class="tile"><div class="v">'+(bpd[1]+bpd[2]+bpd[3])+'</div><div class="k">Biere · '+bpd[1]+' + '+bpd[2]+' + '+bpd[3]+' pro Tag</div></div>'+
    '<div class="tile"><div class="v">'+Math.floor(ride/60)+' h '+String(ride%60).padStart(2,'0')+'</div><div class="k">im Zug</div></div>'+
    '<div class="tile"><div class="v">'+ntr+'</div><div class="k">Züge</div></div>'+
    '<div class="tile"><div class="v">'+shortest+'′</div><div class="k">kürzester Halt</div></div>'+
    '<div class="tile"><div class="v">'+home+'</div><div class="k">zuhause in Zürich, Sonntag</div></div>';
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

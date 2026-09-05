import json,re
S='/tmp/claude-1000/-home-nunigan-Documents-kantonstour/459284f2-91ac-4974-8dc6-ab56334d110b/scratchpad'
OUT='/home/nunigan/Documents/kantonstour'
v4=json.load(open(S+'/data_v4.json'))
A=json.load(open(S+'/plan_a.json')); B=json.load(open(S+'/plan_b.json'))
B['onboard']=[]
DATA={'a':A,'b':B,'beer_day':v4['beer_day'],'canton_names':v4['canton_names'],'map':v4['map']}
def ends(P): return ' / '.join(d['legs'][-1]['arr'] for d in P['days'])
def home(P): return P['days'][2]['legs'][-1]['arr']
nA=1+sum(1 for d in A['days'] for l in d['legs'] if l['canton']); nOB=len(A['onboard'])
nB=1+sum(1 for d in B['days'] for l in d['legs'] if l['canton'])
assert nA+nOB==26 and nB==26, (nA,nOB,nB)
pre=open(S+'/template_pre.html').read(); rest=open(S+'/template_rest.html').read()
def rep(s,old,new,count=1):
    assert old in s, old[:60]; return s.replace(old,new,count)
pre=rep(pre,'<title>Kantonstour (Copy)</title>','<title>Kantonstour</title>')
pre=rep(pre,re.search(r'<p class="sub">.*?</p>',pre,re.S).group(0),
 f'''<p class="sub">One beer in <b>every</b> canton in three days, entirely by rail — start and end Zürich HB, first night <b>Luzern</b>,
  second night <b>Biel/Bienne</b>. Two ways to do it, both with tight stops: <b>Option A</b> drinks {nOB} of the 26 beers <b>on the train</b> and only gets off
  where you would change trains anyway ({nA} stops); <b>Option B</b> gets off in <b>all 26</b> cantons, 15′ minimum per stop, longer only where the hourly timetable
  forces it. Zürich is start and finish only — in between the route never passes through it (Saturday: Option A goes Zug → Rotkreuz → Muri → Lenzburg → Olten on the S 26, Option B Zug → Luzern → Sursee → Zofingen → Olten). Pure train plan — every connection is from the official SBB timetable for these exact dates (tap <b>SBB</b> on any leg to open it live); food and hotels are up to you.</p>''')
pre=rep(pre,re.search(r'<div class="verdict">.*?</div>',pre,re.S).group(0),
 f'<div class="verdict"><span class="dot"></span>Verdict: possible — 26/26 cantons · A: {nA} stops + {nOB} on board, home {home(A)} · B: 26 stops, home {home(B)}</div>')
pre=rep(pre,re.search(r'<button id="btn-a".*?</button>',pre,re.S).group(0),
 f'<button id="btn-a" role="tab">Option A · Beer on board<span class="hint">{nA} stops + {nOB} beers on the train · days end {ends(A)}</span></button>')
pre=rep(pre,re.search(r'<button id="btn-b".*?</button>',pre,re.S).group(0),
 f'<button id="btn-b" role="tab">Option B · All on the ground<span class="hint">26 stops, 15′ minimum · days end {ends(B)}</span></button>')
# walk links section
pre=rep(pre,re.search(r'<div class="note"><b>Ziegelbrücke.*?</div>',pre,re.S).group(0),
 '<div class="note"><b>Ziegelbrücke (Friday, both options).</b> The station itself already stands on Glarus soil, but for an honest GL beer walk ~5 min over the Linth channel into Niederurnen (Glarus Nord) and back.</div>')
# good to know
pre=rep(pre,re.search(r'<div class="note warn"><b>Day lengths:</b>.*?</div>',pre,re.S).group(0),
 f'<div class="note warn"><b>Day lengths:</b> Option A — Fri 07:05–{A["days"][0]["legs"][-1]["arr"]}, Sat 07:18–{A["days"][1]["legs"][-1]["arr"]}, Sun 08:18–{home(A)}. Option B — Fri 07:05–{B["days"][0]["legs"][-1]["arr"]}, Sat 07:18–{B["days"][1]["legs"][-1]["arr"]}, Sun 08:18–{home(B)}. Both sleep Luzern, then Biel.</div>')
pre=rep(pre,re.search(r'<div class="note"><b>The CJ leg is a train, not a bus:</b>.*?</div>',pre,re.S).group(0),
 '<div class="note"><b>The CJ leg is a train, not a bus:</b> the narrow-gauge red Chemins de fer du Jura from Glovelier through the Franches-Montagnes to La Chaux-de-Fonds. Option A rides it 16:41→17:56 at dusk and drinks the JU beer on it — 75′ through the Jura, the best ride of the trip. Option B skips it: IC from Delémont straight to Biel, and Neuchâtel on Sunday morning on the way to Genève via Yverdon.</div>')
pre=rep(pre,re.search(r'<div class="note"><b>Drinking your own beer on board is allowed</b>.*?</div>',pre,re.S).group(0),
 '<div class="note"><b>Drinking your own beer on board is allowed</b> on all trains in this plan (SBB, Thurbo, SOB, Appenzeller Bahnen, Zentralbahn, CJ) and on platforms — that is what Option A is built on. Stock up at Zürich HB and top up in Schaffhausen, Landquart, Olten and Basel. Every on-board beer has at least 20′ inside its canton; the shortest is <b>AR</b> (≈22′, Lustmühle → Gais), the longest <b>JU</b> on the CJ (≈96′) and <b>TG</b> on the S 1 (≈88′). AG is taken on the S 26 through the Freiamt (≈44′) — the price is one hour on Saturday (Olten 13:21, next IC with a proper stop 14:04, Biel 19:12).</div>')
pre=rep(pre,'<div class="tag">verified 23.08.2026</div>','<div class="tag">verified 05.09.2026</div>')
pre=rep(pre,'queried 23.08.2026 for 16–18.10.2026','queried 05.09.2026 for 16–18.10.2026')
# script
rest=rep(rest,"const OB = DATA.onboard_b;\nconst OB_SET = new Set(OB.map(o=>o.c));\n","")
rest=rep(rest,"function renderMap(variant){\n  const M = DATA.map, beerDay = DATA.beer_day, routes = DATA[variant].routes;",
              "function renderMap(variant){\n  const M = DATA.map, beerDay = DATA.beer_day, routes = DATA[variant].routes, OB = DATA[variant].onboard || [];")
rest=rep(rest,"  if(variant === 'b'){\n    for(const o of OB){","  if(OB.length){\n    for(const o of OB){")
rest=rep(rest,"$('maptag').textContent = variant==='b' ? 'option B · 26 stops · 15′ minimum' : 'option A · 26 stops · 30′ minimum';",
              "$('maptag').textContent = 'option '+variant.toUpperCase()+' · '+stops.length+' stops'+(OB.length? ' · '+OB.length+' beers on board' : ' · 15′ minimum');")
rest=rep(rest,"if(variant==='b') lg += '<span class=\"lg\" style=\"color:var(--beer-line)\">'","if(OB.length) lg += '<span class=\"lg\" style=\"color:var(--beer-line)\">'")
rest=rep(rest,"function renderDays(variant){\n  const days = DATA[variant].days;","function renderDays(variant){\n  const days = DATA[variant].days, OB = DATA[variant].onboard || [];")
rest=rep(rest,"      if(variant==='b'){\n        OB.filter(o => o.day===d.day && o.leg===li).forEach(o => {\n          rows += '<tr class=\"onboard\"><td class=\"t\">'+o.mins+'′ inside</td><td colspan=\"2\">'+MUG+'<b>'+o.c+' beer on board</b> — '+esc(DATA.canton_names[o.c])+' · '+esc(o.note)+'</td></tr>';\n          bpd[d.day]++;\n        });\n      }",
              "      OB.filter(o => o.day===d.day && o.leg===li).forEach(o => {\n        rows += '<tr class=\"onboard\"><td class=\"t\">≈'+o.mins+'′ inside</td><td colspan=\"2\">'+MUG+'<b>'+o.c+' beer on board</b> — '+esc(DATA.canton_names[o.c])+' · '+esc(o.note)+'</td></tr>';\n        bpd[d.day]++;\n      });")
rest=rep(rest,"'ktour-variant2'","'ktour-variant3'",2)
html=pre+'const DATA = '+json.dumps(DATA,ensure_ascii=False)+';\n'+rest
open(OUT+'/kantonstour.html','w').write(html)
print('html bytes',len(html))

# ---- markdown ----
def table(P,date_of):
    md=''
    for d in P['days']:
        md+=f"\n### {['','Freitag','Samstag','Sonntag'][d['day']]} {d['date'][8:10]}.{d['date'][5:7]}.{d['date'][:4]}\n\n| Ab | Von | An | Nach | Zug/Züge | Bier | SBB |\n|---|---|---|---|---|---|---|\n"
        for li,l in enumerate(d['legs']):
            tr=' + '.join(t['train'] for t in l['trains'])
            if l['transfers']: tr+=' (Umsteigen: '+', '.join(t['dep_station'] for t in l['trains'][1:])+')'
            ob=[o for o in P['onboard'] if o['day']==d['day'] and o['leg']==li]
            for o in ob: tr+=f" · 🚆🍺 **{o['c']}** im Zug ≈{o['mins']}′ – {o['note']}"
            if l['canton']:
                beer=f"🍺 **{l['canton']}** – {l['to']}"+(f" ({l['stop_min']}′)" if l['stop_min'] is not None else ' (Ankunftsbier, Übernachtung)' if 'Übernachtung' in l['note'] else '')
            elif l.get('walk'): beer="🚶 1.7 km (~25′) zu Fuss nach Altstätten SG"
            elif 'Hause' in l['note']: beer='🏁 zuhause'
            else: beer=f"↔ Umsteigen ({l['stop_min']}′) – {l['note']}"
            pl=f" Gl. {l['trains'][0]['dep_platform']}" if l['trains'][0]['dep_platform'] else ''
            md+=f"| **{l['dep']}**{pl} | {l['from']} | {l['arr']} | {l['to']} | {tr} | {beer} | [SBB]({l['sbb']}) |\n"
    return md
md=f'''# Kantonstour 16.–18.10.2026 – alle 26 Kantone mit dem Zug

Ein Bier in jedem Kanton, nur Zug (kein Bus), Start und Ziel **Zürich HB**, Übernachtung **Luzern** und **Neuenburg**.
Zeiten aus dem SBB-Fahrplan (abgefragt 05.09.2026). **SBB** öffnet die Verbindung live – vor der Reise nochmals prüfen.

Bier Nr. 1: **Zürich HB ~06:45**, vor der Abfahrt 07:05. Beide Optionen mit knappen Halten (mind. 15′ pro Bierhalt, länger nur wo der Stundentakt es erzwingt). A: 12 + 9 + 5 Biere pro Tag, B: 12 + 10 + 4.

## Option A – Bier im Zug ({nA} Halte + {nOB} Biere im Zug, So zuhause {home(A)})

Aussteigen nur, wo ohnehin umgestiegen wird; {nOB} Kantone werden im Zug getrunken (🚆🍺-Zeilen, mit dem Abschnitt zum Öffnen). Fr 07:05–{A['days'][0]['legs'][-1]['arr']} · Sa 07:18–{A['days'][1]['legs'][-1]['arr']} · So {A['days'][2]['legs'][0]['dep']}–{home(A)}.
{table(A,None)}
## Option B – alles am Boden (26 Halte, So zuhause {home(B)})

In jedem Kanton aussteigen, mind. 15′. Fr 07:05–{B['days'][0]['legs'][-1]['arr']} · Sa 07:18–{B['days'][1]['legs'][-1]['arr']} · So {B['days'][2]['legs'][0]['dep']}–{home(B)}.
{table(B,None)}
## Hinweise

- **Appenzell → Altstätten:** Zahnradbahn via Gais nach Altstätten Stadt, dann 1.7 km bergab (~20–25′) zum SBB-Bahnhof Altstätten SG.
- **Graubünden / Glarus:** Wende in Landquart (GR-Bier dort, kein Abstecher nach Chur), dann dem Walensee entlang nach Ziegelbrücke – Bahnhof im Glarnerland; 5′ über die Linth nach Niederurnen für ein ehrliches GL-Bier.
- **Voralpen-Express** Pfäffikon SZ → Luzern: SZ-Bier in Option A, ~60′ im Kanton Schwyz.
- **Gotthard:** IR 26 / IR 46 über die Bergstrecke nach Airolo; UR-Bier in Option A zwischen Brunnen und Göschenen.
- **Nicht über Zürich:** Samstag Airolo → Arth-Goldau → Zug (ZG-Halt), dann A: S 1 nach Rotkreuz und S 26 durchs Freiamt (Muri, Wohlen, Lenzburg, Aarau) nach Olten mit AG-Bier im Zug (≈44′); B: Zug → Luzern → Sursee → Zofingen (AG-Halt) → Olten.
- **CJ:** nur Option A – Delémont → Glovelier (R 2), dann die Schmalspurbahn nach La Chaux-de-Fonds (75′) mit JU-Bier im Zug, RE 6 runter nach Neuenburg. Option B: IC Delémont → Biel (BE-Bier) → Neuenburg (NE-Bier, Übernachtung).
- **Sonntag (A):** Neuenburg → Genf via Yverdon (VD im Zug), IR 90 nach Martigny und zurück nach Lausanne, IC 1 via Freiburg und Bern (FR und BE im Zug) nach Zürich.
- **Risiken:** alles stündlich – ein verpasster Zug kostet ~60′. RE 48 fährt kurz durch Deutschland (Ausweis). OLMA in St. Gallen 8.–18.10.: volle Züge am Freitag. Fahrplan kurz vorher auf sbb.ch prüfen.
- **Tickets:** 3× Spartageskarte oder GA – gilt auch für Appenzeller Bahnen, Zentralbahn, CJ. Eigenes Bier ist in allen Zügen und auf den Perrons erlaubt.

Interaktive Karte (unsere Linien, Züge live): https://nunigan.github.io/kantonstour/
'''
open(OUT+'/kantonstour.md','w').write(md)
print('md bytes',len(md))

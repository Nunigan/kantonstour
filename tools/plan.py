import json, datetime, urllib.parse
from api import *
from geo import to_svg, coords
F='2026-10-16'; SA='2026-10-17'; SU='2026-10-18'
STXY=json.load(open('station_xy.json'))
ONB_MIN=9
def L(frm,to,canton,onboard=(),via=None,direct=False,note='',min_stop=None,start=None,walk_after=0,onb_min=None):
    if min_stop is None: min_stop=15 if canton else 5
    return dict(frm=frm,to=to,canton=canton,onboard=list(onboard),via=via,direct=direct,note=note,min_stop=min_stop,start=start,walk_after=walk_after,onb_min=onb_min or ONB_MIN)
PLAN_A=[
 (F,[
  L('Zürich HB','Schaffhausen','SH',note='beer #1 ZH at HB kiosk before departure',start='07:05'),
  L('Schaffhausen','St. Gallen','SG',onboard=['TG']),
  L('St. Gallen','Appenzell','AI',onboard=['AR']),
  L('Appenzell','Altstätten Stadt',None,note="rack railway down; walk 1.7 km (~25') to Altstätten SG",walk_after=40),
  L('Altstätten SG','Landquart','GR',note='turn around here — no detour to Chur'),
  L('Landquart','Ziegelbrücke','GL',note='walk over the Linth bridge into Glarus Nord'),
  L('Ziegelbrücke','Pfäffikon SZ',None,note='change to the Voralpen-Express'),
  L('Pfäffikon SZ','Luzern',None,onboard=['SZ'],direct=True,note='change for the NW/OW loop'),
  L('Luzern','Hergiswil NW','NW'),
  L('Hergiswil NW','Sarnen','OW'),
  L('Sarnen','Luzern','LU',note='arrival beer — overnight Luzern'),
 ]),
 (SA,[
  L('Luzern','Airolo','TI',onboard=['UR'],start='07:00',note='Treno Gottardo over the mountain line'),
  L('Airolo','Zug','ZG'),
  L('Zug','Olten','SO',onboard=['AG'],via='Muri AG',note='S 26 through the Freiamt — never through Zürich'),
  L('Olten','Basel SBB','BS',onboard=['BL']),
  L('Basel SBB','La Chaux-de-Fonds','NE',onboard=['JU'],via='Glovelier',note='CJ — the classic red Jura train'),
  L('La Chaux-de-Fonds','Neuchâtel',None,note='down to the lake — overnight Neuchâtel'),
 ]),
 (SU,[
  L('Neuchâtel','Genève','GE',onboard=['VD'],start='08:00'),
  L('Genève','Martigny','VS'),
  L('Martigny','Zürich HB',None,onboard=['FR','BE'],via='Fribourg/Freiburg',note='home'),
 ]),
]
def tname(s):
    n=str(s['number'] or '')
    if n and n.isalpha(): return n
    return (s['cat']+' '+n.lstrip('0')).strip()
def sbb(c):
    stops=[{"value":c['from_id'],"type":"ID","label":c['from']},{"value":c['to_id'],"type":"ID","label":c['to']}]
    return 'https://www.sbb.ch/en?'+urllib.parse.urlencode({'stops':json.dumps(stops),'date':json.dumps(c['dep'].strftime('%Y-%m-%d')),'time':json.dumps(hm(c['dep'])),'moment':json.dumps('DEPARTURE')})
def xy(name):
    if name in STXY: return STXY[name]
    lat,lon,_,_=coords(name); return to_svg(lat,lon)
ONB_NOTES={
 'TG':"S 1 along the Rhine, the Untersee and Lake Constance — Schlatt TG → Roggwil-Berg, the longest beer of the trip",
 'AR':"Lustmühle → Gais, climbing through Appenzellerland",
 'GL':"Mühlehorn → Ziegelbrücke on the S 17 along the Walensee; finish it on the S 25 as far as Bilten (still Glarus) — the tightest one",
 'SZ':"Voralpen-Express Pfäffikon → Küssnacht: Biberbrugg, Rothenthurm, Arth-Goldau — all Schwyz",
 'UR':"Brunnen → Göschenen up the Gotthard north ramp, past the Wassen church three times",
 'ZG':"Walchwil → Baar along Lake Zug — the train stops in Zug on the way",
 'AG':"Oberrüti → Aarau on the S 26 through the Freiamt — Muri, Wohlen, Lenzburg, Aarau — nearly the whole ride is Aargau",
 'BL':"Hauenstein tunnel → Pratteln: Sissach, Liestal and the Ergolz valley",
 'JU':"Delémont → La Chaux-d'Abel on the CJ through the Franches-Montagnes",
 'VD':"Yverdon → Renens along Lake Neuchâtel and across the Gros-de-Vaud",
 'FR':"Palézieux → Flamatt: Romont, Fribourg and the Saane bridges",
 'BE':"Flamatt → Herzogenbuchsee through Bern — the last one, on the way home",
}
def candidates(leg,date,earliest):
    t=hm(earliest) if earliest else leg['start']
    cands={}
    for page in (0,1):
        for c in connections(leg['frm'],leg['to'],date,t,via=leg['via'],direct=leg['direct'],limit=6,page=page):
            if earliest and c['dep']<earliest: continue
            if leg['direct'] and c['transfers']>0: continue
            cm,wh=canton_minutes(c)
            if not all(cm.get(ab,0)>=leg['onb_min'] for ab in leg['onboard']): continue
            key=(c['dep'],c['arr'],tuple(s['train'] for s in c['trains']))
            cands[key]=(c,cm,wh)
    good=[x for x in cands.values() if not x[0]['relief']] or list(cands.values())
    return good
def search_day(legs,date,beam=4):
    # states: list of (score_tuple, chain) where chain=list of (c,cm,wh); score=(arr, transfers, arrivals..., -deps...)
    states=[((),[])]
    for li,leg in enumerate(legs):
        nxt={}
        for score,chain in states:
            if chain:
                prev=chain[-1][0]['arr']
                gap=legs[li-1]['walk_after'] or legs[li-1]['min_stop']
                earliest=prev+datetime.timedelta(minutes=gap)
            else: earliest=None
            for c,cm,wh in candidates(leg,date,earliest):
                ch=chain+[(c,cm,wh)]
                tr=sum(x[0]['transfers'] for x in ch)
                sc=(c['arr'],tr,tuple(x[0]['arr'] for x in ch),tuple(-x[0]['dep'].timestamp() for x in ch))
                k=c['arr']
                if k not in nxt or sc<nxt[k][0]: nxt[k]=(sc,ch)
        if not nxt: raise SystemExit(f"no candidate for {leg['frm']}→{leg['to']}")
        states=sorted(nxt.values(),key=lambda x:x[0])[:beam]
    return states[0][1]
def run(plan):
    days=[]; routes={}; onboard=[]
    for di,(date,legs) in enumerate(plan):
        day=di+1; out=[]; paths=[]
        chain=search_day(legs,date)
        for li,(leg,(c,cm,wh)) in enumerate(zip(legs,chain)):
            trains=[{'train':tname(s),'dir':s['dir'],'dep_station':s['dep_station'],'dep_time':s['dep_time'],'dep_platform':s['dep_platform'],
                     'arr_station':s['arr_station'],'arr_time':s['arr_time'],'arr_platform':s['arr_platform']} for s in c['trains']]
            rec={'from':leg['frm'],'to':leg['to'],'canton':leg['canton'],'note':leg['note'],'dep':hm(c['dep']),'arr':hm(c['arr']),
                 'duration_min':c['duration_min'],'transfers':c['transfers'],'trains':trains,'sbb':sbb(c),'from_xy':xy(leg['frm']),'to_xy':xy(leg['to']),'stop_min':None}
            for ab in leg['onboard']:
                onboard.append({'c':ab,'day':day,'leg':li,'mins':cm[ab],'note':ONB_NOTES.get(ab,f"{wh[ab][0]} → {wh[ab][1]}")})
            if out: out[-1]['stop_min']=int((c['dep']-prev_arr).total_seconds()//60)
            out.append(rec); prev_arr=c['arr']
            for s in c['trains']:
                paths.append('M'+' '.join(f"{p['xy'][0]},{p['xy'][1]}" for p in s['pass']))
            if leg['walk_after']:
                a=xy(leg['to']); b=xy(legs[li+1]['frm']); paths.append(f"M{a[0]},{a[1]} {b[0]},{b[1]}")
            tr=' + '.join(f"{t['train']}" for t in trains)
            print(f"D{day} {rec['dep']}→{rec['arr']} {leg['frm']}→{leg['to']} [{leg['canton'] or '-'}] {tr}  onboard={ {ab:cm.get(ab) for ab in leg['onboard']} }")
        days.append({'day':day,'date':date,'legs':out}); routes[str(day)]=''.join(paths)
        print(f"  day {day}: {out[0]['dep']}–{out[-1]['arr']}, stops:",[(l['to'],l['canton'],l['stop_min']) for l in out])
    return {'days':days,'routes':routes,'onboard':onboard}
PLAN_B=[
 (F,[
  L('Zürich HB','Schaffhausen','SH',note='beer #1 ZH at HB kiosk before departure',start='07:05'),
  L('Schaffhausen','Frauenfeld','TG'),
  L('Frauenfeld','St. Gallen','SG'),
  L('St. Gallen','Teufen AR','AR'),
  L('Teufen AR','Appenzell','AI'),
  L('Appenzell','Altstätten Stadt',None,note="rack railway down; walk 1.7 km (~25') to Altstätten SG",walk_after=40),
  L('Altstätten SG','Landquart','GR',note='turn around here — no detour to Chur'),
  L('Landquart','Ziegelbrücke','GL',note='walk over the Linth bridge into Glarus Nord'),
  L('Ziegelbrücke','Pfäffikon SZ','SZ'),
  L('Pfäffikon SZ','Luzern',None,direct=True,note='Voralpen-Express direct — change for the NW/OW loop'),
  L('Luzern','Hergiswil NW','NW'),
  L('Hergiswil NW','Sarnen','OW'),
  L('Sarnen','Luzern','LU',note='arrival beer — overnight Luzern'),
 ]),
 (SA,[
  L('Luzern','Flüelen','UR',start='07:00'),
  L('Flüelen','Airolo','TI',note='Treno Gottardo over the mountain line'),
  L('Airolo','Zug','ZG'),
  L('Zug','Zofingen','AG',note='via Luzern and Sursee — never through Zürich'),
  L('Zofingen','Olten','SO'),
  L('Olten','Liestal','BL'),
  L('Liestal','Basel SBB','BS'),
  L('Basel SBB','Delémont','JU'),
  L('Delémont','Biel/Bienne','BE'),
  L('Biel/Bienne','Neuchâtel','NE',note='arrival beer — overnight Neuchâtel'),
 ]),
 (SU,[
  L('Neuchâtel','Genève','GE',start='08:00',note='via Yverdon'),
  L('Genève','Lausanne','VD'),
  L('Lausanne','Martigny','VS'),
  L('Martigny','Fribourg/Freiburg','FR'),
  L('Fribourg/Freiburg','Zürich HB',None,note='home'),
 ]),
]
if __name__=='__main__':
    import sys
    which=sys.argv[1] if len(sys.argv)>1 else 'a'
    P=run(PLAN_A if which=='a' else PLAN_B)
    json.dump(P,open(f'plan_{which}.json','w'),ensure_ascii=False,indent=1)

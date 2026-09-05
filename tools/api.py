import json, os, urllib.request, urllib.parse, datetime, time, hashlib
from geo import to_svg, canton_of, coords
S=os.path.dirname(os.path.abspath(__file__))
CDIR=S+'/api_cache'; os.makedirs(CDIR,exist_ok=True)
TRAIN_CATS={'IC','IR','RE','S','R','VAE','PE','EXT','EC','ICE','TGV','RJ','RJX','NJ','SN','TER','ICN','IRE','RB','GEX','BEX','CJ','TE'}
def get(url):
    h=hashlib.md5(url.encode()).hexdigest(); f=f'{CDIR}/{h}.json'
    if os.path.exists(f): return json.load(open(f))
    for i in range(4):
        try:
            j=json.load(urllib.request.urlopen(url,timeout=40)); break
        except Exception as e:
            print('retry',e); time.sleep(3)
    json.dump(j,open(f,'w')); return j
def ts(s): return datetime.datetime.fromisoformat(s) if s else None
def hm(dt): return dt.strftime('%H:%M')
def raw_connections(frm,to,date,tm,via=None,direct=False,limit=6,page=0):
    q=[('from',frm),('to',to),('date',date),('time',tm),('limit',limit),('page',page),('transportations[]','train')]
    if via: q.append(('via[]',via))
    if direct: q.append(('direct',1))
    return get('https://transport.opendata.ch/v1/connections?'+urllib.parse.urlencode(q))['connections']
def parse(c):
    secs=[]
    for s in c['sections']:
        if not s.get('journey'): return None  # walk
        j=s['journey']; cat=j['category']
        if cat not in TRAIN_CATS: return None
        pl=[]
        for p in j['passList']:
            st=p['station']; co=st['coordinate']
            if co['x'] is None: continue
            a=ts(p.get('arrival')); d=ts(p.get('departure'))
            pl.append({'name':st['name'],'id':st.get('id'),'lat':co['x'],'lon':co['y'],'arr':a,'dep':d,'xy':to_svg(co['x'],co['y'])})
        # trim passList to this section's dep/arr stations
        dn=s['departure']['station']['name']; an=s['arrival']['station']['name']
        names=[p['name'] for p in pl]; pl_full=pl
        try: i0=names.index(dn); i1=names.index(an); pl=pl[i0:i1+1]
        except ValueError: pass
        secs.append({'train':(cat+' '+(j['number'] or '')).strip(),'cat':cat,'number':j['number'],'name':j['name'],'dir':j['to'],
            'dep_station':dn,'dep_time':hm(ts(s['departure']['departure'])),'dep_ts':ts(s['departure']['departure']),'dep_platform':s['departure']['platform'] or '',
            'arr_station':an,'arr_time':hm(ts(s['arrival']['arrival'])),'arr_ts':ts(s['arrival']['arrival']),'arr_platform':s['arrival']['platform'] or '','pass':pl,'pass_full':pl_full})
    dep=ts(c['from']['departure']); arr=ts(c['to']['arrival'])
    return {'from':c['from']['station']['name'],'to':c['to']['station']['name'],'from_id':c['from']['station']['id'],'to_id':c['to']['station']['id'],
            'dep':dep,'arr':arr,'duration_min':int((arr-dep).total_seconds()//60),'transfers':len(secs)-1,'trains':secs,
            'relief':any(s['number'] and len(str(s['number']).lstrip('0'))>=5 for s in secs)}
def connections(frm,to,date,tm,**kw):
    out=[]
    for c in raw_connections(frm,to,date,tm,**kw):
        p=parse(c)
        if p: out.append(p)
    return out
def canton_minutes(conn, samples=16):
    mins={}; where={}
    def add(ab,m,name):
        if not ab: return
        mins[ab]=mins.get(ab,0)+m
        w=where.setdefault(ab,[name,name]); w[1]=name
    for s in conn['trains']:
        pl=s['pass']
        for i in range(len(pl)):
            p=pl[i]
            # dwell
            if p['arr'] and p['dep']: add(canton_of(p['xy']),(p['dep']-p['arr']).total_seconds()/60,p['name'])
            if i+1<len(pl):
                q=pl[i+1]; t0=p['dep'] or p['arr']; t1=q['arr'] or q['dep']
                if not t0 or not t1: continue
                dt=(t1-t0).total_seconds()/60
                for k in range(samples):
                    f=(k+0.5)/samples
                    xy=(p['xy'][0]+(q['xy'][0]-p['xy'][0])*f, p['xy'][1]+(q['xy'][1]-p['xy'][1])*f)
                    add(canton_of(xy),dt/samples, p['name'] if f<0.5 else q['name'])
    return {k:round(v) for k,v in mins.items()}, where
def show(conns, want=None):
    for c in conns:
        cm,wh=canton_minutes(c)
        tr=' + '.join(f"{s['train']}({s['dep_station']} {s['dep_time']}→{s['arr_station']} {s['arr_time']})" for s in c['trains'])
        flag=' RELIEF' if c['relief'] else ''
        print(f"  {hm(c['dep'])}→{hm(c['arr'])} {c['duration_min']}′ x{c['transfers']}{flag} {tr}")
        keys=want or sorted(cm,key=lambda k:-cm[k])
        print('     ', {k:(cm.get(k,0),wh.get(k)) for k in keys if k in cm or want})

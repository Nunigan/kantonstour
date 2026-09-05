import json, datetime, sys
from api import connections, hm
from track import segment, simplify
import plan as P
def key(leg): return leg['frm'],leg['to']
def rebuild(plan_json, plan_def):
    d=json.load(open(plan_json)); stats={'real':0,'straight':0}
    lines={}
    for day,(date,legs) in zip(d['days'],plan_def):
        for leg,ld in zip(day['legs'],legs):
            cs=connections(ld['frm'],ld['to'],date,leg['dep'],via=ld['via'],direct=ld['direct'],limit=6)
            c=next((c for c in cs if hm(c['dep'])==leg['dep'] and hm(c['arr'])==leg['arr']),None)
            if c is None:
                for page in (0,1):
                    for cc in connections(ld['frm'],ld['to'],date,leg['dep'],via=ld['via'],direct=ld['direct'],limit=6,page=page):
                        if hm(cc['dep'])==leg['dep'] and hm(cc['arr'])==leg['arr']: c=cc
            assert c, (ld['frm'],ld['to'],leg['dep'])
            leg['geo']=[]
            for s,t in zip(c['trains'],leg['trains']):
                t['name']=s['name']; t['cat']=s['cat']; t['num']=str(s['number'] or '')
                pl=[p for p in s['pass'] if p['id'] and str(p['id']).startswith('85')]
                plf=[p for p in s['pass_full'] if p['id'] and str(p['id']).startswith('85')]
                path=[]
                lk=t['train']
                L=lines.setdefault(lk,{'order':[],'stations':{},'seg':{},'paths':[]})
                for p in plf:
                    if p['id'] not in L['stations']:
                        L['stations'][p['id']]=[round(p['lat'],5),round(p['lon'],5),p['name']]
                # station order along the full line (merge: keep existing order, insert new ones after their predecessor)
                for i,p in enumerate(plf):
                    if p['id'] not in L['order']:
                        prev=plf[i-1]['id'] if i>0 and plf[i-1]['id'] in L['order'] else None
                        L['order'].insert(L['order'].index(prev)+1 if prev else len(L['order']), p['id'])
                full=[]
                for p,q in zip(plf,plf[1:]):
                    k=f"{p['id']}|{q['id']}"
                    if k in L['seg']: ll=L['seg'][k]
                    else:
                        g=segment((p['lon'],p['lat']),(q['lon'],q['lat']))
                        if g: stats['real']+=1; g=simplify(g)
                        else: stats['straight']+=1; g=[[p['lon'],p['lat']],[q['lon'],q['lat']]]
                        ll=[[round(y,5),round(x,5)] for x,y in g]; L['seg'][k]=ll
                    full.extend(ll if not full else ll[1:])
                L['paths'].append(full)
                for p,q in zip(pl,pl[1:]):
                    k=f"{p['id']}|{q['id']}"; ll=L['seg'].get(k) or [[p['lat'],p['lon']],[q['lat'],q['lon']]]
                    path.extend(ll if not path else ll[1:])
                t['dep_id']=pl[0]['id'] if pl else None; t['arr_id']=pl[-1]['id'] if pl else None
                leg['geo'].append(path)
            leg['from_ll']=[round(c['trains'][0]['pass'][0]['lat'],5),round(c['trains'][0]['pass'][0]['lon'],5)]
            leg['to_ll']=[round(c['trains'][-1]['pass'][-1]['lat'],5),round(c['trains'][-1]['pass'][-1]['lon'],5)]
    # full extent of each line: station boards at our boarding/alighting stations, any train of that line, to its terminus
    from api import get
    import urllib.parse
    def norm(cat,num):
        num=str(num or '')
        return num.upper() if num.isalpha() else (cat+' '+num.lstrip('0')).strip()
    boards={}
    for lk,L in lines.items():
        L['paths']=[]
        ends=set()
        for day in d['days']:
            for leg in day['legs']:
                for t in leg['trains']:
                    if t['train']==lk:
                        for sid in (t.get('dep_id'),t.get('arr_id')):
                            if sid: ends.add(sid)
        runs={}
        for sid in ends:
            if sid not in boards:
                u='https://transport.opendata.ch/v1/stationboard?'+urllib.parse.urlencode([('station',sid),('limit',120),('transportations[]','train')])
                try: boards[sid]=get(u)
                except Exception as e: print('board fail',sid,e); boards[sid]={'stationboard':[]}
            j=boards[sid]
            for e in j.get('stationboard',[]):
                if norm(e['category'],e['number'])!=lk: continue
                st=[]
                for i,p in enumerate(e.get('passList',[])):
                    s=p.get('station') or {}
                    if i==0: s=j.get('station') or s
                    c=s.get('coordinate') or {}
                    if not s.get('id') or c.get('x') is None or not str(s['id']).startswith('85'): continue
                    st.append({'id':s['id'],'name':s.get('name'),'lat':c['x'],'lon':c['y']})
                if len(st)>=2:
                    key=(st[0]['id'],st[-1]['id'])
                    if key not in runs or len(st)>len(runs[key]): runs[key]=st
        for key,st in runs.items():
            for p in st:
                if p['id'] not in L['stations']: L['stations'][p['id']]=[round(p['lat'],5),round(p['lon'],5),p['name']]
            for i,p in enumerate(st):
                if p['id'] not in L['order']:
                    prev=st[i-1]['id'] if i>0 and st[i-1]['id'] in L['order'] else None
                    L['order'].insert(L['order'].index(prev)+1 if prev else len(L['order']), p['id'])
            full=[]
            for p,q in zip(st,st[1:]):
                k=f"{p['id']}|{q['id']}"; kr=f"{q['id']}|{p['id']}"
                if k in L['seg']: ll=L['seg'][k]
                elif kr in L['seg']: ll=L['seg'][kr][::-1]
                else:
                    gg=segment((p['lon'],p['lat']),(q['lon'],q['lat']))
                    if gg: stats['real']+=1; gg=simplify(gg)
                    else: stats['straight']+=1; gg=[[p['lon'],p['lat']],[q['lon'],q['lat']]]
                    ll=[[round(y,5),round(x,5)] for x,y in gg]; L['seg'][k]=ll
                full.extend(ll if not full else ll[1:])
            L['paths'].append(full)
        print(f"  {lk}: {len(runs)} runs, {len(L['order'])} stations, {len(L['seg'])} segments")
    d['lines']=lines
    json.dump(d,open(plan_json,'w'),ensure_ascii=False)
    print(plan_json,stats,'lines',list(lines))
if __name__=='__main__':
    which=sys.argv[1]
    rebuild(f'plan_{which}.json',P.PLAN_A if which=='a' else P.PLAN_B)

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
                path=[]
                lk=t['train']
                L=lines.setdefault(lk,{'order':[],'stations':{},'seg':{}})
                for p in pl:
                    if p['id'] not in L['stations']:
                        L['stations'][p['id']]=[round(p['lat'],5),round(p['lon'],5),p['name']]
                    if p['id'] not in L['order']: L['order'].append(p['id'])
                for p,q in zip(pl,pl[1:]):
                    g=segment((p['lon'],p['lat']),(q['lon'],q['lat']))
                    if g: stats['real']+=1; g=simplify(g)
                    else: stats['straight']+=1; g=[[p['lon'],p['lat']],[q['lon'],q['lat']]]
                    ll=[[round(y,5),round(x,5)] for x,y in g]
                    L['seg'][f"{p['id']}|{q['id']}"]=ll
                    path.extend(ll if not path else ll[1:])
                t['dep_id']=pl[0]['id'] if pl else None; t['arr_id']=pl[-1]['id'] if pl else None
                leg['geo'].append(path)
            leg['from_ll']=[round(c['trains'][0]['pass'][0]['lat'],5),round(c['trains'][0]['pass'][0]['lon'],5)]
            leg['to_ll']=[round(c['trains'][-1]['pass'][-1]['lat'],5),round(c['trains'][-1]['pass'][-1]['lon'],5)]
    d['lines']=lines
    json.dump(d,open(plan_json,'w'),ensure_ascii=False)
    print(plan_json,stats,'lines',list(lines))
if __name__=='__main__':
    which=sys.argv[1]
    rebuild(f'plan_{which}.json',P.PLAN_A if which=='a' else P.PLAN_B)

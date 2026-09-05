import json, math, os, heapq, numpy as np
S=os.path.dirname(os.path.abspath(__file__))
CX=111320*math.cos(math.radians(46.8)); CY=110540
def _xy(lon,lat): return np.array([lon*CX, lat*CY])
_L=None; _G=None
def load():
    global _L,_G
    if _L is not None: return _L
    g=json.load(open(S+'/sbb/linie-mit-polygon.geojson'))
    per={}
    for f in g['features']:
        p=f['properties']; per.setdefault(p['linienr'],[]).append((p['km_agm_von'],p['km_agm_bis'],f['geometry']['coordinates']))
    _L={}
    for ln,parts in per.items():
        parts.sort(key=lambda x:x[0]); pts=[]; off=parts[0][0]
        for _,_,c in parts:
            if pts:
                d0=np.linalg.norm(_xy(*pts[-1])-_xy(*c[0])); d1=np.linalg.norm(_xy(*pts[-1])-_xy(*c[-1]))
                if d1<d0: c=c[::-1]
            pts.extend(c)
        P=np.array(pts,dtype=float); XY=np.stack([P[:,0]*CX,P[:,1]*CY],1)
        seg=np.diff(XY,axis=0); L=np.hypot(seg[:,0],seg[:,1]); cum=np.concatenate([[0],np.cumsum(L)])+off
        _L[ln]={'ll':P,'xy':XY,'seg':seg,'len':L,'cum':cum,'lo':cum[0],'hi':cum[-1],
                'bx':(XY[:,0].min(),XY[:,0].max()),'by':(XY[:,1].min(),XY[:,1].max())}
    # graph of betriebspunkte
    bp=json.load(open(S+'/sbb/betriebspunkte.json'))
    nodes={}  # (line,s) -> node id
    _G={'adj':{},'pos':{}}
    byid={}
    for r in bp:
        if r.get('km') is None or r['linie'] not in _L or not r.get('geopos'): continue
        s=r['km']*1000.0; ln=r['linie']
        if s<_L[ln]['lo']-500 or s>_L[ln]['hi']+500: continue
        n=(ln,round(s,1)); _G['pos'][n]=s
        byid.setdefault(r.get('bpuic') or r.get('abkurzung_bpk'),[]).append(n)
    perline={}
    for (ln,s) in _G['pos']: perline.setdefault(ln,[]).append((s,(ln,s)))
    def add(a,b,w): _G['adj'].setdefault(a,[]).append((b,w)); _G['adj'].setdefault(b,[]).append((a,w))
    for ln,lst in perline.items():
        lst.sort()
        for (s1,n1),(s2,n2) in zip(lst,lst[1:]): add(n1,n2,s2-s1)
    for k,ns in byid.items():
        for i in range(len(ns)):
            for j in range(i+1,len(ns)): add(ns[i],ns[j],50.0)
    _G['perline']={ln:[x[1] for x in lst] for ln,lst in perline.items()}
    return _L
def _project(line,pt):
    XY,seg,L=line['xy'],line['seg'],line['len']
    v=pt-XY[:-1]; L2=np.maximum(L*L,1e-9)
    t=np.clip((v[:,0]*seg[:,0]+v[:,1]*seg[:,1])/L2,0,1)
    proj=XY[:-1]+seg*t[:,None]; d=np.hypot(proj[:,0]-pt[0],proj[:,1]-pt[1])
    i=int(np.argmin(d)); return d[i], line['cum'][i]+t[i]*L[i]
def _near_lines(pt,tol):
    out=[]
    for ln,line in load().items():
        if pt[0]<line['bx'][0]-tol or pt[0]>line['bx'][1]+tol or pt[1]<line['by'][0]-tol or pt[1]>line['by'][1]+tol: continue
        d,s=_project(line,pt)
        if d<=tol: out.append((ln,s,d))
    return out
def _slice(ln,a,b):
    line=load()[ln]; cum=line['cum']; lo,hi=min(a,b),max(a,b)
    def at(s):
        i=int(np.searchsorted(cum,s,side='right')-1); i=max(0,min(i,len(line['len'])-1))
        t=(s-cum[i])/(line['len'][i] or 1); p=line['ll'][i]+(line['ll'][i+1]-line['ll'][i])*t; return [float(p[0]),float(p[1])]
    mid=line['ll'][(cum>lo)&(cum<hi)]
    out=[at(lo)]+[[float(x),float(y)] for x,y in mid]+[at(hi)]
    return out if a<=b else out[::-1]
def segment(a,b,tol=350):
    """a,b=(lon,lat) -> [[lon,lat],...] along real tracks (multi-line Dijkstra) or None"""
    load(); pa=_xy(*a); pb=_xy(*b); straight=float(np.linalg.norm(pa-pb))
    na=_near_lines(pa,tol); nb=_near_lines(pb,tol)
    if not na or not nb: return None
    # direct single-line
    best=None
    for ln,sa,_ in na:
        for ln2,sb,_ in nb:
            if ln==ln2 and abs(sb-sa)<=straight*1.8+3000 and (best is None or abs(sb-sa)<best[0]): best=(abs(sb-sa),ln,sa,sb)
    if best: return _slice(best[1],best[2],best[3])
    # Dijkstra over betriebspunkt graph with virtual endpoints
    adj=_G['adj']; perline=_G['perline']
    def virtual(ln,s,tag):
        v=(ln,s,tag); lst=perline.get(ln,[])
        # neighbours: nearest bp before/after along the line
        before=[n for n in lst if n[1]<=s]; after=[n for n in lst if n[1]>s]
        nb=[]
        if before: nb.append((before[-1],s-before[-1][1]))
        if after: nb.append((after[0],after[0][1]-s))
        return v,nb
    src=[virtual(ln,s,'A') for ln,s,_ in na]; dst=[virtual(ln,s,'B') for ln,s,_ in nb]
    extra={}
    for v,nb in src+dst:
        extra[v]=nb
        for n,w in nb: extra.setdefault(n,[]).append((v,w))
    dist={}; prev={}; pq=[]
    for v,_ in src: dist[v]=0.0; heapq.heappush(pq,(0.0,v))
    targets={v for v,_ in dst}; found=None
    while pq:
        d,u=heapq.heappop(pq)
        if d>dist.get(u,1e18): continue
        if u in targets: found=u; break
        if d>straight*2.5+20000: break
        for n,w in adj.get(u,[])+extra.get(u,[]):
            nd=d+w
            if nd<dist.get(n,1e18): dist[n]=nd; prev[n]=u; heapq.heappush(pq,(nd,n))
    if not found: return None
    path=[found]
    while path[-1] in prev: path.append(prev[path[-1]])
    path=path[::-1]
    out=[]
    for u,v in zip(path,path[1:]):
        if u[0]!=v[0]: continue  # transfer between lines at same bp
        seg=_slice(u[0],u[1],v[1])
        out.extend(seg if not out else seg[1:])
    return out or None
def simplify(pts,tol_m=20):
    if len(pts)<3: return pts
    P=np.array(pts); XY=np.stack([P[:,0]*CX,P[:,1]*CY],1)
    keep=np.zeros(len(P),bool); keep[0]=keep[-1]=True
    stack=[(0,len(P)-1)]
    while stack:
        i,j=stack.pop()
        if j<=i+1: continue
        a=XY[i]; d=XY[j]-a; L2=max(float(d@d),1e-9)
        v=XY[i+1:j]-a; t=np.clip((v@d)/L2,0,1); perp=np.hypot(*(v-np.outer(t,d)).T)
        k=int(np.argmax(perp))
        if perp[k]>tol_m: keep[i+1+k]=True; stack+=[(i,i+1+k),(i+1+k,j)]
    return [[float(x),float(y)] for x,y in P[keep]]

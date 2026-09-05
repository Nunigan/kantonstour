import json, re, math, os, urllib.request, urllib.parse
S=os.path.dirname(os.path.abspath(__file__))
D=json.load(open(S+'/data_v4.json'))
M=D['map']

def wgs_to_lv95(lat, lon):
    # swisstopo approximate formulas
    phi=(lat*3600-169028.66)/10000; lam=(lon*3600-26782.5)/10000
    E=2600072.37+211455.93*lam-10938.51*lam*phi-0.36*lam*phi**2-44.54*lam**3
    N=1200147.07+308807.95*phi+3745.25*lam**2+76.63*phi**2-194.56*lam**2*phi+119.79*phi**3
    return E,N

def parse_paths(p):
    polys=[]
    for sub in re.split(r'M', p):
        sub=sub.strip().rstrip('Z').strip()
        if not sub: continue
        pts=[tuple(map(float,t.split(','))) for t in sub.split()]
        polys.append(pts)
    return polys
CANTONS={ab:parse_paths(p) for ab,p in M['cantons'].items()}

def pip(pt, poly):
    x,y=pt; inside=False; n=len(poly)
    for i in range(n):
        x1,y1=poly[i]; x2,y2=poly[(i+1)%n]
        if (y1>y)!=(y2>y):
            xi=x1+(y-y1)*(x2-x1)/(y2-y1)
            if xi>x: inside=not inside
    return inside
def canton_of(xy):
    for ab,polys in CANTONS.items():
        if any(pip(xy,p) for p in polys): return ab
    return None

_cache_file=S+'/coords_cache.json'
_cache=json.load(open(_cache_file)) if os.path.exists(_cache_file) else {}
def coords(name):
    if name in _cache: return _cache[name]
    u='https://transport.opendata.ch/v1/locations?'+urllib.parse.urlencode({'query':name,'type':'station'})
    j=json.load(urllib.request.urlopen(u,timeout=30))
    st=j['stations'][0]; c=st['coordinate']
    _cache[name]=[c['x'],c['y'],st['id'],st['name']]
    json.dump(_cache,open(_cache_file,'w'),ensure_ascii=False,indent=1)
    return _cache[name]

_fit_file=S+'/fit.json'
def fit():
    st=json.load(open(S+'/station_xy.json'))
    A=[];B=[]
    for n,xy in st.items():
        lat,lon,_,_=coords(n); E,N=wgs_to_lv95(lat,lon)
        A.append((E,N)); B.append(xy)
    # least squares x = a*E + b*N + c ; y = d*E + e*N + f
    import numpy as np
    X=np.array([[e,n,1] for e,n in A]); Y=np.array(B)
    coef,res,_,_=np.linalg.lstsq(X,Y,rcond=None)
    pred=X@coef; err=np.sqrt(((pred-Y)**2).sum(1))
    print('fit max err px',err.max().round(2),'mean',err.mean().round(2))
    for (n,xy),e in zip(st.items(),err):
        if e>3: print('  ',n,round(e,1))
    json.dump(coef.tolist(),open(_fit_file,'w'))
    return coef
def to_svg(lat,lon):
    coef=json.load(open(_fit_file))
    E,N=wgs_to_lv95(lat,lon)
    return [round(coef[0][0]*E+coef[1][0]*N+coef[2][0],1), round(coef[0][1]*E+coef[1][1]*N+coef[2][1],1)]

if __name__=='__main__':
    fit()
    st=json.load(open(S+'/station_xy.json'))
    for n in st:
        lat,lon,_,_=coords(n)
        print(n, canton_of(to_svg(lat,lon)), to_svg(lat,lon), st[n])

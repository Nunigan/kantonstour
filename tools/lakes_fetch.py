import json, urllib.request, urllib.parse, math, os
S=os.path.dirname(os.path.abspath(__file__))
q='''[out:json][timeout:120];
(
  relation["natural"="water"]["water"~"lake|reservoir"](45.75,5.85,47.9,10.6);
  way["natural"="water"]["water"~"lake|reservoir"](45.75,5.85,47.9,10.6);
);
out geom;'''
raw=S+'/sbb/lakes_raw.json'
if not os.path.exists(raw):
    r=urllib.request.urlopen(urllib.request.Request('https://overpass-api.de/api/interpreter',data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'kantonstour-build'}),timeout=300)
    open(raw,'wb').write(r.read())
d=json.load(open(raw))
def area_km2(ring):
    a=0
    for (x1,y1),(x2,y2) in zip(ring,ring[1:]+ring[:1]):
        a+=(x1*y2-x2*y1)
    cx=math.cos(math.radians(46.8))
    return abs(a)/2*111.32*cx*110.54
def stitch(ways):
    # ways: list of [(lon,lat),...] outer segments -> rings
    segs=[list(w) for w in ways if len(w)>1]; rings=[]
    while segs:
        ring=segs.pop(0)
        changed=True
        while changed and ring[0]!=ring[-1]:
            changed=False
            for i,s in enumerate(segs):
                if s[0]==ring[-1]: ring+=s[1:]; segs.pop(i); changed=True; break
                if s[-1]==ring[-1]: ring+=s[::-1][1:]; segs.pop(i); changed=True; break
                if s[-1]==ring[0]: ring=s[:-1]+ring; segs.pop(i); changed=True; break
                if s[0]==ring[0]: ring=s[::-1][:-1]+ring; segs.pop(i); changed=True; break
        rings.append(ring)
    return rings
lakes=[]
for el in d['elements']:
    name=el.get('tags',{}).get('name','')
    if el['type']=='way':
        ring=[(p['lon'],p['lat']) for p in el.get('geometry',[])]
        rings=[ring]
    else:
        outers=[[(p['lon'],p['lat']) for p in m.get('geometry',[])] for m in el.get('members',[]) if m.get('role')=='outer']
        rings=stitch(outers)
    for ring in rings:
        if len(ring)<4: continue
        a=area_km2(ring)
        if a>=1.5: lakes.append((a,name,ring))
lakes.sort(reverse=True)
print(len(lakes),'lakes ≥1.5 km²;', [ (round(a,1),n) for a,n,_ in lakes[:12]])
from track import simplify
out=[]
for a,n,ring in lakes:
    s=simplify([list(p) for p in ring],40)
    out.append([[round(y,4),round(x,4)] for x,y in s])
json.dump(out,open(S+'/sbb/lakes.json','w'),separators=(',',':'))
print('bytes',os.path.getsize(S+'/sbb/lakes.json'))

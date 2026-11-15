import sys,os,struct,collections,re
sys.path.insert(0,os.path.dirname(__file__))
def segs(d):
    i=2;out=[]
    while i<len(d) and d[i]==0xFF:
        m=d[i+1]
        if m in (0xDA,0xD9): break
        L=struct.unpack('>H',d[i+2:i+4])[0]; out.append((m,d[i+4:i+2+L])); i+=2+L
    return out
def tiff(b):
    E='<' if b[:2]==b'II' else '>'
    res={}
    def ifd(off,pre):
        n=struct.unpack(E+'H',b[off:off+2])[0]
        for k in range(n):
            e=off+2+12*k; tag,typ,cnt=struct.unpack(E+'HHI',b[e:e+8]); raw=b[e+8:e+12]
            sz={1:1,2:1,3:2,4:4,5:8,7:1,10:8}.get(typ,1)*cnt
            data=raw[:sz] if sz<=4 else b[struct.unpack(E+'I',raw)[0]:][:sz]
            if typ==2: v=data.rstrip(b'\0').decode('latin1')
            elif typ==3: v=struct.unpack(E+'%dH'%cnt,data)
            elif typ==4: v=struct.unpack(E+'%dI'%cnt,data)
            elif typ==5: t=struct.unpack(E+'%dI'%(2*cnt),data); v=tuple(round(t[j]/t[j+1],3) if t[j+1] else 0 for j in range(0,len(t),2))
            else: v=None
            res[pre+str(tag)]=v
            if tag==34665: ifd(v[0],'X')
    ifd(struct.unpack(E+'I',b[4:8])[0],'')
    return res
rows=[]
for f in sorted(os.listdir(sys.argv[1])):
    d=open(os.path.join(sys.argv[1],f),'rb').read(); ss=segs(d)
    r={'file':f}
    for m,b in ss:
        if m==0xE1 and b.startswith(b'Exif'):
            t=tiff(b[6:]); r.update(make=t.get('271'),w=t.get('256'),h=t.get('257'),bits=t.get('258'),ppi=t.get('282'),dto=t.get('X36867'),lens=t.get('X42036'),exp=t.get('X33434'),fn=t.get('X33437'),iso=t.get('X34855'),scanw=t.get('X256'))
        if m==0xE1 and b.startswith(b'http'):
            x=b.decode('utf8','replace'); r['fw']=bool(re.search('aux:Firmware',x)); r['xmpcreate']=re.search(r'xmp:CreateDate="([^"]+)',x) is not None or '<xmp:CreateDate>' in x
        if m==0xED: 
            mm=re.search(rb'8BIM\x04\x1a.{0,60}?\x00\x00\x00(.)((?:\x00[\x20-\x7e])+)',b,re.S); r['slice']=mm.group(2).decode('utf-16-be') if mm else None
        if m==0xE2 and b.startswith(b'ICC'): r['icc']='AdobeRGB' if b'Adobe RGB' in b else 'sRGB' if b'sRGB' in b else 'other'
    rows.append(r)
C=collections.Counter
print('make',C(r.get('make') for r in rows))
print('bits',C(r.get('bits') for r in rows)); print('ppi',C(r.get('ppi') for r in rows))
print('has DateTimeOriginal',C(bool(r.get('dto')) for r in rows)); print('has lens',C(bool(r.get('lens')) for r in rows))
print('has exposure (phase)',C((r.get('make'),bool(r.get('exp'))) for r in rows))
print('has i2s full-scan dims',C((r.get('make'),bool(r.get('scanw'))) for r in rows))
print('has source width',C(bool(r.get('w')) for r in rows))
print('slice name',C(bool(r.get('slice')) for r in rows), [r.get('slice') for r in rows[:3]])
print('icc',C(r.get('icc') for r in rows))
for r in rows:
    if not r.get('make') or r.get('icc')!='AdobeRGB': print('OUTLIER',r)

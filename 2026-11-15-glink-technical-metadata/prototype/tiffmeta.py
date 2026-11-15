"""Parse TIFF metadata from a sparse buffer (head+tail ranges) or a full buffer."""
import struct, re
TS={1:1,2:1,3:2,4:4,5:8,6:1,7:1,8:2,9:4,10:8,11:4,12:8,13:4}
class Sparse:
    def __init__(self,chunks,size): self.chunks=chunks; self.size=size; self.missing=[]
    def read(self,off,n):
        for start,data in self.chunks:
            if start<=off and off+n<=start+len(data): return data[off-start:off-start+n]
        self.missing.append((off,n)); return None
def sparse_from_s3(head,tail,size): return Sparse([(0,head),(size-len(tail),tail)],size)
def full(buf): return Sparse([(0,buf)],len(buf))
def parse(src):
    E='<' if src.read(0,2)==b'II' else '>'
    off=struct.unpack(E+'I',src.read(4,4))[0]
    ifds=[]
    def rd(off):
        n=struct.unpack(E+'H',src.read(off,2))[0]; d={}
        for i in range(n):
            tag,typ,cnt=struct.unpack(E+'HHI',src.read(off+2+12*i,8)); raw=src.read(off+10+12*i,4)
            sz=TS.get(typ,1)*cnt
            data=raw[:sz] if sz<=4 else src.read(struct.unpack(E+'I',raw)[0],sz)
            if data is None: d[tag]=None; continue
            if typ==2: v=data.rstrip(b'\0').decode('latin1').strip()
            elif typ==3: v=struct.unpack(E+'%dH'%cnt,data)
            elif typ in(4,13): v=struct.unpack(E+'%dI'%cnt,data)
            elif typ in(5,10): v=struct.unpack(E+'%d%s'%(2*cnt,'I' if typ==5 else 'i'),data); v=tuple((v[i],v[i+1]) for i in range(0,len(v),2))
            else: v=data
            if isinstance(v,tuple) and len(v)==1 and tag not in (258,): v=v[0]
            d[tag]=v
        nxt=struct.unpack(E+'I',src.read(off+2+12*n,4))[0]
        return d,nxt
    i=0
    while off and i<5:
        d,off=rd(off); ifds.append(d); i+=1
    exif=rd(ifds[0][34665])[0] if 34665 in ifds[0] else {}
    return {'E':E,'ifd0':ifds[0],'ifds':ifds,'exif':exif,'missing':src.missing}
def rat(v): return v[0]/v[1] if v and v[1] else None
def icc_info(b):
    if not b: return {}
    out={'icc_size':len(b)}
    n=struct.unpack('>I',b[128:132])[0]
    for i in range(n):
        sig,o,l=struct.unpack('>4sII',b[132+12*i:144+12*i]); t=b[o:o+l]
        if sig in(b'desc',b'cprt'):
            if t[:4]==b'desc': s=t[12:12+struct.unpack('>I',t[8:12])[0]].rstrip(b'\0').decode('latin1')
            elif t[:4]==b'text': s=t[8:].rstrip(b'\0').decode('latin1')
            elif t[:4]==b'mluc':
                c,rs=struct.unpack('>II',t[8:16]); ln,of=struct.unpack('>II',t[20:28]); s=t[of:of+ln].decode('utf-16-be')
            else: s=repr(t[:20])
            out['icc_'+sig.decode()]=s
    return out
def ps_resources(b):
    res={}; i=0
    while b and i+12<=len(b) and b[i:i+4]==b'8BIM':
        rid=struct.unpack('>H',b[i+4:i+6])[0]; nl=b[i+6]; nlen=nl+1; nlen+=nlen%2
        p=i+6+nlen; sz=struct.unpack('>I',b[p:p+4])[0]; res[rid]=b[p+4:p+4+sz]; i=p+4+sz+(sz%2)
    return res
def slice_name(r):
    b=r.get(1050)
    if not b: return None
    try:
        # version(4) bounds(16) name: unicode string (len4 + utf16)
        n=struct.unpack('>I',b[20:24])[0]; return b[24:24+2*n].decode('utf-16-be')
    except Exception: return None
def xmp_get(x,name):
    if not x: return None
    m=re.search(r'%s="([^"]*)"'%re.escape(name),x) or re.search(r'<%s>([^<]*)</%s>'%(re.escape(name),re.escape(name)),x)
    return m.group(1) if m else None

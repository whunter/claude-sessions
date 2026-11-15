import sys,struct,os,collections
def segs(p):
    d=open(p,'rb').read(); i=2; out=[]
    while i<len(d) and d[i]==0xFF:
        m=d[i+1]
        if m==0xDA or m==0xD9: 
            break
        L=struct.unpack('>H',d[i+2:i+4])[0]; out.append((m,d[i+4:i+2+L])); i+=2+L
    return out,d
mode=sys.argv[1]
if mode=='one':
    out,d=segs(sys.argv[2])
    for m,b in out:
        tag=b[:30].split(b'\0')[0]
        print(hex(m),len(b),tag)
        if m==0xC0 or m==0xC2: print('  SOF bits',b[0],'h',struct.unpack('>H',b[1:3])[0],'w',struct.unpack('>H',b[3:5])[0],'comps',b[5])
        if m==0xE0 and b.startswith(b'JFIF'): print('  JFIF density unit',b[7],struct.unpack('>HH',b[8:12]))
        if m==0xE1 and b.startswith(b'Exif'): open(sys.argv[3],'wb').write(b[6:])
        if m==0xE1 and b.startswith(b'http'): print(b.decode('utf8','replace')[:3000])
        if m==0xE2 and b.startswith(b'ICC_PROFILE'): print('  ICC desc present', b'Adobe RGB' in b, b'sRGB' in b)
        if m==0xFE: print('  COM',b[:200])
else:
    c=collections.Counter()
    for f in sorted(os.listdir(sys.argv[2])):
        out,d=segs(os.path.join(sys.argv[2],f))
        kinds=[]
        for m,b in out:
            if m==0xE1 and b.startswith(b'Exif'): kinds.append('EXIF')
            elif m==0xE1: kinds.append('XMP')
            elif m==0xE2 and b.startswith(b'ICC'): kinds.append('ICC-'+('AdobeRGB' if b'Adobe RGB' in b else 'sRGB' if b'sRGB' in b else 'other'))
            elif m==0xED: kinds.append('IPTC/PS')
            elif m==0xFE: kinds.append('COM')
        c[tuple(kinds)]+=1
    print(c)

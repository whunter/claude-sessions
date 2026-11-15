import sys,os,json,struct,re
sys.path.insert(0,os.path.dirname(__file__)); import tiffmeta as T
def jpeg_parts(d):
    i=2; exif=xmp=None; ps=b''; icc=[]; sof=None
    while i<len(d) and d[i]==0xFF:
        m=d[i+1]
        if m in(0xDA,0xD9): break
        L=struct.unpack('>H',d[i+2:i+4])[0]; p=d[i+4:i+2+L]
        if m==0xE1 and p[:6]==b'Exif\0\0': exif=p[6:]
        elif m==0xE1 and p.startswith(b'http://ns.adobe.com/xap/1.0/\0'): xmp=p[29:]
        elif m==0xED and p.startswith(b'Photoshop 3.0\0'): ps+=p[14:]
        elif m==0xE2 and p.startswith(b'ICC_PROFILE\0'): icc.append((p[12],p[14:]))
        elif m in(0xC0,0xC1,0xC2): sof=struct.unpack('>HH',p[1:5])[::-1]
        i+=2+L
    return exif,xmp,ps,b''.join(x for _,x in sorted(icc)),sof
def fields(meta,xmp,psres,icc):
    d=meta['ifd0']; x=meta['exif']; X=(xmp or b'').decode('utf-8','replace')
    g=T.xmp_get
    hist=re.findall(r'<stEvt:action>([^<]*)</stEvt:action>.*?<stEvt:when>([^<]*)</stEvt:when>(?:.*?<stEvt:softwareAgent>([^<]*)</stEvt:softwareAgent>)?',X,re.S)
    f={
     'width':d.get(256),'height':d.get(257),'bps':d.get(258),'compression':d.get(259),'photometric':d.get(262),
     'orientation':d.get(274),'spp':d.get(277),'planar':d.get(284),'xres':T.rat(d.get(282)),'yres':T.rat(d.get(283)),'resunit':d.get(296),
     'make':d.get(271),'model':d.get(272),'software':d.get(305),'datetime':d.get(306),
     'exposure_time':x.get(33434),'fnumber':x.get(33437),'iso':x.get(34855),'program':x.get(34850),'bias':x.get(37380),
     'metering':x.get(37383),'lightsource':x.get(37384),'wb':x.get(41987),'focal':x.get(37386),'fpxres':x.get(41486),'fpunit':x.get(41488),
     'sensing':x.get(41495),'unique_id':x.get(42016),'body_serial':x.get(42033),'lensspec':x.get(42034),'lensmodel':x.get(42036),'lensserial':x.get(42037),
     'dto':x.get(36867),'colorspace':x.get(40961),'pixelx':x.get(40962),'pixely':x.get(40963),
     'cap_w':x.get(256),'cap_h':x.get(257),'cap_res':T.rat(x.get(282)),'cap_sw':x.get(305),'cap_dt':x.get(306),
     'ucm':x.get(50708),'t50709':x.get(50709),'cam_serial':x.get(50735),
     'firmware':g(X,'aux:Firmware'),'image_number':g(X,'aux:ImageNumber'),'xmp_serial':g(X,'aux:SerialNumber'),
     'document_id':g(X,'xmpMM:DocumentID'),'modify_date':g(X,'xmp:ModifyDate'),'color_mode':g(X,'photoshop:ColorMode'),
     'creator_tool':g(X,'xmp:CreatorTool'),'derived_from':g(X,'stRef:documentID'),
     'history':'; '.join(f'{a} {w} {s}'.strip() for a,w,s in hist) or None,
     'slice_name':T.slice_name(psres),'ps_thumb':1036 in psres,
     'ifd1_thumb':(lambda i1:(i1.get(256),i1.get(257)) if i1 else None)(meta['ifds'][1] if len(meta['ifds'])>1 else None),
    }
    for k,v in T.icc_info(icc).items(): f[k]=v
    for k in ('xres','yres','cap_res'):
        if f[k] is not None: f[k]=round(f[k],4)
    return f
def from_s3(hdrdir,i):
    h=json.load(open(f'{hdrdir}/{i}.json'))
    src=T.sparse_from_s3(open(f'{hdrdir}/{i}.head.bin','rb').read(),open(f'{hdrdir}/{i}.tail.bin','rb').read(),h['ContentLength'])
    m=T.parse(src); d=m['ifd0']
    f=fields(m,d.get(700),T.ps_resources(d.get(34377) or b''),d.get(34675))
    f['exif_icc']=T.icc_info(m['exif'].get(34675)).get('icc_desc')
    f['size']=h['ContentLength']; f['etag_md5']=h['ETag'].strip('"'); f['crc64nvme']=h.get('ChecksumCRC64NVME'); f['s3_key']=h['Key']; f['s3_lastmod']=h['LastModified']
    f['missing']=m['missing']; f['big_endian']=m['E']=='>'
    return f
def from_jpg(path):
    d=open(path,'rb').read(); exif,xmp,ps,icc,sof=jpeg_parts(d)
    m=T.parse(T.full(exif))
    f=fields(m,xmp,T.ps_resources(ps),icc)
    f['exif_icc']=T.icc_info(m['exif'].get(34675)).get('icc_desc')
    f['jpg_dims']=sof; f['jpg_size']=len(d)
    return f

import struct, sys
TAGS={254:'NewSubfileType',256:'ImageWidth',257:'ImageLength',258:'BitsPerSample',259:'Compression',262:'Photometric',270:'ImageDescription',271:'Make',272:'Model',273:'StripOffsets',274:'Orientation',277:'SamplesPerPixel',278:'RowsPerStrip',279:'StripByteCounts',282:'XResolution',283:'YResolution',284:'PlanarConfig',296:'ResolutionUnit',305:'Software',306:'DateTime',315:'Artist',316:'HostComputer',317:'Predictor',318:'WhitePoint',319:'PrimaryChromaticities',322:'TileWidth',323:'TileLength',324:'TileOffsets',325:'TileByteCounts',330:'SubIFDs',338:'ExtraSamples',339:'SampleFormat',700:'XMP',33432:'Copyright',33723:'IPTC',34377:'Photoshop',34665:'ExifIFD',34675:'ICCProfile',34853:'GPSIFD',
33434:'ExposureTime',33437:'FNumber',34850:'ExposureProgram',34855:'ISO',34864:'SensitivityType',36864:'ExifVersion',36867:'DateTimeOriginal',36868:'DateTimeDigitized',36880:'OffsetTime',37377:'ShutterSpeedValue',37378:'ApertureValue',37380:'ExposureBias',37381:'MaxAperture',37383:'MeteringMode',37384:'LightSource',37385:'Flash',37386:'FocalLength',37500:'MakerNote',37510:'UserComment',37520:'SubSecTime',37521:'SubSecTimeOriginal',40960:'FlashpixVersion',40961:'ColorSpace',40962:'PixelXDimension',40963:'PixelYDimension',41486:'FocalPlaneXRes',41487:'FocalPlaneYRes',41488:'FocalPlaneResUnit',41495:'SensingMethod',41728:'FileSource',41729:'SceneType',41985:'CustomRendered',41986:'ExposureMode',41987:'WhiteBalance',41988:'DigitalZoom',41989:'FocalLen35mm',41990:'SceneCaptureType',42016:'ImageUniqueID',42032:'CameraOwner',42033:'BodySerialNumber',42034:'LensSpecification',42035:'LensMake',42036:'LensModel',42037:'LensSerialNumber',50706:'DNGVersion',50708:'UniqueCameraModel',50735:'CameraSerialNumber',37399:'SensingMethod2',41483:'ExposureIndex'}
TS={1:1,2:1,3:2,4:4,5:8,6:1,7:1,8:2,9:4,10:8,11:4,12:8,16:8,17:8,18:8}
def run(path):
    f=open(path,'rb'); bo=f.read(2); E='<' if bo==b'II' else '>'
    magic=struct.unpack(E+'H',f.read(2))[0]
    big = magic==43
    if big:
        f.read(4); off=struct.unpack(E+'Q',f.read(8))[0]
    else: off=struct.unpack(E+'I',f.read(4))[0]
    print('byteorder',bo,'bigtiff',big)
    blobs={}
    def rd_ifd(off,name,depth=0):
        f.seek(off)
        n=struct.unpack(E+('Q' if big else 'H'),f.read(8 if big else 2))[0]
        ents=[]
        for i in range(n):
            if big: tag,typ,cnt=struct.unpack(E+'HHQ',f.read(12)); raw=f.read(8)
            else: tag,typ,cnt=struct.unpack(E+'HHI',f.read(8)); raw=f.read(4)
            ents.append((tag,typ,cnt,raw))
        nxt=struct.unpack(E+('Q' if big else 'I'),f.read(8 if big else 4))[0]
        print(f'--- {name} @ {off} ({n} entries) next={nxt}')
        subs=[]
        for tag,typ,cnt,raw in ents:
            sz=TS.get(typ,1)*cnt
            if sz<=len(raw): data=raw[:sz]
            else:
                p=struct.unpack(E+('Q' if big else 'I'),raw)[0]; cur=f.tell(); f.seek(p); data=f.read(sz); f.seek(cur)
            nm=TAGS.get(tag,str(tag))
            if typ==2: val=data.rstrip(b'\0').decode('latin1')
            elif typ in (7,1) and cnt>16: val=f'<{cnt} bytes>'; blobs[nm]=data
            elif typ==3: val=struct.unpack(E+'%dH'%cnt,data)
            elif typ==4 or typ==13: val=struct.unpack(E+'%dI'%cnt,data)
            elif typ==16: val=struct.unpack(E+'%dQ'%cnt,data)
            elif typ==5: v=struct.unpack(E+'%dI'%(2*cnt),data); val=[f'{v[i]}/{v[i+1]}' for i in range(0,len(v),2)]
            elif typ==10: v=struct.unpack(E+'%di'%(2*cnt),data); val=[f'{v[i]}/{v[i+1]}' for i in range(0,len(v),2)]
            elif typ==8: val=struct.unpack(E+'%dh'%cnt,data)
            elif typ==11: val=struct.unpack(E+'%df'%cnt,data)
            elif typ==12: val=struct.unpack(E+'%dd'%cnt,data)
            else: val=data
            if tag in (700,33723,34377,34675,37500): blobs[nm]=data; val=f'<{len(data)} bytes>'
            if isinstance(val,tuple) and len(val)>8: val=f'{val[:4]}... ({len(val)} vals)'
            print(f'  {tag:5d} {nm}: {val}')
            if tag in (34665,34853): subs.append((val[0],nm))
            if tag==330: subs += [(v,'SubIFD') for v in (val if isinstance(val,tuple) else [])]
        for o,nmm in subs: rd_ifd(o,nmm,depth+1)
        return nxt
    i=0
    while off and i<10:
        off=rd_ifd(off,f'IFD{i}'); i+=1
    return blobs
if __name__=='__main__':
    import os,pickle
    b=run(sys.argv[1])
    out=sys.argv[2]; os.makedirs(out,exist_ok=True)
    for k,v in b.items(): open(os.path.join(out,k+'.bin'),'wb').write(v)

import sys,os,pickle,csv,collections,json,base64
S3,J=pickle.load(open(sys.argv[1],'rb')); OUT=sys.argv[2]; SRCOUT=sys.argv[3]
D={r['identifier']:r for r in csv.DictReader(open('/Users/whunter/dev/dlp/assets/glink/docs/20261109_glink_consolidation_archive_metadata.csv',encoding='utf-8-sig'))}
COLS=open('/Users/whunter/dev/dlp/assets/glink/technical_meta/technical_metadata.csv').readline().strip().split(',')
COLS.insert(COLS.index('file_size_bytes')+1,'md5_checksum'); COLS.insert(COLS.index('md5_checksum')+1,'s3_crc64nvme_checksum')
COLS.insert(COLS.index('md5_checksum')+2,'s3_uri')
COLS.insert(COLS.index('associated_object_identifier')+1,'sequence_number')
COLS.append('technical_notes')
used=collections.defaultdict(collections.Counter)   # column -> Counter(source)
def rat(t): return t[0]/t[1]
def fmt_exp(t):
    if t is None: return 'Not recorded'
    v=rat(t); return f'1/{round(1/v)} s' if v<1 and abs(1/v-round(1/v))<0.01 else f'{v:g} s'
PROG={1:'1 (Manual)',2:'2 (Program AE)'}; METER={1:'1 (Average)',2:'2 (Center-weighted)',3:'3 (Spot)'}
rows=[]
for i in sorted(S3):
    s,j=S3[i],J[i]; item=i[:11]; d=D[item]; P=s['make']=='Phase One'
    def g(k,col):
        """Use derivative value only when it equals the S3 original; otherwise S3."""
        if s.get(k) is None and j.get(k) is None: return None
        if j.get(k)==s.get(k): used[col]['derivative (verified = S3 TIFF)']+=1; return j[k]
        used[col]['S3 TIFF header']+=1; return s.get(k)
    def s3(k,col): used[col]['S3 TIFF header / HEAD']+=1; return s.get(k)
    def doc(col,src,v): used[col][src]+=1; return v
    r={}
    w,h=g('width','pixel_width_px'),g('height','pixel_height_px'); bps=g('bps','bits_per_sample'); ppi=g('xres','resolution_ppi'); g('yres','resolution_ppi')
    r['file_name']=i+'.tif'
    sl=s3('slice_name','original_capture_file_name'); r['original_capture_file_name']=sl if sl and sl!=i else ''
    r['associated_object_identifier']=item; r['sequence_number']=int(i[11:])
    r['object_title']=doc('object_title','descriptive CSV',d['title'])
    r['file_size_bytes']=s3('size','file_size_bytes')
    r['md5_checksum']=s3('etag_md5','md5_checksum'); r['s3_crc64nvme_checksum']=s3('crc64nvme','s3_crc64nvme_checksum')
    r['s3_uri']='s3://ingest-dev-vtlib-store/'+s3('s3_key','s3_uri')
    r['file_format']='TIFF (baseline, '+('big-endian / Motorola' if s['big_endian'] else 'little-endian / Intel')+' byte order)'
    c=g('compression','compression'); r['compression']='None (uncompressed)' if c==1 else str(c)
    t=s3('ifd1_thumb','embedded_thumbnail')
    if t: r['embedded_thumbnail']=f'{t[0]} x {t[1]} px, 8-bit RGB (IFD1)'
    elif s3('ps_thumb','embedded_thumbnail'): r['embedded_thumbnail']='Photoshop JPEG thumbnail (image resource 1036)'
    else: r['embedded_thumbnail']='None'
    r['pixel_width_px'],r['pixel_height_px']=w,h; r['megapixels']=round(w*h/1e6,2)
    o=g('orientation','orientation'); r['orientation']='1 (normal)' if o==1 else str(o)
    r['bits_per_sample']=','.join(map(str,bps)); r['total_bit_depth']=f'{sum(bps)}-bit RGB'
    r['samples_per_pixel']=g('spp','samples_per_pixel')
    r['photometric_interpretation']={2:'RGB'}.get(g('photometric','photometric_interpretation'))
    r['planar_configuration']={1:'Chunky (interleaved)',2:'Planar'}.get(g('planar','planar_configuration'))
    assert g('resunit','resolution_ppi')==2
    r['resolution_ppi']=f'{ppi:g}'; r['physical_size_of_image_area_in']=f'{w/ppi:.2f} x {h/ppi:.2f}'
    r['icc_profile']=g('icc_desc','icc_profile'); r['icc_profile_copyright_string']=g('icc_cprt','icc_profile_copyright_string'); g('icc_size','icc_profile_copyright_string')
    cs=g('colorspace','exif_color_space'); r['exif_color_space']={65535:'65535 (Uncalibrated)',1:'1 (sRGB)'}.get(cs,'(not set)')
    cm=g('color_mode','photoshop_color_mode'); r['photoshop_color_mode']=f'{cm} (RGB)' if cm=='3' else ''
    r['color_target_id']=doc('color_target_id','descriptive CSV (capture_target)',d['capture_target'])
    r['target_aim_values']=doc('target_aim_values','scanning guide','White 242, Gray 160, Black 52 (+/- 5)')
    r['capture_person']=doc('capture_person','descriptive CSV',d['capture_person'])
    r['capture_standard']=doc('capture_standard','scanning guide','FADGI (star level not stated)')
    r['device_label_in_descriptive_metadata']=doc('device_label_in_descriptive_metadata','descriptive CSV',d['capture_device'])
    mk=g('make','make'); md=g('model','model')
    notes=[]
    if P:
        fw=g('firmware','firmware'); lm=g('lensmodel','lens_model'); ls=g('lensserial','lens_serial_number'); spec=g('lensspec','lens_specification')
        fl=rat(g('focal','focal_length_mm')); fp=rat(g('fpxres','sensor_pixel_pitch_um')); assert g('fpunit','sensor_pixel_pitch_um')==3
        g('sensing','sensor_type')
        r.update({'device_type':'Camera (digital back + lens on copy stand)','make':mk,'model':f'{md} (IQ3 100MP Trichromatic)',
          'camera_head_sensor_unit':'IQ3 100MP Trichromatic digital back','body_camera_serial_number':g('body_serial','body_camera_serial_number'),
          'firmware':fw.split('Firmware: ')[-1]+' (Factory Firmware)','sensor_type':'Single-chip color area sensor (CMOS)',
          'sensor_pixel_pitch_um':f'{10000/fp:.1f}','native_sensor_resolution_px':'11608 x 8708 (101 MP)',
          'lens_model':lm,'lens_serial_number':ls,
          'lens_specification':f'{rat(spec[0]):g} mm, max aperture f/{rat(spec[3]):.1f}'.replace('.0,',',').replace('f/4.0','f/4')+f', min aperture f/{rat(spec[2]):g}',
          'focal_length_mm':f'{fl:g}','reproduction_ratio':(lambda m:f'{m:.3f}x (about 1:{round(1/m)})')((ppi/25.4)/(fp/10)),
          'exposure_time':fmt_exp(g('exposure_time','exposure_time')),'aperture':f"f/{rat(g('fnumber','aperture')):g}",'iso':g('iso','iso'),
          'exposure_program':PROG.get(g('program','exposure_program')),'exposure_bias':f"{rat(g('bias','exposure_bias')):g} EV",
          'metering_mode':METER.get(g('metering','metering_mode')),'light_source':{0:'0 (Unknown)'}.get(g('lightsource','light_source')),
          'white_balance':{0:'0 (Auto, as tagged)',1:'1 (Manual)'}.get(g('wb','white_balance')),
          'camera_image_number':g('image_number','camera_image_number'),'image_unique_id':g('unique_id','image_unique_id'),
          'capture_software':'Capture One 22 (Windows)' if g('software','capture_software')=='Capture One 22 Windows' else s['software'],
          'post_processing_software':'None recorded (exported directly from Capture One)','original_capture_dimensions_px':'',
          'last_modified_date_time':'','photoshop_document_id':''})
        g('xmp_serial','body_camera_serial_number'); g('creator_tool','capture_software')
        if lm and '45mm' in lm: notes.append('45 mm lens is not listed in the scanning guide (guide lists only the 120 mm Macro LS)')
    else:
        g('ucm','camera_head_sensor_unit'); g('t50709','camera_head_sensor_unit'); g('creator_tool','post_processing_software')
        cw,ch,cr=g('cap_w','original_capture_dimensions_px'),g('cap_h','original_capture_dimensions_px'),g('cap_res','original_capture_dimensions_px')
        nr='Not recorded'
        r.update({'device_type':'Large-format flatbed scanner (A0)','make':mk,'model':md.split(' [')[0],'camera_head_sensor_unit':s['ucm'],
          'body_camera_serial_number':f"{g('cam_serial','body_camera_serial_number')} (Quartz HD head)",
          'firmware':doc('firmware','scanning guide','0.02'),'sensor_type':nr,'sensor_pixel_pitch_um':nr,'native_sensor_resolution_px':nr,
          'lens_model':doc('lens_model','scanning guide','135 mm (make/model not recorded)'),'lens_serial_number':nr,'lens_specification':'',
          'focal_length_mm':doc('focal_length_mm','scanning guide','135'),'reproduction_ratio':'',
          'exposure_time':nr,'aperture':nr,'iso':nr,'exposure_program':nr,'exposure_bias':nr,'metering_mode':nr,'light_source':nr,'white_balance':nr,
          'camera_image_number':'','image_unique_id':'','capture_software':'i2S '+g('cap_sw','capture_software'),
          'post_processing_software':g('software','post_processing_software'),
          'original_capture_dimensions_px':f'{cw} x {ch} at {cr:g} ppi ({cw/cr:.2f} x {ch/cr:.2f} in)',
          'last_modified_date_time':s3('modify_date','last_modified_date_time'),'photoshop_document_id':s3('document_id','photoshop_document_id')})
        s3('datetime','last_modified_date_time'); s3('history','last_modified_date_time')
    dto=g('dto','capture_date_time'); r['capture_date_time']=dto[:10].replace(':','-')+'T'+dto[11:]+' (no time zone)'
    # date sanity checks against descriptive metadata
    import datetime as DT
    cap=DT.datetime.strptime(dto,'%Y:%m:%d %H:%M:%S'); local=(cap-DT.timedelta(hours=5)) if P else cap
    if local.date().isoformat()!=d['capture_date']:
        notes.append(f"Capture date in file ({local.date().isoformat()}{' local, assuming UTC camera clock' if P else ''}) differs from descriptive capture_date {d['capture_date']}; color target {d['capture_target']} may not match this session")
    r['technical_notes']='; '.join(notes)
    rows.append(r)
with open(OUT,'w',newline='') as f:
    wr=csv.DictWriter(f,COLS); wr.writeheader(); [wr.writerow(x) for x in rows]
json.dump({k:dict(v) for k,v in used.items()},open(SRCOUT,'w'),indent=1)
print(len(rows),'rows',len(COLS),'cols'); print(collections.Counter(r['technical_notes'][:60] for r in rows))

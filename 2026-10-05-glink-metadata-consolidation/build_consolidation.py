import sys,json,csv,re,collections,datetime
S=sys.argv[1]; D='/Users/whunter/dev/dlp/assets/glink'
def rd(p): return list(csv.DictReader(open(p,newline='',encoding='utf-8-sig')))
full=rd(f'{D}/docs/glink_scanning_guide_.csv')      # most complete guide
mid=rd(f'{D}/docs/glink_scanning_guide.csv'); old=rd(f'{D}/glink_scanning_guide.csv')
tmpl={r['identifier'] for r in rd(f'{D}/glink_template_archive_metadata.csv')}
dyn={i['identifier']:i for i in json.load(open(f'{S}/arch_scan_plain.json'))}
man=json.load(open(f'{S}/man_dims.json'))
# cross-check the three guide versions agree on shared descriptive fields
chk=0
for name,other in (('docs/glink_scanning_guide.csv',mid),('glink_scanning_guide.csv',old)):
    fi=[r for r in full if r['Title'] not in('s7','s8','s9','s10')]
    for a,b in zip(fi,other):
        for c in ('Format','Title','Width','Height','Medium','Notes'):
            if a[c].strip()!=b[c].strip(): chk+=1; print('GUIDE DIFF',name,a['Title'],c,repr(a[c]),repr(b[c]))
print('descriptive diffs between guide versions:',chk)
tif=collections.defaultdict(list)
for l in open(f'{D}/done.txt'):
    m=re.search(r'(lgpst\S+\.tif)\s*$',l)
    if not m: continue
    f=m.group(1)
    k='lgpst002129' if 'windmill' in f else f[:11]
    tif[k].append(f)
iso=lambda d: datetime.datetime.strptime(d,'%m/%d/%Y').strftime('%Y-%m-%d') if d else ''
cols=['identifier','source_identifier','sticker_identifier','title','description','alt_text','visual_description','format','medium','width_in','height_in','page_count','page1_width_px','page1_height_px','project','volume','capture_person','capture_date','capture_device','capture_target','sensitive_content','content_note','handling_notes','source_tiff_files','ark','dynamo_id','dynamo_title','manifest_url','thumbnail_path','in_dynamo','in_s3','in_template_csv','guide_count','consolidation_notes']
out=[]; sb=0
for r in full:
    notes=[]
    if r['Format']=='sketchbook':
        sb+=1; src=r['Identifier'] or f'lgpst001{sb:03d}'
        if not r['Identifier']: notes.append(f'Guide has no identifier for {r["Title"]}; assigned {src} by sketchbook sequence, matching the S3/Dynamo record')
        title=f'Sketchbook {sb}'; notes.append(f'Guide title is "{r["Title"]}"; Dynamo title is "Sketchbook glink001{sb:03d}"')
    else: src=r['Identifier']; title=r['Title'].strip()
    gid=src.replace('lgpst','glink'); d=dyn.get(gid); pg=man.get(gid)
    st=r['Sticker']
    if st=='lgpst00094': st='lgpst000094'; notes.append('Sticker identifier typo "lgpst00094" in all guide versions corrected to lgpst000094')
    if r['Format']!='sketchbook' and not st: notes.append('No sticker identifier recorded')
    w,h=r['Width'],r['Height']
    if w and pg and (float(w)>float(h))!=(pg[0][0]>pg[0][1]):
        notes.append(f'Guide lists {w}x{h} in but the hosted image is portrait; width/height swapped to match the S3 image'); w,h=h,w
    cnt=r['Count']; pc=len(pg) if pg else cnt
    if pg and cnt and int(cnt)!=len(pg): notes.append(f'Guide count {cnt} conflicts with {len(pg)} page(s) in S3; S3 used')
    if pg and not cnt: notes.append(f'Guide has no count; {len(pg)} pages taken from S3')
    t=tif.get(src,[])
    if pg and t and len(t)!=len(pg): notes.append(f'{len(t)} source TIFFs listed in done.txt but {len(pg)} page(s) hosted')
    if gid=='glink002129': notes.append('Source TIFF named lgpst002_windmill.tif in done.txt; local copy is lgpst002129001.tif (same size)')
    if not d: notes.append('Captured per scanning guide but no Dynamo record or S3 assets exist; not yet ingested')
    if d and re.fullmatch(r'title for glink\d+',d['title']): notes.append('Dynamo/manifest title and description are template placeholders; title taken from scanning guide')
    if d and r['Format']=='sketchbook': notes.append('Dynamo/manifest description is a template placeholder')
    out.append(dict(identifier=gid,source_identifier=src,sticker_identifier=st,title=title,description='',alt_text='',visual_description='',format=r['Format'],medium=r['Medium'],width_in=w,height_in=h,page_count=pc,page1_width_px=pg[0][0] if pg else '',page1_height_px=pg[0][1] if pg else '',project='GLink',volume=r['Volume'],capture_person=r['Capture Person'],capture_date=iso(r['Capture Date']),capture_device=r['Capture Device'],capture_target=r['Capture Target'],sensitive_content=r['Sensitive Content'],content_note=r['Content Note'],handling_notes=r['Notes'].strip(),source_tiff_files=';'.join(t),ark=d['custom_key'] if d else '',dynamo_id=d['id'] if d else '',dynamo_title=d['title'] if d else '',manifest_url=d['manifest_url'] if d else '',thumbnail_path=d['thumbnail_path'] if d else '',in_dynamo='yes' if d else 'no',in_s3='yes' if pg else 'no',in_template_csv='yes' if gid in tmpl else 'no',guide_count=cnt,consolidation_notes='; '.join(notes)))
out.sort(key=lambda r:r['identifier'])
ids=[r['identifier'] for r in out]
assert len(ids)==len(set(ids))
real={i for i in dyn if '_' not in i}
print('rows',len(out),'| dynamo records not in output:',sorted(real-set(ids)),'| S3 not in output:',sorted(set(man)-set(ids)),'| template not in output:',sorted(tmpl-set(ids)))
print('in both:',sum(r['in_dynamo']=='yes' for r in out),'not ingested:',[r['identifier'] for r in out if r['in_dynamo']=='no'])
with open(f'{D}/20261005_archive_consolidation.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,cols); w.writeheader(); w.writerows(out)
for r in out:
    if r['identifier'] in('glink001001','glink001002','glink001008','glink002086','glink002094','glink002121','glink002128','glink002129','glink002140'):
        print(r['identifier'],'|',r['title'],'|',r['page_count'],'|',r['width_in'],r['height_in'],'|',r['source_tiff_files'][:60],'|',r['consolidation_notes'])

import csv,sys
S=sys.argv[1]; n=sys.argv[2]
OUT='/Users/whunter/dev/dlp/assets/glink/docs/20261009_glink_extracted_dates.csv'
H=['identifier','page','image_id','date_as_written','date_normalized','confidence','notes']
want=[l.split(' | ')[0] for l in open(f'{S}/batches/batch{n}.txt') if l.strip()]
rows=list(csv.DictReader(open(f'{S}/results/batch{n}.csv')))
assert list(rows[0].keys())==H, rows[0].keys()
got={r['image_id'] for r in rows}
assert got==set(want), (set(want)-got, got-set(want))
for r in rows: assert r['image_id']==f"{r['identifier']}-{r['page']}", r
have={r['image_id'] for r in csv.DictReader(open(OUT))}
dated=[r for r in rows if r['date_as_written'].strip().lower()!='none']
assert not ({r['image_id'] for r in dated}&have), 'already appended'
for r in dated: assert r['date_normalized'] and r['confidence'] in('high','medium','low'), r
raw=open(OUT,'rb').read()
with open(OUT,'a',newline='') as f:
    if not raw.endswith(b'\n'): f.write('\n')
    w=csv.DictWriter(f,H,lineterminator='\r\n' if b'\r\n' in raw else '\n'); w.writerows(dated)
print(f'batch {n}: {len(want)} images, appended {len(dated)} rows')
for r in rows: print(' ',r['image_id'],'|',r['date_as_written'],'|',r['date_normalized'],'|',r['confidence'],'|',r['notes'][:150])

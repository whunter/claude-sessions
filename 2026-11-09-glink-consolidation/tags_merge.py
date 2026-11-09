import csv, io, glob, os, collections, sys
S = os.path.dirname(os.path.abspath(__file__))
os.chdir('/Users/whunter/dev/dlp/assets/glink/docs')
p = '20261109_glink_consolidation_archive_metadata.csv'

# collect agent output, check against manifests
tags = {}
for f in sorted(glob.glob(f'{S}/in/batch_*.csv')):
    inp = list(csv.DictReader(open(f)))
    out = list(csv.DictReader(open(f.replace('/in/', '/out/'))))
    assert [r['image_id'] for r in inp] == [r['image_id'] for r in out], f
    for r in out:
        t = [x.strip().lower() for x in r['tags'].split(';') if x.strip()]
        t = list(dict.fromkeys(t))  # dedupe, keep order
        assert t, r['image_id']
        tags[r['image_id']] = (r['identifier'], int(r['page']), '; '.join(t))
assert len(tags) == 536, len(tags)

by_id = collections.defaultdict(list)
for iid, (ident, pg, t) in tags.items():
    by_id[ident].append((pg, iid, t))

orig = open(p, 'rb').read()
rows = list(csv.reader(io.StringIO(orig.decode('utf-8'), newline='')))
def dump(rows, f=None):
    s = io.StringIO(); csv.writer(s, lineterminator='\r\n').writerows(rows); return s.getvalue().encode('utf-8')
assert dump(rows) == orig
hdr = rows[0]
assert 'tags' not in hdr
pos = hdr.index('visual_description') + 1
hdr.insert(pos, 'tags')
idx = hdr.index('identifier')
multi = []
for r in rows[1:]:
    ident = r[idx]
    imgs = sorted(by_id[ident])
    assert imgs, ident
    if len(imgs) == 1:
        val = imgs[0][2]
    else:
        fn = f'{ident}_tags.csv'
        with open(fn, 'wb') as fh:
            fh.write(dump([['identifier', 'page', 'image_id', 'tags']] + [[ident, pg, iid, t] for pg, iid, t in imgs]))
        val = f'path: {fn}'
        multi.append((ident, len(imgs)))
    r.insert(pos, val)
assert all(len(r) == len(hdr) for r in rows)
open(p, 'wb').write(dump(rows))
print('columns', len(hdr), 'records', len(rows) - 1)
print('multi-image files:', multi)
print('single-image records tagged:', len(rows) - 1 - len(multi))
c = collections.Counter(x for _, _, t in tags.values() for x in t.split('; '))
print('distinct tags', len(c)); print(c.most_common(25))

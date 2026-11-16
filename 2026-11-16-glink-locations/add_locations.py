import csv, sys, io
path = sys.argv[1]

# place key -> (spatial hierarchy, lat, long, source)
P = {
 'staunton':   ("Staunton, Virginia, United States", "38.149576", "-79.0716958"),                       # GNIS 1500154
 'mintspring': ("Mint Spring, Augusta County, Virginia, United States", "38.0745775", "-79.1008624"),   # GNIS 1499751
 'quicksmill': ("Quicks Mill, Augusta County, Virginia, United States", "38.2123526", "-79.0291955"),   # GNIS 1499926
 'fortdef':    ("Fort Defiance, Augusta County, Virginia, United States", "38.2404078", "-78.9719724"), # GNIS 1494937
 'augusta':    ("Augusta County, Virginia, United States", "38.1644265", "-79.1338545"),                # GNIS 1480098
 'mcdowell':   ("McDowell, Highland County, Virginia, United States", "38.3356787", "-79.4905999"),     # GNIS 1485285
 'clovercreek':("Clover Creek, Highland County, Virginia, United States", "38.2701242", "-79.5489345"), # GNIS 1495400
 'ivy':        ("Ivy, Albemarle County, Virginia, United States", "38.0565268", "-78.5966823"),         # GNIS 1493130
 'nagshead':   ("Nags Head, Dare County, North Carolina, United States", "35.9573922", "-75.6240619"),  # GNIS 1021599
 'obx':        ("Outer Banks, North Carolina, United States", "35.5668467", "-75.4684908"),             # GNIS 1985747
 'ocracoke':   ("Ocracoke, Hyde County, North Carolina, United States", "35.1146152", "-75.9810097"),   # GNIS 1021718
 'charleston': ("Charleston, Charleston County, South Carolina, United States", "32.7765656", "-79.9309216"), # GNIS 1221516
 'folly':      ("Folly Beach, Charleston County, South Carolina, United States", "32.6551798", "-79.9403673"), # GNIS 1231287
 'hhi':        ("Hilton Head Island, Beaufort County, South Carolina, United States", "32.216316", "-80.752608"), # GNIS 1246002
 'dc':         ("Washington, District of Columbia, United States", "38.8951118", "-77.0363658"),        # GNIS 531871
 'woodshole':  ("Woods Hole, Barnstable County, Massachusetts, United States", "41.5264977", "-70.6730857"), # GNIS 617060
 'capecod':    ("Cape Cod, Barnstable County, Massachusetts, United States", "41.7001111", "-70.0327945"), # GNIS 606914
 # outside GNIS coverage (US only) -> OpenStreetMap Nominatim
 'albufeira':  ("Albufeira, Faro, Portugal", "37.088241", "-8.2526339"),
 'cascais':    ("Cascais, Lisbon, Portugal", "38.6968919", "-9.4204495"),
 'portugal':   ("Portugal", "39.6621648", "-8.1353519"),
 'torremolinos':("Torremolinos, Málaga, Andalusia, Spain", "36.6242841", "-4.4995448"),
 'windsor':    ("Windsor, Berkshire, England, United Kingdom", None, None),
}
# more specific features (GNIS 2021-08-25 archive unless noted)
F = {
 'gypsyhill':   ("38.1606867", "-79.0866965"),  # Gypsy Hill Park 1478712
 'lydahunt':    ("38.1519444", "-79.0702778"),  # Lyda B Hunt Dining Hall 2110234
 'spencer':     ("38.1522222", "-79.0686111"),  # Samuel R Spencer, Junior Residence Hall 2110243
 'sma':         ("38.1542983", "-79.0680847"),  # Staunton Military Academy (historical) 1479672
 'stuarthall':  ("38.1506824", "-79.0766367"),  # Stuart Hall School - Upper and Middle Campus 1479688
 'beverley':    ("38.1479095", "-79.0680846"),  # Beverley Historic District 1739525
 'wharf':       ("38.1476317", "-79.0725292"),  # Wharf Area Historic District 1739575
 'stonechurch': ("38.2381856", "-78.9755835"),  # Augusta Stone Church 1462615
 'clovercreekch':("38.2701243", "-79.5433787"), # Clover Creek Presbyterian Church 1673766
 'ocracokelt':  ("35.1090596", "-75.9860099"),  # Ocracoke Light House 1003937
 'citymarket':  ("32.7807322", "-79.9314771"),  # City Market 1252783
 'harbourtown': ("32.1381", "-80.8121"),        # Harbour Town Yacht Basin 2490414
 'nationalmall':("38.889866", "-77.0227844"),   # National Mall 2733438
 'greatharbor': ("41.5237198", "-70.6786413"),  # Great Harbor 616058
 'mcclung':     ("38.27010472896028", "-79.54108003201007"),  # McClung farm, supplied by curator
 'windsorcastle':("51.4837886", "-0.6040419"),  # Nominatim
}

A = {  # identifier -> (place, specific feature or None)
 'glink001008': ('obx', None),
 'glink001010': ('staunton', None),
 'glink002001': ('mintspring', None),
 'glink002002': ('quicksmill', None),
 'glink002008': ('nagshead', None),
 'glink002012': ('staunton', None),
 'glink002013': ('charleston', 'citymarket'),
 'glink002018': ('staunton', None),
 'glink002019': ('augusta', None),
 'glink002020': ('dc', 'nationalmall'),
 'glink002021': ('obx', None),
 'glink002026': ('fortdef', 'stonechurch'),
 'glink002028': ('staunton', 'lydahunt'),
 'glink002029': ('clovercreek', 'mcclung'),
 'glink002030': ('clovercreek', 'clovercreekch'),
 'glink002031': ('staunton', None),
 'glink002035': ('staunton', 'gypsyhill'),
 'glink002036': ('clovercreek', 'mcclung'),
 'glink002037': ('staunton', None),
 'glink002038': ('staunton', None),
 'glink002040': ('albufeira', None),
 'glink002043': ('ocracoke', 'ocracokelt'),
 'glink002044': ('staunton', 'stuarthall'),
 'glink002053': ('hhi', 'harbourtown'),
 'glink002054': ('nagshead', None),
 'glink002056': ('staunton', 'beverley'),
 'glink002057': ('staunton', 'gypsyhill'),
 'glink002061': ('woodshole', 'greatharbor'),
 'glink002066': ('fortdef', None),
 'glink002067': ('nagshead', None),
 'glink002076': ('staunton', None),
 'glink002084': ('quicksmill', None),
 'glink002088': ('folly', None),
 'glink002089': ('windsor', 'windsorcastle'),
 'glink002090': ('staunton', 'gypsyhill'),
 'glink002095': ('staunton', None),
 'glink002096': ('ivy', None),
 'glink002097': ('staunton', 'sma'),
 'glink002099': ('staunton', None),
 'glink002101': ('staunton', 'wharf'),
 'glink002102': ('mintspring', None),
 'glink002103': ('staunton', 'beverley'),
 'glink002104': ('torremolinos', None),
 'glink002105': ('staunton', 'beverley'),
 'glink002106': ('staunton', 'wharf'),
 'glink002108': ('staunton', 'spencer'),
 'glink002115': ('capecod', None),
 'glink002117': ('staunton', None),
 'glink002122': ('cascais', None),
 'glink002123': ('quicksmill', None),
 'glink002129': ('portugal', None),
}

with open(path, newline='', encoding='utf-8') as f:
    rows = list(csv.reader(f))
hdr = rows[0]
assert 'spatial' not in hdr and 'location' not in hdr
idx = hdr.index('identifier')
ids = {r[idx] for r in rows[1:]}
assert set(A) <= ids, set(A) - ids
hdr += ['spatial', 'location']
for r in rows[1:]:
    a = A.get(r[idx])
    if not a:
        r += ['', '']; continue
    spatial, lat, lon = P[a[0]]
    if a[1]: lat, lon = F[a[1]]
    r += [spatial, f"{lat}||{lon}"]
with open(path, 'w', newline='', encoding='utf-8') as f:
    b = io.StringIO(); csv.writer(b, lineterminator='\r\n').writerows(rows); f.write(b.getvalue().removesuffix('\r\n'))  # match original CRLF, no trailing newline
print(len(A), 'rows populated of', len(rows)-1)

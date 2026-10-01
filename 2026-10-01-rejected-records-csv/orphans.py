import csv, json, os, sys, collections
sys.argv = ["x"]
D = os.path.expanduser("~/dev/dlp/claude-sessions/2026-09-30-item-inspection/")

def un(attr):
    (t, v), = attr.items()
    if t in ("S", "BOOL", "SS"): return v
    if t == "NULL": return None
    if t == "N": return float(v) if "." in v or "e" in v.lower() else int(v)
    if t == "NS": return [float(x) for x in v]
    if t == "L": return [un(x) for x in v]
    if t == "M": return {k: un(x) for k, x in v.items()}
    raise ValueError(t)

def load(m):
    return [{k: un(v) for k, v in i.items()} for i in json.load(open(m + ".json"))["Items"]]

def cell(v):
    if v is None: return ""
    if isinstance(v, list):
        return "; ".join(cell(x) for x in v) if all(not isinstance(x, (dict, list)) for x in v) else json.dumps(v, ensure_ascii=False)
    if isinstance(v, dict): return json.dumps(v, ensure_ascii=False)
    return str(v)

archives = load("Archive")
cids = {c["id"] for c in load("Collection")}
rejected = {r["id"] for r in csv.DictReader(open(D + "gen2-opensearch-rejected-records.csv", newline=""))}
orph = [a for a in archives if any(p not in cids for p in (a.get("parent_collection") or []))]
first = ["id", "identifier", "title", "parent_collection"]
keys = first + sorted({k for a in archives for k in a} - set(first))
orph.sort(key=lambda a: (cell(a.get("parent_collection")), cell(a.get("identifier"))))
with open(D + "gen2-orphaned-archives.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(keys + ["rejected_by_opensearch"])
    for a in orph:
        w.writerow([cell(a.get(k)) for k in keys] + [str(a["id"] in rejected)])
print(len(orph), "rows,", len(keys) + 1, "columns")
print(collections.Counter(cell(a.get("parent_collection")) for a in orph))
print("empty cols:", [k for k in keys if not any(cell(a.get(k)) for a in orph)])
print(collections.Counter(type(a.get(k)).__name__ for a in orph for k in keys))

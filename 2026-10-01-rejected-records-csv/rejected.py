import csv, json, os, re, subprocess, sys, time, collections

EP = "search-dguapwk5zhfbjhfosoj4a7n4uri-h6h32vch36iuywtzs7u2zxyjji.us-east-1.es.amazonaws.com"
OUT = os.path.expanduser(
    "~/dev/dlp/claude-sessions/2026-09-30-item-inspection/gen2-opensearch-rejected-records.csv"
)
HERE = os.path.dirname(os.path.abspath(__file__))
creds = json.loads(
    subprocess.check_output(["aws", "configure", "export-credentials", "--format", "process"])
)


def req(method, path, body=None, ctype="application/json"):
    args = ["curl", "-s", "--aws-sigv4", "aws:amz:us-east-1:es", "--user",
            f"{creds['AccessKeyId']}:{creds['SecretAccessKey']}", "-X", method,
            f"https://{EP}{path}"]
    if creds.get("SessionToken"):
        args += ["-H", f"x-amz-security-token: {creds['SessionToken']}"]
    data = None
    if body is not None:
        args += ["-H", f"content-type: {ctype}", "--data-binary", "@-"]
        data = (body if isinstance(body, str) else json.dumps(body)).encode()
    res = json.loads(subprocess.check_output(args, input=data))
    if isinstance(res, dict) and res.get("error"):
        raise RuntimeError(f"{method} {path}: {json.dumps(res['error'])[:500]}")
    return res


def un(attr):
    (t, v), = attr.items()
    if t in ("S", "BOOL", "SS"):
        return v
    if t == "NULL":
        return None
    if t == "N":
        return float(v) if "." in v or "e" in v.lower() else int(v)
    if t == "NS":
        return [float(x) for x in v]
    if t == "L":
        return [un(x) for x in v]
    if t == "M":
        return {k: un(x) for k, x in v.items()}
    raise ValueError(t)


def load(model):
    items = json.load(open(os.path.join(HERE, f"{model}.json")))["Items"]
    return {i["id"]["S"]: {k: un(v) for k, v in i.items()} for i in items}


def index_ids(index):
    ids = set()
    res = req("POST", f"/{index}/_search?scroll=2m",
              {"size": 5000, "_source": False, "query": {"match_all": {}}})
    while res["hits"]["hits"]:
        ids.update(h["_id"] for h in res["hits"]["hits"])
        res = req("POST", "/_search/scroll", {"scroll": "2m", "scroll_id": res["_scroll_id"]})
    req("DELETE", "/_search/scroll", {"scroll_id": res["_scroll_id"]})
    return ids


def replay(index, docs):
    """Index docs into a temporary copy of the live mapping; return id -> error."""
    mapping = req("GET", f"/{index}/_mapping")[index]["mappings"]
    tmp = f"{index}-rejected-check-{int(time.time())}"
    req("PUT", f"/{tmp}", {"mappings": mapping})
    errors = {}
    try:
        lines, size = [], 0

        def flush():
            nonlocal lines, size
            if not lines:
                return
            res = req("POST", f"/{tmp}/_bulk", "\n".join(lines) + "\n", "application/x-ndjson")
            for it in res["items"]:
                if it["index"].get("error"):
                    errors[it["index"]["_id"]] = it["index"]["error"]
            lines, size = [], 0

        for d in docs:
            s = json.dumps(d)
            lines += [json.dumps({"index": {"_id": d["id"]}}), s]
            size += len(s)
            if size > 4 * 1024 * 1024:
                flush()
        flush()
    finally:
        req("DELETE", f"/{tmp}")
    return errors


def cell(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return "; ".join(cell(x) for x in v)
    if isinstance(v, (dict,)):
        return json.dumps(v)
    return str(v)


tables = {"Archive": load("Archive"), "Collection": load("Collection")}
collections_by_id = tables["Collection"]
FIELDS = ["display_date", "date", "start_date", "end_date", "created", "create_date",
          "modified_date", "updatedAt"]
rows, not_rejected = [], []
for model, items in tables.items():
    index = model.lower()
    indexed = index_ids(index)
    missing = [items[i] for i in items if i not in indexed]
    extra = indexed - set(items)
    print(f"{model}: table {len(items)}, index {len(indexed)}, missing {len(missing)}, "
          f"in index but not table {len(extra)}", file=sys.stderr)
    errors = replay(index, missing) if missing else {}
    for d in missing:
        err = errors.get(d["id"])
        if not err:
            not_rejected.append((model, d["id"]))
        err = err or {}
        m = re.search(r"failed to parse field \[([^\]]+)\]", err.get("reason", ""))
        field = m.group(1) if m else ""
        cause = err.get("caused_by", {})
        while cause.get("caused_by") and "failed to parse date field" not in cause.get("reason", ""):
            cause = cause["caused_by"]
        parents = d.get("parent_collection") or []
        if not isinstance(parents, list):
            parents = [parents]
        absent = [p for p in parents if p not in collections_by_id]
        rows.append({
            "model": model,
            "id": d["id"],
            "identifier": cell(d.get("identifier")),
            "title": cell(d.get("title")),
            "parent_collection": cell(parents),
            "parent_collection_title": cell(
                [collections_by_id[p].get("title") for p in parents if p in collections_by_id]),
            "orphaned": (str(bool(absent)) if model == "Archive" else ""),
            "custom_key": cell(d.get("custom_key")),
            "visibility": cell(d.get("visibility")),
            "rejected_field": field,
            "rejected_value": cell(d.get(field)) if field else "",
            "error_type": err.get("type", "" if err else "not rejected on replay"),
            "error_reason": cause.get("reason") or err.get("reason", ""),
            **{f: cell(d.get(f)) for f in FIELDS},
        })

rows.sort(key=lambda r: (r["model"], r["parent_collection_title"], r["identifier"]))
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(len(rows), "rows; not rejected on replay:", len(not_rejected), not_rejected[:5], file=sys.stderr)
print(collections.Counter(r["rejected_field"] for r in rows), file=sys.stderr)
print("orphaned", collections.Counter(r["orphaned"] for r in rows), file=sys.stderr)
print("error types", collections.Counter(r["error_type"] for r in rows), file=sys.stderr)
orph_all = sum(1 for a in tables["Archive"].values()
               if any(p not in collections_by_id for p in (a.get("parent_collection") or [])))
print("orphaned archives in whole table:", orph_all, file=sys.stderr)
print(collections.Counter(r["parent_collection"] for r in rows if r["orphaned"] == "True").most_common(10), file=sys.stderr)

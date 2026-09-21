import json,collections,subprocess,sys
env,suffix,out=sys.argv[1:4]
def scan(t,proj):
    r=subprocess.run(["aws","dynamodb","scan","--table-name",t,"--projection-expression",proj,"--expression-attribute-names",json.dumps({"#t":"title"}) if "#t" in proj else "{}","--output","json"],capture_output=True,text=True)
    return json.loads(r.stdout)['Items']
def scan2(t,proj,names=None):
    cmd=["aws","dynamodb","scan","--table-name",t,"--projection-expression",proj,"--output","json"]
    if names: cmd+=["--expression-attribute-names",json.dumps(names)]
    return json.loads(subprocess.run(cmd,capture_output=True,text=True,check=True).stdout)['Items']
def v(x,k):
    a=x.get(k)
    if a is None: return None
    a=list(a.values())[0]
    if isinstance(a,list): return a[0].get('S') if a else None
    return a
cols={v(c,'id'):c for c in scan2(f"Collection-{suffix}","id, identifier, #t, parent_collection",{"#t":"title"})}
items=scan2(f"Archive-{suffix}","id, identifier, #t, #c, parent_collection, item_category",{"#t":"title","#c":"collection"})
def cinfo(cid):
    c=cols.get(cid)
    return (v(c,'identifier'),v(c,'title'),v(c,'parent_collection')) if c else (None,None,None)
g=collections.defaultdict(list)
mism=0
for i in items:
    t=(v(i,'title') or '').strip()
    if not t: continue
    cid=v(i,'collection'); ci,ct,pid=cinfo(cid)
    if v(i,'parent_collection') and v(i,'parent_collection')!=cid: mism+=1
    pi=cols[pid] and v(cols[pid],'identifier') if pid in cols else None
    g[v(i,'title')].append({'identifier':v(i,'identifier') or '(no identifier) '+v(i,'id'),'collection_id':cid,'collection':ci,'collection_title':ct,'parent_collection_identifier':pi,'item_category':v(i,'item_category')})
d={t:sorted(x,key=lambda r:r['identifier']) for t,x in g.items() if len(x)>1}
res={"environment":env,"table":f"Archive-{suffix}","title_count":len(d),"record_count":sum(map(len,d.values())),
"duplicates":[{"title":t,"count":len(d[t]),"records":d[t]} for t in sorted(d,key=lambda t:(-len(d[t]),t))]}
json.dump(res,open(out,'w'),indent=2,ensure_ascii=False)
print(env,res["title_count"],res["record_count"])

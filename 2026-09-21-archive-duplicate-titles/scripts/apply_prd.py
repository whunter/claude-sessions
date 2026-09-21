import json,subprocess
T="Archive-77eik3yv7rbdbjhjemas6h7dmi-vtdlppprd"
d=json.load(open('dry_prd.json'))
bk=[]
for u in d['update']:
    r=subprocess.run(["aws","dynamodb","get-item","--table-name",T,"--key",json.dumps({"id":{"S":u['id']}}),"--output","json"],capture_output=True,text=True,check=True)
    bk.append(json.loads(r.stdout)['Item'])
json.dump(bk,open('backup_prd_collection_fix.json','w'))
ok,fail=0,[]
for u in d['update']:
    r=subprocess.run(["aws","dynamodb","update-item","--table-name",T,"--key",json.dumps({"id":{"S":u['id']}}),
      "--update-expression","SET #c = :v","--condition-expression","attribute_not_exists(#c)",
      "--expression-attribute-names",'{"#c":"collection"}',"--expression-attribute-values",json.dumps({":v":{"S":u['parent_collection'][0]}})],capture_output=True,text=True)
    if r.returncode==0: ok+=1
    else: fail.append((u['id'],r.stderr[:150]))
with open('skipped_prd_no_parent.log','w') as f:
    for s in d['skip']: f.write(json.dumps(s)+"\n")
print("updated",ok,"failed",fail,"logged",len(d['skip']))

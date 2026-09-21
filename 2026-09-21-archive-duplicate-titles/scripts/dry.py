import json,subprocess,sys
env,suffix=sys.argv[1:3]
cmd=["aws","dynamodb","scan","--table-name",f"Archive-{suffix}","--filter-expression","attribute_not_exists(#c) OR #c = :n OR #c = :e","--expression-attribute-names",'{"#c":"collection"}',"--expression-attribute-values",'{":n":{"NULL":true},":e":{"S":""}}',"--output","json"]
items=json.loads(subprocess.run(cmd,capture_output=True,text=True,check=True).stdout)['Items']
upd,skip=[],[]
for i in items:
    pc=i.get('parent_collection',{})
    vals=[x.get('S') for x in pc.get('L',[])] if 'L' in pc else ([pc['S']] if 'S' in pc else [])
    vals=[x for x in vals if x]
    (upd if vals else skip).append({"id":i['id']['S'],"identifier":i.get('identifier',{}).get('S'),"parent_collection":vals,"collection_attr":i.get('collection')})
json.dump({"update":upd,"skip":skip},open(f"dry_{env}.json","w"),indent=1)
print(env,"no collection:",len(items),"updatable:",len(upd),"no parent:",len(skip),"multi-valued parent:",sum(1 for u in upd if len(u['parent_collection'])>1))
print([u for u in upd][:2]); print(skip[:5])

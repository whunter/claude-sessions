"""Fetch only the header/trailer byte ranges of each S3 TIFF (plus HEAD info).
Output per id: <id>.head.bin (first N bytes), <id>.tail.bin (last M bytes), <id>.json (head-object)."""
import subprocess, sys, os, json, concurrent.futures as cf
BUCKET='ingest-dev-vtlib-store'; HEADN=65536; TAILN=262144
out=sys.argv[1]; keys=[l.strip() for l in open(sys.argv[2]) if l.strip()]
def run(cmd):
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: raise RuntimeError(r.stderr)
    return r.stdout
def one(key):
    i=os.path.basename(key)[:-4]
    if os.path.exists(f'{out}/{i}.json'): return i,'cached'
    h=json.loads(run(['aws','s3api','head-object','--bucket',BUCKET,'--key',key,'--checksum-mode','ENABLED']))
    run(['aws','s3api','get-object','--bucket',BUCKET,'--key',key,'--range',f'bytes=0-{HEADN-1}',f'{out}/{i}.head.bin'])
    run(['aws','s3api','get-object','--bucket',BUCKET,'--key',key,'--range',f'bytes=-{TAILN}',f'{out}/{i}.tail.bin'])
    h['Key']=key
    json.dump(h,open(f'{out}/{i}.json','w'))
    return i,'ok'
with cf.ThreadPoolExecutor(12) as ex:
    futs=[ex.submit(one,k) for k in keys]
    n=0
    for f in cf.as_completed(futs):
        try: f.result(); n+=1
        except Exception as e: print('ERR',e,file=sys.stderr)
print('done',n)

const fs=require("fs"),path=require("path");
const root=process.argv[2];const nodes=[];
(function walk(d){if(!fs.existsSync(d))return;for(const n of fs.readdirSync(d)){if(n.startsWith(".")) continue; if(n.startsWith("@")){walk(path.join(d,n));continue}const p=path.join(d,n,"package.json");if(fs.existsSync(p)){nodes.push(path.join(d,n));walk(path.join(d,n,"node_modules"));}}})(root);
const semver=require(process.argv[3]);let bad=0;
for(const dir of nodes){const j=JSON.parse(fs.readFileSync(dir+"/package.json"));for(const [dn,spec] of Object.entries(j.dependencies||{})){let d=dir,found=null;while(true){const c=path.join(d,"node_modules",dn,"package.json");if(fs.existsSync(c)){found=JSON.parse(fs.readFileSync(c)).version;break}const up=path.dirname(d);if(!up.startsWith(root)||up===d)break;d=up.endsWith("node_modules")?path.dirname(up):up;}
 if(found&&!semver.satisfies(found,spec)){bad++; if(bad<4) console.log("  bad:",j.name+"@"+j.version,"->",dn,spec,"have",found);}}}
console.log("  invalid edges:",bad);

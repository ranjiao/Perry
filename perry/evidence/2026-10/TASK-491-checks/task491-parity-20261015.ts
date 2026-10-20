import { KernelClient, type KernelRunner } from "/Users/bytedance/.codex/worktrees/task-491-aimark-kernel/aimark/src/perry-kernel.ts";
const root = "/tmp/perry-scratch/Perry/task491-parity-import-20261015";
const run: KernelRunner = async (bin,args) => {
 const p=Bun.spawn([bin,...args],{stdout:"pipe",stderr:"pipe",env:{...process.env,PERRY_KERNEL_TESTING:"1"}});
 const [out,err,code]=await Promise.all([new Response(p.stdout).text(),new Response(p.stderr).text(),p.exited]);return {out,err,code};
};
const old=await Bun.file("/tmp/perry-scratch/Perry/task491-old-rows.json").json();
const work=await new KernelClient("/Users/bytedance/.codex/worktrees/task-490-kernel-cutover/Perry",root+"/anchor",run,root+"/store.db").read();
const ids=new Map(old.tasks.map((x:any)=>[x.id,x]));
const blank=(v:unknown)=>v===null||v===undefined||v==="—"||v===""?"":v;
const differences:unknown[]=[];
for(const row of work.tasks.tasks){
 const prev=ids.get(row.id) as any;if(!prev){differences.push({id:row.id,missing:true});continue;}
 for(const key of ["title","status","priority","owner","track","summary", ...(prev.open ? ["next_action","evidence"] as const : [])] as const)
  if(blank(prev[key])!==blank(row[key]))differences.push({id:row.id,key,old:prev[key],kernel:row[key]});
}
const result={scope:"IDs and six core fields for all rows; next action and evidence for open rows. Null/empty/em dash normalized per importer. Closed next actions intentionally excluded by reviewed importer mapping.",old_rows:old.tasks.length,kernel_rows:work.tasks.tasks.length,old_open:old.open,kernel_open:work.tasks.open,differences,contract:work.tasks.contract};
await Bun.write("/tmp/perry-scratch/Perry/task491-parity-results.json",JSON.stringify(result,null,2));
console.log(JSON.stringify({ ...result,differences:differences.slice(0,5)},null,2));
if(differences.length||old.tasks.length!==work.tasks.tasks.length)process.exit(1);

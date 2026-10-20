export type User={id:string;username:string;display_name:string;email:string;phone?:string|null;is_demo:boolean;wallet_id?:string;balance?:string|number;currency:string};
export type Transfer={id:string;amount:string|number;currency:string;description?:string;status:string;direction?:string;created_at:string;sender?:User|null;recipient?:User|null;ledger_entries?:{id:string;entry_type:string;amount:string|number;wallet_id:string}[]};
async function req(path:string, opts:RequestInit={}){
  let r:Response;
  try{ r=await fetch(path,{...opts,credentials:"include",headers:{"Content-Type":"application/json",...(opts.headers||{})}}); }
  catch{ throw new Error("Cannot reach the LedgerLab backend. Is it running on port 8000? Start it, then try again."); }
  const data=await r.json().catch(()=>({}));
  if(!r.ok){ const d=(data as any).detail;
    if(Array.isArray(d)) throw new Error(d.map((e:any)=>`${(e.loc||[]).slice(-1)[0]||"Field"}: ${e.msg||"invalid"}`).join(" · "));
    throw new Error(typeof d==="string"?d:(d?.message||"Request failed. Please check your connection and try again.")); }
  return data;
}
export const api={
  me:()=>req("/api/v1/auth/me"),
  demoUsers:()=>req("/api/v1/demo-users"),
  demoLogin:(user_id:string)=>req("/api/v1/sessions",{method:"POST",body:JSON.stringify({user_id})}),
  register:(b:object)=>req("/api/v1/auth/register",{method:"POST",body:JSON.stringify(b)}),
  login:(b:object)=>req("/api/v1/auth/login",{method:"POST",body:JSON.stringify(b)}),
  logout:()=>req("/api/v1/auth/logout",{method:"POST"}),
  resolve:(id:string)=>req(`/api/v1/users/resolve?identifier=${encodeURIComponent(id)}`),
  summary:(wid:string)=>req(`/api/v1/wallets/${wid}/summary`),
  wallet:(wid:string)=>req(`/api/v1/wallets/${wid}`),
  txns:(wid:string,p=1,status="",direction="")=>req(`/api/v1/wallets/${wid}/transactions?page=${p}&page_size=8${status?`&status=${status}`:""}${direction?`&direction=${direction}`:""}`),
  transfer:(b:object)=>req("/api/v1/transfers",{method:"POST",body:JSON.stringify(b)}),
  transferDetail:(id:string)=>req(`/api/v1/transfers/${id}`),
  analytics:()=>req("/api/v1/analytics/summary"),
  events:()=>req("/api/v1/analytics/events?limit=12"),
};
export const naira=(v:any)=>"₦"+Number(v||0).toLocaleString("en-NG",{minimumFractionDigits:2,maximumFractionDigits:2});

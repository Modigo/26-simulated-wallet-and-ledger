"use client";
import {useEffect,useState,useCallback} from "react";
import {motion,AnimatePresence} from "framer-motion";
import {Wallet,Send,History,BarChart3,LogOut,ShieldCheck,ArrowUpRight,ArrowDownLeft,Search,RefreshCw,X,CheckCircle2,AlertTriangle,BookOpen} from "lucide-react";
import {api,naira,User,Transfer} from "@/lib/api";

const Badge=()=><span className="text-[11px] font-bold tracking-widest bg-amber-400/15 text-amber-300 border border-amber-400/30 rounded-full px-3 py-1">SIMULATION MODE — NO REAL MONEY</span>;
const Btn=(p:any)=><button {...p} className={"rounded-xl bg-accent px-4 py-2.5 font-semibold hover:bg-violet-500 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-accent2 "+(p.className||"")}/>;
const Input=(p:any)=><input {...p} className="w-full bg-[#0B1020] border border-line rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-accent" />;
const Card=(p:any)=><div className="bg-panel border border-line rounded-2xl p-5 shadow-xl">{p.children}</div>;

export default function App(){
 const [user,setUser]=useState<User|null>(null); const [demo,setDemo]=useState<User[]>([]); const [view,setView]=useState("dashboard");
 const [loading,setLoading]=useState(true); const [toast,setToast]=useState(""); const [summary,setSummary]=useState<any>(null); const [txns,setTxns]=useState<any>({items:[],total:0,page:1,pages:0});
 const [page,setPage]=useState(1); const [statusF,setStatusF]=useState(""); const [dirF,setDirF]=useState(""); const [analytics,setAnalytics]=useState<any>(null); const [events,setEvents]=useState<any[]>([]);
 const [detail,setDetail]=useState<any>(null);
 const notify=(m:string)=>{setToast(m); setTimeout(()=>setToast(""),4500)};
 const refresh=useCallback(async(u:User)=>{ if(!u.wallet_id) return; const [s,t,a,e]=await Promise.all([api.summary(u.wallet_id),api.txns(u.wallet_id,page,statusF,dirF),api.analytics(),api.events()]); setSummary(s); setTxns(t); setAnalytics(a); setEvents(e); const me=await api.me(); setUser(me); },[page,statusF,dirF]);
 useEffect(()=>{(async()=>{ try{ const me=await api.me(); setUser(me);}catch{} setDemo(await api.demoUsers().catch(()=>[])); setLoading(false); })()},[]);
 useEffect(()=>{ if(user) refresh(user).catch(e=>notify(e.message)); },[user?.id,page,statusF,dirF]); // eslint-disable-line
 async function enter(fn:()=>Promise<any>){ try{ const r=await fn(); setUser(r.user||r); setView("dashboard"); notify("Welcome to LedgerLab — you are now in the dashboard."); return null; }catch(e:any){ notify(e.message); return e.message as string; } }
 async function logout(){ await api.logout().catch(()=>{}); setUser(null); setSummary(null); }
 if(loading) return <main className="p-8 max-w-6xl mx-auto"><div className="animate-pulse space-y-4"><div className="h-10 bg-panel rounded"/><div className="h-64 bg-panel rounded-2xl"/></div></main>;
 if(!user) return <Welcome demo={demo} enter={enter} notify={notify} toast={toast}/>;
 return <main className="min-h-screen">
  <header className="sticky top-0 bg-ink/90 backdrop-blur border-b border-line z-10"><div className="max-w-6xl mx-auto px-4 py-3 flex flex-wrap gap-3 items-center justify-between">
   <div className="flex items-center gap-3"><div className="bg-accent p-2 rounded-xl"><BookOpen size={20}/></div><div><b className="text-lg">LedgerLab</b><p className="text-xs text-slate-400">Simulated wallet & transaction ledger</p></div></div>
   <Badge/><div className="flex items-center gap-3 text-sm"><span>{user.display_name} <span className="text-slate-400">@{user.username}{user.is_demo?" · DEMO":""}</span></span><button aria-label="Log out" onClick={logout} className="flex gap-1 items-center border border-line rounded-lg px-3 py-2"><LogOut size={16}/> Log out</button></div>
  </div></header>
  <div className="max-w-6xl mx-auto px-4 py-6 grid md:grid-cols-[200px_1fr] gap-6">
   <nav className="flex md:flex-col gap-2" aria-label="Main">
    {[["dashboard",Wallet,"Dashboard"],["send",Send,"Send money"],["history",History,"History"],["analytics",BarChart3,"Analytics"]].map(([v,I,l]:any)=><button key={v} onClick={()=>setView(v)} className={"flex items-center gap-2 px-3 py-2.5 rounded-xl text-left "+(view===v?"bg-accent":"border border-line")}><I size={18}/>{l}</button>)}
   </nav>
   <section>
    {view==="dashboard"&&<><div className="grid sm:grid-cols-3 gap-4">
      <Card><p className="text-slate-400 text-sm flex gap-2"><Wallet size={16}/> Available balance</p><motion.p key={String(user.balance)} initial={{scale:.96,opacity:.5}} animate={{scale:1,opacity:1}} className="text-3xl font-bold mt-2">{naira(user.balance)}</motion.p><p className="text-xs text-slate-500 mt-2">Wallet {user.wallet_id?.slice(0,8)}… · NGN</p></Card>
      <Card><p className="text-emerald-300 text-sm flex gap-2"><ArrowDownLeft size={16}/> Incoming</p><p className="text-2xl font-bold mt-2">{naira(summary?.incoming_amount)}</p><p className="text-xs text-slate-400">{summary?.incoming_count||0} transfers</p></Card>
      <Card><p className="text-rose-300 text-sm flex gap-2"><ArrowUpRight size={16}/> Outgoing</p><p className="text-2xl font-bold mt-2">{naira(summary?.outgoing_amount)}</p><p className="text-xs text-slate-400">{summary?.outgoing_count||0} transfers</p></Card></div>
      <div className="mt-5"><Btn onClick={()=>setView("send")}><span className="flex gap-2 items-center"><Send size={16}/> Send money</span></Btn></div>
      <h2 className="font-bold mt-8 mb-3">Recent transactions</h2><TxnList items={txns.items?.slice(0,5)} onOpen={async(id:string)=>setDetail(await api.transferDetail(id))}/></>}
    {view==="send"&&<SendMoney user={user} done={async(msg:string)=>{notify(msg); setView("dashboard"); await refresh(user);}} notify={notify}/>}
    {view==="history"&&<><h2 className="text-xl font-bold mb-4">Transaction history</h2><div className="flex flex-wrap gap-2 mb-4"><select aria-label="Status filter" value={statusF} onChange={e=>{setStatusF(e.target.value);setPage(1)}} className="bg-panel border border-line rounded-xl px-3 py-2"><option value="">All statuses</option><option>COMPLETED</option><option>REJECTED</option></select><select aria-label="Direction filter" value={dirF} onChange={e=>{setDirF(e.target.value);setPage(1)}} className="bg-panel border border-line rounded-xl px-3 py-2"><option value="">All directions</option><option value="OUTGOING">Outgoing</option><option value="INCOMING">Incoming</option></select></div><TxnList items={txns.items} onOpen={async(id:string)=>setDetail(await api.transferDetail(id))}/><div className="flex gap-2 mt-4 items-center"><button disabled={page<=1} onClick={()=>setPage(page-1)} className="border border-line rounded-lg px-3 py-2 disabled:opacity-40">Previous</button><span>Page {txns.page} of {txns.pages||1} · {txns.total} total</span><button disabled={page>=(txns.pages||1)} onClick={()=>setPage(page+1)} className="border border-line rounded-lg px-3 py-2 disabled:opacity-40">Next</button></div></>}
    {view==="analytics"&&<div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">{[["Successful transfers (all users)",analytics?.total_successful_transfers],["Total simulated volume",naira(analytics?.total_volume)],["Rejected attempts",analytics?.rejected_attempts],["My activity",analytics?.recent_activity],["My incoming",`${analytics?.my_incoming_count||0} · ${naira(analytics?.my_incoming_amount)}`],["My outgoing",`${analytics?.my_outgoing_count||0} · ${naira(analytics?.my_outgoing_amount)}`],["Session started",analytics?.current_session_started_at?new Date(analytics.current_session_started_at).toLocaleString():"—"],["Last seen",analytics?.current_session_last_seen_at?new Date(analytics.current_session_last_seen_at).toLocaleString():"—"]].map(([l,v]:any)=><Card key={l}><p className="text-xs text-slate-400">{l}</p><p className="font-bold text-lg mt-1">{v??"—"}</p></Card>)}
      <div className="sm:col-span-2 lg:col-span-4"><Card><h3 className="font-bold mb-3">Recent simulation activity</h3>{events.length?events.map(e=><p key={e.id} className="text-sm py-1 border-b border-line/50">{e.event_type} <span className="text-slate-500">· {new Date(e.created_at).toLocaleString()}</span></p>):<p className="text-slate-400">No activity yet.</p>}</Card></div></div>}
   </section>
  </div>
  <AnimatePresence>{detail&&<div className="fixed inset-0 bg-black/60 flex justify-end z-20" role="dialog" aria-label="Transaction details"><motion.div initial={{x:40,opacity:0}} animate={{x:0,opacity:1}} exit={{opacity:0}} className="bg-panel w-full max-w-md p-6 overflow-auto"><button className="float-right" aria-label="Close" onClick={()=>setDetail(null)}><X/></button><h3 className="font-bold text-lg">Transaction details</h3><dl className="space-y-3 mt-4 text-sm"><div>Reference<br/><b className="break-all">{detail.id}</b></div><div>Amount<br/><b>{naira(detail.amount)} {detail.currency}</b></div><div>Status<br/><b>{detail.status}</b></div><div>From<br/><b>{detail.sender?.display_name} (@{detail.sender?.username})</b></div><div>To<br/><b>{detail.recipient?.display_name} (@{detail.recipient?.username})</b></div><div>Date<br/><b>{new Date(detail.created_at).toLocaleString()}</b></div><div>Description<br/><b>{detail.description||"—"}</b></div></dl><h4 className="font-bold mt-6">Ledger entries (signed amounts sum to zero)</h4>{detail.ledger_entries?.map((e:any)=><p key={e.id} className="text-sm py-2 border-b border-line">{e.entry_type}: {naira(e.amount)} · wallet {e.wallet_id.slice(0,8)}…</p>)}</motion.div></div>}</AnimatePresence>
  {toast&&<div role="status" className="fixed bottom-5 right-5 bg-panel border border-accent rounded-xl px-4 py-3 shadow-2xl flex gap-2 max-w-sm"><ShieldCheck className="text-emerald-400 shrink-0"/>{toast}</div>}
 </main>;
}
function TxnList({items,onOpen}:{items:Transfer[];onOpen:(id:string)=>void}){
 if(!items?.length) return <Card><p className="text-slate-400">No transactions yet. Send your first simulated transfer to see it here.</p></Card>;
 return <div className="space-y-2">{items.map(t=><button key={t.id} onClick={()=>onOpen(t.id)} className="w-full text-left bg-panel border border-line rounded-2xl p-4 flex justify-between gap-3 hover:border-accent">
  <span className="flex gap-3">{t.direction==="INCOMING"?<ArrowDownLeft className="text-emerald-400"/>:<ArrowUpRight className="text-rose-400"/>}<span><b>{t.direction==="INCOMING"?t.sender?.display_name:t.recipient?.display_name}</b><br/><span className="text-xs text-slate-400">{new Date(t.created_at).toLocaleString()} · {t.description||"No description"} · {t.id.slice(0,8)}…</span></span></span>
  <span className="text-right"><b className={t.direction==="INCOMING"?"text-emerald-300":"text-rose-300"}>{t.direction==="INCOMING"?"+":"−"}{naira(t.amount)}</b><br/><span className="text-xs">{t.status}</span></span></button>)}</div>;
}
function SendMoney({user,done,notify}:{user:User;done:(m:string)=>void;notify:(m:string)=>void}){
 const [identifier,setIdentifier]=useState(""); const [recipient,setRecipient]=useState<User|null>(null); const [amount,setAmount]=useState(""); const [desc,setDesc]=useState(""); const [step,setStep]=useState(1); const [busy,setBusy]=useState(false); const [err,setErr]=useState(""); const [key,setKey]=useState("");
 async function resolve(){ setErr(""); try{ setRecipient(await api.resolve(identifier)); setKey(crypto.randomUUID()); }catch(e:any){ setRecipient(null); setErr(e.message);} }
 async function submit(){ setBusy(true); setErr(""); try{ const r=await api.transfer({recipient_identifier:identifier,amount,description:desc||null,idempotency_key:key}); done(r.idempotent_replay?"Duplicate safely ignored — original transfer returned.":"Transfer completed successfully."); }catch(e:any){ setErr(e.message+" Your form is preserved — fix it or retry with the same key."); } finally{ setBusy(false);} }
 const amt=Number(amount); const valid=recipient&&amt>0&&amt<=Number(user.balance||0);
 return <Card><h2 className="text-xl font-bold">Send simulated money</h2><p className="text-sm text-slate-400 mt-1">NGN only. This never moves real money.</p>
  {step===1&&<div className="space-y-4 mt-5"><label className="block text-sm">Recipient (username, email or Nigerian phone)<div className="flex gap-2 mt-1"><Input value={identifier} onChange={(e:any)=>setIdentifier(e.target.value)} placeholder="e.g. bello, bello@example.com, 0803…" aria-label="Recipient identifier"/><button onClick={resolve} className="border border-line rounded-xl px-4 flex gap-2 items-center"><Search size={16}/> Resolve</button></div></label>
  {recipient&&<div className="border border-emerald-400/40 bg-emerald-400/10 rounded-xl p-3 text-sm"><CheckCircle2 className="inline mr-2 text-emerald-300"/>{recipient.display_name} (@{recipient.username}) · {recipient.email} · {recipient.phone}</div>}
  <label className="block text-sm">Amount (NGN)<div className="mt-1"><Input type="number" min="0" step="0.01" value={amount} onChange={(e:any)=>setAmount(e.target.value)} aria-label="Amount in naira"/></div></label>
  {amount&&!valid&&<p className="text-amber-300 text-sm flex gap-2"><AlertTriangle size={16}/> Enter an amount above ₦0 and no more than your balance ({naira(user.balance)}).</p>}
  <label className="block text-sm">Description (optional)<div className="mt-1"><Input value={desc} onChange={(e:any)=>setDesc(e.target.value)} aria-label="Description"/></div></label>
  {err&&<p role="alert" className="text-rose-300 text-sm">{err}</p>}<Btn disabled={!valid} onClick={()=>setStep(2)}>Review transfer</Btn></div>}
  {step===2&&recipient&&<div className="space-y-3 mt-5 text-sm"><p>Send <b className="text-xl">{naira(amount)}</b> to <b>{recipient.display_name}</b> (@{recipient.username})?</p><p className="text-slate-400">Description: {desc||"—"} · Idempotency key: {key.slice(0,8)}… (reused automatically on retry)</p>{err&&<p role="alert" className="text-rose-300">{err}</p>}<div className="flex gap-2"><button onClick={()=>setStep(1)} className="border border-line rounded-xl px-4 py-2">Back</button><Btn disabled={busy} onClick={submit}>{busy?"Processing…":"Confirm simulated transfer"}</Btn></div></div>}
 </Card>;
}
function Welcome({demo,enter,notify,toast}:{demo:User[];enter:(f:()=>Promise<any>)=>Promise<string|null>;notify:(m:string)=>void;toast:string}){
 const [mode,setMode]=useState("demo"); const [form,setForm]=useState({display_name:"",username:"",email:"",phone:"",password:"",confirm:""}); const [login,setLogin]=useState({identifier:"",password:""});
 const [busy,setBusy]=useState(""); const [error,setError]=useState("");
 const set=(k:string,v:string)=>setForm({...form,[k]:v});
 async function run(id:string,fn:()=>Promise<any>){ setError(""); setBusy(id); const err=await enter(fn); if(err) setError(err); setBusy(""); }
 const initials=(n:string)=>n.split(" ").map(w=>w[0]).slice(0,2).join("").toUpperCase();
 return (<main className="min-h-screen lg:grid lg:grid-cols-[1.05fr_1fr]">
  {/* Left: brand / story panel */}
  <section className="relative overflow-hidden px-6 py-10 lg:px-14 lg:py-14 bg-gradient-to-br from-[#141B36] via-ink to-[#1E1440]">
   <div className="absolute -top-24 -right-24 h-72 w-72 rounded-full bg-accent/25 blur-3xl" aria-hidden="true"/><div className="absolute bottom-0 left-1/3 h-56 w-56 rounded-full bg-accent2/15 blur-3xl" aria-hidden="true"/>
   <div className="relative flex items-center justify-between"><div className="flex gap-3 items-center"><div className="bg-accent p-2.5 rounded-2xl shadow-lg shadow-accent/40"><BookOpen/></div><div><h1 className="text-2xl font-bold leading-none">LedgerLab</h1><p className="text-xs text-slate-400 mt-1">Simulated wallet &amp; transaction ledger</p></div></div><Badge/></div>
   <h2 className="relative text-4xl lg:text-5xl font-extrabold leading-tight mt-14">See how digital money <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent to-accent2">actually moves.</span></h2>
   <p className="relative text-slate-300 mt-5 max-w-md">Send simulated naira between accounts and watch the double-entry ledger balance itself — every debit matched by a credit, every kobo accounted for.</p>
   <motion.div initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{delay:.15}} className="relative mt-10 max-w-md rounded-3xl border border-white/10 bg-white/5 backdrop-blur p-6 shadow-2xl">
    <p className="text-xs tracking-widest text-slate-400 flex items-center gap-2"><Wallet size={14}/> DEMO WALLET · ADAEZE NWOSU</p>
    <p className="text-4xl font-extrabold mt-3">₦250,000.00</p>
    <div className="mt-5 space-y-2 text-sm">
     <p className="flex justify-between border-b border-white/5 pb-2"><span className="text-rose-300">− ₦5,000.00</span><span className="text-slate-400">DEBIT · to bello</span></p>
     <p className="flex justify-between border-b border-white/5 pb-2"><span className="text-emerald-300">+ ₦5,000.00</span><span className="text-slate-400">CREDIT · from adaeze</span></p>
     <p className="flex justify-between font-semibold"><span>Ledger check</span><span className="text-emerald-300 flex items-center gap-1"><CheckCircle2 size={15}/> Sums to ₦0.00</span></p>
    </div>
   </motion.div>
   <ul className="relative mt-8 space-y-2 text-sm text-slate-300">
    <li className="flex gap-2"><ShieldCheck size={17} className="text-accent2 shrink-0"/> Atomic transfers — a transfer completes fully or not at all</li>
    <li className="flex gap-2"><RefreshCw size={17} className="text-accent2 shrink-0"/> Idempotency keys — safe retries never double-charge</li>
    <li className="flex gap-2"><Search size={17} className="text-accent2 shrink-0"/> Find anyone by username, email or Nigerian phone number</li>
   </ul>
  </section>
  {/* Right: access panel */}
  <section className="px-5 py-10 lg:px-12 flex items-start lg:items-center justify-center">
   <div className="w-full max-w-md">
    <h3 className="text-2xl font-bold">{mode==="demo"?"Enter the demo":mode==="register"?"Create your account":"Welcome back"}</h3>
    <p className="text-sm text-slate-400 mt-1">{mode==="demo"?"One click, no password — pick an identity and present both sides of a transfer.":mode==="register"?"Your wallet starts at ₦0.00. Ask a demo account to send you funds.":"Log in with your username, email or phone."}</p>
    <div className="grid grid-cols-3 gap-1 bg-panel border border-line rounded-2xl p-1 mt-6" role="tablist" aria-label="Access options">
     {[["demo","Demo"],["register","Register"],["login","Log in"]].map(([m,l])=><button key={m} role="tab" aria-selected={mode===m} onClick={()=>{setMode(m);setError("");}} className={"px-3 py-2 rounded-xl text-sm font-semibold transition "+(mode===m?"bg-accent shadow-lg shadow-accent/30":"text-slate-400 hover:text-white")}>{l}</button>)}
    </div>
    {error&&<p role="alert" className="mt-4 flex gap-2 text-sm text-rose-200 bg-rose-500/10 border border-rose-400/40 rounded-xl px-4 py-3"><AlertTriangle size={17} className="shrink-0 mt-0.5"/>{error}</p>}
    {mode==="demo"&&<div className="space-y-3 mt-6">{demo.length===0&&<p className="text-amber-300 text-sm bg-amber-400/10 border border-amber-400/30 rounded-xl px-4 py-3">No demo accounts loaded. Is the backend running on port 8000, and did you run <code>python -m app.seed</code> in <code>ledgerlab/backend</code>?</p>}{demo.map(u=><div key={u.id} className="group bg-panel border border-line hover:border-accent rounded-2xl p-4 flex items-center gap-4 transition">
      <div className="h-11 w-11 shrink-0 rounded-full bg-gradient-to-br from-accent to-accent2 flex items-center justify-center font-bold">{initials(u.display_name)}</div>
      <div className="min-w-0 flex-1"><p className="font-bold truncate">{u.display_name} <span className="text-slate-400 font-normal text-sm">@{u.username}</span></p><p className="text-xs text-slate-400 truncate">{u.email} · {u.phone}</p><p className="font-bold mt-0.5">{naira(u.balance)}</p></div>
      <Btn disabled={busy===u.id} onClick={()=>run(u.id,()=>api.demoLogin(u.id))}>{busy===u.id?"Entering…":"Enter"}</Btn></div>)}</div>}
    {mode==="register"&&<form className="space-y-3 mt-6" onSubmit={async e=>{e.preventDefault(); if(form.password!==form.confirm){ setError("Passwords do not match — retype the same password in both fields."); return; } const {confirm,...b}=form; await run("register",()=>api.register(b));}}>
      {[["display_name","Display name","text","e.g. Chiamaka Obi"],["username","Username","text","lowercase, no spaces"],["email","Email","email","you@example.com"],["phone","Phone (optional)","tel","0803 000 0000"]].map(([k,l,t,ph])=><label key={k} className="block text-sm font-medium">{l}<Input className="mt-1" required={k!=="phone"} type={t} placeholder={ph} autoComplete={k==="email"?"email":"off"} value={(form as any)[k]} onChange={(e:any)=>set(k,e.target.value)}/></label>)}
      <label className="block text-sm font-medium">Password <span className="text-slate-400 font-normal">(8+ characters, a letter and a number)</span><Input className="mt-1" required type="password" autoComplete="new-password" value={form.password} onChange={(e:any)=>set("password",e.target.value)}/></label>
      <label className="block text-sm font-medium">Confirm password<Input className="mt-1" required type="password" autoComplete="new-password" value={form.confirm} onChange={(e:any)=>set("confirm",e.target.value)}/></label>
      <Btn type="submit" disabled={busy==="register"} className="w-full">{busy==="register"?"Creating account…":"Create account — start with ₦0.00"}</Btn></form>}
    {mode==="login"&&<form className="space-y-3 mt-6" onSubmit={async e=>{e.preventDefault(); await run("login",()=>api.login(login));}}>
      <label className="block text-sm font-medium">Username, email or phone<Input className="mt-1" required autoComplete="username" value={login.identifier} onChange={(e:any)=>setLogin({...login,identifier:e.target.value})}/></label>
      <label className="block text-sm font-medium">Password<Input className="mt-1" required type="password" autoComplete="current-password" value={login.password} onChange={(e:any)=>setLogin({...login,["pass"+"word"]:e.target.value})}/></label>
      <Btn type="submit" disabled={busy==="login"} className="w-full">{busy==="login"?"Logging in…":"Log in"}</Btn>
      <p className="text-xs text-slate-500">Demo accounts need no password — use the Demo tab.</p></form>}
   </div>
  </section>
  {toast&&!error&&<div role="status" className="fixed bottom-5 right-5 bg-panel border border-accent rounded-xl px-4 py-3 max-w-sm shadow-2xl z-30">{toast}</div>}
 </main>);
}

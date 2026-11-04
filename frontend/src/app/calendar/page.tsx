"use client";

import { useCallback, useEffect, useState } from "react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { CalendarEntry, getCalendarEvents, syncGoogleService } from "@/lib/api";

export default function CalendarPage() {
  const [events,setEvents]=useState<CalendarEntry[]>([]); const [error,setError]=useState(""); const [notice,setNotice]=useState(""); const [busy,setBusy]=useState(false);
  const token=()=>window.localStorage.getItem("applytrack_session")||"";
  const load=useCallback(async()=>{const t=token();if(!t)return;try{setEvents(await getCalendarEvents(t));setError("")}catch(cause){setError(cause instanceof Error?cause.message:"Could not load calendar events.")}},[]);
  useEffect(()=>{void load()},[load]);
  async function sync(){setBusy(true);setError("");setNotice("");try{const result=await syncGoogleService(token(),"calendar");setNotice(`Checked ${result.checked} events and imported ${result.new_events} new items.`);await load()}catch(cause){setError(cause instanceof Error?cause.message:"Calendar sync failed.")}finally{setBusy(false)}}
  return <WorkspaceShell title="Calendar"><div className="mb-7 flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-semibold uppercase tracking-[.14em] text-moss">Schedule</p><h2 className="mt-2 text-4xl font-semibold tracking-[-.045em]">Upcoming events.</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-muted">Synced event titles, organizers, and times from Google Calendar appear here.</p></div><button className="primary-button" disabled={busy} onClick={()=>void sync()}>{busy?"Syncing…":"Sync Calendar"}</button></div>
    {error&&<Notice tone="error">{error}</Notice>}{notice&&<Notice tone="success">{notice}</Notice>}{events.length?<div className="space-y-3">{events.map(e=><article key={e.id} className="flex flex-wrap items-center justify-between gap-4 rounded-[20px] border border-[#e4e8df] bg-white p-5"><div><h3 className="font-semibold">{e.summary}</h3><p className="mt-1 text-sm text-muted">{e.organizer||"No organizer listed"}</p></div><div className="text-sm sm:text-right"><p className="font-medium">{new Date(e.starts_at).toLocaleString()}</p>{e.ends_at&&<p className="mt-1 text-xs text-muted">Until {new Date(e.ends_at).toLocaleString()}</p>}</div></article>)}</div>:<div className="rounded-[22px] border border-dashed border-[#dce3d7] bg-white p-10 text-center"><h3 className="font-semibold">No calendar events imported</h3><p className="mt-2 text-sm text-muted">Connect Google Calendar in Connected apps, then sync your schedule.</p></div>}</WorkspaceShell>;
}
function Notice({tone,children}:{tone:"success"|"error";children:React.ReactNode}){return <div role="status" className={`mb-5 rounded-xl border px-4 py-3 text-sm ${tone==="success"?"border-[#d2e2be] bg-[#f3f8ec] text-forest":"border-[#f2c9bd] bg-[#fff5f1] text-[#9b402b]"}`}>{children}</div>}

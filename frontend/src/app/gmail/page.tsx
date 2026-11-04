"use client";

import { useCallback, useEffect, useState } from "react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { Application, applicationStatuses, confirmMailEvent, getApplications, getMailEvents, MailEvent, syncGoogleService } from "@/lib/api";

export default function GmailPage() {
  const [events, setEvents] = useState<MailEvent[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [choices, setChoices] = useState<Record<number, { application: string; status: string }>>({});
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState<number | "sync" | null>(null);
  const token = () => window.localStorage.getItem("applytrack_session") || "";
  const load = useCallback(async () => {
    const t = token(); if (!t) return;
    try { const [mail, apps] = await Promise.all([getMailEvents(t), getApplications(t)]); setEvents(mail); setApplications(apps); setError(""); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load Gmail activity."); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  async function sync() { setBusy("sync"); setError(""); setNotice(""); try { const result = await syncGoogleService(token(), "gmail"); setNotice(`Checked ${result.checked} messages and imported ${result.new_events} new items.`); await load(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Gmail sync failed."); } finally { setBusy(null); } }
  async function confirm(event: MailEvent) { const choice = choices[event.id]; if (!choice?.application) { setError("Choose the application this message belongs to."); return; } setBusy(event.id); setError(""); try { await confirmMailEvent(token(), event.id, Number(choice.application), choice.status || "Under Review"); setNotice("Application status updated from the message you reviewed."); await load(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not confirm this event."); } finally { setBusy(null); } }
  return <WorkspaceShell title="Gmail activity"><div className="mb-7 flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-semibold uppercase tracking-[.14em] text-moss">Inbox signals</p><h2 className="mt-2 text-4xl font-semibold tracking-[-.045em]">Review job updates.</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-muted">Only message metadata is imported. Nothing changes in your application tracker until you confirm a message.</p></div><button className="primary-button" onClick={() => void sync()} disabled={busy !== null}>{busy === "sync" ? "Syncing…" : "Sync Gmail"}</button></div>
    {error && <Notice tone="error">{error}</Notice>}{notice && <Notice tone="success">{notice}</Notice>}
    {events.length ? <div className="space-y-3">{events.map(event => <article key={event.id} className="rounded-[20px] border border-[#e4e8df] bg-white p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><span className="rounded-full bg-[#edf3e4] px-3 py-1 text-xs font-semibold capitalize text-forest">{event.classification.replaceAll("_", " ")}</span><h3 className="mt-3 font-semibold">{event.subject || "(No subject)"}</h3><p className="mt-1 text-sm text-muted">{event.sender || "Unknown sender"} · {event.received_at ? new Date(event.received_at).toLocaleString() : "Date unavailable"}</p></div><span className="text-xs text-muted">{event.reviewed ? "Reviewed" : "Needs review"}</span></div>
      {!event.reviewed && applications.length > 0 && <div className="mt-5 flex flex-wrap items-end gap-3"><label className="text-xs font-semibold text-muted">Application<select className="form-input mt-1 block min-w-56" value={choices[event.id]?.application || ""} onChange={e => setChoices(old => ({ ...old, [event.id]: { application: e.target.value, status: old[event.id]?.status || "Under Review" } }))}><option value="">Choose an application</option>{applications.map(a => <option key={a.id} value={a.id}>{a.job.title} · {a.job.company}</option>)}</select></label><label className="text-xs font-semibold text-muted">New status<select className="form-input mt-1 block" value={choices[event.id]?.status || "Under Review"} onChange={e => setChoices(old => ({ ...old, [event.id]: { application: old[event.id]?.application || "", status: e.target.value } }))}>{applicationStatuses.map(s => <option key={s}>{s}</option>)}</select></label><button className="secondary-button" disabled={busy !== null} onClick={() => void confirm(event)}>{busy === event.id ? "Saving…" : "Confirm update"}</button></div>}
      {!event.reviewed && applications.length === 0 && <p className="mt-4 text-sm text-muted">Add an application first to link and confirm this message.</p>}</article>)}</div> : <div className="rounded-[22px] border border-dashed border-[#dce3d7] bg-white p-10 text-center"><h3 className="font-semibold">No Gmail activity imported</h3><p className="mt-2 text-sm text-muted">Connect Gmail in Connected apps, then sync to review job related messages.</p></div>}
  </WorkspaceShell>;
}
function Notice({tone,children}:{tone:"success"|"error";children:React.ReactNode}){return <div role="status" className={`mb-5 rounded-xl border px-4 py-3 text-sm ${tone==="success"?"border-[#d2e2be] bg-[#f3f8ec] text-forest":"border-[#f2c9bd] bg-[#fff5f1] text-[#9b402b]"}`}>{children}</div>}

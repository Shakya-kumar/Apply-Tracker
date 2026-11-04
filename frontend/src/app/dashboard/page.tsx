"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DashboardMetrics, getDashboard } from "@/lib/api";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const token = window.localStorage.getItem("applytrack_session");
    if (!token) return;
    getDashboard(token).then(setMetrics).catch(cause => setError(cause instanceof Error ? cause.message : "Could not load dashboard data."));
  }, []);

  return <WorkspaceShell title="Overview">
    <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><p className="text-sm font-semibold uppercase tracking-[.14em] text-moss">Your job search</p><h2 className="mt-2 text-4xl font-semibold tracking-[-.045em]">A clearer next step.</h2><p className="mt-3 max-w-xl text-sm leading-6 text-[#657169]">Keep your experience, opportunities, and application progress together.</p></div><Link href="/jobs" className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-forest px-5 text-sm font-semibold text-white hover:bg-[#123d30]">＋ Add a job</Link></div>
    {error && <div role="alert" className="mt-7 rounded-2xl border border-[#f2c9bd] bg-[#fff5f1] p-4 text-sm text-[#9b402b]">{error}</div>}
    <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-5"><Metric label="Jobs saved" value={metrics?.saved_jobs} detail="Opportunities in your list" icon="⌕"/><Metric label="Applications" value={metrics?.applications} detail="Being tracked" icon="↗"/><Metric label="Submitted" value={metrics?.submitted} detail="Marked as submitted" icon="✓"/><Metric label="Interviews" value={metrics?.interviews} detail="Scheduled or completed" icon="◷"/><Metric label="Response rate" value={metrics?.response_rate == null ? "—" : `${metrics.response_rate}%`} detail={metrics?.submitted ? "Of submitted applications" : "Available after submissions"} icon="％"/></div>

    <div className="mt-8 grid gap-5 xl:grid-cols-[1.35fr_.65fr]">
      <section className="rounded-[26px] border border-[#e4e8df] bg-white p-6 sm:p-8"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[.16em] text-moss">Start here</p><h3 className="mt-3 text-2xl font-semibold tracking-tight">Build your career profile</h3><p className="mt-2 max-w-lg text-sm leading-6 text-muted">Add details you can verify. They’ll be the source for future job matching and resume tailoring.</p></div><span className="hidden h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[#f0f5e8] text-xl text-forest sm:grid">◎</span></div>
        <div className="mt-6 space-y-3">{[
          {href:"/resume", title:"Upload your master resume", done:metrics?.has_master_resume, note:"PDF or DOCX · up to 8 MB"},
          {href:"/profile", title:"Add your career details and preferences", done:metrics?.profile_complete, note:"Experience, education, skills, and goals"},
          {href:"/integrations", title:"Review connected apps", done:false, note:"See what’s available and what needs setup"},
        ].map(step => <Link key={step.href} href={step.href} className="focus-ring flex items-center gap-4 rounded-2xl border border-[#edf0e9] p-4 transition hover:border-[#c8d6bd] hover:bg-[#fbfcf8]"><span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl text-sm ${step.done ? "bg-[#edf6df] text-forest" : "bg-[#f4f6ef] text-moss"}`}>{step.done ? "✓" : "→"}</span><span className="min-w-0 flex-1"><span className="block text-sm font-semibold">{step.title}</span><span className="mt-1 block text-xs text-muted">{step.note}</span></span><span className="text-[#829087]">›</span></Link>)}</div>
      </section>
      <section className="rounded-[26px] bg-forest p-6 text-white sm:p-8"><p className="text-xs font-bold uppercase tracking-[.16em] text-[#d7e8b3]">Your workspace</p><h3 className="mt-3 text-2xl font-semibold">Your data, in one place.</h3><p className="mt-3 text-sm leading-6 text-[#d2ded7]">Dashboard counts come from your saved jobs and applications. New workspaces start empty and grow as you add real information.</p><div className="mt-7 border-t border-white/15 pt-5"><p className="text-xs text-[#c1d1c8]">Upcoming actions</p><p className="mt-2 text-sm">{metrics?.upcoming_actions.length ? `${metrics.upcoming_actions.length} action${metrics.upcoming_actions.length === 1 ? "" : "s"}` : "No reminders yet"}</p></div><Link href="/applications" className="focus-ring mt-6 inline-flex rounded-xl bg-[#c9e47b] px-4 py-2.5 text-sm font-semibold text-forest hover:bg-[#d6eb98]">View application tracker <span className="ml-2">→</span></Link></section>
    </div>
  </WorkspaceShell>;
}

function Metric({label,value,detail,icon}:{label:string;value:number|string|undefined;detail:string;icon:string}) { return <article className="rounded-2xl border border-[#e4e8df] bg-white p-5"><div className="flex items-center justify-between"><p className="text-xs font-semibold text-muted">{label}</p><span className="text-base text-moss">{icon}</span></div><p className="mt-4 text-3xl font-semibold tracking-tight">{value ?? "—"}</p><p className="mt-1 text-xs text-muted">{detail}</p></article>; }

"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import { Account, getAccount, logout } from "@/lib/api";

const navigation = [
  ["/dashboard", "Overview", "◫"], ["/profile", "My profile", "◎"], ["/resume", "Master resume", "▤"],
  ["/jobs", "Jobs", "⌕"], ["/applications", "Applications", "↗"], ["/calendar", "Calendar", "▦"],
  ["/gmail", "Gmail activity", "✉"], ["/integrations", "Connected apps", "⌘"],
];

export function WorkspaceShell({ children, title }: { children: ReactNode; title: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const [account, setAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [connectionError, setConnectionError] = useState("");

  useEffect(() => {
    let active = true;
    const token = window.localStorage.getItem("applytrack_session");
    if (!token) { router.replace("/login"); return; }
    getAccount(token).then(value => { if (active) setAccount(value); }).catch(error => {
      if (error instanceof Error && error.message.includes("Can’t reach")) {
        if (active) setConnectionError(error.message);
      } else {
        window.localStorage.removeItem("applytrack_session");
        router.replace("/login");
      }
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [router]);

  async function signOut() {
    const token = window.localStorage.getItem("applytrack_session");
    if (token) await logout(token).catch(() => undefined);
    window.localStorage.removeItem("applytrack_session");
    router.replace("/login");
  }

  if (loading) return <div className="grid min-h-screen place-items-center text-sm text-muted">Loading your workspace…</div>;
  if (connectionError) return <div className="grid min-h-screen place-items-center p-6"><div className="max-w-md rounded-3xl border border-[#e5e9e0] bg-white p-8 shadow-soft"><p className="text-lg font-semibold">Couldn’t connect to ApplyTrack</p><p className="mt-2 text-sm leading-6 text-muted">{connectionError}</p><button onClick={() => window.location.reload()} className="mt-5 rounded-xl bg-forest px-4 py-2 text-sm font-semibold text-white">Try again</button></div></div>;
  if (!account) return null;

  return <div className="min-h-screen bg-paper">
    <aside className="fixed inset-y-0 left-0 z-20 hidden w-[250px] flex-col border-r border-[#e5e9e0] bg-white lg:flex">
      <Link href="/dashboard" className="flex h-[76px] items-center gap-3 border-b border-[#edf0e9] px-6"><span className="grid h-10 w-10 place-items-center rounded-2xl bg-forest text-lime"><BrandMark /></span><span className="text-lg font-bold tracking-tight">applytrack</span></Link>
      <div className="px-4 pt-7"><p className="px-3 text-[10px] font-bold uppercase tracking-[.18em] text-[#96a099]">Workspace</p><nav className="mt-3 space-y-1">{navigation.map(([href, label, icon]) => <NavLink key={href} href={href} label={label} icon={icon} active={pathname === href} />)}</nav></div>
      <div className="mt-auto p-4"><div className="rounded-2xl bg-[#f4f6ef] p-4"><p className="text-xs font-semibold text-ink">Keep your search grounded</p><p className="mt-2 text-xs leading-5 text-muted">Your profile and application history are private to your account.</p></div><button onClick={signOut} className="focus-ring mt-3 flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium text-[#647168] hover:bg-[#f6f7f2]"><span>↪</span> Sign out</button></div>
    </aside>
    <div className="lg:pl-[250px]">
      <header className="sticky top-0 z-10 border-b border-[#e5e9e0] bg-white/95 backdrop-blur"><div className="mx-auto flex h-[76px] max-w-[1440px] items-center justify-between px-5 sm:px-8"><div><p className="text-xs text-muted">ApplyTrack / Workspace</p><h1 className="mt-1 text-lg font-semibold">{title}</h1></div><div className="flex items-center gap-3"><span className="hidden max-w-[240px] truncate text-sm text-muted sm:block">{account.email}</span><span className="grid h-9 w-9 place-items-center rounded-full bg-[#e8efdf] text-sm font-bold text-forest">{(account.email[0] || "U").toUpperCase()}</span><button onClick={signOut} className="focus-ring rounded-xl border border-[#dfe5dc] px-3 py-2 text-sm font-semibold hover:bg-[#f6f7f2] lg:hidden">Exit</button></div></div>
        <nav className="flex gap-1 overflow-x-auto border-t border-[#f0f2ec] px-4 py-2 lg:hidden">{navigation.map(([href, label, icon]) => <NavLink key={href} href={href} label={label} icon={icon} active={pathname === href} compact />)}</nav>
      </header>
      <main className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 sm:py-10">{children}</main>
    </div>
  </div>;
}

function NavLink({ href, label, icon, active, compact = false }: { href: string; label: string; icon: string; active: boolean; compact?: boolean }) {
  return <Link href={href} className={`focus-ring flex shrink-0 items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${active ? "bg-[#edf3e4] text-forest" : "text-[#68756c] hover:bg-[#f6f7f2]"} ${compact ? "px-2.5 text-xs" : ""}`}><span className="w-5 text-center text-base">{icon}</span>{label}</Link>;
}

function BrandMark() { return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 17.5 10.2 6l3.1 7 2.2-4.2 3.5 8.7M5 19h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>; }

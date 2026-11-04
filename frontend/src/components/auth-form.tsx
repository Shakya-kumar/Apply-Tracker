"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { login, register } from "@/lib/api";

type Props = { mode: "login" | "register" };

export function AuthForm({ mode }: Props) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const isRegister = mode === "register";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const session = isRegister ? await register(email, password) : await login(email, password);
      window.localStorage.setItem("applytrack_session", session.access_token);
      router.replace("/dashboard");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-grid min-h-screen px-5 py-8 sm:px-8">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between">
        <Link href="/login" className="flex items-center gap-3 text-ink">
          <span className="grid h-10 w-10 place-items-center rounded-2xl bg-forest text-lime"><BrandMark /></span>
          <span className="text-lg font-bold tracking-tight">applytrack</span>
        </Link>
        <span className="hidden text-sm text-muted sm:block">A clearer way to move your career forward</span>
      </div>

      <div className="mx-auto grid min-h-[calc(100vh-100px)] w-full max-w-6xl items-center gap-12 py-12 lg:grid-cols-[1.1fr_.9fr] lg:gap-20">
        <section className="hidden max-w-xl lg:block">
          <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-[#dfe5d9] bg-white/75 px-4 py-2 text-xs font-semibold uppercase tracking-[.16em] text-moss">
            <span className="h-2 w-2 rounded-full bg-[#8dbb48]" /> Make your next move count
          </div>
          <h1 className="text-6xl font-semibold leading-[1.05] tracking-[-.055em] text-ink">Your search,<br />in <span className="text-moss">motion.</span></h1>
          <p className="mt-6 max-w-md text-lg leading-8 text-[#657169]">One calm place to organize the opportunities, applications and conversations moving your career forward.</p>
          <div className="mt-12 rounded-[28px] border border-[#e5e9e0] bg-white/80 p-6 shadow-soft">
            <div className="flex items-center justify-between border-b border-[#edf0e9] pb-5">
              <div><p className="text-sm font-semibold">A little more clarity</p><p className="mt-1 text-xs text-muted">Your job search, brought together</p></div>
              <span className="rounded-xl bg-[#f0f5e8] p-3 text-forest"><SparkIcon /></span>
            </div>
            <div className="mt-5 grid grid-cols-3 gap-3">
              {["Discover", "Prepare", "Track"].map((item, index) => <div key={item} className="rounded-2xl bg-[#f6f7f2] p-4"><span className="text-xs font-semibold text-moss">0{index + 1}</span><p className="mt-3 text-sm font-semibold">{item}</p></div>)}
            </div>
            <p className="mt-4 text-xs leading-5 text-muted">A preview of what you can organize as your ApplyTrack workspace grows.</p>
          </div>
        </section>

        <section className="mx-auto w-full max-w-md rounded-[30px] border border-[#e5e9e0] bg-white p-7 shadow-soft sm:p-10">
          <div className="mb-8 flex items-center gap-3 lg:hidden"><span className="grid h-10 w-10 place-items-center rounded-2xl bg-forest text-lime"><BrandMark /></span><span className="text-lg font-bold">applytrack</span></div>
          <div className="mb-8">
            <p className="text-sm font-semibold text-moss">{isRegister ? "YOUR NEXT CHAPTER STARTS HERE" : "WELCOME BACK"}</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight">{isRegister ? "Create your account" : "Sign in to ApplyTrack"}</h2>
            <p className="mt-2 text-sm leading-6 text-muted">{isRegister ? "Set up your private workspace and bring your search into focus." : "Pick up where you left off in your job search."}</p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-5">
            <label className="block"><span className="mb-2 block text-sm font-medium">Email address</span><input className="focus-ring h-12 w-full rounded-xl border border-[#dfe5dc] bg-[#fcfcfa] px-4 text-sm outline-none transition focus:border-moss" type="email" autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="you@example.com" required /></label>
            <label className="block"><span className="mb-2 block text-sm font-medium">Password</span><input className="focus-ring h-12 w-full rounded-xl border border-[#dfe5dc] bg-[#fcfcfa] px-4 text-sm outline-none transition focus:border-moss" type="password" autoComplete={isRegister ? "new-password" : "current-password"} value={password} onChange={event => setPassword(event.target.value)} placeholder={isRegister ? "At least 12 characters" : "Enter your password"} minLength={isRegister ? 12 : 1} required /></label>
            {error && <div role="alert" className="rounded-xl border border-[#f2c9bd] bg-[#fff5f1] px-4 py-3 text-sm leading-5 text-[#9b402b]">{error}</div>}
            <button disabled={busy} className="focus-ring flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-forest px-4 text-sm font-semibold text-white transition hover:bg-[#123d30] disabled:cursor-wait disabled:opacity-60">{busy ? "Please wait…" : isRegister ? "Create account" : "Sign in"}<ArrowIcon /></button>
          </form>
          <p className="mt-7 text-center text-sm text-muted">{isRegister ? "Already have an account?" : "New to ApplyTrack?"} <Link className="font-semibold text-forest hover:underline" href={isRegister ? "/login" : "/register"}>{isRegister ? "Sign in" : "Create an account"}</Link></p>
          <p className="mt-8 border-t border-[#edf0e9] pt-5 text-center text-xs leading-5 text-muted">By continuing, you agree to use ApplyTrack responsibly. Your workspace is private to your account.</p>
        </section>
      </div>
      <footer className="mx-auto flex w-full max-w-6xl justify-between text-xs text-[#8b948e]"><span>© 2026 ApplyTrack</span><span>Built for the next step</span></footer>
    </main>
  );
}

function BrandMark() { return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 17.5 10.2 6l3.1 7 2.2-4.2 3.5 8.7M5 19h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>; }
function ArrowIcon() { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>; }
function SparkIcon() { return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m12 3 1.7 6.3L20 11l-6.3 1.7L12 19l-1.7-6.3L4 11l6.3-1.7L12 3Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/><path d="m19 16 .7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7L19 16Z" fill="currentColor"/></svg>; }

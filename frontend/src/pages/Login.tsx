import React, { useState } from "react";
import { Navigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { errorMessage, post } from "@/api/client";
import { useAuth } from "@/context/AuthContext";

export default function Login() {
  const { me, refresh } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  if (me) return <Navigate to="/" replace />;
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await post("/auth/login", { email, password });
      await refresh();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#EFECE4] px-5">
      <form onSubmit={submit} className="w-full max-w-sm rounded-3xl bg-[#FDFBF7] p-8 shadow-sm fade-up" data-testid="login-form">
        <p className="eyebrow">Burlington, Ontario</p>
        <h1 className="mt-2 font-serif text-4xl tracking-tight text-stone-900">Excursion Curator</h1>
        <p className="mt-2 text-stone-600">A shared board for the two of you. Accounts are provisioned — there is no public sign-up.</p>
        <label className="mt-6 block text-sm font-medium text-stone-700" htmlFor="email">Email</label>
        <input id="email" data-testid="login-email-input" type="email" autoComplete="username" required className="input mt-1"
          value={email} onChange={(e) => setEmail(e.target.value)} />
        <label className="mt-4 block text-sm font-medium text-stone-700" htmlFor="password">Password</label>
        <input id="password" data-testid="login-password-input" type="password" autoComplete="current-password" required className="input mt-1"
          value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <p data-testid="login-error" role="alert" className="mt-3 text-sm text-red-700">{error}</p>}
        <button data-testid="login-submit-btn" disabled={busy} className="btn-primary mt-6 w-full">
          {busy && <Loader2 className="h-5 w-5 animate-spin" />} Sign in
        </button>
        <p className="mt-4 text-xs text-stone-500">Forgot your password? An administrator resets it (see README). No reset emails are sent in Phase 1.</p>
      </form>
    </div>
  );
}

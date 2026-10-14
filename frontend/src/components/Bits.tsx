import React from "react";
import { AlertTriangle, Loader2 } from "lucide-react";

export function Pill({ children, tone = "neutral", testId }: {
  children: React.ReactNode; tone?: "neutral" | "forest" | "clay" | "warn" | "demo" | "muted"; testId?: string;
}) {
  const tones = {
    neutral: "bg-stone-100 text-stone-700 border-stone-200",
    forest: "bg-[#E6EDE9] text-[#2D4A3E] border-[#CFDDD5]",
    clay: "bg-[#F7E7E0] text-[#8E4229] border-[#EDD0C3]",
    warn: "bg-amber-50 text-amber-800 border-amber-200",
    demo: "bg-[#2D4A3E] text-white border-[#2D4A3E]",
    muted: "bg-transparent text-stone-500 border-stone-300 border-dashed",
  };
  return (
    <span data-testid={testId} className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}

export const DemoBadge = ({ testId }: { testId?: string }) => (
  <Pill tone="demo" testId={testId}>DEMO · not a real recommendation</Pill>
);

export function Unknown({ children }: { children: React.ReactNode }) {
  return <span className="italic text-stone-500">{children}</span>;
}

export function PageHeader({ eyebrow, title, children }: { eyebrow?: string; title: string; children?: React.ReactNode }) {
  return (
    <header className="mb-6 fade-up">
      {eyebrow && <p className="eyebrow mb-2">{eyebrow}</p>}
      <h1 className="font-serif text-3xl sm:text-4xl tracking-tight text-stone-900">{title}</h1>
      {children && <div className="mt-2 text-stone-600 leading-relaxed">{children}</div>}
    </header>
  );
}

export function EmptyState({ icon, title, children, testId }: {
  icon?: React.ReactNode; title: string; children?: React.ReactNode; testId?: string;
}) {
  return (
    <div data-testid={testId} className="rounded-2xl border border-dashed border-stone-300 bg-[#F5F3ED] p-8 text-center fade-up">
      {icon && <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-white text-[#2D4A3E]">{icon}</div>}
      <h3 className="font-serif text-xl text-stone-800">{title}</h3>
      {children && <div className="mt-2 text-sm leading-relaxed text-stone-600">{children}</div>}
    </div>
  );
}

export const Loading = ({ label = "Loading" }: { label?: string }) => (
  <div data-testid="loading-state" className="flex items-center gap-3 py-10 text-stone-500" role="status">
    <Loader2 className="h-5 w-5 animate-spin" /> {label}…
  </div>
);

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div data-testid="error-state" role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-5 text-red-800">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
        <div>
          <p className="font-medium">Couldn't load this right now.</p>
          <p className="text-sm">{message}</p>
          {onRetry && (
            <button data-testid="error-retry-btn" onClick={onRetry} className="btn-secondary mt-3">Try again</button>
          )}
        </div>
      </div>
    </div>
  );
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="py-2">
      <dt className="eyebrow mb-1">{label}</dt>
      <dd className="text-[15px] leading-relaxed text-stone-800">{children}</dd>
    </div>
  );
}

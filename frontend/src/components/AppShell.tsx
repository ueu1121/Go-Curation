import React, { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { CalendarDays, Compass, History, Lightbulb, LogOut, Menu, MessageCircle, Settings2, Sparkles, Wrench, X } from "lucide-react";
import { useAuth, useMe } from "@/context/AuthContext";
import { useCurator } from "@/components/curator/CuratorContext";

const TABS = [
  { to: "/", label: "Today", icon: Compass, id: "today" },
  { to: "/upcoming", label: "Upcoming", icon: CalendarDays, id: "upcoming" },
  { to: "/ideas", label: "Our ideas", icon: Lightbulb, id: "ideas" },
  { to: "/history", label: "History", icon: History, id: "history" },
];

function SecondaryMenu({ onClose }: { onClose: () => void }) {
  const { logout } = useAuth();
  const me = useMe();
  const nav = useNavigate();
  const go = (to: string) => { onClose(); nav(to); };
  const items = [
    { to: "/preferences", label: "Preferences", icon: Settings2, id: "preferences" },
    { to: "/learned", label: "What the curator has learned", icon: Sparkles, id: "learned" },
    ...(me.member.is_admin ? [{ to: "/admin", label: "Admin: setup & candidates", icon: Wrench, id: "admin" }] : []),
  ];
  return (
    <div className="absolute right-4 top-16 z-40 w-72 rounded-2xl border border-stone-200 bg-white p-2 shadow-lg fade-up" data-testid="secondary-menu">
      <p className="px-3 py-2 text-sm text-stone-500">Signed in as {me.member.display_name}</p>
      {items.map((i) => (
        <button key={i.to} data-testid={`menu-${i.id}`} onClick={() => go(i.to)} className="menu-item"><i.icon className="h-5 w-5" />{i.label}</button>
      ))}
      <button data-testid="menu-logout" onClick={logout} className="menu-item text-red-700"><LogOut className="h-5 w-5" />Sign out</button>
    </div>
  );
}

function useKeyboardOpen(): boolean {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const vv = window.visualViewport;
    if (!vv) return undefined;
    const onResize = () => setOpen(window.innerHeight - vv.height > 150);
    vv.addEventListener("resize", onResize);
    return () => vv.removeEventListener("resize", onResize);
  }, []);
  return open;
}

export default function AppShell() {
  const [menu, setMenu] = useState(false);
  const keyboardOpen = useKeyboardOpen();
  const curator = useCurator();
  const { environment } = useMe();
  return (
    <div className="min-h-screen bg-[#EFECE4]">
      <div className="relative mx-auto min-h-screen max-w-lg bg-[#FDFBF7] pb-48 shadow-sm">
        <header className="sticky top-0 z-30 flex items-center justify-between border-b border-stone-200/70 bg-[#FDFBF7]/90 px-5 py-3 backdrop-blur-md">
          <div>
            <p className="font-serif text-lg leading-tight text-stone-900">Excursion Curator</p>
            <p className="text-xs text-stone-500">Burlington, ON · {environment.demo_mode ? "Demo mode on" : "Live records"}</p>
          </div>
          <button data-testid="menu-toggle-btn" aria-label="Menu" aria-expanded={menu} onClick={() => setMenu(!menu)}
            className="flex h-12 w-12 items-center justify-center rounded-full hover:bg-stone-100">
            {menu ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </header>
        {menu && <SecondaryMenu onClose={() => setMenu(false)} />}
        <main className="px-5 pt-6"><Outlet /></main>
        <footer className={`fixed bottom-0 left-1/2 z-30 w-full max-w-lg -translate-x-1/2 border-t border-stone-200 bg-white/95 backdrop-blur-md pb-[env(safe-area-inset-bottom)] ${keyboardOpen ? "hidden" : ""}`}
          data-testid="app-footer">
          <div className="px-4 pt-3">
            <button data-testid="tell-curator-fab" onClick={() => curator.open()}
              className="flex min-h-[48px] w-full items-center gap-3 rounded-full border border-[#E3C9BC] bg-[#FBF3EF] px-5 text-left text-[15px] text-[#8E4229] transition-colors hover:bg-[#F7E7E0]">
              <MessageCircle className="h-5 w-5 shrink-0" /> <span className="whitespace-nowrap font-medium">Tell the curator</span>
              <span className="hidden truncate text-sm text-stone-500 min-[400px]:inline">— an idea, a visit, a preference…</span>
            </button>
          </div>
          <nav className="grid grid-cols-4" aria-label="Primary">
            {TABS.map((t) => (
              <NavLink key={t.to} to={t.to} end data-testid={`nav-${t.id}`}
                className={({ isActive }) => `flex min-h-[60px] flex-col items-center justify-center gap-1 text-xs font-medium ${isActive ? "text-[#2D4A3E]" : "text-stone-500"}`}>
                <t.icon className="h-6 w-6" />{t.label}
              </NavLink>
            ))}
          </nav>
        </footer>
      </div>
    </div>
  );
}

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { get, post } from "@/api/client";
import type { Me } from "@/api/types";

interface AuthValue {
  me: Me | null | false;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
  nameOf: (memberId: string) => string;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [me, setMe] = useState<Me | null | false>(null);
  const refresh = useCallback(async () => {
    try {
      setMe(await get<Me>("/auth/me"));
    } catch {
      setMe(false);
    }
  }, []);
  useEffect(() => {
    refresh();
  }, [refresh]);
  const logout = async () => {
    try {
      await post("/auth/logout");
    } finally {
      setMe(false);
    }
  };
  const nameOf = (id: string) => (me ? me.members.find((m) => m.id === id)?.display_name ?? "Participant" : "");
  return <AuthContext.Provider value={{ me, refresh, logout, nameOf }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside AuthProvider");
  return ctx;
}

export function useMe(): Me {
  const { me } = useAuth();
  if (!me) throw new Error("useMe requires a signed-in participant");
  return me;
}

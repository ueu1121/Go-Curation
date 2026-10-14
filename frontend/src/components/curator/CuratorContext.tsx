import React, { createContext, useContext, useState } from "react";
import { CuratorSheet } from "@/components/curator/CuratorSheet";

export interface CuratorRef { batch_item_id?: string; title?: string }
interface CuratorValue { open: (ref?: CuratorRef, prefill?: string) => void }

const Ctx = createContext<CuratorValue>({ open: () => undefined });

export function CuratorProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<{ open: boolean; ref?: CuratorRef; prefill?: string }>({ open: false });
  return (
    <Ctx.Provider value={{ open: (ref, prefill) => setState({ open: true, ref, prefill }) }}>
      {children}
      {state.open && (
        <CuratorSheet contextRef={state.ref} prefill={state.prefill} onClose={() => setState({ open: false })} />
      )}
    </Ctx.Provider>
  );
}

export const useCurator = () => useContext(Ctx);

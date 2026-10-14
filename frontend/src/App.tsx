import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";
import "@/App.css";
import AppShell from "@/components/AppShell";
import { Loading } from "@/components/Bits";
import { CuratorProvider } from "@/components/curator/CuratorContext";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import Admin from "@/pages/Admin";
import History from "@/pages/History";
import Ideas from "@/pages/Ideas";
import Learned from "@/pages/Learned";
import Login from "@/pages/Login";
import Preferences from "@/pages/Preferences";
import Today from "@/pages/Today";
import Upcoming from "@/pages/Upcoming";

function Protected() {
  const { me } = useAuth();
  if (me === null) return <div className="px-6"><Loading label="Checking your session" /></div>;
  if (me === false) return <Navigate to="/login" replace />;
  return <CuratorProvider><AppShell /></CuratorProvider>;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<Protected />}>
            <Route path="/" element={<Today />} />
            <Route path="/upcoming" element={<Upcoming />} />
            <Route path="/ideas" element={<Ideas />} />
            <Route path="/history" element={<History />} />
            <Route path="/preferences" element={<Preferences />} />
            <Route path="/learned" element={<Learned />} />
            <Route path="/admin" element={<Admin />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-center" richColors />
    </AuthProvider>
  );
}

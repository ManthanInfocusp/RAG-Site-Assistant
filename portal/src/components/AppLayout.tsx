import { Link, Outlet } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";

export function AppLayout() {
  const { user, logout } = useAuth();
  return (
    <div className="min-h-full">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <Link to="/sites" className="text-lg font-semibold text-slate-900">
            RAG Site Assistant
          </Link>
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <span>{user?.email}</span>
            <button
              onClick={() => void logout()}
              className="rounded-md border border-slate-300 px-3 py-1 hover:bg-slate-50"
            >
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}

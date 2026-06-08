import { NavLink, Outlet, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";

import { Sites } from "@/lib/api";

const tabs = [
  { to: "knowledge", label: "Knowledge" },
  { to: "widget", label: "Widget" },
  { to: "conversations", label: "Conversations" },
  { to: "analytics", label: "Analytics" },
  { to: "settings", label: "Settings" },
];

export function SiteLayout() {
  const { siteId = "" } = useParams();
  const { data: site } = useQuery({
    queryKey: ["site", siteId],
    queryFn: () => Sites.get(siteId),
    enabled: !!siteId,
  });

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-slate-900">
          {site?.name || "Site"}
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Public key: <code className="font-mono">{site?.public_key}</code>
        </p>
      </div>
      <div className="mb-6 border-b border-slate-200">
        <nav className="flex gap-1">
          {tabs.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              className={({ isActive }) =>
                clsx(
                  "border-b-2 px-3 py-2 text-sm font-medium",
                  isActive
                    ? "border-slate-900 text-slate-900"
                    : "border-transparent text-slate-500 hover:text-slate-800",
                )
              }
            >
              {t.label}
            </NavLink>
          ))}
        </nav>
      </div>
      <Outlet context={{ site }} />
    </div>
  );
}

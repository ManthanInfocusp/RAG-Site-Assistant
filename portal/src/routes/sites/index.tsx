import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Sites } from "@/lib/api";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";

export function SitesIndex() {
  const qc = useQueryClient();
  const { data: sites, isLoading } = useQuery({
    queryKey: ["sites"],
    queryFn: Sites.list,
  });

  const [name, setName] = useState("");
  const [origins, setOrigins] = useState("");
  const create = useMutation({
    mutationFn: () => Sites.create({ name, allowed_origins: origins }),
    onSuccess: () => {
      setName("");
      setOrigins("");
      qc.invalidateQueries({ queryKey: ["sites"] });
    },
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    create.mutate();
  };

  return (
    <div>
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Your sites</h1>
          <p className="mt-1 text-sm text-slate-500">
            Each site is an isolated knowledge base + chat widget.
          </p>
        </div>
      </div>

      <form
        onSubmit={onSubmit}
        className="mb-8 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
      >
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-600">
          New site
        </h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Input
            placeholder="Display name (e.g. acme.com)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Input
            placeholder="Allowed origins (comma-separated)"
            value={origins}
            onChange={(e) => setOrigins(e.target.value)}
          />
          <Button type="submit" disabled={create.isPending}>
            {create.isPending ? "Creating…" : "Create site"}
          </Button>
        </div>
      </form>

      {isLoading ? (
        <p className="text-slate-500">Loading…</p>
      ) : !sites || sites.length === 0 ? (
        <p className="text-slate-500">No sites yet — create your first one above.</p>
      ) : (
        <ul className="space-y-2">
          {sites.map((s) => (
            <li
              key={s.id}
              className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4 hover:border-slate-300"
            >
              <div>
                <Link
                  to={`/sites/${s.id}/knowledge`}
                  className="font-medium text-slate-900 hover:underline"
                >
                  {s.name}
                </Link>
                <div className="mt-1 text-xs text-slate-500">
                  Origins: {s.allowed_origins || "—"}
                </div>
              </div>
              <code className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-700">
                {s.public_key}
              </code>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

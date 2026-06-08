import { useEffect, useState, type FormEvent } from "react";
import { useOutletContext, useParams } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Sites, type Site } from "@/lib/api";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";

export function SettingsTab() {
  const { site } = useOutletContext<{ site: Site | undefined }>();
  const { siteId = "" } = useParams();
  const qc = useQueryClient();

  const [name, setName] = useState("");
  const [origins, setOrigins] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");

  useEffect(() => {
    if (site) {
      setName(site.name);
      setOrigins(site.allowed_origins);
      setSystemPrompt(site.system_prompt ?? "");
    }
  }, [site]);

  const update = useMutation({
    mutationFn: () =>
      Sites.update(siteId, {
        name,
        allowed_origins: origins,
        system_prompt: systemPrompt.trim() || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["site", siteId] });
    },
  });

  const remove = useMutation({
    mutationFn: () => Sites.remove(siteId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sites"] });
      window.location.href = "/sites";
    },
  });

  if (!site) return null;

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    update.mutate();
  };

  return (
    <div className="grid gap-6">
      <form
        onSubmit={onSubmit}
        className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
      >
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-600">
          Site details
        </h2>
        <label className="mb-3 block">
          <span className="mb-1 block text-sm font-medium text-slate-700">Name</span>
          <Input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label className="mb-3 block">
          <span className="mb-1 block text-sm font-medium text-slate-700">
            Allowed origins (comma-separated)
          </span>
          <Input
            value={origins}
            onChange={(e) => setOrigins(e.target.value)}
            placeholder="https://example.com,https://www.example.com"
          />
        </label>
        <label className="mb-4 block">
          <span className="mb-1 block text-sm font-medium text-slate-700">System prompt</span>
          <textarea
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            rows={6}
            placeholder={`Leave blank to use the default system prompt.\n\nExample:\nYou are a helpful assistant for Acme Corp. Answer only in English. Always recommend contacting support@acme.com for billing questions.`}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm font-mono text-slate-900 placeholder:font-sans placeholder:text-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
          />
          <p className="mt-1 text-xs text-slate-400">
            Overrides the default assistant instructions. The context block and citation rules
            are always appended automatically — focus on tone, language, and domain constraints.
          </p>
        </label>
        <Button type="submit" disabled={update.isPending}>
          {update.isPending ? "Saving…" : "Save"}
        </Button>
        {update.isSuccess && <span className="ml-3 text-sm text-green-600">Saved!</span>}
      </form>

      <div className="rounded-xl border border-red-200 bg-white p-4 shadow-sm">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-red-700">
          Danger zone
        </h2>
        <p className="mb-3 text-sm text-slate-500">
          Deleting a site removes all its data sources, documents, chunks, and conversations.
          This cannot be undone.
        </p>
        <Button
          variant="danger"
          onClick={() => {
            if (confirm(`Delete site "${site.name}"? This is irreversible.`)) {
              remove.mutate();
            }
          }}
        >
          Delete site
        </Button>
      </div>
    </div>
  );
}

import { useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import axios from "axios";

import { Sources, type DataSource } from "@/lib/api";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";

export function KnowledgeTab() {
  const { siteId = "" } = useParams();
  const qc = useQueryClient();

  const { data: sources, isLoading } = useQuery({
    queryKey: ["sources", siteId],
    queryFn: () => Sources.list(siteId),
    refetchInterval: (q) => {
      const data = q.state.data as DataSource[] | undefined;
      const hasRunning = data?.some((s) => s.status === "pending" || s.status === "running");
      return hasRunning ? 3000 : false;
    },
  });

  const [url, setUrl] = useState("");
  const [maxPages, setMaxPages] = useState(50);
  const [maxDepth, setMaxDepth] = useState(2);
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const createUrl = useMutation({
    mutationFn: () =>
      Sources.createUrl(siteId, { url, max_pages: maxPages, max_depth: maxDepth }),
    onSuccess: () => {
      setUrl("");
      qc.invalidateQueries({ queryKey: ["sources", siteId] });
    },
  });

  const resync = useMutation({
    mutationFn: (id: string) => Sources.resync(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources", siteId] }),
  });

  const remove = useMutation({
    mutationFn: (id: string) => Sources.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources", siteId] }),
  });

  const onUploadChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    setUploading(true);
    try {
      const keys: string[] = [];
      const names: string[] = [];
      for (const f of files) {
        const presigned = await Sources.presign(siteId, f.name, f.type || "application/octet-stream");
        await axios.put(presigned.upload_url, f, {
          headers: { "Content-Type": f.type || "application/octet-stream" },
        });
        keys.push(presigned.s3_key);
        names.push(f.name);
      }
      await Sources.createUpload(siteId, { s3_keys: keys, original_names: names });
      qc.invalidateQueries({ queryKey: ["sources", siteId] });
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const onUrlSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    createUrl.mutate();
  };

  return (
    <div className="grid gap-6">
      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-600">
          Add a URL source
        </h2>
        <form onSubmit={onUrlSubmit} className="grid grid-cols-1 gap-3 md:grid-cols-4">
          <Input
            className="md:col-span-2"
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
          <Input
            type="number"
            min={1}
            max={500}
            value={maxPages}
            onChange={(e) => setMaxPages(Number(e.target.value))}
            placeholder="Max pages"
          />
          <div className="flex gap-2">
            <Input
              type="number"
              min={1}
              max={10}
              value={maxDepth}
              onChange={(e) => setMaxDepth(Number(e.target.value))}
              placeholder="Max depth"
            />
            <Button type="submit" disabled={createUrl.isPending}>
              {createUrl.isPending ? "Queueing…" : "Crawl"}
            </Button>
          </div>
        </form>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-600">
          Upload documents
        </h2>
        <p className="mb-3 text-sm text-slate-500">PDF, DOCX, TXT, MD, HTML.</p>
        <input
          ref={fileRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.md,.html,.htm"
          onChange={onUploadChange}
          disabled={uploading}
          className="text-sm"
        />
        {uploading && <p className="mt-2 text-sm text-slate-500">Uploading…</p>}
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-600">
          Data sources
        </h2>
        {isLoading ? (
          <p className="text-slate-500">Loading…</p>
        ) : !sources || sources.length === 0 ? (
          <p className="text-slate-500">No data sources yet.</p>
        ) : (
          <ul className="space-y-2">
            {sources.map((s) => (
              <li
                key={s.id}
                className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-sm font-medium text-slate-900">
                      {s.type === "url"
                        ? String((s.config as any)?.url || "URL source")
                        : `${((s.config as any)?.original_names || []).length} file(s)`}
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      Status: <StatusBadge status={s.status} />
                      {s.stats && Object.keys(s.stats).length > 0 ? (
                        <>
                          {" "}
                          · {Object.entries(s.stats).map(([k, v]) => `${k}=${v}`).join(", ")}
                        </>
                      ) : null}
                    </div>
                    {s.error_message && (
                      <div className="mt-1 text-xs text-red-600">{s.error_message}</div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      onClick={() => resync.mutate(s.id)}
                      disabled={resync.isPending || s.status === "running"}
                    >
                      Re-sync
                    </Button>
                    <Button
                      variant="danger"
                      onClick={() => {
                        if (confirm("Delete this source and all its chunks?")) {
                          remove.mutate(s.id);
                        }
                      }}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "ready"
      ? "bg-green-100 text-green-800"
      : status === "running" || status === "pending"
      ? "bg-amber-100 text-amber-800"
      : status === "failed"
      ? "bg-red-100 text-red-800"
      : "bg-slate-100 text-slate-800";
  return (
    <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${color}`}>{status}</span>
  );
}

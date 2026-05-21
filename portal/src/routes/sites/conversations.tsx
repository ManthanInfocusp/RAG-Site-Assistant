import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { Conversations } from "@/lib/api";

export function ConversationsTab() {
  const { siteId = "" } = useParams();
  const [selected, setSelected] = useState<string | null>(null);

  const { data: convos, isLoading } = useQuery({
    queryKey: ["conversations", siteId],
    queryFn: () => Conversations.list(siteId),
  });
  const { data: convo } = useQuery({
    queryKey: ["conversation", selected],
    queryFn: () => Conversations.get(selected!),
    enabled: !!selected,
  });

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-[280px_1fr]">
      <aside className="rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
        {isLoading ? (
          <p className="p-2 text-sm text-slate-500">Loading…</p>
        ) : !convos || convos.length === 0 ? (
          <p className="p-2 text-sm text-slate-500">No conversations yet.</p>
        ) : (
          <ul className="space-y-1">
            {convos.map((c) => (
              <li key={c.id}>
                <button
                  onClick={() => setSelected(c.id)}
                  className={`block w-full rounded-md px-2 py-1.5 text-left text-sm hover:bg-slate-100 ${
                    selected === c.id ? "bg-slate-100 font-medium" : ""
                  }`}
                >
                  <div className="truncate">{c.visitor_id || c.id.slice(0, 8)}</div>
                  <div className="text-xs text-slate-500">
                    {new Date(c.created_at).toLocaleString()}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </aside>
      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        {!convo ? (
          <p className="text-sm text-slate-500">Select a conversation to view messages.</p>
        ) : (
          <div className="space-y-3">
            {convo.messages.map((m) => (
              <div key={m.id}>
                <div className="text-[10px] uppercase tracking-wide text-slate-500">
                  {m.role}
                </div>
                <div className="whitespace-pre-wrap text-sm text-slate-900">{m.content}</div>
                {m.citations?.length > 0 && (
                  <div className="mt-1 text-xs text-slate-500">
                    {m.citations.map((c) => (
                      <span key={c.chunk_id} className="mr-2">
                        [{c.index}] {c.title || c.source_uri}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

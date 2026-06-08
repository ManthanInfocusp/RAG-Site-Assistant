import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { Analytics, type AnalyticsData } from "@/lib/api";

export function AnalyticsTab() {
  const { siteId = "" } = useParams();

  const { data, isLoading, isError } = useQuery<AnalyticsData>({
    queryKey: ["analytics", siteId],
    queryFn: () => Analytics.get(siteId),
    enabled: !!siteId,
    refetchInterval: 60_000,
  });

  if (isLoading) return <p className="text-slate-500">Loading analytics…</p>;
  if (isError || !data) return <p className="text-red-500">Failed to load analytics.</p>;

  const maxDaily = Math.max(...data.daily_conversations.map((d) => d.count), 1);

  return (
    <div className="grid gap-6">
      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Total conversations" value={data.total_conversations} />
        <StatCard label="Total messages" value={data.total_messages} />
        <StatCard label="Today" value={data.conversations_today} />
        <StatCard label="Last 7 days" value={data.conversations_last_7d} />
      </div>

      {/* Daily chart */}
      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-600">
          Conversations — last 30 days
        </h2>
        {data.daily_conversations.length === 0 ? (
          <p className="text-sm text-slate-400">No conversations yet.</p>
        ) : (
          <div className="flex h-40 items-end gap-1 overflow-x-auto">
            {data.daily_conversations.map((d) => (
              <div key={d.date} className="group relative flex flex-1 flex-col items-center">
                <div
                  className="w-full min-w-[8px] rounded-t bg-slate-800 transition-colors group-hover:bg-slate-600"
                  style={{ height: `${Math.max(4, (d.count / maxDaily) * 140)}px` }}
                />
                <span className="mt-1 hidden text-[9px] text-slate-400 group-hover:block absolute -top-5 bg-white border border-slate-200 rounded px-1 py-0.5 whitespace-nowrap z-10">
                  {d.date}: {d.count}
                </span>
                <span className="mt-1 block text-[8px] text-slate-300 rotate-45 origin-left">
                  {d.date.slice(5)}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Top cited sources */}
        <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-600">
            Top cited sources
          </h2>
          {data.top_sources.length === 0 ? (
            <p className="text-sm text-slate-400">No citations yet.</p>
          ) : (
            <ul className="space-y-2">
              {data.top_sources.map((src, i) => (
                <li key={src.source_uri} className="flex items-start gap-2 text-sm">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-bold text-slate-600">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <a
                      href={src.source_uri.startsWith("http") ? src.source_uri : undefined}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="truncate block font-medium text-slate-800 hover:underline"
                      title={src.source_uri}
                    >
                      {src.title || src.source_uri}
                    </a>
                    <span className="text-xs text-slate-400">{src.citation_count} citation{src.citation_count !== 1 ? "s" : ""}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Recent questions */}
        <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-600">
            Recent questions
          </h2>
          {data.recent_questions.length === 0 ? (
            <p className="text-sm text-slate-400">No questions yet.</p>
          ) : (
            <ul className="space-y-1.5">
              {data.recent_questions.map((q, i) => (
                <li
                  key={i}
                  className="truncate rounded bg-slate-50 px-3 py-1.5 text-sm text-slate-700"
                  title={q}
                >
                  {q}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-semibold text-slate-900">{value.toLocaleString()}</p>
    </div>
  );
}

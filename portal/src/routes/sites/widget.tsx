import { useOutletContext } from "react-router-dom";
import type { Site } from "@/lib/api";

export function WidgetTab() {
  const { site } = useOutletContext<{ site: Site | undefined }>();
  if (!site) return null;

  const port = window.location.port ? `:${window.location.port}` : "";
  const cdnHost = `${window.location.protocol}//cdn.localhost${port}`;
  const snippet = `<script async src="${cdnHost}/chat.js" data-site-key="${site.public_key}"></script>`;

  return (
    <div className="grid gap-6">
      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-600">
          Embed snippet
        </h2>
        <p className="mb-3 text-sm text-slate-500">
          Paste this just before the closing <code>&lt;/body&gt;</code> tag of any page on
          your site.
        </p>
        <pre className="overflow-x-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
          <code>{snippet}</code>
        </pre>
        <button
          onClick={() => navigator.clipboard.writeText(snippet)}
          className="mt-3 rounded-md border border-slate-300 bg-white px-3 py-1 text-sm hover:bg-slate-50"
        >
          Copy
        </button>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-600">
          Live preview
        </h2>
        <p className="mb-3 text-sm text-slate-500">
          The widget below loads using your site's public key.
        </p>
        <iframe
          title="Widget preview"
          srcDoc={`<!doctype html><html><body style="font-family:system-ui;padding:24px"><h2>Your site preview</h2><p>The chat launcher appears in the bottom-right corner.</p><script async src="${cdnHost}/chat.js" data-site-key="${site.public_key}"></script></body></html>`}
          className="h-96 w-full rounded border border-slate-200"
        />
      </section>
    </div>
  );
}

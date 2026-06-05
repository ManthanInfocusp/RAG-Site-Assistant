import { useEffect, useState, type FormEvent } from "react";
import { useOutletContext, useParams } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Sites, type Site } from "@/lib/api";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";

export function WidgetTab() {
  const { site } = useOutletContext<{ site: Site | undefined }>();
  const { siteId = "" } = useParams();
  const qc = useQueryClient();

  const [displayName, setDisplayName] = useState("");
  const [logoUrl, setLogoUrl] = useState("");
  const [welcomeMessage, setWelcomeMessage] = useState("");
  const [collectVisitorInfo, setCollectVisitorInfo] = useState(false);
  const [visitorInfoLabel, setVisitorInfoLabel] = useState("");
  const [visitorInfoRequired, setVisitorInfoRequired] = useState(false);

  useEffect(() => {
    if (site) {
      setDisplayName(site.name);
      setLogoUrl((site.widget_config.logo_url as string | undefined) ?? "");
      setWelcomeMessage((site.widget_config.welcome_message as string | undefined) ?? "");
      setCollectVisitorInfo(!!(site.widget_config.collect_visitor_info as boolean | undefined));
      setVisitorInfoLabel((site.widget_config.visitor_info_label as string | undefined) ?? "");
      setVisitorInfoRequired(!!(site.widget_config.visitor_info_required as boolean | undefined));
    }
  }, [site]);

  const updateAppearance = useMutation({
    mutationFn: () =>
      Sites.update(siteId, {
        name: displayName,
        widget_config: {
          ...site?.widget_config,
          logo_url: logoUrl || undefined,
          welcome_message: welcomeMessage || undefined,
          collect_visitor_info: collectVisitorInfo || undefined,
          visitor_info_label: visitorInfoLabel || undefined,
          visitor_info_required: visitorInfoRequired || undefined,
        },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["site", siteId] });
    },
  });

  if (!site) return null;

  const port = window.location.port ? `:${window.location.port}` : "";
  const cdnHost = `${window.location.protocol}//cdn.localhost${port}`;
  const snippet = `<script async src="${cdnHost}/chat.js" data-site-key="${site.public_key}"></script>`;

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    updateAppearance.mutate();
  };

  return (
    <div className="grid gap-6">
      <form
        onSubmit={onSubmit}
        className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
      >
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-600">
          Widget appearance
        </h2>

        <label className="mb-3 block">
          <span className="mb-1 block text-sm font-medium text-slate-700">Display name</span>
          <Input
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Site assistant"
            required
          />
          <p className="mt-1 text-xs text-slate-400">Shown in the chat panel header.</p>
        </label>

        <label className="mb-3 block">
          <span className="mb-1 block text-sm font-medium text-slate-700">Logo URL</span>
          <Input
            type="url"
            value={logoUrl}
            onChange={(e) => setLogoUrl(e.target.value)}
            placeholder="https://example.com/logo.png"
          />
          <p className="mt-1 text-xs text-slate-400">
            Shown in the chat panel header and as the launcher button icon. Leave blank to use
            the default chat bubble icon.
          </p>
        </label>

        {logoUrl && (
          <div className="mb-3 flex items-center gap-3">
            <img
              src={logoUrl}
              alt="Logo preview"
              className="h-10 w-10 rounded-full object-cover border border-slate-200"
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).style.display = "none";
              }}
            />
            <span className="text-xs text-slate-400">Logo preview</span>
          </div>
        )}

        <label className="mb-4 block">
          <span className="mb-1 block text-sm font-medium text-slate-700">Welcome message</span>
          <Input
            value={welcomeMessage}
            onChange={(e) => setWelcomeMessage(e.target.value)}
            placeholder="Hi! Ask me anything about this site."
          />
          <p className="mt-1 text-xs text-slate-400">
            First message shown to visitors when the chat opens.
          </p>
        </label>

        <div className="mb-4 rounded-lg border border-slate-200 p-3">
          <label className="mb-2 flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={collectVisitorInfo}
              onChange={(e) => setCollectVisitorInfo(e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 accent-slate-800"
            />
            <span className="text-sm font-medium text-slate-700">Collect visitor identity</span>
          </label>
          <p className="mb-3 text-xs text-slate-400">
            When enabled, visitors are prompted to enter an identifier (e.g. email or name)
            before chatting. It appears in the Conversations view.
          </p>

          {collectVisitorInfo && (
            <div className="space-y-3 pl-6">
              <label className="block">
                <span className="mb-1 block text-xs font-medium text-slate-600">Prompt label</span>
                <Input
                  value={visitorInfoLabel}
                  onChange={(e) => setVisitorInfoLabel(e.target.value)}
                  placeholder="Enter your email or name to get started"
                />
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={visitorInfoRequired}
                  onChange={(e) => setVisitorInfoRequired(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 accent-slate-800"
                />
                <span className="text-xs text-slate-600">Required (visitors cannot skip)</span>
              </label>
            </div>
          )}
        </div>

        <Button type="submit" disabled={updateAppearance.isPending}>
          {updateAppearance.isPending ? "Saving…" : "Save appearance"}
        </Button>
        {updateAppearance.isSuccess && (
          <span className="ml-3 text-sm text-green-600">Saved!</span>
        )}
      </form>

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

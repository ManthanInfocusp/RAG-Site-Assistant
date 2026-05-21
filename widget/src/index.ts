/**
 * Embed widget entrypoint. Bundled to a single iife `chat.js` and served by
 * Traefik. Site owners include:
 *
 *   <script async src="https://cdn.../chat.js" data-site-key="pk_..."></script>
 *
 * The script reads `data-site-key`, fetches widget config from the API, and
 * mounts a Shadow DOM chat panel.
 */

import { css } from "./styles";
import { sseFetch } from "./sse";

interface ScriptConfig {
  siteKey: string;
  apiBase: string;
  chatBase: string;
}

interface Citation {
  index: number;
  source_uri: string;
  title: string | null;
}

(function bootstrap() {
  const cfg = readConfig();
  if (!cfg) return;
  // Defer until DOM is interactive.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => mount(cfg));
  } else {
    mount(cfg);
  }
})();

function readConfig(): ScriptConfig | null {
  const script =
    (document.currentScript as HTMLScriptElement | null) ||
    (document.querySelector("script[data-site-key]") as HTMLScriptElement | null);
  if (!script) {
    console.warn("[rag-widget] script element with data-site-key not found");
    return null;
  }
  const siteKey = script.dataset.siteKey;
  if (!siteKey) {
    console.warn("[rag-widget] missing data-site-key");
    return null;
  }
  // The widget is served from cdn.<host>; derive api + chat hostnames by
  // swapping the subdomain. Allow override via data-attrs.
  const url = new URL(script.src);
  const host = url.hostname;
  const portSuffix = url.port ? `:${url.port}` : "";
  const apiHost = script.dataset.apiHost || host.replace(/^cdn\./, "api.") + portSuffix;
  const chatHost = script.dataset.chatHost || host.replace(/^cdn\./, "chat.") + portSuffix;
  return {
    siteKey,
    apiBase: `${url.protocol}//${apiHost}`,
    chatBase: `${url.protocol}//${chatHost}`,
  };
}

async function mount(cfg: ScriptConfig) {
  let widgetConfig: { name?: string; widget_config?: Record<string, unknown> } = {};
  try {
    const resp = await fetch(
      `${cfg.apiBase}/v1/widget/config?key=${encodeURIComponent(cfg.siteKey)}`,
    );
    if (resp.ok) widgetConfig = await resp.json();
  } catch (err) {
    console.warn("[rag-widget] failed to load config", err);
  }

  const host = document.createElement("div");
  host.id = "rag-widget-host";
  document.body.appendChild(host);
  const shadow = host.attachShadow({ mode: "open" });
  const style = document.createElement("style");
  style.textContent = css;
  shadow.appendChild(style);

  const launcher = document.createElement("button");
  launcher.className = "rag-launcher";
  launcher.title = "Chat";
  launcher.innerHTML = "&#128172;";
  shadow.appendChild(launcher);

  const panel = document.createElement("div");
  panel.className = "rag-panel";
  panel.innerHTML = `
    <div class="rag-header">
      <span>${escapeHtml(String(widgetConfig.name || "Site assistant"))}</span>
      <button class="rag-close" title="Close">&times;</button>
    </div>
    <div class="rag-messages"></div>
    <div class="rag-input-row">
      <textarea class="rag-input" rows="1" placeholder="Ask a question…"></textarea>
      <button class="rag-send">Send</button>
    </div>
  `;
  shadow.appendChild(panel);

  const messagesEl = panel.querySelector(".rag-messages") as HTMLElement;
  const inputEl = panel.querySelector(".rag-input") as HTMLTextAreaElement;
  const sendBtn = panel.querySelector(".rag-send") as HTMLButtonElement;
  const closeBtn = panel.querySelector(".rag-close") as HTMLButtonElement;

  launcher.addEventListener("click", () => panel.classList.toggle("open"));
  closeBtn.addEventListener("click", () => panel.classList.remove("open"));

  const visitorId = ensureVisitorId();
  let conversationId: string | null = null;
  let inflight = false;

  const welcome =
    (widgetConfig.widget_config?.welcome_message as string | undefined) ||
    "Hi! Ask me anything about this site.";
  appendMessage(messagesEl, "assistant", welcome, []);

  async function send() {
    const text = inputEl.value.trim();
    if (!text || inflight) return;
    inflight = true;
    inputEl.value = "";
    sendBtn.disabled = true;

    appendMessage(messagesEl, "user", text, []);
    const assistantBubble = appendMessage(messagesEl, "assistant", "", []);

    try {
      const body = {
        site_key: cfg.siteKey,
        message: text,
        conversation_id: conversationId,
        visitor_id: visitorId,
      };
      let pendingCitations: Citation[] = [];
      for await (const ev of sseFetch(`${cfg.chatBase}/v1/chat/stream`, body)) {
        if (ev.event === "ready") {
          try {
            conversationId = JSON.parse(ev.data).conversation_id;
          } catch {
            /* ignore */
          }
        } else if (ev.event === "citations") {
          try {
            pendingCitations = JSON.parse(ev.data);
          } catch {
            pendingCitations = [];
          }
        } else if (ev.event === "delta") {
          assistantBubble.text.textContent += ev.data;
          messagesEl.scrollTop = messagesEl.scrollHeight;
        } else if (ev.event === "error") {
          assistantBubble.text.textContent = "Sorry, something went wrong.";
        } else if (ev.event === "done") {
          renderCitations(assistantBubble.cites, pendingCitations);
        }
      }
    } catch (err) {
      assistantBubble.text.textContent = "Sorry, the assistant is unreachable.";
      console.error(err);
    } finally {
      inflight = false;
      sendBtn.disabled = false;
      inputEl.focus();
    }
  }

  sendBtn.addEventListener("click", () => void send());
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  });
}

function appendMessage(
  container: HTMLElement,
  role: "user" | "assistant",
  text: string,
  citations: Citation[],
): { text: HTMLElement; cites: HTMLElement } {
  const wrapper = document.createElement("div");
  wrapper.className = `rag-msg ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "rag-bubble";
  bubble.textContent = text;
  const cites = document.createElement("div");
  cites.className = "rag-citations";
  wrapper.appendChild(bubble);
  wrapper.appendChild(cites);
  container.appendChild(wrapper);
  container.scrollTop = container.scrollHeight;
  renderCitations(cites, citations);
  return { text: bubble, cites };
}

function renderCitations(el: HTMLElement, citations: Citation[]) {
  el.innerHTML = "";
  if (!citations || citations.length === 0) return;
  for (const c of citations) {
    const a = document.createElement("a");
    a.href = c.source_uri;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = `[${c.index}] ${c.title || c.source_uri}`;
    el.appendChild(a);
  }
}

function ensureVisitorId(): string {
  try {
    const KEY = "rag-visitor-id";
    let id = localStorage.getItem(KEY);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(KEY, id);
    }
    return id;
  } catch {
    return Math.random().toString(36).slice(2);
  }
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

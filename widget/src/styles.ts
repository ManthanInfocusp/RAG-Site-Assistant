// All widget styles live in a single string and are injected into the Shadow
// DOM. This guarantees the host site's CSS can't bleed in and we don't pollute
// the global stylesheet.

export const css = `
:host { all: initial; }
* { box-sizing: border-box; }

.rag-launcher {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 56px;
  height: 56px;
  border-radius: 9999px;
  background: #0f172a;
  color: white;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  font-size: 24px;
  display: grid;
  place-items: center;
  z-index: 2147483647;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}

.rag-panel {
  position: fixed;
  bottom: 90px;
  right: 20px;
  width: 380px;
  max-width: calc(100vw - 40px);
  height: 560px;
  max-height: calc(100vh - 120px);
  background: white;
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0,0,0,0.2);
  overflow: hidden;
  display: none;
  flex-direction: column;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  color: #0f172a;
  z-index: 2147483647;
}

.rag-panel.open { display: flex; }

.rag-header {
  padding: 12px 16px;
  background: #0f172a;
  color: white;
  font-weight: 600;
  font-size: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rag-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
}

.rag-header-logo {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.rag-launcher-logo {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  object-fit: cover;
}

.rag-close {
  background: transparent;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}

.rag-identity-form {
  padding: 14px 16px;
  background: #f1f5f9;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.rag-identity-prompt {
  margin: 0 0 8px 0;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.rag-identity-input {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 7px 10px;
  font-size: 13px;
  font-family: inherit;
  color: #0f172a;
  outline: none;
  margin-bottom: 8px;
  box-sizing: border-box;
}

.rag-identity-input:focus {
  border-color: #94a3b8;
  box-shadow: 0 0 0 2px rgba(15,23,42,0.08);
}

.rag-identity-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rag-identity-submit {
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 6px 14px;
  cursor: pointer;
  font-weight: 500;
  font-size: 13px;
  font-family: inherit;
}

.rag-identity-skip {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 12px;
  color: #64748b;
  font-family: inherit;
  text-decoration: underline;
  padding: 0;
}

.rag-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  background: #f8fafc;
  font-size: 14px;
}

.rag-msg {
  margin-bottom: 12px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.rag-msg.user .rag-bubble {
  background: #0f172a;
  color: white;
  align-self: flex-end;
}
.rag-msg.assistant .rag-bubble {
  background: white;
  color: #0f172a;
  border: 1px solid #e2e8f0;
}
.rag-msg {
  display: flex;
  flex-direction: column;
}
.rag-msg.user { align-items: flex-end; }
.rag-msg.assistant { align-items: flex-start; }
.rag-bubble {
  display: inline-block;
  padding: 8px 12px;
  border-radius: 12px;
  max-width: 85%;
}

.rag-citations {
  margin-top: 4px;
  font-size: 11px;
  color: #64748b;
}
.rag-citations a {
  color: #475569;
  text-decoration: underline;
  margin-right: 6px;
}

.rag-typing {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 4px;
}
.rag-typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #94a3b8;
  animation: rag-bounce 1.1s ease-in-out infinite;
}
.rag-typing span:nth-child(2) { animation-delay: 0.18s; }
.rag-typing span:nth-child(3) { animation-delay: 0.36s; }
@keyframes rag-bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
  30% { transform: translateY(-5px); opacity: 1; }
}

.rag-input-row {
  display: flex;
  padding: 10px;
  gap: 8px;
  border-top: 1px solid #e2e8f0;
  background: white;
}

.rag-input {
  flex: 1;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 14px;
  font-family: inherit;
  color: #0f172a;
  outline: none;
  resize: none;
  min-height: 40px;
  max-height: 120px;
}

.rag-send {
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0 14px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
}
.rag-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
`;

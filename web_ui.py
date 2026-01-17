from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Dict, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.config import config
from app.harness.recording import RunRecorder


if TYPE_CHECKING:
    from app.agent.manus import Manus


LOG_DIR = config.root_path / "logs" / "runs"


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ResetRequest(BaseModel):
    session_id: str


class SessionState:
    def __init__(self, session_id: str, agent: Manus, recorder: RunRecorder) -> None:
        self.session_id = session_id
        self.agent = agent
        self.recorder = recorder
        self.lock = asyncio.Lock()


app = FastAPI()
_sessions: Dict[str, SessionState] = {}
_sessions_lock = asyncio.Lock()


def _html_page() -> str:
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>OpenManus Studio</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600&family=Libre+Baskerville:ital@0;1&display=swap');

    :root {
      --bg-a: #f6f1e6;
      --bg-b: #ffe8d6;
      --bg-c: #d7f3ef;
      --ink: #1b1b1b;
      --muted: #5b5b5b;
      --accent: #0f766e;
      --accent-2: #ef6f55;
      --card: rgba(255, 255, 255, 0.86);
      --stroke: rgba(27, 27, 27, 0.1);
      --shadow: 0 24px 60px rgba(22, 30, 29, 0.12);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: 'Space Grotesk', sans-serif;
      background: radial-gradient(circle at 10% 20%, var(--bg-c), transparent 48%),
                  radial-gradient(circle at 90% 15%, var(--bg-b), transparent 45%),
                  linear-gradient(135deg, var(--bg-a), #fffaf3 60%);
      overflow-x: hidden;
    }

    .orb {
      position: fixed;
      border-radius: 50%;
      filter: blur(0px);
      opacity: 0.22;
      z-index: 0;
      animation: float 18s ease-in-out infinite;
    }

    .orb.one {
      width: 260px;
      height: 260px;
      background: var(--accent);
      top: -80px;
      right: -40px;
      animation-delay: 1s;
    }

    .orb.two {
      width: 220px;
      height: 220px;
      background: var(--accent-2);
      bottom: -90px;
      left: -60px;
      animation-delay: 3s;
    }

    .shell {
      position: relative;
      z-index: 1;
      max-width: 1040px;
      margin: 0 auto;
      padding: 48px 24px 64px;
      display: grid;
      gap: 28px;
    }

    header {
      display: grid;
      gap: 12px;
      animation: rise 0.6s ease forwards;
    }

    h1 {
      font-family: 'Libre Baskerville', serif;
      font-size: clamp(2.2rem, 3.6vw, 3.2rem);
      margin: 0;
      letter-spacing: -0.02em;
    }

    .subtitle {
      color: var(--muted);
      font-size: 1.05rem;
      max-width: 640px;
    }

    .panel {
      background: var(--card);
      border: 1px solid var(--stroke);
      border-radius: 22px;
      box-shadow: var(--shadow);
      display: grid;
      grid-template-rows: minmax(200px, 1fr) auto;
      overflow: hidden;
      min-height: 520px;
      animation: rise 0.6s ease 0.1s forwards;
    }

    .messages {
      padding: 24px;
      overflow-y: auto;
      display: grid;
      gap: 16px;
    }

    .message {
      padding: 14px 16px;
      border-radius: 16px;
      border: 1px solid var(--stroke);
      background: #fff;
      box-shadow: 0 12px 30px rgba(27, 27, 27, 0.06);
      animation: fadeIn 0.3s ease;
    }

    .message.user {
      background: rgba(15, 118, 110, 0.12);
      border-color: rgba(15, 118, 110, 0.25);
      justify-self: end;
    }

    .message.tool {
      background: rgba(239, 111, 85, 0.12);
      border-color: rgba(239, 111, 85, 0.25);
      font-size: 0.92rem;
    }

    .role {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 6px;
      color: var(--muted);
    }

    .content {
      white-space: pre-wrap;
      line-height: 1.4;
    }

    .composer {
      display: grid;
      gap: 12px;
      padding: 18px 20px 22px;
      border-top: 1px solid var(--stroke);
      background: rgba(255, 255, 255, 0.9);
    }

    textarea {
      width: 100%;
      min-height: 96px;
      border-radius: 14px;
      border: 1px solid var(--stroke);
      padding: 12px 14px;
      font-family: inherit;
      font-size: 1rem;
      resize: vertical;
      background: #fff;
    }

    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      justify-content: space-between;
    }

    button {
      border: none;
      border-radius: 999px;
      padding: 12px 22px;
      background: var(--accent);
      color: #fff;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    button:hover {
      transform: translateY(-1px);
      box-shadow: 0 12px 20px rgba(15, 118, 110, 0.24);
    }

    button:disabled {
      opacity: 0.7;
      cursor: not-allowed;
      transform: none;
      box-shadow: none;
    }

    .spinner {
      display: inline-block;
      width: 12px;
      height: 12px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      border-top-color: #fff;
      animation: spin 0.8s linear infinite;
      margin-right: 8px;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .meta {
      color: var(--muted);
      font-size: 0.85rem;
    }

    @keyframes rise {
      from {
        opacity: 0;
        transform: translateY(12px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(6px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @keyframes float {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(18px); }
    }

    @media (max-width: 720px) {
      .panel {
        min-height: 420px;
      }
      .controls {
        flex-direction: column;
        align-items: flex-start;
      }
      button {
        width: 100%;
        justify-content: center;
      }
    }
  </style>
</head>
<body>
  <div class=\"orb one\"></div>
  <div class=\"orb two\"></div>
  <div class=\"shell\">
    <header>
      <h1>OpenManus Studio</h1>
      <div class=\"subtitle\">A focused chat surface for Manus plus tool traces. Each run is recorded so you can inspect what the agent tried.</div>
    </header>

    <section class=\"panel\">
      <div id=\"messages\" class=\"messages\"></div>
      <form id=\"chat-form\" class=\"composer\">
        <textarea id="message" placeholder="Describe the task you want the agent to complete..." aria-label="Message to Manus"></textarea>
        <div class=\"controls\">
          <button type=\"submit\">Send to Manus</button>
          <div class=\"meta\" id=\"status\">Session: new</div>
        </div>
      </form>
    </section>
  </div>

  <script>
    const messagesEl = document.getElementById('messages');
    const formEl = document.getElementById('chat-form');
    const messageEl = document.getElementById('message');
    const statusEl = document.getElementById('status');
    let sessionId = localStorage.getItem('openmanus.session');

    const addMessage = (role, content) => {
      const wrapper = document.createElement('div');
      wrapper.className = `message ${role}`;

      const roleEl = document.createElement('div');
      roleEl.className = 'role';
      roleEl.textContent = role;

      const contentEl = document.createElement('div');
      contentEl.className = 'content';
      contentEl.textContent = content || '';

      wrapper.appendChild(roleEl);
      wrapper.appendChild(contentEl);
      messagesEl.appendChild(wrapper);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    };

    const updateStatus = (text) => {
      statusEl.textContent = text;
    };

    if (sessionId) {
      updateStatus(`Session: ${sessionId}`);
    }

    formEl.addEventListener('submit', async (event) => {
      event.preventDefault();
      const message = messageEl.value.trim();
      if (!message) {
        return;
      }

      const submitBtn = formEl.querySelector('button[type="submit"]');
      const originalBtnText = submitBtn.innerHTML;

      try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span> Sending...';
        messageEl.disabled = true;

        addMessage('user', message);
        messageEl.value = '';
        updateStatus('Thinking...');

        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message, session_id: sessionId })
        });

        if (!response.ok) {
          updateStatus('Error');
          addMessage('system', 'Something went wrong while calling the agent.');
          return;
        }

        const payload = await response.json();
        sessionId = payload.session_id;
        localStorage.setItem('openmanus.session', sessionId);
        if (payload.summary) {
          const parts = [`Session: ${sessionId}`];
          if (payload.summary.steps !== undefined) {
            parts.push(`steps: ${payload.summary.steps}`);
          }
          if (payload.summary.tool_calls !== undefined) {
            parts.push(`tools: ${payload.summary.tool_calls}`);
          }
          updateStatus(parts.join(' | '));
        } else {
          updateStatus(`Session: ${sessionId}`);
        }

        (payload.messages || []).forEach((msg) => {
          if (msg.role === 'user') {
            return;
          }
          addMessage(msg.role || 'assistant', msg.content || '');
        });
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
        messageEl.disabled = false;
        messageEl.focus();
      }
    });
  </script>
</body>
</html>"""


async def _create_session(session_id: str) -> SessionState:
    from app.agent.manus import Manus

    agent = await Manus.create()
    recorder = RunRecorder(session_id, LOG_DIR)
    agent.run_recorder = recorder
    return SessionState(session_id, agent, recorder)


async def _get_session(session_id: Optional[str]) -> SessionState:
    sid = session_id or uuid4().hex
    async with _sessions_lock:
        session = _sessions.get(sid)
        if session:
            return session
        session = await _create_session(sid)
        _sessions[sid] = session
        return session


@app.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse(_html_page())


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(request: ChatRequest) -> dict:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    session = await _get_session(request.session_id)
    async with session.lock:
        session.agent.current_step = 0
        before = len(session.agent.memory.messages)
        await session.agent.run(message)
        new_messages = session.agent.memory.messages[before:]
        summary = session.agent.get_run_summary()

    return {
        "session_id": session.session_id,
        "messages": [msg.to_dict() for msg in new_messages],
        "summary": summary,
    }


@app.post("/api/reset")
async def reset(request: ResetRequest) -> dict:
    async with _sessions_lock:
        session = _sessions.pop(request.session_id, None)
    if session:
        await session.agent.cleanup()
        session.recorder.close()
    return {"reset": True}


@app.on_event("shutdown")
async def shutdown() -> None:
    async with _sessions_lock:
        sessions = list(_sessions.values())
        _sessions.clear()
    for session in sessions:
        await session.agent.cleanup()
        session.recorder.close()

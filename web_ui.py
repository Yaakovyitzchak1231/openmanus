"""
OpenManus Web UI - Full-featured chat interface with authentication,
WebSocket streaming, and debug console.
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.auth import get_current_user, require_auth, signin, signup
from app.config import config
from app.database import db
from app.harness.recording import RunRecorder
from app.models import (
    AuthToken,
    LogEntry,
    SessionSummary,
    UserCreate,
    UserLogin,
    UserPublic,
)

# ==================== App Setup ====================

app = FastAPI(title="OpenManus Studio")

# In-memory agent state per session
_agents: Dict[str, dict] = {}
_agents_lock = asyncio.Lock()

# WebSocket connections per session
_ws_connections: Dict[str, List[WebSocket]] = {}

LOG_DIR = config.root_path / "logs" / "runs"


# ==================== Request/Response Models ====================


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ResetRequest(BaseModel):
    session_id: str


# ==================== HTML Template ====================


def _html_page() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenManus - AI Code Assistant</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
    <style>
        :root {
            --bg-primary: #1e1e2e;
            --bg-secondary: #2d2d3d;
            --bg-tertiary: #363647;
            --bg-hover: #3d3d4f;
            --text-primary: #e4e4e7;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --accent-blue: #3b82f6;
            --accent-blue-hover: #2563eb;
            --accent-green: #22c55e;
            --accent-yellow: #eab308;
            --accent-red: #ef4444;
            --accent-purple: #a855f7;
            --border-color: #3f3f46;
            --sidebar-width: 280px;
            --console-height: 200px;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            height: 100vh;
            overflow: hidden;
        }

        /* Layout */
        .app {
            display: flex;
            height: 100vh;
        }

        /* Sidebar */
        .sidebar {
            width: var(--sidebar-width);
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }

        .sidebar-header {
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
        }

        .sidebar-title {
            font-size: 14px;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .new-chat-btn {
            width: 100%;
            padding: 10px 16px;
            background: var(--accent-blue);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: background 0.2s;
        }

        .new-chat-btn:hover {
            background: var(--accent-blue-hover);
        }

        .sessions-list {
            flex: 1;
            overflow-y: auto;
            padding: 8px;
        }

        .session-item {
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            margin-bottom: 4px;
            transition: background 0.15s;
        }

        .session-item:hover {
            background: var(--bg-hover);
        }

        .session-item.active {
            background: var(--bg-tertiary);
        }

        .session-title {
            font-size: 14px;
            font-weight: 500;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .session-time {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
        }

        .sidebar-footer {
            padding: 16px;
            border-top: 1px solid var(--border-color);
        }

        .auth-btn {
            width: 100%;
            padding: 10px 16px;
            background: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
        }

        .auth-btn:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
        }

        /* Main content */
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            min-width: 0;
        }

        /* Header */
        .header {
            padding: 16px 24px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--bg-secondary);
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .header-title {
            font-size: 18px;
            font-weight: 600;
        }

        .connection-status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-green);
        }

        .status-dot.disconnected {
            background: var(--accent-red);
        }

        .latency {
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .settings-btn {
            padding: 8px;
            background: transparent;
            border: none;
            border-radius: 6px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s;
        }

        .settings-btn:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
        }

        /* Chat area */
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
        }

        .message {
            max-width: 800px;
            margin: 0 auto 16px;
            padding: 16px;
            border-radius: 12px;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            background: var(--bg-tertiary);
            margin-left: auto;
            margin-right: 0;
            max-width: 600px;
        }

        .message.assistant {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
        }

        .message.tool {
            background: rgba(168, 85, 247, 0.1);
            border: 1px solid rgba(168, 85, 247, 0.3);
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
        }

        .message-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }

        .message-avatar {
            width: 28px;
            height: 28px;
            border-radius: 6px;
            background: var(--accent-blue);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }

        .message-role {
            font-size: 12px;
            font-weight: 500;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .message-time {
            font-size: 11px;
            color: var(--text-muted);
            margin-left: auto;
        }

        .message-content {
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        .message-content code {
            font-family: 'JetBrains Mono', monospace;
            background: var(--bg-primary);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
        }

        .message-content pre {
            background: var(--bg-primary);
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
            overflow-x: auto;
        }

        .message-content pre code {
            background: transparent;
            padding: 0;
        }

        /* Composer */
        .composer {
            padding: 16px 24px 24px;
            border-top: 1px solid var(--border-color);
            background: var(--bg-secondary);
        }

        .composer-inner {
            max-width: 800px;
            margin: 0 auto;
            display: flex;
            gap: 12px;
        }

        .composer-input {
            flex: 1;
            padding: 14px 16px;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 14px;
            resize: none;
            min-height: 48px;
            max-height: 200px;
        }

        .composer-input:focus {
            outline: none;
            border-color: var(--accent-blue);
        }

        .composer-input::placeholder {
            color: var(--text-muted);
        }

        .send-btn {
            padding: 14px 20px;
            background: var(--accent-blue);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .send-btn:hover {
            background: var(--accent-blue-hover);
        }

        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Debug Console */
        .console {
            height: var(--console-height);
            background: var(--bg-primary);
            border-top: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            transition: height 0.3s ease;
        }

        .console.collapsed {
            height: 40px;
        }

        .console-header {
            padding: 8px 16px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 12px;
            cursor: pointer;
            flex-shrink: 0;
        }

        .console-title {
            font-size: 13px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .console-badge {
            background: var(--bg-tertiary);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            color: var(--text-muted);
        }

        .console-filters {
            display: flex;
            gap: 4px;
            margin-left: auto;
        }

        .filter-btn {
            padding: 4px 10px;
            background: transparent;
            border: none;
            border-radius: 4px;
            color: var(--text-muted);
            font-size: 12px;
            cursor: pointer;
            transition: all 0.15s;
        }

        .filter-btn:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
        }

        .filter-btn.active {
            background: var(--accent-blue);
            color: white;
        }

        .console-actions {
            display: flex;
            gap: 8px;
        }

        .console-action-btn {
            padding: 4px 8px;
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 14px;
            transition: color 0.15s;
        }

        .console-action-btn:hover {
            color: var(--text-primary);
        }

        .console-logs {
            flex: 1;
            overflow-y: auto;
            padding: 8px 16px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
        }

        .log-entry {
            display: flex;
            gap: 12px;
            padding: 4px 0;
            border-bottom: 1px solid var(--border-color);
        }

        .log-time {
            color: var(--text-muted);
            flex-shrink: 0;
        }

        .log-source {
            padding: 1px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 500;
            text-transform: uppercase;
            flex-shrink: 0;
        }

        .log-source.system { background: var(--bg-tertiary); color: var(--text-secondary); }
        .log-source.ai { background: rgba(59, 130, 246, 0.2); color: var(--accent-blue); }
        .log-source.tool { background: rgba(168, 85, 247, 0.2); color: var(--accent-purple); }
        .log-source.api { background: rgba(34, 197, 94, 0.2); color: var(--accent-green); }

        .log-message {
            color: var(--text-primary);
            flex: 1;
            word-break: break-word;
        }

        .log-entry.warn .log-message { color: var(--accent-yellow); }
        .log-entry.error .log-message { color: var(--accent-red); }

        /* Auth Modal */
        .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.2s;
        }

        .modal-overlay.visible {
            opacity: 1;
            visibility: visible;
        }

        .modal {
            background: var(--bg-secondary);
            border-radius: 16px;
            padding: 32px;
            width: 100%;
            max-width: 400px;
            border: 1px solid var(--border-color);
            transform: scale(0.95);
            transition: transform 0.2s;
        }

        .modal-overlay.visible .modal {
            transform: scale(1);
        }

        .modal-title {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .modal-subtitle {
            color: var(--text-secondary);
            margin-bottom: 24px;
        }

        .form-group {
            margin-bottom: 16px;
        }

        .form-label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 6px;
        }

        .form-input {
            width: 100%;
            padding: 12px 14px;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 14px;
        }

        .form-input:focus {
            outline: none;
            border-color: var(--accent-blue);
        }

        .form-error {
            color: var(--accent-red);
            font-size: 12px;
            margin-top: 4px;
        }

        .modal-btn {
            width: 100%;
            padding: 12px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            margin-top: 8px;
        }

        .modal-btn.primary {
            background: var(--accent-blue);
            color: white;
            border: none;
        }

        .modal-btn.primary:hover {
            background: var(--accent-blue-hover);
        }

        .modal-btn.oauth {
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .modal-btn.oauth:hover {
            background: var(--bg-hover);
        }

        .modal-divider {
            display: flex;
            align-items: center;
            margin: 20px 0;
            color: var(--text-muted);
            font-size: 12px;
        }

        .modal-divider::before,
        .modal-divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: var(--border-color);
        }

        .modal-divider span {
            padding: 0 12px;
        }

        .modal-switch {
            text-align: center;
            margin-top: 16px;
            font-size: 13px;
            color: var(--text-secondary);
        }

        .modal-switch a {
            color: var(--accent-blue);
            cursor: pointer;
        }

        /* Typing indicator */
        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 16px;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            background: var(--text-muted);
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }

        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
            30% { transform: translateY(-8px); opacity: 1; }
        }

        /* User dropdown */
        .user-menu {
            position: relative;
        }

        .user-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            background: var(--bg-tertiary);
            border: none;
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 13px;
            cursor: pointer;
        }

        .user-avatar {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: var(--accent-blue);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 500;
        }

        .user-dropdown {
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 8px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 8px;
            min-width: 180px;
            display: none;
        }

        .user-dropdown.visible {
            display: block;
        }

        .dropdown-item {
            padding: 10px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.15s;
        }

        .dropdown-item:hover {
            background: var(--bg-hover);
        }

        .dropdown-item.danger {
            color: var(--accent-red);
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: transparent;
        }

        ::-webkit-scrollbar-thumb {
            background: var(--bg-tertiary);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--bg-hover);
        }

        /* Hidden */
        .hidden {
            display: none !important;
        }
    </style>
</head>
<body>
    <div class="app">
        <!-- Sidebar -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-title">
                    Chat History
                    <span id="collapse-sidebar" style="cursor: pointer;">&lt;</span>
                </div>
                <button class="new-chat-btn" id="new-chat-btn">
                    <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M8 3v10M3 8h10"/>
                    </svg>
                    New Chat
                </button>
            </div>
            <div class="sessions-list" id="sessions-list">
                <!-- Sessions loaded dynamically -->
            </div>
            <div class="sidebar-footer">
                <button class="auth-btn" id="auth-btn">
                    <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M8 8a3 3 0 100-6 3 3 0 000 6zM2 14c0-2.5 2.5-4 6-4s6 1.5 6 4"/>
                    </svg>
                    <span id="auth-btn-text">Sign In</span>
                </button>
            </div>
        </aside>

        <!-- Main content -->
        <main class="main">
            <!-- Header -->
            <header class="header">
                <div class="header-left">
                    <h1 class="header-title">AI Code Assistant</h1>
                    <div class="connection-status">
                        <span class="status-dot" id="status-dot"></span>
                        <span id="status-text">Connected</span>
                        <span class="latency" id="latency">--ms</span>
                    </div>
                </div>
                <div class="header-right">
                    <button class="settings-btn" id="settings-btn" title="Settings">
                        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="10" cy="10" r="3"/>
                            <path d="M10 1v2M10 17v2M1 10h2M17 10h2M3.5 3.5l1.4 1.4M15.1 15.1l1.4 1.4M3.5 16.5l1.4-1.4M15.1 4.9l1.4-1.4"/>
                        </svg>
                    </button>
                    <div class="user-menu hidden" id="user-menu">
                        <button class="user-btn" id="user-btn">
                            <span class="user-avatar" id="user-avatar">U</span>
                            <span id="user-name">User</span>
                        </button>
                        <div class="user-dropdown" id="user-dropdown">
                            <div class="dropdown-item">Profile</div>
                            <div class="dropdown-item">Preferences</div>
                            <div class="dropdown-item danger" id="signout-btn">Sign Out</div>
                        </div>
                    </div>
                </div>
            </header>

            <!-- Chat container -->
            <div class="chat-container">
                <div class="messages" id="messages">
                    <div class="message assistant">
                        <div class="message-header">
                            <div class="message-avatar">AI</div>
                            <span class="message-role">Assistant</span>
                            <span class="message-time" id="welcome-time"></span>
                        </div>
                        <div class="message-content">Hello! I'm your AI assistant. I can help you write code, debug issues, and integrate with various tools. What would you like to work on today?</div>
                    </div>
                </div>

                <!-- Composer -->
                <div class="composer">
                    <div class="composer-inner">
                        <textarea
                            class="composer-input"
                            id="message-input"
                            placeholder="Ask me anything about code..."
                            rows="1"
                        ></textarea>
                        <button class="send-btn" id="send-btn">
                            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M16 2L8 10M16 2l-5 14-3-6-6-3 14-5z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Debug Console -->
            <div class="console" id="console">
                <div class="console-header" id="console-header">
                    <div class="console-title">
                        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 3l5 5-5 5M8 13h5"/>
                        </svg>
                        Debug Console
                        <span class="console-badge" id="log-count">0</span>
                    </div>
                    <div class="console-filters">
                        <button class="filter-btn active" data-filter="all">All</button>
                        <button class="filter-btn" data-filter="error">Errors (0)</button>
                        <button class="filter-btn" data-filter="warn">Warnings (0)</button>
                    </div>
                    <div class="console-actions">
                        <button class="console-action-btn" id="download-logs" title="Download logs">
                            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M7 1v10M3 8l4 4 4-4M1 13h12"/>
                            </svg>
                        </button>
                        <button class="console-action-btn" id="clear-logs" title="Clear">
                            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M1 1l12 12M13 1L1 13"/>
                            </svg>
                        </button>
                        <button class="console-action-btn" id="collapse-console" title="Collapse">
                            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" id="collapse-icon">
                                <path d="M2 5l5 5 5-5"/>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="console-logs" id="console-logs">
                    <!-- Logs loaded dynamically -->
                </div>
            </div>
        </main>
    </div>

    <!-- Auth Modal -->
    <div class="modal-overlay" id="auth-modal">
        <div class="modal">
            <h2 class="modal-title" id="modal-title">Sign In</h2>
            <p class="modal-subtitle" id="modal-subtitle">Welcome back! Please sign in to continue.</p>

            <form id="auth-form">
                <div class="form-group" id="name-group" style="display: none;">
                    <label class="form-label">Name</label>
                    <input type="text" class="form-input" id="auth-name" placeholder="Your name">
                </div>
                <div class="form-group">
                    <label class="form-label">Email</label>
                    <input type="email" class="form-input" id="auth-email" placeholder="you@example.com" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" class="form-input" id="auth-password" placeholder="Enter password" required>
                    <div class="form-error hidden" id="auth-error"></div>
                </div>
                <button type="submit" class="modal-btn primary" id="auth-submit">Sign In</button>
            </form>

            <div class="modal-divider"><span>or continue with</span></div>

            <button class="modal-btn oauth" disabled title="Coming soon">
                <svg width="18" height="18" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Google
            </button>
            <button class="modal-btn oauth" disabled title="Coming soon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                GitHub
            </button>

            <div class="modal-switch">
                <span id="modal-switch-text">Don't have an account?</span>
                <a id="modal-switch-link">Sign Up</a>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js"></script>
    <script>
        // Safe localStorage helpers
        function safeGetJSON(key, defaultValue) {
            try {
                const val = localStorage.getItem(key);
                return val ? JSON.parse(val) : defaultValue;
            } catch (e) {
                console.error('Error parsing localStorage key:', key, e);
                localStorage.removeItem(key);
                return defaultValue;
            }
        }

        // State
        let token = localStorage.getItem('openmanus.token');
        let user = safeGetJSON('openmanus.user', null);
        let currentSessionId = localStorage.getItem('openmanus.session');
        let sessions = [];
        let logs = [];
        let ws = null;
        let isSignUp = false;

        // Elements
        const messagesEl = document.getElementById('messages');
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        const authBtn = document.getElementById('auth-btn');
        const authBtnText = document.getElementById('auth-btn-text');
        const authModal = document.getElementById('auth-modal');
        const authForm = document.getElementById('auth-form');
        const authError = document.getElementById('auth-error');
        const userMenu = document.getElementById('user-menu');
        const userName = document.getElementById('user-name');
        const userAvatar = document.getElementById('user-avatar');
        const userDropdown = document.getElementById('user-dropdown');
        const signoutBtn = document.getElementById('signout-btn');
        const sessionsList = document.getElementById('sessions-list');
        const newChatBtn = document.getElementById('new-chat-btn');
        const consoleLogs = document.getElementById('console-logs');
        const logCount = document.getElementById('log-count');
        const consoleEl = document.getElementById('console');
        const collapseConsole = document.getElementById('collapse-console');
        const clearLogs = document.getElementById('clear-logs');
        const downloadLogs = document.getElementById('download-logs');
        const filterBtns = document.querySelectorAll('.filter-btn');
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');
        const latencyEl = document.getElementById('latency');

        // Initialize
        document.getElementById('welcome-time').textContent = formatTime(new Date());
        updateAuthUI();
        loadSessions();
        checkConnection();
        setInterval(checkConnection, 10000);

        // Create initial session if none exists
        if (!currentSessionId) {
            currentSessionId = crypto.randomUUID().replace(/-/g, '');
            localStorage.setItem('openmanus.session', currentSessionId);
        }

        // Format time
        function formatTime(date) {
            return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        }

        // Check connection status
        async function checkConnection() {
            const start = Date.now();
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                const latency = Date.now() - start;
                statusDot.classList.remove('disconnected');
                statusText.textContent = 'Connected';
                latencyEl.textContent = latency + 'ms';
            } catch (e) {
                statusDot.classList.add('disconnected');
                statusText.textContent = 'Disconnected';
                latencyEl.textContent = '--ms';
            }
        }

        // Update auth UI
        function updateAuthUI() {
            if (token && user) {
                authBtn.classList.add('hidden');
                userMenu.classList.remove('hidden');
                userName.textContent = user.display_name || user.email.split('@')[0];
                userAvatar.textContent = (user.display_name || user.email)[0].toUpperCase();
            } else {
                authBtn.classList.remove('hidden');
                userMenu.classList.add('hidden');
            }
        }

        // Load sessions
        async function loadSessions() {
            if (!token) {
                // Show local sessions for unauthenticated users
                const localSessions = safeGetJSON('openmanus.sessions', []);
                renderSessions(localSessions);
                return;
            }

            try {
                const res = await fetch('/api/sessions', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (res.ok) {
                    sessions = await res.json();
                    renderSessions(sessions);
                }
            } catch (e) {
                console.error('Failed to load sessions', e);
            }
        }

        // Render sessions
        function renderSessions(items) {
            sessionsList.innerHTML = items.map(s => `
                <div class="session-item ${s.id === currentSessionId ? 'active' : ''}" data-id="${s.id}">
                    <div class="session-title">${escapeHtml(s.title)}</div>
                    <div class="session-time">${formatRelativeTime(s.updated_at || s.created_at)}</div>
                </div>
            `).join('');

            // Add click handlers
            sessionsList.querySelectorAll('.session-item').forEach(el => {
                el.addEventListener('click', () => selectSession(el.dataset.id));
            });
        }

        // Format relative time
        function formatRelativeTime(dateStr) {
            const date = new Date(dateStr);
            const now = new Date();
            const diff = now - date;
            const mins = Math.floor(diff / 60000);
            const hours = Math.floor(diff / 3600000);
            const days = Math.floor(diff / 86400000);

            if (mins < 1) return 'Just now';
            if (mins < 60) return mins + ' min ago';
            if (hours < 24) return hours + ' hours ago';
            return days + ' days ago';
        }

        // Select session
        async function selectSession(sessionId) {
            currentSessionId = sessionId;
            localStorage.setItem('openmanus.session', sessionId);

            // Update active state
            sessionsList.querySelectorAll('.session-item').forEach(el => {
                el.classList.toggle('active', el.dataset.id === sessionId);
            });

            // Load session messages
            if (token) {
                try {
                    const res = await fetch('/api/sessions/' + sessionId, {
                        headers: { 'Authorization': 'Bearer ' + token }
                    });
                    if (res.ok) {
                        const session = await res.json();
                        renderMessages(session.messages || []);
                    }
                } catch (e) {
                    console.error('Failed to load session', e);
                }
            }

            // Connect WebSocket
            connectWebSocket(sessionId);
        }

        // New chat
        async function createNewChat() {
            const sessionId = crypto.randomUUID().replace(/-/g, '');
            const newSession = {
                id: sessionId,
                title: 'New Chat',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                messages: []
            };

            if (token) {
                try {
                    const res = await fetch('/api/sessions', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer ' + token
                        },
                        body: JSON.stringify({ title: 'New Chat' })
                    });
                    if (res.ok) {
                        const data = await res.json();
                        newSession.id = data.id;
                    }
                } catch (e) {
                    console.error('Failed to create session', e);
                }
            } else {
                // Store locally
                const localSessions = JSON.parse(localStorage.getItem('openmanus.sessions') || '[]');
                localSessions.unshift(newSession);
                localStorage.setItem('openmanus.sessions', JSON.stringify(localSessions));
            }

            sessions.unshift(newSession);
            renderSessions(sessions);
            selectSession(newSession.id);

            // Clear messages
            messagesEl.innerHTML = `
                <div class="message assistant">
                    <div class="message-header">
                        <div class="message-avatar">AI</div>
                        <span class="message-role">Assistant</span>
                        <span class="message-time">${formatTime(new Date())}</span>
                    </div>
                    <div class="message-content">Hello! I'm your AI assistant. I can help you write code, debug issues, and integrate with various tools. What would you like to work on today?</div>
                </div>
            `;

            // Clear logs
            logs = [];
            renderLogs();
        }

        // Render messages
        function renderMessages(messages) {
            messagesEl.innerHTML = messages.map(m => createMessageHTML(m)).join('');
            messagesEl.scrollTop = messagesEl.scrollHeight;
            Prism.highlightAll();
        }

        // Create message HTML
        function createMessageHTML(msg) {
            const role = msg.role || 'assistant';
            const avatar = role === 'user' ? 'U' : role === 'tool' ? 'T' : 'AI';
            const time = msg.timestamp ? formatTime(new Date(msg.timestamp)) : '';
            const content = formatContent(msg.content || '');

            return `
                <div class="message ${role}">
                    <div class="message-header">
                        <div class="message-avatar">${avatar}</div>
                        <span class="message-role">${role}${msg.name ? ' (' + escapeHtml(msg.name) + ')' : ''}</span>
                        <span class="message-time">${time}</span>
                    </div>
                    <div class="message-content">${content}</div>
                </div>
            `;
        }

        // Format content with code blocks
        function formatContent(text) {
            if (!text) return '';
            // Simple code block detection
            return escapeHtml(text)
                .replace(/```(\\w+)?\\n([\\s\\S]*?)```/g, (_, lang, code) => {
                    return `<pre><code class="language-${lang || 'text'}">${code}</code></pre>`;
                })
                .replace(/`([^`]+)`/g, '<code>$1</code>');
        }

        // Escape HTML
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Add message to UI
        function addMessage(msg) {
            const html = createMessageHTML(msg);
            messagesEl.insertAdjacentHTML('beforeend', html);
            messagesEl.scrollTop = messagesEl.scrollHeight;
            Prism.highlightAll();
        }

        // Add log entry
        function addLog(level, source, message, metadata = {}) {
            const entry = {
                timestamp: new Date().toISOString(),
                level,
                source,
                message,
                metadata
            };
            logs.push(entry);
            renderLogs();
        }

        // Render logs
        function renderLogs(filter = 'all') {
            const filtered = filter === 'all' ? logs : logs.filter(l => l.level === filter);
            consoleLogs.innerHTML = filtered.map(l => `
                <div class="log-entry ${l.level}">
                    <span class="log-time">${formatTime(new Date(l.timestamp))}</span>
                    <span class="log-source ${l.source}">${l.source}</span>
                    <span class="log-message">${escapeHtml(l.message)}</span>
                </div>
            `).join('');
            consoleLogs.scrollTop = consoleLogs.scrollHeight;

            // Update counts
            logCount.textContent = logs.length;
            const errors = logs.filter(l => l.level === 'error').length;
            const warns = logs.filter(l => l.level === 'warn').length;
            filterBtns[1].textContent = `Errors (${errors})`;
            filterBtns[2].textContent = `Warnings (${warns})`;
        }

        // Connect WebSocket
        function connectWebSocket(sessionId) {
            if (ws) {
                ws.close();
            }

            const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${location.host}/ws/chat/${sessionId}`);

            ws.onopen = () => {
                addLog('info', 'system', 'WebSocket connected');
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleWSMessage(data);
            };

            ws.onerror = (error) => {
                addLog('error', 'system', 'WebSocket error');
            };

            ws.onclose = () => {
                addLog('warn', 'system', 'WebSocket disconnected');
            };
        }

        // Handle WebSocket message
        function handleWSMessage(data) {
            switch (data.type) {
                case 'connected':
                    addLog('info', 'system', 'Session connected');
                    break;
                case 'thinking':
                    showTypingIndicator();
                    addLog('info', 'ai', 'Agent is thinking...');
                    break;
                case 'tool_call':
                    addLog('info', 'tool', `Calling: ${data.payload.name}`, data.payload);
                    break;
                case 'tool_result':
                    addLog('info', 'tool', `Result from ${data.payload.name}: ${data.payload.output?.substring(0, 100)}...`);
                    break;
                case 'message':
                    hideTypingIndicator();
                    addMessage(data.payload);
                    break;
                case 'step':
                    addLog('info', 'ai', `Step ${data.payload.step}/${data.payload.max_steps}`);
                    break;
                case 'token_usage':
                    addLog('info', 'api', `Tokens: ${data.payload.input} in / ${data.payload.output} out`);
                    break;
                case 'complete':
                    hideTypingIndicator();
                    addLog('info', 'system', 'Agent completed');
                    break;
                case 'error':
                    hideTypingIndicator();
                    addLog('error', 'system', data.payload.message || 'An error occurred');
                    break;
            }
        }

        // Show typing indicator
        function showTypingIndicator() {
            if (!document.getElementById('typing-indicator')) {
                messagesEl.insertAdjacentHTML('beforeend', `
                    <div id="typing-indicator" class="typing-indicator">
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                    </div>
                `);
                messagesEl.scrollTop = messagesEl.scrollHeight;
            }
        }

        // Hide typing indicator
        function hideTypingIndicator() {
            const indicator = document.getElementById('typing-indicator');
            if (indicator) indicator.remove();
        }

        // Send message
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            // Add user message
            addMessage({ role: 'user', content: message, timestamp: new Date().toISOString() });
            messageInput.value = '';
            sendBtn.disabled = true;

            // Update session title if first message
            if (sessions.length > 0 && sessions[0].id === currentSessionId && sessions[0].title === 'New Chat') {
                sessions[0].title = message.substring(0, 50) + (message.length > 50 ? '...' : '');
                renderSessions(sessions);
            }

            addLog('info', 'api', 'Sending message to agent');

            // Send via HTTP (fallback) or WebSocket
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ message, session_id: currentSessionId }));
                showTypingIndicator();
            } else {
                try {
                    const res = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            ...(token && { 'Authorization': 'Bearer ' + token })
                        },
                        body: JSON.stringify({ message, session_id: currentSessionId })
                    });

                    if (res.ok) {
                        const data = await res.json();
                        currentSessionId = data.session_id;
                        localStorage.setItem('openmanus.session', currentSessionId);

                        // Add messages
                        (data.messages || []).forEach(msg => {
                            if (msg.role !== 'user') {
                                addMessage(msg);
                            }
                        });

                        // Add logs
                        (data.logs || []).forEach(log => {
                            addLog(log.level, log.source, log.message, log.metadata);
                        });

                        if (data.summary) {
                            addLog('info', 'system', `Completed: ${data.summary.steps} steps, ${data.summary.tool_calls} tool calls`);
                        }
                    } else {
                        addLog('error', 'api', 'Request failed: ' + res.status);
                    }
                } catch (e) {
                    addLog('error', 'system', 'Network error: ' + e.message);
                }
            }

            sendBtn.disabled = false;
        }

        // Auth modal
        function showAuthModal(signup = false) {
            isSignUp = signup;
            authModal.classList.add('visible');

            if (signup) {
                document.getElementById('modal-title').textContent = 'Create Account';
                document.getElementById('modal-subtitle').textContent = 'Sign up to save your chat history.';
                document.getElementById('auth-submit').textContent = 'Sign Up';
                document.getElementById('modal-switch-text').textContent = 'Already have an account? ';
                document.getElementById('modal-switch-link').textContent = 'Sign In';
                document.getElementById('name-group').style.display = 'block';
            } else {
                document.getElementById('modal-title').textContent = 'Sign In';
                document.getElementById('modal-subtitle').textContent = 'Welcome back! Please sign in to continue.';
                document.getElementById('auth-submit').textContent = 'Sign In';
                document.getElementById('modal-switch-text').textContent = "Don't have an account? ";
                document.getElementById('modal-switch-link').textContent = 'Sign Up';
                document.getElementById('name-group').style.display = 'none';
            }
        }

        function hideAuthModal() {
            authModal.classList.remove('visible');
            authError.classList.add('hidden');
            authForm.reset();
        }

        // Auth form submit
        async function handleAuth(e) {
            e.preventDefault();

            // Clear previous errors
            authError.classList.add('hidden');
            authError.textContent = '';

            const email = document.getElementById('auth-email').value.trim();
            const password = document.getElementById('auth-password').value;
            const name = document.getElementById('auth-name').value.trim();

            // Basic validation
            if (!email || !password) {
                authError.textContent = 'Please enter email and password';
                authError.classList.remove('hidden');
                return;
            }

            // Disable submit button while processing
            const submitBtn = document.getElementById('auth-submit');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Please wait...';

            try {
                const endpoint = isSignUp ? '/api/auth/signup' : '/api/auth/signin';
                const body = isSignUp
                    ? { email, password, display_name: name || undefined }
                    : { email, password };

                console.log('Auth request:', endpoint, body);

                const res = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });

                console.log('Auth response status:', res.status);

                if (res.ok) {
                    const data = await res.json();
                    console.log('Auth success:', data);
                    token = data.access_token;
                    user = data.user;
                    localStorage.setItem('openmanus.token', token);
                    localStorage.setItem('openmanus.user', JSON.stringify(user));
                    updateAuthUI();
                    hideAuthModal();
                    loadSessions();
                    addLog('info', 'system', 'Signed in as ' + user.email);
                } else {
                    const err = await res.json();
                    console.log('Auth error:', err);
                    authError.textContent = err.detail || 'Authentication failed';
                    authError.classList.remove('hidden');
                }
            } catch (err) {
                console.error('Auth exception:', err);
                authError.textContent = 'Network error. Please try again.';
                authError.classList.remove('hidden');
            } finally {
                // Re-enable submit button
                submitBtn.disabled = false;
                submitBtn.textContent = isSignUp ? 'Sign Up' : 'Sign In';
            }
        }

        // Sign out
        function signOut() {
            token = null;
            user = null;
            localStorage.removeItem('openmanus.token');
            localStorage.removeItem('openmanus.user');
            updateAuthUI();
            loadSessions();
            addLog('info', 'system', 'Signed out');
        }

        // Event listeners
        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        authBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Sign In button clicked');
            showAuthModal(false);
        });
        authForm.addEventListener('submit', handleAuth);
        authModal.addEventListener('click', (e) => {
            if (e.target === authModal) hideAuthModal();
        });
        document.getElementById('modal-switch-link').addEventListener('click', (e) => {
            e.preventDefault();
            showAuthModal(!isSignUp);
        });

        document.getElementById('user-btn').addEventListener('click', () => {
            userDropdown.classList.toggle('visible');
        });
        signoutBtn.addEventListener('click', signOut);
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.user-menu')) {
                userDropdown.classList.remove('visible');
            }
        });

        newChatBtn.addEventListener('click', createNewChat);

        // Console controls
        collapseConsole.addEventListener('click', () => {
            consoleEl.classList.toggle('collapsed');
        });
        clearLogs.addEventListener('click', () => {
            logs = [];
            renderLogs();
        });
        downloadLogs.addEventListener('click', () => {
            const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'openmanus-logs-' + Date.now() + '.json';
            a.click();
            URL.revokeObjectURL(url);
        });
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                renderLogs(btn.dataset.filter);
            });
        });

        // Auto-resize textarea
        messageInput.addEventListener('input', () => {
            messageInput.style.height = 'auto';
            messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
        });

        // Initial log
        addLog('info', 'system', 'OpenManus UI initialized');
        addLog('info', 'system', 'Debug mode enabled');

        // Global error handler for debugging
        window.onerror = function(msg, url, lineNo, columnNo, error) {
            console.error('Global error:', msg, url, lineNo, columnNo, error);
            addLog('error', 'system', 'JavaScript error: ' + msg);
            return false;
        };

        console.log('OpenManus UI loaded successfully');
    </script>
</body>
</html>"""


# ==================== Startup ====================


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    await db.initialize()


# ==================== Static Routes ====================


@app.get("/")
async def index() -> HTMLResponse:
    """Serve the main UI."""
    return HTMLResponse(_html_page())


@app.get("/api/status")
async def status():
    """Health check with latency."""
    return {"status": "ok", "connected": True, "model": "default"}


# ==================== Auth Routes ====================


@app.post("/api/auth/signup")
async def api_signup(user_data: UserCreate) -> AuthToken:
    """Create a new user account."""
    return await signup(user_data)


@app.post("/api/auth/signin")
async def api_signin(credentials: UserLogin) -> AuthToken:
    """Sign in and get access token."""
    return await signin(credentials)


@app.get("/api/auth/me")
async def api_me(user: UserPublic = Depends(require_auth)) -> UserPublic:
    """Get current user info."""
    return user


# ==================== Session Routes ====================


@app.get("/api/sessions")
async def api_list_sessions(user: UserPublic = Depends(require_auth)) -> list[dict]:
    """List all sessions for the current user."""
    return await db.get_user_sessions(user.id)


@app.post("/api/sessions")
async def api_create_session(
    data: dict,
    user: UserPublic = Depends(require_auth),
) -> dict:
    """Create a new chat session."""
    session_id = uuid4().hex
    return await db.create_session(
        session_id=session_id,
        user_id=user.id,
        title=data.get("title", "New Chat"),
    )


@app.get("/api/sessions/{session_id}")
async def api_get_session(
    session_id: str,
    user: Optional[UserPublic] = Depends(get_current_user),
) -> dict:
    """Get a specific session."""
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # Allow unauthenticated access for now (local sessions)
    return session


@app.delete("/api/sessions/{session_id}")
async def api_delete_session(
    session_id: str,
    user: UserPublic = Depends(require_auth),
) -> dict:
    """Delete a session."""
    deleted = await db.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}


# ==================== Chat Routes ====================


@app.post("/api/chat")
async def api_chat(
    request: ChatRequest,
    user: Optional[UserPublic] = Depends(get_current_user),
) -> dict:
    """Send a message and get a response."""
    from app.agent.manus import Manus

    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    session_id = request.session_id or uuid4().hex

    # Get or create agent for this session
    async with _agents_lock:
        agent_state = _agents.get(session_id)
        if not agent_state:
            agent = await Manus.create()
            recorder = RunRecorder(session_id, LOG_DIR)
            agent.run_recorder = recorder
            agent_state = {
                "agent": agent,
                "recorder": recorder,
                "lock": asyncio.Lock(),
            }
            _agents[session_id] = agent_state

    agent = agent_state["agent"]
    recorder = agent_state["recorder"]

    logs_before = []

    async with agent_state["lock"]:
        agent.current_step = 0
        before = len(agent.memory.messages)

        # Capture logs during execution
        start_time = time.time()
        logs_before.append(
            LogEntry(
                level="info",
                source="system",
                message=f"Starting agent run",
            )
        )

        await agent.run(message)

        new_messages = agent.memory.messages[before:]
        summary = agent.get_run_summary()
        duration = time.time() - start_time

        logs_before.append(
            LogEntry(
                level="info",
                source="system",
                message=f"Agent completed in {duration:.1f}s",
            )
        )

    # Save to database if user is authenticated
    if user:
        session = await db.get_session(session_id)
        if session:
            messages = session.get("messages", [])
            messages.append({"role": "user", "content": message, "timestamp": datetime.utcnow().isoformat()})
            for msg in new_messages:
                messages.append(msg.to_dict())
            await db.update_session(session_id, messages=messages)

    return {
        "session_id": session_id,
        "messages": [msg.to_dict() for msg in new_messages],
        "summary": summary,
        "logs": [log.model_dump() for log in logs_before],
    }


# ==================== WebSocket Routes ====================


@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    from app.agent.manus import Manus

    await websocket.accept()

    # Send connected event
    await websocket.send_json({
        "type": "connected",
        "payload": {"session_id": session_id},
    })

    # Get or create agent
    async with _agents_lock:
        agent_state = _agents.get(session_id)
        if not agent_state:
            agent = await Manus.create()
            recorder = RunRecorder(session_id, LOG_DIR)
            agent.run_recorder = recorder
            agent_state = {
                "agent": agent,
                "recorder": recorder,
                "lock": asyncio.Lock(),
            }
            _agents[session_id] = agent_state

    agent = agent_state["agent"]

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "").strip()

            if not message:
                continue

            async with agent_state["lock"]:
                # Send thinking indicator
                await websocket.send_json({
                    "type": "thinking",
                    "payload": {},
                })

                agent.current_step = 0
                before = len(agent.memory.messages)

                # Run agent
                try:
                    await agent.run(message)

                    # Send new messages
                    new_messages = agent.memory.messages[before:]
                    for msg in new_messages:
                        await websocket.send_json({
                            "type": "message",
                            "payload": msg.to_dict(),
                        })

                    # Send summary
                    summary = agent.get_run_summary()
                    await websocket.send_json({
                        "type": "complete",
                        "payload": summary,
                    })

                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": str(e)},
                    })

    except WebSocketDisconnect:
        pass


# ==================== Cleanup ====================


@app.on_event("shutdown")
async def shutdown():
    """Cleanup agents on shutdown."""
    async with _agents_lock:
        for session_id, state in _agents.items():
            try:
                await state["agent"].cleanup()
                state["recorder"].close()
            except Exception:
                pass
        _agents.clear()

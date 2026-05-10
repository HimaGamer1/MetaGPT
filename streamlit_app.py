"""Megan — Streamlit launcher.

This is the user-facing Megan app. It wraps the underlying multi-agent
framework (re-exported via :mod:`megan`) with:

* A guided API-key intake form (OpenAI / Anthropic / Azure / OpenRouter /
  DeepSeek / Gemini / Ollama / custom).
* A "Run Megan" workflow that lets a user describe an idea and watch a
  product manager, architect, engineer, etc. collaborate.
* A custom Megan brand palette (deep violet + amber on warm cream) — fully
  distinct from the upstream MetaGPT cyan/blue look.
"""

from __future__ import annotations

import asyncio
import copy
import html
import io
import logging
import sys
import threading
import time
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

import streamlit as st

# ---------------------------------------------------------------------------
# Brand constants
# ---------------------------------------------------------------------------

BRAND_NAME = "Megan"
BRAND_TAGLINE = "A multi-agent software company in your browser"
BRAND_VERSION = "0.1.0"

REPO_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = REPO_ROOT / "megan" / "_assets"

# ---------------------------------------------------------------------------
# Page config — must be the first Streamlit call.
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title=f"{BRAND_NAME} — {BRAND_TAGLINE}",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _inject_css() -> None:
    css_path = ASSETS_DIR / "megan.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


_inject_css()


# ---------------------------------------------------------------------------
# Provider catalog
# ---------------------------------------------------------------------------

PROVIDERS: dict[str, dict[str, Any]] = {
    "OpenAI": {
        "api_type": "openai",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "key_help": "Starts with `sk-...`. Get one at https://platform.openai.com/api-keys",
    },
    "Anthropic (Claude)": {
        "api_type": "anthropic",
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-3-5-sonnet-20241022",
        "models": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
        ],
        "key_help": "Starts with `sk-ant-...`. Get one at https://console.anthropic.com/",
    },
    "Azure OpenAI": {
        "api_type": "azure",
        "base_url": "",
        "default_model": "gpt-4",
        "models": ["gpt-4", "gpt-4-turbo", "gpt-35-turbo"],
        "key_help": "Use the key from Azure Portal → your OpenAI resource.",
        "needs_base_url": True,
        "needs_api_version": True,
    },
    "OpenRouter": {
        "api_type": "openrouter",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "openrouter/auto",
        "models": [
            "openrouter/auto",
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o-mini",
            "meta-llama/llama-3.1-70b-instruct",
        ],
        "key_help": "Get one at https://openrouter.ai/keys",
    },
    "DeepSeek": {
        "api_type": "deepseek",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-coder"],
        "key_help": "Get one at https://platform.deepseek.com/",
    },
    "Google Gemini": {
        "api_type": "gemini",
        "base_url": "",
        "default_model": "gemini-1.5-pro",
        "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
        "key_help": "Get one at https://aistudio.google.com/app/apikey",
    },
    "Ollama (local)": {
        "api_type": "ollama",
        "base_url": "http://localhost:11434/api",
        "default_model": "llama3",
        "models": ["llama3", "llama3.1", "qwen2.5", "mistral"],
        "key_help": "Local Ollama needs no key — leave blank or use `ollama`.",
    },
    "Custom / OpenAI-compatible": {
        "api_type": "openai",
        "base_url": "",
        "default_model": "",
        "models": [],
        "key_help": "Any OpenAI-compatible endpoint (Together, Groq, vLLM, …).",
        "needs_base_url": True,
    },
}


# ---------------------------------------------------------------------------
# Session-state defaults
# ---------------------------------------------------------------------------


def _init_state() -> None:
    defaults = {
        "provider": "OpenAI",
        "api_key": "",
        "base_url": "",
        "api_version": "",
        "model": "",
        "search_api_key": "",
        "search_cse_id": "",
        "config_saved": False,
        "run_log": "",
        "last_run_idea": "",
        "last_run_status": None,
        "last_run_workspace": "",
        # Chat tab state. chat_history is a list of {"role": "user|assistant",
        # "content": str, "tasks": list[dict]?}. chat_tasks tracks the
        # planner output from the most recent turn for the sticky todo panel.
        "chat_history": [],
        "chat_tasks": [],
        "chat_busy": False,
    }
    for key, val in defaults.items():
        st.session_state.setdefault(key, val)


_init_state()


# ---------------------------------------------------------------------------
# Apply user config to the Megan / metagpt runtime.
# ---------------------------------------------------------------------------


def apply_user_config() -> tuple[bool, str]:
    """Build a per-session Megan config from the user's inputs.

    Streamlit shares the same Python process across all browser sessions,
    so mutating ``metagpt.config2.config`` (a module-level singleton) would
    leak one user's keys into another user's run. Instead we build a fresh
    :class:`metagpt.config2.Config` per session and stash it in
    ``st.session_state["megan_config"]``. The worker thread then receives
    that isolated copy, never the global one.

    Returns ``(ok, message)``.
    """

    provider_meta = PROVIDERS[st.session_state.provider]
    api_key = (st.session_state.api_key or "").strip()
    base_url = (st.session_state.base_url or provider_meta["base_url"]).strip()
    model = (st.session_state.model or provider_meta["default_model"]).strip()
    api_type = provider_meta["api_type"]

    if api_type != "ollama" and not api_key:
        return False, "Please enter an API key for your selected provider."
    if provider_meta.get("needs_base_url") and not base_url:
        return False, "This provider needs a base URL — please fill it in."
    if not model:
        return False, "Please choose or enter a model name."

    # Lazy-import so the page renders even when heavy deps are missing.
    try:
        from megan import config as global_config
    except Exception as exc:  # pragma: no cover - import diagnostics
        return False, f"Could not load Megan runtime: {exc}"

    # Deep-copy so the per-session config is fully detached from the
    # global singleton; this prevents API-key leakage between sessions.
    # Pydantic does not coerce strings to enums on attribute assignment
    # (validate_assignment is off on the framework's YamlModel), so we have
    # to construct the enum explicitly or the LLM provider registry lookup
    # will fail with KeyError on the raw string.
    from metagpt.configs.llm_config import LLMType
    from metagpt.configs.search_config import SearchEngineType

    try:
        llm_type_enum = LLMType(api_type)
    except ValueError:
        return False, f"Unsupported provider api_type: {api_type!r}"

    session_config = copy.deepcopy(global_config)
    session_config.llm.api_type = llm_type_enum
    session_config.llm.api_key = api_key or "ollama"
    session_config.llm.base_url = base_url
    session_config.llm.model = model
    if provider_meta.get("needs_api_version"):
        session_config.llm.api_version = (st.session_state.api_version or "").strip() or None

    if st.session_state.search_api_key.strip():
        session_config.search.api_type = SearchEngineType.DIRECT_GOOGLE
        session_config.search.api_key = st.session_state.search_api_key.strip()
        session_config.search.cse_id = st.session_state.search_cse_id.strip()

    st.session_state["megan_config"] = session_config
    st.session_state.config_saved = True
    return True, f"Megan is configured to use {st.session_state.provider} ({model})."


# ---------------------------------------------------------------------------
# Background runner — execute the Megan team in a worker thread and stream
# its log output back to the UI.
# ---------------------------------------------------------------------------


class _StreamCapture(io.StringIO):
    """A StringIO that also forwards writes to a shared list (thread-safe)."""

    def __init__(self, sink: list[str], lock: threading.Lock) -> None:
        super().__init__()
        self._sink = sink
        self._lock = lock

    def write(self, data: str) -> int:  # type: ignore[override]
        if data:
            with self._lock:
                self._sink.append(data)
        return super().write(data)


def _run_team_worker(
    idea: str,
    investment: float,
    n_round: int,
    selected_roles: list[str],
    session_config: Any,
    sink: list[str],
    lock: threading.Lock,
    status: dict[str, Any],
) -> None:
    """Run the Megan team. Lives on a worker thread.

    ``session_config`` MUST be the per-session Config built by
    :func:`apply_user_config` — never the global ``megan.config`` — so
    concurrent users do not clobber each other's API keys.
    """

    capture = _StreamCapture(sink, lock)

    # Loguru writes to stderr by default — redirect both, plus add a sink.
    try:
        from loguru import logger as _logger

        sink_id = _logger.add(capture, level="INFO", format="{time:HH:mm:ss} | {level: <7} | {message}")
    except Exception:
        sink_id = None

    log_handler = logging.StreamHandler(capture)
    log_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(log_handler)

    try:
        with redirect_stdout(capture), redirect_stderr(capture):
            from megan import (
                Architect,
                Context,
                DataAnalyst,
                Engineer2,
                ProductManager,
                ProjectManager,
                QaEngineer,
                Team,
                TeamLeader,
            )

            role_factory = {
                "TeamLeader": TeamLeader,
                "ProductManager": ProductManager,
                "Architect": Architect,
                "ProjectManager": ProjectManager,
                "Engineer": Engineer2,
                "DataAnalyst": DataAnalyst,
                "QaEngineer": QaEngineer,
            }
            roles = [role_factory[name]() for name in selected_roles if name in role_factory]
            if not roles:
                roles = [TeamLeader(), ProductManager(), Architect(), Engineer2()]

            ctx = Context(config=session_config)
            team = Team(context=ctx)
            team.hire(roles)
            team.invest(investment)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(team.run(n_round=n_round, idea=idea))
            finally:
                loop.close()

            workspace = ctx.kwargs.get("project_path", "") if hasattr(ctx, "kwargs") else ""
            status["workspace"] = str(workspace) if workspace else ""
            status["state"] = "done"
    except Exception as exc:  # pragma: no cover - surfaced to UI
        status["state"] = "error"
        status["error"] = f"{type(exc).__name__}: {exc}"
        with lock:
            sink.append(f"\n[megan] ERROR: {type(exc).__name__}: {exc}\n")
    finally:
        if sink_id is not None:
            try:
                from loguru import logger as _logger

                _logger.remove(sink_id)
            except Exception:
                pass
        logging.getLogger().removeHandler(log_handler)


# ---------------------------------------------------------------------------
# Chat worker — drives a DataInterpreter for a single chat turn.
# ---------------------------------------------------------------------------


def _run_chat_worker(
    user_message: str,
    prior_history: list[dict[str, str]],
    session_config: Any,
    sink: list[str],
    lock: threading.Lock,
    status: dict[str, Any],
) -> None:
    """Run a single agentic chat turn on a worker thread.

    Uses :class:`metagpt.roles.di.data_interpreter.DataInterpreter` in
    ``plan_and_act`` mode so the Planner produces a Plan whose ``tasks``
    we can stream back to the UI as a live todo list. ``session_config``
    is the per-session :class:`metagpt.config2.Config` built by
    :func:`apply_user_config` — the global singleton is never touched.

    The role object is parked on ``status['role']`` so the polling UI can
    read ``role.planner.plan.tasks`` while the run is in flight.
    """

    capture = _StreamCapture(sink, lock)

    try:
        from loguru import logger as _logger

        sink_id = _logger.add(capture, level="INFO", format="{time:HH:mm:ss} | {level: <7} | {message}")
    except Exception:
        sink_id = None

    log_handler = logging.StreamHandler(capture)
    log_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(log_handler)

    try:
        with redirect_stdout(capture), redirect_stderr(capture):
            from megan import Context
            from metagpt.roles.di.data_interpreter import DataInterpreter

            ctx = Context(config=session_config)
            di = DataInterpreter(
                context=ctx,
                react_mode="plan_and_act",
                max_react_loop=5,
                use_reflection=False,
            )
            status["role"] = di

            # Assemble a single requirement from prior turns + new user message
            # so DataInterpreter sees the full chat context.
            history_lines: list[str] = []
            for turn in prior_history[-6:]:
                speaker = "User" if turn["role"] == "user" else "Megan"
                history_lines.append(f"{speaker}: {turn['content']}")
            history_block = "\n".join(history_lines)
            if history_block:
                requirement = f"Recent conversation:\n{history_block}\n\n" f"New user request:\n{user_message}"
            else:
                requirement = user_message

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(di.run(with_message=requirement))
            finally:
                loop.close()

            reply = result.content if result is not None else ""
            tasks_dump = [
                {
                    "task_id": t.task_id,
                    "instruction": t.instruction,
                    "is_finished": bool(t.is_finished),
                    "is_success": bool(t.is_success),
                }
                for t in di.planner.plan.tasks
            ]
            status["reply"] = reply
            status["tasks"] = tasks_dump
            status["state"] = "done"
    except Exception as exc:  # pragma: no cover - surfaced to UI
        status["state"] = "error"
        status["error"] = f"{type(exc).__name__}: {exc}"
        with lock:
            sink.append(f"\n[megan] CHAT ERROR: {type(exc).__name__}: {exc}\n")
    finally:
        if sink_id is not None:
            try:
                from loguru import logger as _logger

                _logger.remove(sink_id)
            except Exception:
                pass
        logging.getLogger().removeHandler(log_handler)


def _render_todo_html(tasks: list[dict[str, Any]], current_task_id: str | None) -> str:
    """Build the HTML for the live todo list panel.

    Each task is rendered as a row with one of three states:
      ✓ finished, ▸ in-progress (matches current_task_id), ○ pending.
    The instruction text is html-escaped before being interpolated.
    """

    if not tasks:
        return (
            '<div class="megan-todo megan-todo--empty">'
            "Megan hasn't decomposed a plan yet. Send a message to start."
            "</div>"
        )
    rows: list[str] = []
    for task in tasks:
        if task.get("is_finished"):
            state = "done"
            mark = "✓"
        elif current_task_id and task.get("task_id") == current_task_id:
            state = "running"
            mark = "▸"
        else:
            state = "pending"
            mark = "○"
        instruction = html.escape(task.get("instruction", ""))
        task_id = html.escape(task.get("task_id", ""))
        rows.append(
            f'<li class="megan-todo-item megan-todo-item--{state}">'
            f'<span class="megan-todo-mark">{mark}</span>'
            f'<span class="megan-todo-id">{task_id}</span>'
            f'<span class="megan-todo-text">{instruction}</span>'
            "</li>"
        )
    return '<ul class="megan-todo">' + "".join(rows) + "</ul>"


# ---------------------------------------------------------------------------
# UI building blocks
# ---------------------------------------------------------------------------


def render_hero() -> None:
    st.markdown(
        f"""
        <div class="megan-hero">
          <div style="display:flex; align-items:center;">
            <span class="megan-mark">M</span>
            <div>
              <h1>{BRAND_NAME}</h1>
              <p class="megan-tagline">{BRAND_TAGLINE}</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"### {BRAND_NAME}")
        st.caption(f"v{BRAND_VERSION} · multi-agent framework")

        configured = st.session_state.config_saved
        badge_class = "megan-badge--ok" if configured else "megan-badge--warn"
        badge_text = "Configured" if configured else "Needs API key"
        st.markdown(
            f'<span class="megan-badge {badge_class}">{badge_text}</span>',
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown("**The team**")
        st.markdown(
            """
            - 🧭  Team Leader — orchestrates the run
            - 📋  Product Manager — writes the PRD
            - 🏗️  Architect — designs the system
            - 💻  Engineer — implements the code
            - 📊  Data Analyst — runs analytics tasks
            - 🧪  QA Engineer (optional)
            """
        )

        st.divider()
        st.caption(
            "Megan is built on the open-source MetaGPT multi-agent framework " "and re-skinned with a fresh palette."
        )


def render_api_key_tab() -> None:
    with st.container(border=True):
        st.markdown(
            '<div class="megan-section-head">'
            '<span class="megan-step">Step 1</span>'
            '<span class="megan-section-title">API keys</span>'
            '<span class="megan-pill">your keys, your machine</span>'
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            "Megan never ships keys. Pick a provider, paste your key, and "
            "Megan will use it only for the agent runs you start in this session."
        )

        provider = st.selectbox(
            "Provider",
            list(PROVIDERS.keys()),
            index=list(PROVIDERS.keys()).index(st.session_state.provider),
            key="provider",
        )
        meta = PROVIDERS[provider]

        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.text_input(
                "API key",
                type="password",
                placeholder="sk-...",
                help=meta["key_help"],
                key="api_key",
            )
        with col_b:
            if meta["models"]:
                current_model = st.session_state.model
                idx = meta["models"].index(current_model) if current_model in meta["models"] else 0
                st.selectbox("Model", options=meta["models"], index=idx, key="model")
            else:
                st.text_input(
                    "Model",
                    value=st.session_state.model or meta["default_model"],
                    key="model",
                )

        if meta.get("needs_base_url") or st.session_state.base_url:
            st.text_input(
                "Base URL",
                value=st.session_state.base_url or meta["base_url"],
                placeholder=meta["base_url"] or "https://...",
                key="base_url",
            )
        if meta.get("needs_api_version"):
            st.text_input("API version", placeholder="2024-02-15-preview", key="api_version")

        with st.expander("Optional · web search keys (Google CSE)", expanded=False):
            st.text_input("Google API key", type="password", key="search_api_key")
            st.text_input("Google CSE ID", key="search_cse_id")

        btn_col, msg_col = st.columns([1, 3])
        with btn_col:
            save_clicked = st.button("Save configuration", use_container_width=True)
        if save_clicked:
            ok, msg = apply_user_config()
            if ok:
                msg_col.success(msg)
                # Force a rerun so the sidebar status badge picks up the new
                # config_saved=True value on this turn instead of waiting for
                # the next user interaction.
                st.rerun()
            else:
                msg_col.error(msg)


def render_run_tab() -> None:
    with st.container(border=True):
        st.markdown(
            '<div class="megan-section-head">'
            '<span class="megan-step">Step 2</span>'
            '<span class="megan-section-title">Brief the team</span>'
            '<span class="megan-pill">describe an idea</span>'
            "</div>",
            unsafe_allow_html=True,
        )

        idea = st.text_area(
            "Project idea",
            placeholder="e.g. Build a CLI flashcard app that reviews Spanish vocab with spaced repetition.",
            height=120,
            key="idea_input",
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            n_round = st.slider(
                "Rounds", min_value=1, max_value=10, value=3, help="How many cycles the team should run."
            )
        with col2:
            investment = st.slider("Budget ($)", min_value=1.0, max_value=20.0, value=3.0, step=0.5)
        with col3:
            roles = st.multiselect(
                "Roles to hire",
                options=[
                    "TeamLeader",
                    "ProductManager",
                    "Architect",
                    "ProjectManager",
                    "Engineer",
                    "DataAnalyst",
                    "QaEngineer",
                ],
                default=["TeamLeader", "ProductManager", "Architect", "Engineer"],
            )

        run_disabled = not st.session_state.config_saved or not idea.strip()

        btn_col, info_col = st.columns([1, 3])
        with btn_col:
            run_clicked = st.button(
                "Run Megan",
                type="primary",
                use_container_width=True,
                disabled=run_disabled,
            )
        with info_col:
            if not st.session_state.config_saved:
                st.info("Save an API key on the **API keys** tab first.")
            elif not idea.strip():
                st.info("Describe the project Megan should build.")

    if run_clicked:
        session_config = st.session_state.get("megan_config")
        if session_config is None:
            st.error("No saved configuration — please re-save your API key on the API keys tab.")
            return
        sink: list[str] = []
        lock = threading.Lock()
        status: dict[str, Any] = {"state": "running"}
        thread = threading.Thread(
            target=_run_team_worker,
            args=(
                idea.strip(),
                float(investment),
                int(n_round),
                roles,
                session_config,
                sink,
                lock,
                status,
            ),
            daemon=True,
        )
        thread.start()

        with st.container(border=True):
            st.markdown(
                '<div class="megan-section-head">'
                '<span class="megan-step">Step 3</span>'
                '<span class="megan-section-title">Live log</span>'
                '<span class="megan-pill">streaming</span>'
                "</div>",
                unsafe_allow_html=True,
            )
            log_box = st.empty()
            progress_box = st.empty()

            while thread.is_alive():
                with lock:
                    snapshot = "".join(sink[-2000:])
                escaped = html.escape(snapshot) if snapshot else "Booting up the Megan team…"
                log_box.markdown(
                    f'<div class="megan-log">{escaped}</div>',
                    unsafe_allow_html=True,
                )
                progress_box.caption(f"Status: running · {time.strftime('%H:%M:%S')}")
                time.sleep(1.5)

            thread.join(timeout=2)
            with lock:
                final_log = "".join(sink)
            log_box.markdown(
                f'<div class="megan-log">{html.escape(final_log) if final_log else "(no output)"}</div>',
                unsafe_allow_html=True,
            )

            st.session_state.run_log = final_log
            st.session_state.last_run_idea = idea.strip()
            st.session_state.last_run_status = status.get("state")
            st.session_state.last_run_workspace = status.get("workspace", "")

            if status.get("state") == "done":
                st.success("Megan finished the run.")
                if status.get("workspace"):
                    st.info(f"Workspace: `{status['workspace']}`")
            else:
                st.error(status.get("error", "Megan stopped before completing the run."))


def render_chat_tab() -> None:
    with st.container(border=True):
        st.markdown(
            '<div class="megan-section-head">'
            '<span class="megan-step">Chat</span>'
            '<span class="megan-section-title">Talk to Megan</span>'
            '<span class="megan-pill">agentic reply</span>'
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            "Megan plans, decomposes, and acts on your request using the same "
            "DataInterpreter loop as the upstream framework. Watch the live "
            "todo list on the right."
        )

        if not st.session_state.config_saved:
            st.info("Save an API key on the **API keys** tab first.")
            return

        chat_col, todo_col = st.columns([2, 1])

        # --- Chat history (left column) --------------------------------------
        with chat_col:
            history_box = st.container()
            with history_box:
                if not st.session_state.chat_history:
                    st.caption("_No conversation yet — ask Megan to plan, build, or " "analyse something._")
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

        # --- Live todo list (right column) -----------------------------------
        with todo_col:
            st.markdown(
                '<div class="megan-todo-head">'
                '<span class="megan-todo-title">Todo list</span>'
                '<span class="megan-todo-sub">planner output</span>'
                "</div>",
                unsafe_allow_html=True,
            )
            todo_box = st.empty()
            todo_box.markdown(
                _render_todo_html(st.session_state.chat_tasks, None),
                unsafe_allow_html=True,
            )

        # --- Chat input ------------------------------------------------------
        user_input = st.chat_input(
            "Ask Megan to plan, build, or analyse...",
            disabled=st.session_state.chat_busy,
        )

        if user_input:
            st.session_state.chat_busy = True
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            prior = list(st.session_state.chat_history[:-1])
            session_config = st.session_state.get("megan_config")

            sink: list[str] = []
            lock = threading.Lock()
            status: dict[str, Any] = {"state": "running", "role": None, "reply": "", "tasks": []}
            thread = threading.Thread(
                target=_run_chat_worker,
                args=(user_input, prior, session_config, sink, lock, status),
                daemon=True,
            )
            thread.start()

            with chat_col:
                with st.chat_message("user"):
                    st.markdown(user_input)
                with st.chat_message("assistant"):
                    reply_box = st.empty()
                    reply_box.markdown("_Megan is thinking…_")

                    while thread.is_alive():
                        with lock:
                            recent = "".join(sink[-1500:])
                        tail = "\n".join(recent.splitlines()[-6:])
                        escaped_tail = html.escape(tail) if tail else ""
                        reply_box.markdown(
                            "_Megan is thinking…_\n\n" f'<div class="megan-log megan-log--inline">{escaped_tail}</div>',
                            unsafe_allow_html=True,
                        )

                        role = status.get("role")
                        if role is not None and getattr(role, "planner", None) is not None:
                            tasks_live = [
                                {
                                    "task_id": t.task_id,
                                    "instruction": t.instruction,
                                    "is_finished": bool(t.is_finished),
                                }
                                for t in role.planner.plan.tasks
                            ]
                            current = role.planner.plan.current_task_id
                            todo_box.markdown(
                                _render_todo_html(tasks_live, current),
                                unsafe_allow_html=True,
                            )
                        time.sleep(1.0)

                    thread.join(timeout=2)

                    if status.get("state") == "done":
                        reply = status.get("reply") or "_(no reply)_"
                        reply_box.markdown(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                        st.session_state.chat_tasks = status.get("tasks", [])
                        todo_box.markdown(
                            _render_todo_html(st.session_state.chat_tasks, None),
                            unsafe_allow_html=True,
                        )
                    else:
                        err = status.get("error", "Megan stopped before completing the turn.")
                        reply_box.error(err)
                        st.session_state.chat_history.append({"role": "assistant", "content": f":warning: {err}"})

            st.session_state.chat_busy = False
            st.rerun()


def render_about_tab() -> None:
    with st.container(border=True):
        st.markdown(
            '<div class="megan-section-head">' '<span class="megan-section-title">About Megan</span>' "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            **Megan** is a re-skinned distribution of the open-source MetaGPT
            multi-agent framework. The runtime is unchanged — the same product
            managers, architects, and engineers — but the user surface has been
            rebuilt with a fresh palette and a guided UI.

            - **Bring your own key.** Megan never stores credentials server-side.
            - **Pick your provider.** OpenAI, Anthropic, Azure, OpenRouter,
              DeepSeek, Gemini, Ollama, or any OpenAI-compatible endpoint.
            - **Watch the team work.** Logs stream live as agents collaborate.

            Built on top of the [`metagpt`](https://github.com/geekan/MetaGPT)
            package; the framework code is preserved verbatim under
            [`metagpt/`](./metagpt) and re-exported through [`megan`](./megan).
            """
        )


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def main() -> None:
    render_sidebar()
    render_hero()

    tab_keys, tab_chat, tab_run, tab_about = st.tabs(["API keys", "Chat", "Run a project", "About Megan"])
    with tab_keys:
        render_api_key_tab()
    with tab_chat:
        render_chat_tab()
    with tab_run:
        render_run_tab()
    with tab_about:
        render_about_tab()

    st.markdown(
        f'<div class="megan-footer">{BRAND_NAME} · {BRAND_TAGLINE} · ' f"powered by the MetaGPT framework</div>",
        unsafe_allow_html=True,
    )


# Streamlit always executes this script as __main__ inside its runtime, so a
# top-level call is the simplest, most idiomatic invocation. Importing this
# module directly (e.g. for syntax checks) would otherwise fire all the
# st.* calls without a ScriptRunContext, so we guard against that.
def _has_streamlit_context() -> bool:
    try:
        from streamlit.runtime.scriptrunner_utils.script_run_context import (
            get_script_run_ctx,
        )

        return get_script_run_ctx(suppress_warning=True) is not None
    except Exception:
        return False


if __name__ == "__main__" or _has_streamlit_context():
    main()
elif __name__ != "__main__" and "streamlit" in sys.modules:
    # Imported by the Streamlit runtime in non-__main__ mode.
    main()

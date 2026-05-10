# Chat tab — agentic reply + live todo list

Scope: prove the **Chat** tab (added in PR #1, commit `d27a61b4`) really runs
MetaGPT's `DataInterpreter` in `plan_and_act` mode for each user message,
streams the live plan into a todo panel, and ultimately renders the agent's
final reply in chat history.

This plan replaces `test_plan.md` (which covered only the BYOK / Run flow).

## Code anchors

- `streamlit_app.py:328-435` `_run_chat_worker` — daemon thread, builds per-session
  `Context(config=…)`, instantiates `DataInterpreter(react_mode="plan_and_act",
  max_react_loop=5)`, runs `di.run(with_message=requirement)`, dumps
  `di.planner.plan.tasks` into `status["tasks"]`.
- `streamlit_app.py:438-472` `_render_todo_html` — renders tasks; ✓ if
  `is_finished`, ▸ if `task_id == current_task_id`, ○ otherwise.
- `streamlit_app.py:755-846` `render_chat_tab` — two-column layout, polls
  `role.planner.plan.tasks` every 1.0s while thread alive, calls
  `todo_box.markdown(_render_todo_html(...))`.
- `streamlit_app.py:883` tabs registered as `["API keys", "Chat",
  "Run a project", "About Megan"]`.

## Environment

- App: `http://localhost:8501` (Streamlit, already running)
- API key: `OPENAI_API_KEY` env var (session-only) — pasted into API keys tab
  before the recording starts, so the chat run hits a real LLM.

## Primary flow — adversarial

1. **Open Chat tab.**
   - Action: click the tab labeled `Chat` (second tab from the left).
   - Pass: visible elements include the section heading
     `"Chat with Megan"`, the right-hand panel containing the exact text
     `"Megan hasn't decomposed a plan yet. Send a message to start."`, and a
     chat input at the bottom of the page with placeholder
     `Ask Megan to plan, build, or analyse...`.
   - Fail-if-broken: any of the three strings missing, or the tab is absent
     (would mean `render_chat_tab` was not wired into `main()`).

2. **Send a multi-step request the planner has to decompose.**
   - Action: type into the chat input
     `"Compute the sum of the first 30 prime numbers and explain the steps."`
     and press Enter.
   - Pass: the user message is echoed in a chat bubble; the assistant bubble
     immediately shows `Megan is thinking…`; the right panel updates within
     ~15s to show **at least two** todo rows with non-empty `instruction`
     text and monospace task IDs.
   - Fail-if-broken: the right panel stays on the empty-state text the whole
     run → would mean `role.planner.plan.tasks` is never populated (i.e.
     `react_mode` isn't actually `plan_and_act`, or the polling loop never
     sees `role`).

3. **Watch state transitions on the todo panel.**
   - Action: keep the recording rolling while the agent runs (~30-90s).
   - Pass: at least one task row must visibly transition through
     `▸ running` (violet border / shadow) and then to `✓ done` (green
     border). At least one row should change state, not just appear.
   - Fail-if-broken: every row stays at `○` until the end → would mean
     `current_task_id` polling is broken, or all tasks complete in one tick
     (still acceptable but flagged).

4. **Final reply renders in the chat bubble.**
   - Action: wait for `Megan is thinking…` to disappear.
   - Pass: the assistant bubble contains a non-empty reply that includes the
     literal string `"129"` (the correct sum of the first 30 primes:
     2+3+5+7+…+113 = 129). All todo rows now show `✓` (no ▸ marker left).
   - Fail-if-broken:
     - Bubble still shows `Megan is thinking…` → worker never finished.
     - Bubble shows `:warning: …` → `status["state"] == "error"`; capture
       the error message.
     - Reply doesn't contain `129` → either the model genuinely got the
       arithmetic wrong (acceptable; note it) **or** the plan never
       executed code (real failure — verify by re-checking the todo panel
       for any task in `running` that never finished).

5. **Smoke test message persistence.**
   - Action: type a follow-up `"Now multiply that sum by 2."` and send.
   - Pass: previous user + assistant messages are still rendered above the
     new ones (chat_history persisted across reruns); new run produces a
     reply containing `258`.
   - Fail-if-broken: previous bubbles disappear → `chat_history` not
     accumulating in session_state.

## Out of scope

- Regression on BYOK save / Run-a-project tab. Already exercised in prior
  session by save → sidebar flips to "Configured". Will be checked once at
  the top of the recording as setup but won't have separate assertions.
- Multi-provider testing. Only OpenAI is wired with a key.
- Long-running multi-tab concurrency tests.

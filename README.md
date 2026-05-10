# Megan — A Multi-Agent Software Company

> **Megan** is a re-skinned distribution of the open-source
> [MetaGPT](https://github.com/geekan/MetaGPT) multi-agent framework. The
> agent runtime is preserved verbatim — same product manager, architect,
> engineer, data analyst, QA — wrapped in a fresh Streamlit UI with a
> distinct violet/amber palette and a built-in **bring-your-own-key** form.

<p align="center">
  <em>One idea in. A working repo out. From a team of LLM agents that
  collaborate the way a real software company does.</em>
</p>

---

## ✨ What Megan gives you

- **Bring-your-own-key UI.** OpenAI, Anthropic (Claude), Azure OpenAI,
  OpenRouter, DeepSeek, Gemini, Ollama, or any OpenAI-compatible endpoint.
  Keys never leave your browser session.
- **The full MetaGPT team, unchanged.** TeamLeader, ProductManager,
  Architect, ProjectManager, Engineer, DataAnalyst, optional QaEngineer.
- **Live streaming logs.** Watch the agents debate, write a PRD, sketch
  a design, and ship code in real time.
- **A guided three-step flow.** Pick a provider → brief the team →
  watch Megan run.
- **Runs anywhere Streamlit runs.** Local, Docker, Streamlit Cloud,
  Fly.io, etc.

## 🚀 Quickstart

```bash
git clone https://github.com/HimaGamer1/MetaGPT.git megan
cd megan

python -m venv .venv && source .venv/bin/activate   # Python 3.9–3.11
pip install -r requirements.txt
pip install -e .            # installs the `megan` and `metagpt` console scripts
pip install streamlit       # Streamlit is only needed for the UI

streamlit run streamlit_app.py
```

Then open <http://localhost:8501>, paste an API key on the **API keys**
tab, and brief Megan with an idea on the **Run a project** tab.

### CLI

The CLI is preserved exactly as in upstream MetaGPT, available under both
the `megan` and `metagpt` console-script aliases:

```bash
megan "Write a CLI 2048 game in Python."
# or
metagpt "Write a CLI 2048 game in Python."
```

## 🧠 Library use

The unmodified MetaGPT package is re-exported under the Megan brand so
you can write idiomatic Megan code without touching the framework:

```python
from megan import Architect, Context, Engineer2, ProductManager, Team, TeamLeader, config

config.llm.api_key = "sk-..."          # set at runtime, like the UI does
config.llm.model = "gpt-4o-mini"

team = Team(context=Context(config=config))
team.hire([TeamLeader(), ProductManager(), Architect(), Engineer2()])
team.invest(3.0)

import asyncio
asyncio.run(team.run(n_round=3, idea="Build a flashcard CLI app."))
```

The `megan/` package is a thin re-export layer — every class above is
the same object you would get from `metagpt`.

## 🎨 Design

| Token            | Hex        | Use                           |
| ---------------- | ---------- | ----------------------------- |
| Megan Primary    | `#6D28D9`  | buttons, accents, headings    |
| Megan Primary 100| `#EDE9FE`  | soft pill backgrounds         |
| Megan Accent     | `#F59E0B`  | "describe an idea" pills      |
| Megan Surface    | `#FFFFFF`  | cards                         |
| Megan Background | `#FAF8F5`  | warm cream app background     |
| Megan Text       | `#1F2937`  | body text                     |
| Megan Muted      | `#6B7280`  | captions and footnotes        |

The palette intentionally avoids the upstream MetaGPT cyan/blue so the
two products are immediately distinguishable.

## 🗂 Repository layout

```
megan/                  # public package — re-exports the framework under
                        #   the Megan brand and ships the brand assets
metagpt/                # upstream agent framework, copied verbatim
streamlit_app.py        # the Megan Streamlit launcher (the UI you see)
.streamlit/config.toml  # Megan theme tokens for Streamlit
config/config2.yaml     # boot-time placeholder; UI overrides at runtime
docs/UPSTREAM_README.md # original MetaGPT README, preserved as attribution
```

## 🙏 Attribution

Megan stands on the shoulders of the [MetaGPT](https://github.com/geekan/MetaGPT)
project by Alexander Wu and the DeepWisdom team. The agent framework
under `metagpt/` is unchanged — please cite the original project when you
use the runtime, and read the [original README](docs/UPSTREAM_README.md)
for papers, citations, and history.

## 📝 License

MIT — same as upstream MetaGPT.

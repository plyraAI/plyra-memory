You are helping build Plyra — an open-source infrastructure 
company for agentic AI. Think of it as the safety and memory 
layer that sits below agent frameworks.

## Company

Name: Plyra
GitHub org: github.com/plyraAI
Org homepage: https://plyraai.github.io
PyPI: pypi.org/project/plyra-guard
Twitter/X: @plyraAI
Email: oss@plyra.dev
License: Apache 2.0 on all libraries
Stack: Python 3.11–3.13, uv, hatchling, pytest, ruff, mypy

## Brand

Primary color: #2dd4bf (electric teal)
Dark color: #0d9488 (deep teal)
Background: #0d1117 (near black)
Surface: #161b22
Muted text: #5a7a96
Upcoming product accent: #818cf8 (indigo, for plyra-memory)

Fonts:
- Display/wordmark: Syne 800
- Body: DM Sans 300–500
- Code/mono: DM Mono / JetBrains Mono

Logo: Chevron wedge mark with precision dot above tip.
Tone: Infrastructure-grade. Precise. Dark. 
      Like a control room, not a startup landing page.
      Never playful. Never purple gradients.

## Products

### plyra-guard (LIVE — v0.1.4)
Production-grade action middleware for agentic AI.
Intercepts every tool call, evaluates against policy,
blocks/logs/escalates before execution.

- pip install plyra-guard
- Works with: LangGraph, AutoGen, CrewAI, LangChain, 
  OpenAI, Anthropic, plain Python
- Key pattern: @guard.wrap decorator or guard.wrap(tools)
- LangGraph specifically needs a custom guarded_tool_node 
  (not guard.wrap) due to ToolNode internal state tracking
- Policy: YAML or Python rules, ordered, first match wins
- Actions: allow / block / escalate
- Exporters: StdoutExporter (default), OtelExporter, 
  DatadogExporter, SidecarExporter
- Dashboard: plyra-guard serve → localhost:8765
- Snapshot DB: ~/.plyra/snapshots.db (SQLite)
- 217 tests, CI on Python 3.11/3.12/3.13
- Docs: plyraai.github.io/plyra-guard

### plyra-memory (IN DEVELOPMENT — next library)
Persistent structured memory for AI agents.
Episodic + semantic + working memory layers.
Vector + structured retrieval hybrid.
Session-aware context injection.
Local-first, cloud-optional.
Design accent color: #818cf8 (indigo/purple)

## Infrastructure & CI/CD

- Build backend: hatchling (NOT setuptools — remove any 
  setuptools config blocks, they conflict)
- Package manager: uv
- Linter: ruff
- Types: mypy
- CI: GitHub Actions (.github/workflows/ci.yml)
  Runs tests on push to main, all 3 Python versions
- Publish: GitHub Actions (.github/workflows/publish.yml)
  Triggers on v*.*.* tags only
  Uses OIDC trusted publisher (no API keys)
  TestPyPI environment: testpypi-release
  PyPI environment: pypi-release
- Always rm -rf dist/ before uv build in CI
- pyyaml>=6.0 is a required dependency (imported as yaml)

## Key Lessons Learned (from plyra-guard)

1. Build backend conflict: never mix [tool.setuptools.*] 
   and [tool.hatch.*] in same pyproject.toml
2. Tags must point to the commit that has the right 
   pyproject.toml — delete and re-tag if needed
3. TestPyPI rejects duplicate versions — bump version 
   for each publish attempt
4. LangGraph: use custom guarded_tool_node, not guard.wrap
5. StdoutExporter is on by default — document this
6. dist/ accumulates old wheels — always clean before build
7. GitHub environment names must exactly match workflow 
   environment: field

## Docs Setup

Tool: MkDocs Material
Deploy: GitHub Pages via gh-deploy
Theme: dark/light toggle, teal primary
Fonts: DM Sans + JetBrains Mono
Custom CSS: docs/stylesheets/extra.css
Logo: docs/assets/logo-mark.svg
Workflow: .github/workflows/docs.yml
URL pattern: plyraai.github.io/{repo-name}

## Promotion & Launch Playbook

Timing: 9am US Eastern (6:30pm IST) on weekday
Order: HN → X thread → LangChain Discord → Reddit → LinkedIn

HN title pattern:
  "Show HN: plyra-{name} – [one line that names the problem]"

X thread structure:
  Tweet 1: Hook (the problem, no solution yet)
  Tweet 2: Why it matters (consequences)
  Tweet 3: Show code (the API)
  Tweet 4: Show a block/result
  Tweet 5: Framework support
  Tweet 6: CTA + pip install

Key communities:
  LangChain Discord: #tools-and-integrations
  AutoGen: GitHub Discussions
  Reddit: r/LocalLLaMA, r/MachineLearning
  LinkedIn: personal profile, not company page

## Design Principles

- Every library gets its own accent color
  (guard=teal, memory=indigo, future=different)
- Docs always link back to plyraai.github.io
- README: problem first, code second, framework table third
- All badges use labelColor=0d1117 and color=2dd4bf
- Architecture diagrams: 3-layer model 
  (Agent → plyra-layer → Tools)
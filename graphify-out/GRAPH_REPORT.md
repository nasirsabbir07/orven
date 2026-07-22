# Graph Report - orven  (2026-07-22)

## Corpus Check
- 40 files · ~8,716 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 330 nodes · 840 edges · 27 communities (18 shown, 9 thin omitted)
- Extraction: 70% EXTRACTED · 30% INFERRED · 0% AMBIGUOUS · INFERRED: 252 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a5084f79`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Config & Shell Commands|Config & Shell Commands]]
- [[_COMMUNITY_Provider Abstraction & Ollama Backend|Provider Abstraction & Ollama Backend]]
- [[_COMMUNITY_Tool Base & Filesystem Tools|Tool Base & Filesystem Tools]]
- [[_COMMUNITY_CLI Doctor & Entry Tests|CLI Doctor & Entry Tests]]
- [[_COMMUNITY_Agent Execution & Tool Registry|Agent Execution & Tool Registry]]
- [[_COMMUNITY_Model & Provider Selection Commands|Model & Provider Selection Commands]]
- [[_COMMUNITY_Conversation History|Conversation History]]
- [[_COMMUNITY_General CLI Commands|General CLI Commands]]
- [[_COMMUNITY_README Project Overview|README Project Overview]]
- [[_COMMUNITY_CLI App Entrypoint|CLI App Entrypoint]]
- [[_COMMUNITY_Skills Command|Skills Command]]
- [[_COMMUNITY_Workflows Command|Workflows Command]]
- [[_COMMUNITY_Claude  graphify-out Reference|Claude / graphify-out Reference]]
- [[_COMMUNITY_Package Root|Package Root]]
- [[_COMMUNITY_graphify-out knowledge graph directory|graphify-out/ knowledge graph directory]]
- [[_COMMUNITY_CLI entrypoint (orven.mainapp)|CLI entrypoint (orven.main:app)]]
- [[_COMMUNITY_hello sample command|hello sample command]]
- [[_COMMUNITY_Local model provider integration (OllamavLLM)|Local model provider integration (Ollama/vLLM)]]
- [[_COMMUNITY_Local skill & structured workflow support|Local skill & structured workflow support]]
- [[_COMMUNITY_general.py|general.py]]

## God Nodes (most connected - your core abstractions)
1. `load_config()` - 34 edges
2. `ProviderError` - 30 edges
3. `Agent` - 28 edges
4. `ToolContext` - 26 edges
5. `ToolRegistry` - 26 edges
6. `Message` - 22 edges
7. `BaseTool` - 19 edges
8. `OllamaProvider` - 19 edges
9. `ScriptedProvider` - 19 edges
10. `discover_skills()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `test_default_config_path_uses_orven_config_file()` --calls--> `default_config_path()`  [INFERRED]
  tests/test_config.py → src/orven/config/settings.py
- `test_model_set_command()` --calls--> `load_config()`  [INFERRED]
  tests/test_cli.py → src/orven/config/settings.py
- `test_root_command_selects_model()` --calls--> `load_config()`  [INFERRED]
  tests/test_cli.py → src/orven/config/settings.py
- `test_root_command_selects_provider()` --calls--> `load_config()`  [INFERRED]
  tests/test_cli.py → src/orven/config/settings.py
- `test_skills_list_and_show_commands()` --calls--> `load_config()`  [INFERRED]
  tests/test_cli.py → src/orven/config/settings.py

## Import Cycles
- None detected.

## Communities (27 total, 9 thin omitted)

### Community 0 - "Config & Shell Commands"
Cohesion: 0.09
Nodes (51): BaseSettings, InputFunc, format_config(), Return user-facing resolved configuration lines., Show resolved local configuration., show_config(), current_model(), list_models() (+43 more)

### Community 1 - "Provider Abstraction & Ollama Backend"
Cohesion: 0.08
Nodes (38): ABC, Client, Exception, HTTPStatusError, Response, ProviderSettings, ChatRequest, ChatResponse (+30 more)

### Community 2 - "Tool Base & Filesystem Tools"
Cohesion: 0.15
Nodes (25): BaseModel, BaseTool, Any, Execute the tool with validated arguments., ToolContext, ToolResult, ListDirArgs, ListDirTool (+17 more)

### Community 3 - "CLI Doctor & Entry Tests"
Cohesion: 0.07
Nodes (20): doctor(), Check the local Orven environment., ModelInfo, Return models available to this provider., FailingProvider, ModelListProvider, MonkeyPatch, Path (+12 more)

### Community 4 - "Agent Execution & Tool Registry"
Cohesion: 0.35
Nodes (21): Agent, default_tools(), Tools enabled by default. Additional tools (e.g. run_shell) can be appended here, ToolRegistry, _final_text(), Path, ScriptedProvider, test_agent_converts_confirmation_error_into_tool_result() (+13 more)

### Community 6 - "Conversation History"
Cohesion: 0.16
Nodes (7): OnTurnFunc, ConfirmFunc, Path, Conversation, EchoProvider, test_agent_injects_system_prompt_by_default(), test_agent_records_conversation_messages()

### Community 7 - "General CLI Commands"
Cohesion: 0.18
Nodes (10): print_turn_receipt(), Print a one-line-per-tool-call summary of a turn to stderr., _truncate(), _describe_tool_call(), _tool_call_signature(), ToolCallRequest, ToolInvocationRecord, TurnRecord (+2 more)

### Community 8 - "README Project Overview"
Cohesion: 0.20
Nodes (9): Current Status, Development Dependencies, Local Development, Orven, Product Direction, Project Configuration, Project Mission, Repository Layout (+1 more)

### Community 9 - "CLI App Entrypoint"
Cohesion: 0.50
Nodes (3): Context, main(), Orven command-line interface.

### Community 10 - "Skills Command"
Cohesion: 0.15
Nodes (29): ask(), Send a prompt to the configured model provider., _discover(), list_skills(), List discovered local skills., Show the full instructions for a local skill., show_skill(), _discover_in_dir() (+21 more)

### Community 26 - "general.py"
Cohesion: 0.22
Nodes (6): chat(), _make_ask_confirm(), ConfirmFunc, Start an interactive Orven session., Start an interactive chat session., run()

## Knowledge Gaps
- **14 isolated node(s):** `orven`, `graphify`, `Project Mission`, `Product Direction`, `Runtime Dependencies` (+9 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_config()` connect `Config & Shell Commands` to `Skills Command`, `CLI Doctor & Entry Tests`, `Model & Provider Selection Commands`?**
  _High betweenness centrality (0.195) - this node is a cross-community bridge._
- **Why does `ProviderError` connect `Provider Abstraction & Ollama Backend` to `Config & Shell Commands`, `CLI Doctor & Entry Tests`, `Agent Execution & Tool Registry`, `General CLI Commands`, `Skills Command`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Why does `ask()` connect `Skills Command` to `Config & Shell Commands`, `Provider Abstraction & Ollama Backend`, `general.py`, `Agent Execution & Tool Registry`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `load_config()` (e.g. with `show_config()` and `doctor()`) actually correct?**
  _`load_config()` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `ProviderError` (e.g. with `doctor()` and `ask()`) actually correct?**
  _`ProviderError` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `Agent` (e.g. with `ask()` and `Conversation`) actually correct?**
  _`Agent` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `ToolContext` (e.g. with `ListDirArgs` and `ListDirTool`) actually correct?**
  _`ToolContext` has 16 INFERRED edges - model-reasoned connections that need verification._
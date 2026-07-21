# Graph Report - .  (2026-07-18)

## Corpus Check
- Corpus is ~6,659 words - fits in a single context window. You may not need a graph.

## Summary
- 263 nodes · 623 edges · 21 communities (17 shown, 4 thin omitted)
- Extraction: 71% EXTRACTED · 29% INFERRED · 0% AMBIGUOUS · INFERRED: 181 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

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

## God Nodes (most connected - your core abstractions)
1. `load_config()` - 32 edges
2. `ProviderError` - 28 edges
3. `ToolContext` - 23 edges
4. `Message` - 21 edges
5. `OllamaProvider` - 19 edges
6. `ToolRegistry` - 18 edges
7. `ConfigLoadError` - 17 edges
8. `BaseTool` - 17 edges
9. `ChatRequest` - 17 edges
10. `run_shell()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `test_default_config_path_uses_orven_config_file()` --calls--> `default_config_path()`  [INFERRED]
  tests/test_config.py → src/orven/config/settings.py
- `test_model_set_command()` --calls--> `load_config()`  [INFERRED]
  tests/test_cli.py → src/orven/config/settings.py
- `test_root_command_selects_model()` --calls--> `load_config()`  [INFERRED]
  tests/test_cli.py → src/orven/config/settings.py
- `test_root_command_selects_provider()` --calls--> `load_config()`  [INFERRED]
  tests/test_cli.py → src/orven/config/settings.py
- `test_agent_injects_system_prompt_by_default()` --calls--> `Agent`  [INFERRED]
  tests/test_core.py → src/orven/core/agent.py

## Import Cycles
- None detected.

## Communities (21 total, 4 thin omitted)

### Community 0 - "Config & Shell Commands"
Cohesion: 0.10
Nodes (45): BaseSettings, InputFunc, format_config(), Return user-facing resolved configuration lines., Show resolved local configuration., show_config(), _available_models(), _build_agent() (+37 more)

### Community 1 - "Provider Abstraction & Ollama Backend"
Cohesion: 0.10
Nodes (32): Client, Exception, HTTPStatusError, Response, ChatRequest, ChatResponse, Message, ModelProvider (+24 more)

### Community 2 - "Tool Base & Filesystem Tools"
Cohesion: 0.15
Nodes (25): ABC, BaseModel, BaseTool, Any, Execute the tool with validated arguments., ToolContext, ToolResult, ListDirArgs (+17 more)

### Community 3 - "CLI Doctor & Entry Tests"
Cohesion: 0.08
Nodes (16): doctor(), Check the local Orven environment., ModelInfo, Return models available to this provider., FailingProvider, ModelListProvider, MonkeyPatch, Path (+8 more)

### Community 4 - "Agent Execution & Tool Registry"
Cohesion: 0.16
Nodes (19): ask(), Send a prompt to the configured model provider., Agent, _describe_tool_call(), ConfirmFunc, Path, default_tools(), Tools enabled by default. Additional tools (e.g. run_shell) can be appended here (+11 more)

### Community 5 - "Model & Provider Selection Commands"
Cohesion: 0.19
Nodes (12): current_model(), list_models(), List models available from the configured provider., Show the currently selected model., Select the model Orven should use., set_model(), list_providers(), List configured model providers. (+4 more)

### Community 6 - "Conversation History"
Cohesion: 0.24
Nodes (4): Conversation, EchoProvider, test_agent_injects_system_prompt_by_default(), test_agent_records_conversation_messages()

### Community 7 - "General CLI Commands"
Cohesion: 0.22
Nodes (6): chat(), _make_ask_confirm(), ConfirmFunc, Start an interactive Orven session., Start an interactive chat session., run()

### Community 8 - "README Project Overview"
Cohesion: 0.29
Nodes (7): Orven README, CLI entrypoint (orven.main:app), hello sample command, Orven Product Direction (agent runtime / operator shell), Orven Project Mission (local-agent CLI), Local model provider integration (Ollama/vLLM), Local skill & structured workflow support

### Community 9 - "CLI App Entrypoint"
Cohesion: 0.50
Nodes (3): Context, main(), Orven command-line interface.

## Knowledge Gaps
- **8 isolated node(s):** `orven`, `CLAUDE.md (project graphify rules)`, `graphify-out/ knowledge graph directory`, `Orven Product Direction (agent runtime / operator shell)`, `Local model provider integration (Ollama/vLLM)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_config()` connect `Config & Shell Commands` to `CLI Doctor & Entry Tests`, `Agent Execution & Tool Registry`, `Model & Provider Selection Commands`?**
  _High betweenness centrality (0.202) - this node is a cross-community bridge._
- **Why does `ProviderError` connect `Provider Abstraction & Ollama Backend` to `Config & Shell Commands`, `CLI Doctor & Entry Tests`, `Agent Execution & Tool Registry`, `Model & Provider Selection Commands`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Why does `ask()` connect `Agent Execution & Tool Registry` to `Config & Shell Commands`, `Provider Abstraction & Ollama Backend`, `Model & Provider Selection Commands`, `General CLI Commands`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `load_config()` (e.g. with `show_config()` and `doctor()`) actually correct?**
  _`load_config()` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `ProviderError` (e.g. with `doctor()` and `ask()`) actually correct?**
  _`ProviderError` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `ToolContext` (e.g. with `ListDirArgs` and `ListDirTool`) actually correct?**
  _`ToolContext` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `Message` (e.g. with `_final_text()` and `_tool_call_response()`) actually correct?**
  _`Message` has 12 INFERRED edges - model-reasoned connections that need verification._
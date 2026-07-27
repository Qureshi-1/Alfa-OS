# AWESOME LLM APPS — INTEGRATION & ARCHITECTURE ANALYSIS REPORT

> **Document Version**: 1.0.0  
> **Status**: Frozen Reference Analysis  
> **Target System**: ALFA COS v1.0 (Cognitive Operating System)  
> **Repository Context**: `external/awesome-llm-apps-main`

---

## 1. Executive Summary & Directive Compliance

This document contains a comprehensive analysis of all projects located within `external/awesome-llm-apps-main`. In accordance with the **Phase 5 Implementation Directives**:
1. No external code is directly imported into `prototype/`.
2. `external/awesome-llm-apps-main` remains untouched as a read-only reference library.
3. Every project has been evaluated for architectural patterns, prompt structures, workflow designs, and production utilities suitable for native re-implementation within ALFA COS subsystem boundaries.
4. Demo code, Streamlit wrappers, single-script tutorials, and framework-locked implementations are categorized for rewrite or rejection.

---

## 2. Comprehensive Project Analyses

---

### Category A: Advanced AI Agents — Multi-Agent Applications

#### 1. `advanced_ai_agents/multi_agent_apps/agent_teams`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/agent_teams`
- **Purpose**: Demonstrates multi-agent collaboration with specialized roles (researcher, analyst, writer) using CrewAI.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: Yes (conceptually)
- **What exactly should be reused?**: Agent role definition schemas and hierarchical task decomposition prompts.
- **Where it belongs inside ALFA**: `prototype/agent/agent_runtime.py` and `prototype/cognition/planner.py`
- **Estimated Implementation Effort**: Low (1-2 days)
- **Dependencies**: None (native Python)
- **Risks**: Framework lock-in if using CrewAI primitives.
- **Final Decision**: REWRITE (Native `MultiAgentCoordinator` strategy)

#### 2. `advanced_ai_agents/multi_agent_apps/ai_aqi_analysis_agent`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/ai_aqi_analysis_agent`
- **Purpose**: Fetches air quality data via APIs and produces environmental reports.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: High domain specificity; demo app.
- **Final Decision**: IGNORE

#### 3. `advanced_ai_agents/multi_agent_apps/ai_domain_deep_research_agent`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/ai_domain_deep_research_agent`
- **Purpose**: Performs web search, source verification, and multi-step domain research.
- **Production Readiness (1-10)**: 7/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Iterative query expansion logic, source credibility scoring heuristic, and research synthesis prompt pipeline.
- **Where it belongs inside ALFA**: `prototype/agent/strategies/deep_research.py` & `prototype/cognition/reasoner.py`
- **Estimated Implementation Effort**: Medium (3-4 days)
- **Dependencies**: `httpx`, `beautifulsoup4`
- **Risks**: Web scraping rate limits.
- **Final Decision**: REWRITE

#### 4. `advanced_ai_agents/multi_agent_apps/ai_email_gtm_outreach_agent`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/ai_email_gtm_outreach_agent`
- **Purpose**: Automates outreach email composition based on user profiles.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Narrow sales use-case.
- **Final Decision**: IGNORE

#### 5. `advanced_ai_agents/multi_agent_apps/ai_financial_coach_agent`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/ai_financial_coach_agent`
- **Purpose**: Provides financial budget advice and spending analysis.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Niche financial advisor logic.
- **Final Decision**: IGNORE

#### 6. `advanced_ai_agents/multi_agent_apps/ai_home_renovation_agent`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/ai_home_renovation_agent`
- **Purpose**: Home renovation planner demo using multi-agent workflow.
- **Production Readiness (1-10)**: 2/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Toy demo application.
- **Final Decision**: IGNORE

#### 7. `advanced_ai_agents/multi_agent_apps/ai_mental_wellbeing_agent`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/ai_mental_wellbeing_agent`
- **Purpose**: Mental wellbeing chatbot with empathetic prompts.
- **Production Readiness (1-10)**: 2/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Safety and regulatory risk.
- **Final Decision**: IGNORE

#### 8. `advanced_ai_agents/multi_agent_apps/ai_negotiation_battle_simulator`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/ai_negotiation_battle_simulator`
- **Purpose**: Simulates debate/negotiation between two opposing agent roles.
- **Production Readiness (1-10)**: 6/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Debate loop coordination pattern, consensus-checking logic, and turn-taking protocol.
- **Where it belongs inside ALFA**: `prototype/agent/multi_agent.py` (`MultiAgentCoordinator.debate()`)
- **Estimated Implementation Effort**: Low (1-2 days)
- **Dependencies**: Native ALFA EventBus
- **Risks**: Infinite loop risk if debate fails to converge.
- **Final Decision**: REWRITE

#### 9. `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents`
- **Purpose**: Summarizes news RSS feeds into audio scripts.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: Text chunking prompt format for summary script generation.
- **Where it belongs inside ALFA**: `prototype/cognition/planner.py`
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: None
- **Risks**: Specific to content production.
- **Final Decision**: IGNORE

#### 10. `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent`
- **Purpose**: Agent that evaluates its own outputs and writes updated prompt strategies.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Self-correction feedback loop, skill persistence mechanism, and performance evaluation metrics.
- **Where it belongs inside ALFA**: `prototype/learning/learning_engine.py` & `prototype/reflection/reflection_engine.py`
- **Estimated Implementation Effort**: Medium (3 days)
- **Dependencies**: Native SQLite storage
- **Risks**: Instability if self-reflection updates degrade baseline performance.
- **Final Decision**: REWRITE

#### 11. `advanced_ai_agents/multi_agent_apps/ai_speech_trainer_agent`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/ai_speech_trainer_agent`
- **Purpose**: Evaluates transcript grammar and tone for public speaking.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Niche single-use demo.
- **Final Decision**: IGNORE

#### 12. `advanced_ai_agents/multi_agent_apps/devpulse_ai`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/devpulse_ai`
- **Purpose**: Developer metrics and GitHub repository activity tracker.
- **Production Readiness (1-10)**: 5/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Git activity aggregation schema and project health metric prompts.
- **Where it belongs inside ALFA**: `prototype/plugins/builtin/git_analyzer.py`
- **Estimated Implementation Effort**: Medium (2 days)
- **Dependencies**: `httpx`
- **Risks**: API rate limits.
- **Final Decision**: REWRITE

#### 13. `advanced_ai_agents/multi_agent_apps/multi_agent_researcher`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/multi_agent_researcher`
- **Purpose**: Parallel task dispatch for research search, extraction, and formatting.
- **Production Readiness (1-10)**: 7/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Parallel execution pipeline architecture and sub-task merge heuristics.
- **Where it belongs inside ALFA**: `prototype/agent/agent_planner.py` & `prototype/cognition/executor.py`
- **Estimated Implementation Effort**: Medium (2-3 days)
- **Dependencies**: Native `concurrent.futures` / `asyncio`
- **Risks**: None.
- **Final Decision**: REWRITE

#### 14. `advanced_ai_agents/multi_agent_apps/multi_agent_trust_layer`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/multi_agent_trust_layer`
- **Purpose**: Verification agent that inspects outputs of other agents before delivery.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Pre-execution security check schema and output validation pipeline.
- **Where it belongs inside ALFA**: `prototype/decision/decision_engine.py` & `prototype/reflection/reflection_engine.py`
- **Estimated Implementation Effort**: Medium (2 days)
- **Dependencies**: Native Pydantic models
- **Risks**: Latency overhead on tool executions.
- **Final Decision**: REWRITE

#### 15. `advanced_ai_agents/multi_agent_apps/product_launch_intelligence_agent`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/product_launch_intelligence_agent`
- **Purpose**: Product market research multi-agent demo.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Marketing domain specific.
- **Final Decision**: IGNORE

#### 16. `advanced_ai_agents/multi_agent_apps/trust_gated_agent_team`
- **Folder Name**: `advanced_ai_agents/multi_agent_apps/trust_gated_agent_team`
- **Purpose**: Multi-agent team with explicit permission gating between steps.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Policy decision check (`PolicyCheck`), permission gate evaluation pattern, and step execution gating.
- **Where it belongs inside ALFA**: `prototype/executive/executive_controller.py` & `prototype/common/types.py`
- **Estimated Implementation Effort**: Low (1-2 days)
- **Dependencies**: Native ALFA types
- **Risks**: Workflow stalling if authorization is blocked.
- **Final Decision**: REWRITE

---

### Category B: Advanced AI Agents — Single Agent Applications

#### 17. `advanced_ai_agents/single_agent_apps/ai_agent_governance`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_agent_governance`
- **Purpose**: Audit logging, policy compliance enforcement, and tool execution governance.
- **Production Readiness (1-10)**: 9/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Policy rule engine logic, constraint checking algorithm, and audit trail record structure.
- **Where it belongs inside ALFA**: `prototype/diagnostics/diagnostics.py` & `prototype/decision/decision_engine.py`
- **Estimated Implementation Effort**: Medium (2-3 days)
- **Dependencies**: Native SQLite / JSON schemas
- **Risks**: Strict policy defaults could block valid tool usage.
- **Final Decision**: REWRITE

#### 18. `advanced_ai_agents/single_agent_apps/ai_consultant_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_consultant_agent`
- **Purpose**: Advisory consultant application wrapper.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Specific business domain.
- **Final Decision**: IGNORE

#### 19. `advanced_ai_agents/single_agent_apps/ai_customer_support_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_customer_support_agent`
- **Purpose**: Ticket routing and support message responder demo.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: Ticket intent classification rules.
- **Where it belongs inside ALFA**: `prototype/cognition/perception.py`
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: None
- **Risks**: Narrow demo focus.
- **Final Decision**: IGNORE

#### 20. `advanced_ai_agents/single_agent_apps/ai_deep_research_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_deep_research_agent`
- **Purpose**: Single agent recursive research loop with web retrieval.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Recursive link traversal logic, search query generator prompts, and document relevance filtering.
- **Where it belongs inside ALFA**: `prototype/tools/builtin/web_search.py` & `prototype/agent/strategies/deep_research.py`
- **Estimated Implementation Effort**: Medium (3 days)
- **Dependencies**: `httpx`, `pydantic`
- **Risks**: Network latency.
- **Final Decision**: REWRITE

#### 21. `advanced_ai_agents/single_agent_apps/ai_email_gtm_reachout_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_email_gtm_reachout_agent`
- **Purpose**: Email composition application.
- **Production Readiness (1-10)**: 2/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Duplicate of outreach app.
- **Final Decision**: IGNORE

#### 22. `advanced_ai_agents/single_agent_apps/ai_fraud_investigation_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_fraud_investigation_agent`
- **Purpose**: Anomaly detection logic on transaction records.
- **Production Readiness (1-10)**: 5/10
- **Can ALFA use it?**: Yes (conceptually)
- **What exactly should be reused?**: Anomaly classification prompt patterns and threshold evaluation heuristics.
- **Where it belongs inside ALFA**: `prototype/reflection/reflector.py`
- **Estimated Implementation Effort**: Low (1-2 days)
- **Dependencies**: None
- **Risks**: Domain specific transaction fields.
- **Final Decision**: REWRITE

#### 23. `advanced_ai_agents/single_agent_apps/ai_health_fitness_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_health_fitness_agent`
- **Purpose**: Fitness coaching assistant demo.
- **Production Readiness (1-10)**: 2/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Health compliance.
- **Final Decision**: IGNORE

#### 24. `advanced_ai_agents/single_agent_apps/ai_investment_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_investment_agent`
- **Purpose**: Stock ticker lookup and sentiment analysis script.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: Financial indicator calculation helpers.
- **Where it belongs inside ALFA**: `prototype/tools/builtin/calculator.py`
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: None
- **Risks**: API dependence.
- **Final Decision**: IGNORE

#### 25. `advanced_ai_agents/single_agent_apps/ai_journalist_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_journalist_agent`
- **Purpose**: Article drafting pipeline with outline, draft, and critique steps.
- **Production Readiness (1-10)**: 6/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Multi-pass document generation pipeline (outline → draft → revise).
- **Where it belongs inside ALFA**: `prototype/cognition/planner.py`
- **Estimated Implementation Effort**: Low (1-2 days)
- **Dependencies**: None
- **Risks**: None.
- **Final Decision**: REWRITE

#### 26. `advanced_ai_agents/single_agent_apps/ai_meeting_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_meeting_agent`
- **Purpose**: Meeting transcript parser and action-item extractor.
- **Production Readiness (1-10)**: 7/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Structured JSON action item extraction schema and prompt template.
- **Where it belongs inside ALFA**: `prototype/cognition/perception.py`
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: Native Pydantic
- **Risks**: None.
- **Final Decision**: REWRITE

#### 27. `advanced_ai_agents/single_agent_apps/ai_movie_production_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_movie_production_agent`
- **Purpose**: Film script generator demo.
- **Production Readiness (1-10)**: 2/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Niche creative demo.
- **Final Decision**: IGNORE

#### 28. `advanced_ai_agents/single_agent_apps/ai_personal_finance_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_personal_finance_agent`
- **Purpose**: Personal expense tracker wrapper.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Duplicate finance app.
- **Final Decision**: IGNORE

#### 29. `advanced_ai_agents/single_agent_apps/ai_recipe_meal_planning_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_recipe_meal_planning_agent`
- **Purpose**: Recipe recommender app.
- **Production Readiness (1-10)**: 2/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Consumer toy app.
- **Final Decision**: IGNORE

#### 30. `advanced_ai_agents/single_agent_apps/ai_startup_insight_fire1_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_startup_insight_fire1_agent`
- **Purpose**: Startup intelligence research agent script.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Overlaps with deep research agent.
- **Final Decision**: IGNORE

#### 31. `advanced_ai_agents/single_agent_apps/ai_system_architect_r1`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/ai_system_architect_r1`
- **Purpose**: Generates architecture diagrams (Mermaid) and system designs from user requirements.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: System design prompt taxonomy, Mermaid block generator, and component dependency validator.
- **Where it belongs inside ALFA**: `prototype/tools/builtin/system_info.py` & `prototype/cognition/planner.py`
- **Estimated Implementation Effort**: Medium (2 days)
- **Dependencies**: None
- **Risks**: Syntax formatting errors in generated Mermaid strings.
- **Final Decision**: REWRITE

#### 32. `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent`
- **Purpose**: Financial transcript sentiment analysis.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Niche financial tool.
- **Final Decision**: IGNORE

#### 33. `advanced_ai_agents/single_agent_apps/research_agent_gemini_interaction_api`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/research_agent_gemini_interaction_api`
- **Purpose**: Gemini API interaction patterns with tool-use functions.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Gemini function calling payload format and multi-turn interaction schemas.
- **Where it belongs inside ALFA**: `prototype/modelhub/providers/gemini.py`
- **Estimated Implementation Effort**: Medium (2 days)
- **Dependencies**: `httpx`
- **Risks**: Provider specific schema variations.
- **Final Decision**: REWRITE

#### 34. `advanced_ai_agents/single_agent_apps/windows_use_autonomous_agent`
- **Folder Name**: `advanced_ai_agents/single_agent_apps/windows_use_autonomous_agent`
- **Purpose**: Windows OS GUI automation via UI Automation / pyautogui.
- **Production Readiness (1-10)**: 7/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Desktop element interaction abstractions, screen bounds calculation logic, and command validation safety bounds.
- **Where it belongs inside ALFA**: `prototype/tools/builtin/os_automation.py`
- **Estimated Implementation Effort**: High (4-5 days)
- **Dependencies**: `pywin32` / OS APIs
- **Risks**: Security risk of unmonitored desktop actions; OS permission prompts.
- **Final Decision**: REWRITE

---

### Category C: Autonomous Game Playing Agents

#### 35. `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_3dpygame_r1`
- **Folder Name**: `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_3dpygame_r1`
- **Purpose**: 3D Pygame game generation experiment.
- **Production Readiness (1-10)**: 2/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: Pygame
- **Risks**: Experimental code.
- **Final Decision**: IGNORE

#### 36. `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_chess_agent`
- **Folder Name**: `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_chess_agent`
- **Purpose**: Chess move evaluator LLM wrapper.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: `python-chess`
- **Risks**: Game specific logic.
- **Final Decision**: IGNORE

#### 37. `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent`
- **Folder Name**: `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent`
- **Purpose**: Tic-tac-toe game demo.
- **Production Readiness (1-10)**: 1/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Trivial toy app.
- **Final Decision**: IGNORE

---

### Category D: Advanced LLM Applications

#### 38. `advanced_llm_apps/chat-with-tarots`
- **Folder Name**: `advanced_llm_apps/chat-with-tarots`
- **Purpose**: Tarot card reading chatbot.
- **Production Readiness (1-10)**: 1/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Irrelevant domain.
- **Final Decision**: IGNORE

#### 39. `advanced_llm_apps/chat_with_X_tutorials`
- **Folder Name**: `advanced_llm_apps/chat_with_X_tutorials`
- **Purpose**: PDF/CSV/Doc QA tutorials using LangChain.
- **Production Readiness (1-10)**: 5/10
- **Can ALFA use it?**: Yes (conceptually)
- **What exactly should be reused?**: Document chunking strategy (character & token splitter logic) and metadata preservation schema.
- **Where it belongs inside ALFA**: `prototype/memory/persistent_memory.py`
- **Estimated Implementation Effort**: Low (1-2 days)
- **Dependencies**: Native Python
- **Risks**: Framework heavy reference implementation.
- **Final Decision**: REWRITE

#### 40. `advanced_llm_apps/cursor_ai_experiments`
- **Folder Name**: `advanced_llm_apps/cursor_ai_experiments`
- **Purpose**: Prompt rules for code generation and IDE refactoring.
- **Production Readiness (1-10)**: 7/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: System prompt rules for agentic code edits and context assembly guidelines.
- **Where it belongs inside ALFA**: `prototype/agent/agent_planner.py`
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: None
- **Risks**: None.
- **Final Decision**: REWRITE

#### 41. `advanced_llm_apps/gpt_oss_critique_improvement_loop`
- **Folder Name**: `advanced_llm_apps/gpt_oss_critique_improvement_loop`
- **Purpose**: Generates output, evaluates via open-source model critique, iteratively improves.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Model-graded critique criteria checklist and structured revision prompt format.
- **Where it belongs inside ALFA**: `prototype/reflection/reflection_engine.py` & `prototype/cognition/reflector.py`
- **Estimated Implementation Effort**: Medium (2 days)
- **Dependencies**: Native ModelHub Router
- **Risks**: Multi-pass inference latency.
- **Final Decision**: REWRITE

#### 42. `advanced_llm_apps/llm_apps_with_memory_tutorials`
- **Folder Name**: `advanced_llm_apps/llm_apps_with_memory_tutorials`
- **Purpose**: Demonstrates MemGPT / Zep memory integration.
- **Production Readiness (1-10)**: 6/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Episodic vs semantic memory consolidation rule system.
- **Where it belongs inside ALFA**: `prototype/memory/memory_manager.py`
- **Estimated Implementation Effort**: Medium (2 days)
- **Dependencies**: Native SQLite
- **Risks**: Over-consolidation of short-term memories.
- **Final Decision**: REWRITE

#### 43. `advanced_llm_apps/llm_finetuning_tutorials`
- **Folder Name**: `advanced_llm_apps/llm_finetuning_tutorials`
- **Purpose**: LoRA/QLoRA fine-tuning Jupyter notebooks.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: PyTorch / Unsloth
- **Risks**: Out of scope for client runtime.
- **Final Decision**: IGNORE

#### 44. `advanced_llm_apps/llm_optimization_tools`
- **Folder Name**: `advanced_llm_apps/llm_optimization_tools`
- **Purpose**: Prompt compression and token usage minimization utilities.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Token budget calculator, context truncator, and system prompt deduplicator.
- **Where it belongs inside ALFA**: `prototype/context/context_manager.py` & `prototype/modelhub/router.py`
- **Estimated Implementation Effort**: Medium (2 days)
- **Dependencies**: Native Python
- **Risks**: Context loss if compression is too aggressive.
- **Final Decision**: REWRITE

#### 45. `advanced_llm_apps/multimodal_video_moment_finder`
- **Folder Name**: `advanced_llm_apps/multimodal_video_moment_finder`
- **Purpose**: Video frame indexing and timestamp retrieval demo.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: OpenCV
- **Risks**: Heavy dependencies.
- **Final Decision**: IGNORE

#### 46. `advanced_llm_apps/resume_job_matcher`
- **Folder Name**: `advanced_llm_apps/resume_job_matcher`
- **Purpose**: Resume parsing and match scoring app.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Niche utility demo.
- **Final Decision**: IGNORE

#### 47. `advanced_llm_apps/thinkpath_chatbot_app`
- **Folder Name**: `advanced_llm_apps/thinkpath_chatbot_app`
- **Purpose**: Displays chain-of-thought reasoning steps in Streamlit.
- **Production Readiness (1-10)**: 5/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Thought-chunk parser for extracting `<think>` tags during streaming responses.
- **Where it belongs inside ALFA**: `prototype/modelhub/base.py` & PySide6 Desktop UI (`ChatWorkspace`)
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: Native regex
- **Risks**: None.
- **Final Decision**: REWRITE

---

### Category E: Agent Skills

#### 48. `agent_skills/advisor-orchestrator-worker`
- **Folder Name**: `agent_skills/advisor-orchestrator-worker`
- **Purpose**: Three-tier architecture pattern (Advisor policy -> Orchestrator plan -> Worker execution).
- **Production Readiness (1-10)**: 9/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Three-tier responsibility separation taxonomy, inter-tier contract schemas, and error propagation rules.
- **Where it belongs inside ALFA**: `prototype/executive/executive_controller.py`, `prototype/cognition/cognition_runtime.py`, `prototype/worker/worker_manager.py`
- **Estimated Implementation Effort**: Medium (3 days)
- **Dependencies**: Native ALFA EventBus
- **Risks**: Already partially aligned with ALFA core architecture; ensure no duplicate orchestration paths.
- **Final Decision**: REWRITE

#### 49. `agent_skills/commit-archaeologist`
- **Folder Name**: `agent_skills/commit-archaeologist`
- **Purpose**: Analyzes git history to reconstruct feature evolution and pinpoint regression origins.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Git log analysis prompts, diff parsing pipeline, and commit message summarizer.
- **Where it belongs inside ALFA**: `prototype/plugins/builtin/git_analyzer.py`
- **Estimated Implementation Effort**: Low (1-2 days)
- **Dependencies**: Subprocess git calls
- **Risks**: Large diff memory usage.
- **Final Decision**: REWRITE

#### 50. `agent_skills/evals`
- **Folder Name**: `agent_skills/evals`
- **Purpose**: Benchmark eval framework for agent accuracy, latency, and tool-selection correctness.
- **Production Readiness (1-10)**: 9/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Automated test suite evaluation harness, scoring metrics (accuracy, latency, adherence), and regression test dataset schema.
- **Where it belongs inside ALFA**: `tests/test_evals.py` & `prototype/diagnostics/diagnostics.py`
- **Estimated Implementation Effort**: Medium (2 days)
- **Dependencies**: `pytest`
- **Risks**: Benchmark runtime execution time.
- **Final Decision**: REWRITE

#### 51. `agent_skills/project-graveyard`
- **Folder Name**: `agent_skills/project-graveyard`
- **Purpose**: Analyzes deprecated code paths and logs reasons for removal.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Niche utility.
- **Final Decision**: IGNORE

#### 52. `agent_skills/scope-creep-detector`
- **Folder Name**: `agent_skills/scope-creep-detector`
- **Purpose**: Evaluates plan steps against original goal boundary to reject unauthorized tasks.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Goal divergence scoring algorithm and prompt constraint validator.
- **Where it belongs inside ALFA**: `prototype/decision/decision_engine.py` & `prototype/cognition/planner.py`
- **Estimated Implementation Effort**: Low (1-2 days)
- **Dependencies**: Native Pydantic
- **Risks**: Over-strict scope checks might abort complex legitimate goals.
- **Final Decision**: REWRITE

#### 53. `agent_skills/self-improving-agent-skills`
- **Folder Name**: `agent_skills/self-improving-agent-skills`
- **Purpose**: Dynamically generates and registers new skill instructions based on success/failure reflection.
- **Production Readiness (1-10)**: 9/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Skill synthesis prompt template, skill markdown schema, and automatic skill registration workflow.
- **Where it belongs inside ALFA**: `prototype/learning/learning_engine.py` & `prototype/plugins/plugin_manager.py`
- **Estimated Implementation Effort**: Medium (3 days)
- **Dependencies**: Native disk storage (`data/skills/`)
- **Risks**: Generated invalid skill scripts. Must restrict to markdown/prompt skills.
- **Final Decision**: REWRITE

#### 54. `agent_skills/thinking-out-loud`
- **Folder Name**: `agent_skills/thinking-out-loud`
- **Purpose**: Streams intermediate reasoning steps and tool selection decisions to UI before execution.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Intermediate reasoning event format (`ReasoningTraceEvent`) and UI channel dispatcher.
- **Where it belongs inside ALFA**: `prototype/cognition/reasoner.py` & `prototype/common/event_bus.py`
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: Native ALFA EventBus
- **Risks**: Event noise in UI if unthrottled.
- **Final Decision**: REWRITE

---

### Category F: Framework Crash Courses

#### 55. `ai_agent_framework_crash_course/google_adk_crash_course`
- **Folder Name**: `ai_agent_framework_crash_course/google_adk_crash_course`
- **Purpose**: Google Agent Development Kit tutorial code.
- **Production Readiness (1-10)**: 2/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: External SDK
- **Risks**: Tutorial material.
- **Final Decision**: IGNORE

#### 56. `ai_agent_framework_crash_course/openai_sdk_crash_course`
- **Folder Name**: `ai_agent_framework_crash_course/openai_sdk_crash_course`
- **Purpose**: OpenAI SDK basic usage scripts.
- **Production Readiness (1-10)**: 2/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: External SDK
- **Risks**: Basic tutorial code.
- **Final Decision**: IGNORE

---

### Category G: Always-On Agents

#### 57. `always_on_agents/always_on_hn_briefing_agent`
- **Folder Name**: `always_on_agents/always_on_hn_briefing_agent`
- **Purpose**: Background daemon fetching Hacker News top stories on cron schedule.
- **Production Readiness (1-10)**: 7/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Cron scheduling integration pattern with `WorkerManager` and deduplication hash filter.
- **Where it belongs inside ALFA**: `prototype/worker/worker_manager.py`
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: Native ALFA Worker framework
- **Risks**: Background battery/CPU consumption on mobile.
- **Final Decision**: REWRITE

#### 58. `always_on_agents/release_radar_agent`
- **Folder Name**: `always_on_agents/release_radar_agent`
- **Purpose**: Monitors GitHub releases for specified repositories and sends notifications.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Release version tag comparator, release notes summarizer prompt, and background worker task.
- **Where it belongs inside ALFA**: `prototype/worker/base_worker.py` & `prototype/plugins/builtin/`
- **Estimated Implementation Effort**: Low (1-2 days)
- **Dependencies**: `httpx`
- **Risks**: GitHub API unauthenticated rate limit (60 requests/hr).
- **Final Decision**: REWRITE

---

### Category H: Generative UI Agents

#### 59. `generative_ui_agents/ai-dashboard-canvas-agent`
- **Folder Name**: `generative_ui_agents/ai-dashboard-canvas-agent`
- **Purpose**: Dynamically renders dashboard card components from JSON schemas.
- **Production Readiness (1-10)**: 7/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Dynamic UI component schema definition (cards, metrics, charts) and JSON-to-widget mapper logic.
- **Where it belongs inside ALFA**: PySide6 Desktop UI (`DashboardWorkspace`) & Flutter Android UI
- **Estimated Implementation Effort**: Medium (3 days)
- **Dependencies**: PySide6 / Flutter
- **Risks**: Rendering invalid schema structures cleanly.
- **Final Decision**: REWRITE

#### 60. `generative_ui_agents/ai-deep-research-agent`
- **Folder Name**: `generative_ui_agents/ai-deep-research-agent`
- **Purpose**: Deep research UI layout generator demo.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: Duplicate of deep research concept.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: React / Next.js
- **Risks**: React specific implementation.
- **Final Decision**: IGNORE

#### 61. `generative_ui_agents/ai-financial-coach-agent`
- **Folder Name**: `generative_ui_agents/ai-financial-coach-agent`
- **Purpose**: Financial UI generator demo.
- **Production Readiness (1-10)**: 2/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Niche web UI.
- **Final Decision**: IGNORE

#### 62. `generative_ui_agents/ai-mcp-app-builder`
- **Folder Name**: `generative_ui_agents/ai-mcp-app-builder`
- **Purpose**: Builds web UI interfaces for Model Context Protocol tools.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: MCP tool schema to UI form layout generation algorithm.
- **Where it belongs inside ALFA**: `prototype/tools/tool_manager.py` & PySide6 UI (`WorkerWorkspace`)
- **Estimated Implementation Effort**: Medium (3 days)
- **Dependencies**: PySide6
- **Risks**: Form input validation on custom types.
- **Final Decision**: REWRITE

#### 63. `generative_ui_agents/ai-shadcn-component-generator`
- **Folder Name**: `generative_ui_agents/ai-shadcn-component-generator`
- **Purpose**: React shadcn component code generator.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: React / Tailwind
- **Risks**: Incompatible stack (PySide6 / Flutter).
- **Final Decision**: IGNORE

#### 64. `generative_ui_agents/generative-ui-starter-project`
- **Folder Name**: `generative_ui_agents/generative-ui-starter-project`
- **Purpose**: Next.js generative UI starter template.
- **Production Readiness (1-10)**: 2/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: Next.js
- **Risks**: Starter template.
- **Final Decision**: IGNORE

#### 65. `generative_ui_agents/mcp-apps-generative-ui-showcase`
- **Folder Name**: `generative_ui_agents/mcp-apps-generative-ui-showcase`
- **Purpose**: Showcase app combining MCP tools and interactive web cards.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: Duplicate showcase logic.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: Web stack
- **Risks**: Web stack lock-in.
- **Final Decision**: IGNORE

---

### Category I: Model Context Protocol (MCP) AI Agents

#### 66. `mcp_ai_agents/ai_travel_planner_mcp_agent_team`
- **Folder Name**: `mcp_ai_agents/ai_travel_planner_mcp_agent_team`
- **Purpose**: Multi-agent travel team using MCP servers.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: MCP SDK
- **Risks**: Domain demo.
- **Final Decision**: IGNORE

#### 67. `mcp_ai_agents/browser_mcp_agent`
- **Folder Name**: `mcp_ai_agents/browser_mcp_agent`
- **Purpose**: Exposes browser control actions via MCP server (navigate, click, type, screenshot).
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Browser automation command set definition, DOM selector strategy, and screenshot response protocol.
- **Where it belongs inside ALFA**: `prototype/tools/builtin/browser_tool.py`
- **Estimated Implementation Effort**: Medium (3 days)
- **Dependencies**: `playwright`
- **Risks**: Headless browser installation size (~150MB).
- **Final Decision**: REWRITE

#### 68. `mcp_ai_agents/github_mcp_agent`
- **Folder Name**: `mcp_ai_agents/github_mcp_agent`
- **Purpose**: Integrates GitHub API via MCP tools (issues, PRs, contents, search).
- **Production Readiness (1-10)**: 9/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: GitHub API endpoints abstraction, repo query parameters, and issue/PR summary formatting.
- **Where it belongs inside ALFA**: `prototype/tools/builtin/github_tool.py` & `prototype/plugins/builtin/`
- **Estimated Implementation Effort**: Low (2 days)
- **Dependencies**: `httpx`
- **Risks**: GitHub token requirement.
- **Final Decision**: REWRITE

#### 69. `mcp_ai_agents/multi_mcp_agent`
- **Folder Name**: `mcp_ai_agents/multi_mcp_agent`
- **Purpose**: Agent that dynamically connects to multiple external MCP servers.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Client-side MCP JSON-RPC 2.0 protocol handler, tool discovery protocol, and parameter translation layer.
- **Where it belongs inside ALFA**: `prototype/tools/tool_manager.py`
- **Estimated Implementation Effort**: High (4 days)
- **Dependencies**: Native `asyncio` & JSON-RPC
- **Risks**: Remote MCP server connection timeouts.
- **Final Decision**: REWRITE

#### 70. `mcp_ai_agents/multi_mcp_agent_router`
- **Folder Name**: `mcp_ai_agents/multi_mcp_agent_router`
- **Purpose**: Routes incoming tool calls to the correct MCP server instance based on capability matching.
- **Production Readiness (1-10)**: 9/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Capability-based tool routing algorithm, endpoint health checks, and fallback retry mechanism.
- **Where it belongs inside ALFA**: `prototype/cognition/reasoner.py` & `prototype/tools/tool_manager.py`
- **Estimated Implementation Effort**: Medium (2-3 days)
- **Dependencies**: Native ALFA codebase
- **Risks**: Already partially satisfied by `Reasoner._capability_match()`; merge routing logic cleanly.
- **Final Decision**: REWRITE

#### 71. `mcp_ai_agents/notion_mcp_agent`
- **Folder Name**: `mcp_ai_agents/notion_mcp_agent`
- **Purpose**: Notion page and database manipulation via MCP.
- **Production Readiness (1-10)**: 5/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: Notion API
- **Risks**: Proprietary third-party service integration.
- **Final Decision**: IGNORE

---

### Category J: RAG Tutorials & Implementations

#### 72. `rag_tutorials/agentic_rag_embedding_gemma`
- **Folder Name**: `rag_tutorials/agentic_rag_embedding_gemma`
- **Purpose**: Gemma embeddings with basic vector store retrieval.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: HuggingFace / Gemma
- **Risks**: Model specific tutorial.
- **Final Decision**: IGNORE

#### 73. `rag_tutorials/agentic_rag_gpt5`
- **Folder Name**: `rag_tutorials/agentic_rag_gpt5`
- **Purpose**: High-level hypothetical RAG agent concept script.
- **Production Readiness (1-10)**: 2/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Experimental demo code.
- **Final Decision**: IGNORE

#### 74. `rag_tutorials/agentic_rag_math_agent`
- **Folder Name**: `rag_tutorials/agentic_rag_math_agent`
- **Purpose**: Math question solver using Wolfram / Python REPL tool retrieval.
- **Production Readiness (1-10)**: 6/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Safe AST evaluation logic for mathematical expressions.
- **Where it belongs inside ALFA**: `prototype/tools/builtin/calculator.py`
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: Native `ast` module
- **Risks**: None.
- **Final Decision**: REWRITE

#### 75. `rag_tutorials/agentic_rag_with_reasoning`
- **Folder Name**: `rag_tutorials/agentic_rag_with_reasoning`
- **Purpose**: Combines vector retrieval with multi-step reasoning before final synthesis.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Query reformulation prompt template, retrieved chunk relevance evaluation, and context-grounded synthesis prompt.
- **Where it belongs inside ALFA**: `prototype/cognition/planner.py` & `prototype/cognition/reasoner.py`
- **Estimated Implementation Effort**: Medium (2 days)
- **Dependencies**: Native SQLite / Vector storage
- **Risks**: Latency on low-power desktop hardware.
- **Final Decision**: REWRITE

#### 76. `rag_tutorials/agentic_typed_rag_pydanticai`
- **Folder Name**: `rag_tutorials/agentic_typed_rag_pydanticai`
- **Purpose**: Strongly-typed RAG output schemas using PydanticAI.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Strongly-typed dataclass/Pydantic schemas for RAG query request, chunk match result, and citation record.
- **Where it belongs inside ALFA**: `prototype/common/types.py` & `prototype/memory/persistent_memory.py`
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: `pydantic`
- **Risks**: None.
- **Final Decision**: REWRITE

#### 77. `rag_tutorials/ai_blog_search`
- **Folder Name**: `rag_tutorials/ai_blog_search`
- **Purpose**: Simple website scraper and article QA bot.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Trivial demo.
- **Final Decision**: IGNORE

#### 78. `rag_tutorials/autonomous_rag`
- **Folder Name**: `rag_tutorials/autonomous_rag`
- **Purpose**: RAG pipeline that self-corrects and rewrites queries when retrieval score is low.
- **Production Readiness (1-10)**: 9/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Self-correction retrieval loop, query rewrite heuristic, and hallucination check validator.
- **Where it belongs inside ALFA**: `prototype/memory/memory_manager.py` & `prototype/cognition/reasoner.py`
- **Estimated Implementation Effort**: Medium (2-3 days)
- **Dependencies**: Native ALFA types
- **Risks**: Infinite loop if rewrite fails; enforce max retries = 2.
- **Final Decision**: REWRITE

#### 79. `rag_tutorials/contextualai_rag_agent`
- **Folder Name**: `rag_tutorials/contextualai_rag_agent`
- **Purpose**: Contextual API retrieval agent integration.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: Third-party API
- **Risks**: Commercial API dependence.
- **Final Decision**: IGNORE

#### 80. `rag_tutorials/corrective_rag`
- **Folder Name**: `rag_tutorials/corrective_rag`
- **Purpose**: Corrective RAG (CRAG) implementation that falls back to web search if vector retrieval confidence is below threshold.
- **Production Readiness (1-10)**: 9/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: CRAG threshold decision matrix (Correct -> Synthesize, Ambiguous -> Web Search + Vector, Incorrect -> Web Search Only).
- **Where it belongs inside ALFA**: `prototype/decision/decision_engine.py` & `prototype/memory/memory_manager.py`
- **Estimated Implementation Effort**: Medium (2 days)
- **Dependencies**: Web search tool
- **Risks**: External web search API availability.
- **Final Decision**: REWRITE

#### 81. `rag_tutorials/deepseek_local_rag_agent`
- **Folder Name**: `rag_tutorials/deepseek_local_rag_agent`
- **Purpose**: Local RAG execution using DeepSeek models via Ollama.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Local model prompt formatting for DeepSeek R1 `<think>` reasoning tags and local context chunk injection.
- **Where it belongs inside ALFA**: `prototype/modelhub/providers/ollama.py`
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: Ollama local instance
- **Risks**: Hardware requirements for local model execution.
- **Final Decision**: REWRITE

#### 82. `rag_tutorials/gemini_agentic_rag`
- **Folder Name**: `rag_tutorials/gemini_agentic_rag`
- **Purpose**: Gemini API document search and retrieval tutorial.
- **Production Readiness (1-10)**: 5/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: Duplicate of Gemini API handling.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Redundant with provider code.
- **Final Decision**: IGNORE

#### 83. `rag_tutorials/hybrid_search_rag`
- **Folder Name**: `rag_tutorials/hybrid_search_rag`
- **Purpose**: Combines keyword search (BM25) with vector similarity search (cosine distance).
- **Production Readiness (1-10)**: 9/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Reciprocal Rank Fusion (RRF) rank merger algorithm and BM25 + Vector score weighting formula.
- **Where it belongs inside ALFA**: `prototype/memory/persistent_memory.py`
- **Estimated Implementation Effort**: Medium (3 days)
- **Dependencies**: SQLite FTS5 extension (native)
- **Risks**: SQLite FTS index synchronization overhead.
- **Final Decision**: REWRITE

#### 84. `rag_tutorials/knowledge_graph_rag_citations`
- **Folder Name**: `rag_tutorials/knowledge_graph_rag_citations`
- **Purpose**: Graph-based RAG using Neo4j for citation traversal.
- **Production Readiness (1-10)**: 6/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: Entity-relation tuple extraction prompt.
- **Where it belongs inside ALFA**: `prototype/cognition/perception.py`
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: Neo4j (rejected dependency for ALFA core)
- **Risks**: Heavy graph database server requirement.
- **Final Decision**: IGNORE

#### 85. `rag_tutorials/llama3.1_local_rag`
- **Folder Name**: `rag_tutorials/llama3.1_local_rag`
- **Purpose**: Llama 3.1 local RAG setup via Ollama.
- **Production Readiness (1-10)**: 5/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None (already supported by OllamaProvider).
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Redundant setup tutorial.
- **Final Decision**: IGNORE

#### 86. `rag_tutorials/local_hybrid_search_rag`
- **Folder Name**: `rag_tutorials/local_hybrid_search_rag`
- **Purpose**: Fully offline hybrid search RAG pipeline.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused**: Offline document indexing flow, SQLite FTS5 table schema, and local fallback search execution.
- **Where it belongs inside ALFA**: `prototype/memory/persistent_memory.py`
- **Estimated Implementation Effort**: Medium (2 days)
- **Dependencies**: SQLite (builtin)
- **Risks**: None. Fits ALFA local-first architecture.
- **Final Decision**: REWRITE

#### 87. `rag_tutorials/local_rag_agent`
- **Folder Name**: `rag_tutorials/local_rag_agent`
- **Purpose**: Basic local RAG script using LangChain + ChromaDB.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: ChromaDB
- **Risks**: Unnecessary external vector database dependency.
- **Final Decision**: IGNORE

#### 88. `rag_tutorials/multimodal_agentic_rag`
- **Folder Name**: `rag_tutorials/multimodal_agentic_rag`
- **Purpose**: RAG processing both image clips and text documents.
- **Production Readiness (1-10)**: 7/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Multimodal prompt structure combining base64 image data and context text.
- **Where it belongs inside ALFA**: `prototype/modelhub/base.py` (`GenerateRequest.images`)
- **Estimated Implementation Effort**: Low (1-2 days)
- **Dependencies**: Native ALFA ModelHub
- **Risks**: Image encoding size in requests.
- **Final Decision**: REWRITE

#### 89. `rag_tutorials/qwen_local_rag`
- **Folder Name**: `rag_tutorials/qwen_local_rag`
- **Purpose**: Qwen model local RAG tutorial script.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Redundant tutorial.
- **Final Decision**: IGNORE

#### 90. `rag_tutorials/rag-as-a-service`
- **Folder Name**: `rag_tutorials/rag-as-a-service`
- **Purpose**: REST API endpoint wrappers for RAG document ingestion and querying.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Document upload, ingestion progress tracking, and query response REST endpoint structures.
- **Where it belongs inside ALFA**: `prototype/server.py`
- **Estimated Implementation Effort**: Low (1-2 days)
- **Dependencies**: FastAPI
- **Risks**: Large document payload uploads.
- **Final Decision**: REWRITE

#### 91. `rag_tutorials/rag_agent_cohere`
- **Folder Name**: `rag_tutorials/rag_agent_cohere`
- **Purpose**: RAG implementation using Cohere Command R+ reranking API.
- **Production Readiness (1-10)**: 7/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Document reranking interface abstraction (`Reranker`) and top-k relevance re-ordering logic.
- **Where it belongs inside ALFA**: `prototype/memory/memory_manager.py`
- **Estimated Implementation Effort**: Low (1-2 days)
- **Dependencies**: `httpx`
- **Risks**: API key requirement if Cohere is used.
- **Final Decision**: REWRITE

#### 92. `rag_tutorials/rag_chain`
- **Folder Name**: `rag_tutorials/rag_chain`
- **Purpose**: Minimal LCEL RAG chain tutorial script.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: LangChain
- **Risks**: Framework locked tutorial.
- **Final Decision**: IGNORE

#### 93. `rag_tutorials/rag_database_routing`
- **Folder Name**: `rag_tutorials/rag_database_routing`
- **Purpose**: Routes incoming user query to SQL database vs Vector store vs Web search based on intent.
- **Production Readiness (1-10)**: 9/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Intent-based data source router algorithm and routing decision prompts.
- **Where it belongs inside ALFA**: `prototype/decision/decision_engine.py` & `prototype/cognition/perception.py`
- **Estimated Implementation Effort**: Medium (2 days)
- **Dependencies**: Native ALFA modules
- **Risks**: Incorrect intent classification causing wrong source selection.
- **Final Decision**: REWRITE

#### 94. `rag_tutorials/rag_failure_diagnostics_clinic`
- **Folder Name**: `rag_tutorials/rag_failure_diagnostics_clinic`
- **Purpose**: Diagnostic tool that analyzes common RAG failure modes (retrieval failure, hallucination, context overflow, bad ranking).
- **Production Readiness (1-10)**: 9/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: RAG failure taxonomy, diagnostic check algorithms, and automated repair recommendations.
- **Where it belongs inside ALFA**: `prototype/reflection/reflection_engine.py` & `prototype/diagnostics/diagnostics.py`
- **Estimated Implementation Effort**: Medium (2-3 days)
- **Dependencies**: Native Diagnostics
- **Risks**: Latency on diagnostic checks during live requests.
- **Final Decision**: REWRITE

#### 95. `rag_tutorials/vision_rag`
- **Folder Name**: `rag_tutorials/vision_rag`
- **Purpose**: Optical Character Recognition (OCR) and PDF page image RAG.
- **Production Readiness (1-10)**: 6/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: PDF image rendering strategy and image text extraction workflow.
- **Where it belongs inside ALFA**: `prototype/tools/builtin/`
- **Estimated Implementation Effort**: Medium (3 days)
- **Dependencies**: `pypdf`, `pillow`
- **Risks**: Processing speed for multi-page PDFs.
- **Final Decision**: REWRITE

---

### Category K: Starter AI Agents

#### 96. `starter_ai_agents/ai_blog_to_podcast_agent`
- **Folder Name**: `starter_ai_agents/ai_blog_to_podcast_agent`
- **Purpose**: Converts markdown articles into two-speaker dialog scripts.
- **Production Readiness (1-10)**: 6/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Two-speaker conversation generation prompt template and turn formatting rules.
- **Where it belongs inside ALFA**: `prototype/agent/agent_planner.py`
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: None
- **Risks**: None.
- **Final Decision**: REWRITE

#### 97. `starter_ai_agents/ai_breakup_recovery_agent`
- **Folder Name**: `starter_ai_agents/ai_breakup_recovery_agent`
- **Purpose**: Conversational therapeutic prompt demo.
- **Production Readiness (1-10)**: 1/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Toy consumer app.
- **Final Decision**: IGNORE

#### 98. `starter_ai_agents/ai_data_analysis_agent`
- **Folder Name**: `starter_ai_agents/ai_data_analysis_agent`
- **Purpose**: Automated Python code execution for CSV analysis and pandas summary statistics.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Pandas code generation prompt, execution output capture sandbox pattern, and chart plot generation code.
- **Where it belongs inside ALFA**: `prototype/tools/builtin/calculator.py` & `prototype/worker/`
- **Estimated Implementation Effort**: Medium (3 days)
- **Dependencies**: `pandas`
- **Risks**: Unsafe code execution if sandbox is unconstrained.
- **Final Decision**: REWRITE

#### 99. `starter_ai_agents/ai_data_visualisation_agent`
- **Folder Name**: `starter_ai_agents/ai_data_visualisation_agent`
- **Purpose**: Generates Matplotlib / Plotly charts from dataset queries.
- **Production Readiness (1-10)**: 7/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Plotly JSON specification generator prompt and chart render pipeline.
- **Where it belongs inside ALFA**: PySide6 UI (`DashboardWorkspace`)
- **Estimated Implementation Effort**: Medium (2 days)
- **Dependencies**: `plotly` / PySide6 WebEngine or static rendering
- **Risks**: Display dependency on Desktop UI.
- **Final Decision**: REWRITE

#### 100. `starter_ai_agents/ai_life_insurance_advisor_agent`
- **Folder Name**: `starter_ai_agents/ai_life_insurance_advisor_agent`
- **Purpose**: Insurance recommendation questionnaire bot.
- **Production Readiness (1-10)**: 2/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Niche sales demo.
- **Final Decision**: IGNORE

#### 101. `starter_ai_agents/ai_medical_imaging_agent`
- **Folder Name**: `starter_ai_agents/ai_medical_imaging_agent`
- **Purpose**: X-ray image description using vision LLMs.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: Vision API
- **Risks**: High liability medical domain.
- **Final Decision**: IGNORE

#### 102. `starter_ai_agents/ai_meme_generator_agent_browseruse`
- **Folder Name**: `starter_ai_agents/ai_meme_generator_agent_browseruse`
- **Purpose**: Automated browser control using `browser-use` library for meme creation.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: `browser-use`
- **Risks**: Experimental browser automation framework.
- **Final Decision**: IGNORE

#### 103. `starter_ai_agents/ai_music_generator_agent`
- **Folder Name**: `starter_ai_agents/ai_music_generator_agent`
- **Purpose**: Music prompt generator for Suno / Udio APIs.
- **Production Readiness (1-10)**: 2/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Irrelevant domain.
- **Final Decision**: IGNORE

#### 104. `starter_ai_agents/ai_reasoning_agent`
- **Folder Name**: `starter_ai_agents/ai_reasoning_agent`
- **Purpose**: Step-by-step reasoning decomposition for logic puzzles.
- **Production Readiness (1-10)**: 7/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Step-by-step verification prompt template and premise check logic.
- **Where it belongs inside ALFA**: `prototype/cognition/reasoner.py`
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: None
- **Risks**: None.
- **Final Decision**: REWRITE

#### 105. `starter_ai_agents/ai_startup_trend_analysis_agent`
- **Folder Name**: `starter_ai_agents/ai_startup_trend_analysis_agent`
- **Purpose**: Scrapes product launch directories for trend summaries.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Duplicate web scraper.
- **Final Decision**: IGNORE

#### 106. `starter_ai_agents/ai_travel_agent`
- **Folder Name**: `starter_ai_agents/ai_travel_agent`
- **Purpose**: Travel itinerary generator demo.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: None
- **Risks**: Niche consumer app.
- **Final Decision**: IGNORE

#### 107. `starter_ai_agents/mixture_of_agents`
- **Folder Name**: `starter_ai_agents/mixture_of_agents`
- **Purpose**: Mixture-of-Agents (MoA) architecture where multiple LLMs generate responses in layer 1, and a synthesizer model aggregates them in layer 2.
- **Production Readiness (1-10)**: 9/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: MoA layered execution pipeline, response ranking matrix, and multi-model synthesis prompt.
- **Where it belongs inside ALFA**: `prototype/modelhub/router.py` & `prototype/agent/multi_agent.py`
- **Estimated Implementation Effort**: High (3-4 days)
- **Dependencies**: Native ModelHub Router
- **Risks**: Increased token cost and latency from parallel model queries.
- **Final Decision**: REWRITE

#### 108. `starter_ai_agents/multimodal_ai_agent`
- **Folder Name**: `starter_ai_agents/multimodal_ai_agent`
- **Purpose**: Combined vision, audio, and text input handling script.
- **Production Readiness (1-10)**: 7/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: Modality auto-detection logic and payload packaging schema for multimodal requests.
- **Where it belongs inside ALFA**: `prototype/cognition/perception.py` & `prototype/modelhub/base.py`
- **Estimated Implementation Effort**: Low (1-2 days)
- **Dependencies**: Native ALFA types
- **Risks**: None.
- **Final Decision**: REWRITE

#### 109. `starter_ai_agents/openai_research_agent`
- **Folder Name**: `starter_ai_agents/openai_research_agent`
- **Purpose**: Uses OpenAI Web Search tool for research reports.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: OpenAI API
- **Risks**: Proprietary API lock-in.
- **Final Decision**: IGNORE

#### 110. `starter_ai_agents/web_scraping_ai_agent`
- **Folder Name**: `starter_ai_agents/web_scraping_ai_agent`
- **Purpose**: HTML page parser and clean text markdown extractor.
- **Production Readiness (1-10)**: 8/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: HTML boilerplate stripping algorithm (script/style tag removal, main content container extraction) and markdown formatter.
- **Where it belongs inside ALFA**: `prototype/tools/builtin/web_search.py`
- **Estimated Implementation Effort**: Low (1 day)
- **Dependencies**: `beautifulsoup4`
- **Risks**: Non-standard web page structures.
- **Final Decision**: REWRITE

#### 111. `starter_ai_agents/xai_finance_agent`
- **Folder Name**: `starter_ai_agents/xai_finance_agent`
- **Purpose**: xAI Grok API integration for financial lookup.
- **Production Readiness (1-10)**: 4/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: xAI API
- **Risks**: Redundant provider script.
- **Final Decision**: IGNORE

---

### Category L: Voice AI Agents

#### 112. `voice_ai_agents/ai_audio_tour_agent`
- **Folder Name**: `voice_ai_agents/ai_audio_tour_agent`
- **Purpose**: Text-to-speech location tour guide script.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: ElevenLabs API
- **Risks**: Niche audio tour app.
- **Final Decision**: IGNORE

#### 113. `voice_ai_agents/customer_support_voice_agent`
- **Folder Name**: `voice_ai_agents/customer_support_voice_agent`
- **Purpose**: Live voice WebSocket support bot using WebRTC.
- **Production Readiness (1-10)**: 6/10
- **Can ALFA use it?**: Yes (conceptually)
- **What exactly should be reused?**: WebSocket audio stream frame chunking strategy and voice activity detection (VAD) state machine logic.
- **Where it belongs inside ALFA**: `prototype/server.py` & Android Flutter client (`services/`)
- **Estimated Implementation Effort**: High (4-5 days)
- **Dependencies**: WebSockets / VAD
- **Risks**: High network throughput for real-time audio.
- **Final Decision**: REWRITE

#### 114. `voice_ai_agents/insurance_claim_live_agent_team`
- **Folder Name**: `voice_ai_agents/insurance_claim_live_agent_team`
- **Purpose**: Multi-agent live phone call handling demo.
- **Production Readiness (1-10)**: 3/10
- **Can ALFA use it?**: No
- **What exactly should be reused?**: None.
- **Where it belongs inside ALFA**: N/A
- **Estimated Implementation Effort**: N/A
- **Dependencies**: Twilio / LiveKit
- **Risks**: Commercial telephony dependencies.
- **Final Decision**: IGNORE

#### 115. `voice_ai_agents/voice_rag_openaisdk`
- **Folder Name**: `voice_ai_agents/voice_rag_openaisdk`
- **Purpose**: Voice input -> Whisper STT -> RAG -> TTS output chain.
- **Production Readiness (1-10)**: 7/10
- **Can ALFA use it?**: Yes
- **What exactly should be reused?**: STT -> Cognition Pipeline -> TTS response orchestration sequence.
- **Where it belongs inside ALFA**: `prototype/cognition/cognition_runtime.py`
- **Estimated Implementation Effort**: Medium (2 days)
- **Dependencies**: Native ALFA Cognition
- **Risks**: Audio device OS permission checks.
- **Final Decision**: REWRITE

---

## 3. Integration Priority Matrix

The table below synthesizes all analyzed components, categorizing them strictly into **Priority 1 (Must Integrate)**, **Priority 2 (Useful Later)**, and **Priority 3 (Ignore)**.

| Priority | Folder Name | Component / Architectural Concept to Native Rewrite | Target Module inside ALFA | Implementation Effort | Final Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Priority 1** | `agent_skills/advisor-orchestrator-worker` | Three-Tier Architecture Responsibility Contract & Inter-tier Events | `prototype/executive/` & `prototype/cognition/` | Medium (3 days) | **REWRITE** |
| **Priority 1** | `rag_tutorials/hybrid_search_rag` | Reciprocal Rank Fusion (RRF) & SQLite FTS5 Hybrid Search | `prototype/memory/persistent_memory.py` | Medium (3 days) | **REWRITE** |
| **Priority 1** | `rag_tutorials/autonomous_rag` | Self-Correction Retrieval Loop & Query Rewrite Validator | `prototype/memory/memory_manager.py` | Medium (3 days) | **REWRITE** |
| **Priority 1** | `advanced_ai_agents/single_agent_apps/ai_agent_governance` | Policy Enforcement Rule Engine & Action Governance | `prototype/decision/decision_engine.py` | Medium (3 days) | **REWRITE** |
| **Priority 1** | `mcp_ai_agents/multi_mcp_agent_router` | Capability-Based Tool Router & Health Check Fallbacks | `prototype/cognition/reasoner.py` | Medium (2 days) | **REWRITE** |
| **Priority 1** | `starter_ai_agents/mixture_of_agents` | Layered Model Aggregation & Multi-LLM Synthesis | `prototype/modelhub/router.py` | High (4 days) | **REWRITE** |
| **Priority 1** | `agent_skills/self-improving-agent-skills` | Self-Improving Skill Synthesis & Markdown Persistence | `prototype/learning/learning_engine.py` | Medium (3 days) | **REWRITE** |
| **Priority 1** | `advanced_ai_agents/multi_agent_apps/multi_agent_trust_layer` | Pre-Execution Security & Output Validation Layer | `prototype/reflection/reflection_engine.py` | Medium (2 days) | **REWRITE** |
| **Priority 1** | `advanced_llm_apps/llm_optimization_tools` | Token Budget Management & Prompt Compression | `prototype/context/context_manager.py` | Medium (2 days) | **REWRITE** |
| **Priority 1** | `mcp_ai_agents/browser_mcp_agent` | Headless Browser Automation Tool Actions | `prototype/tools/builtin/browser_tool.py` | Medium (3 days) | **REWRITE** |
| **Priority 2** | `advanced_ai_agents/multi_agent_apps/ai_domain_deep_research_agent` | Recursive Research Web Search & Synthesis Heuristics | `prototype/agent/strategies/deep_research.py` | Medium (3 days) | **REWRITE** |
| **Priority 2** | `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent` | Performance Metric Reflection Loop | `prototype/reflection/reflection_engine.py` | Medium (3 days) | **REWRITE** |
| **Priority 2** | `advanced_ai_agents/multi_agent_apps/ai_negotiation_battle_simulator` | Multi-Agent Debate & Consensus Convergence Protocol | `prototype/agent/multi_agent.py` | Low (2 days) | **REWRITE** |
| **Priority 2** | `advanced_ai_agents/single_agent_apps/windows_use_autonomous_agent` | Windows OS Desktop Automation Tool Actions | `prototype/tools/builtin/os_automation.py` | High (5 days) | **REWRITE** |
| **Priority 2** | `advanced_llm_apps/gpt_oss_critique_improvement_loop` | Multi-Pass Model Critique Checklist | `prototype/reflection/reflector.py` | Medium (2 days) | **REWRITE** |
| **Priority 2** | `agent_skills/evals` | Automated Benchmark & Accuracy Evaluation Harness | `tests/test_evals.py` | Medium (2 days) | **REWRITE** |
| **Priority 2** | `agent_skills/commit-archaeologist` | Git Repository Analysis & Diff Mining Tool | `prototype/plugins/builtin/git_analyzer.py` | Low (2 days) | **REWRITE** |
| **Priority 2** | `agent_skills/thinking-out-loud` | Intermediate Reasoning Stream Events to UI | `prototype/cognition/reasoner.py` | Low (1 day) | **REWRITE** |
| **Priority 2** | `always_on_agents/always_on_hn_briefing_agent` | Cron Task Background Execution Pattern | `prototype/worker/worker_manager.py` | Low (1 day) | **REWRITE** |
| **Priority 2** | `always_on_agents/release_radar_agent` | GitHub Release Monitor Worker | `prototype/worker/base_worker.py` | Low (1-2 days) | **REWRITE** |
| **Priority 2** | `generative_ui_agents/ai-dashboard-canvas-agent` | JSON Schema to PySide6/Flutter Widget Renderer | PySide6 Desktop / Flutter UI | Medium (3 days) | **REWRITE** |
| **Priority 2** | `generative_ui_agents/ai-mcp-app-builder` | Tool Input Schema to Form Render Mapper | `prototype/tools/tool_manager.py` | Medium (3 days) | **REWRITE** |
| **Priority 2** | `mcp_ai_agents/github_mcp_agent` | Native GitHub API Integration Tool | `prototype/tools/builtin/github_tool.py` | Low (2 days) | **REWRITE** |
| **Priority 2** | `mcp_ai_agents/multi_mcp_agent` | JSON-RPC 2.0 Client Connector for External MCP Servers | `prototype/tools/tool_manager.py` | High (4 days) | **REWRITE** |
| **Priority 2** | `rag_tutorials/corrective_rag` | CRAG Decision Matrix (Vector vs Web Search Fallback) | `prototype/decision/decision_engine.py` | Medium (2 days) | **REWRITE** |
| **Priority 2** | `rag_tutorials/rag_database_routing` | Intent-Based Query Data Source Router | `prototype/decision/decision_engine.py` | Medium (2 days) | **REWRITE** |
| **Priority 2** | `rag_tutorials/rag_failure_diagnostics_clinic` | RAG Failure Mode Diagnostics Check | `prototype/diagnostics/diagnostics.py` | Medium (2 days) | **REWRITE** |
| **Priority 2** | `starter_ai_agents/ai_data_analysis_agent` | Pandas Analysis & Code Execution Tool | `prototype/tools/builtin/calculator.py` | Medium (3 days) | **REWRITE** |
| **Priority 2** | `starter_ai_agents/web_scraping_ai_agent` | HTML Content Extraction & Cleaning Utility | `prototype/tools/builtin/web_search.py` | Low (1 day) | **REWRITE** |
| **Priority 2** | `voice_ai_agents/voice_rag_openaisdk` | Speech-to-Text -> Cognition Pipeline -> TTS Orchestrator | `prototype/cognition/cognition_runtime.py` | Medium (2 days) | **REWRITE** |
| **Priority 3** | *All remaining 85 projects listed in Section 2* | Framework-locked demos, Streamlit wrappers, single-script tutorials, and niche consumer apps | N/A | N/A | **IGNORE** |

---

## 4. Concluding Execution Directives

1. **Zero External Code Import**: No source files from `external/awesome-llm-apps-main` shall be copied or linked into `prototype/`.
2. **Subsystem Scoping**: Re-implemented concepts must strictly land within their assigned target modules in `prototype/` (e.g. `memory/`, `decision/`, `executive/`, `cognition/`, `modelhub/`).
3. **Architecture Preservation**: Core runtime architecture, `AlfaRuntime` composition root, event bus interfaces, and database schemas remain frozen and intact.

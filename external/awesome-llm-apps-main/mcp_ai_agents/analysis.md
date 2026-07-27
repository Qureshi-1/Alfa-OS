# MCP AI Agents - Deep Architectural Reverse-Engineering Audit

## Project 1: ai_travel_planner_mcp_agent_team

### Files:
- app.py
- README.md
- requirements.txt

### app.py Analysis

#### Imports:
- `re` - Regular expressions for parsing itinerary text
- `asyncio` - Async event loop for MCP connections
- `textwrap.dedent` - Clean multiline strings
- `agno.agent.Agent` - Agent framework for LLM orchestration
- `agno.run.agent.RunOutput` - Agent output handling
- `agno.tools.mcp.MultiMCPTools` - Multiple MCP server connections
- `agno.tools.googlesearch.GoogleSearchTools` - Google search integration
- `agno.models.openai.OpenAIChat` - OpenAI model wrapper
- `icalendar.Calendar, Event` - ICS calendar file generation
- `datetime, timedelta` - Date/time handling
- `streamlit` - Web UI framework
- `os` - Environment variable access

#### Functions:

1. `generate_ics_content(plan_text: str, start_date: datetime = None) -> bytes`
   - Parses travel itinerary text using regex pattern `Day (\d+)[:\s]+(.*?)(?=Day \d+|$)`
   - Creates Calendar object with prodid `-//AI Travel Planner//github.com//`
   - Generates all-day events for each day or single event if no day pattern found
   - Returns ICS bytes for download

2. `async run_mcp_travel_planner(destination, num_days, preferences, budget, openai_key, google_maps_key)`
   - Sets `GOOGLE_MAPS_API_KEY` env var
   - Initializes MultiMCPTools with two MCP servers:
     - `npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt`
     - `npx @gongrzhe/server-travelplanner-mcp`
   - Environment variables passed: `GOOGLE_MAPS_API_KEY`
   - Timeout: 60 seconds
   - Creates Agent with:
     - Model: `gpt-4o` via OpenAIChat
     - Tools: `mcp_tools` + `GoogleSearchTools()`
     - System prompt: Detailed travel consultant instructions
     - 13 specific instructions for itinerary generation
   - Calls `travel_planner.arun(prompt)` with formatted prompt
   - Closes MCP tools in finally block

3. `run_travel_planner(...)` - Sync wrapper using `asyncio.run()`

#### Streamlit UI:
- Session state: `itinerary` for storing generated content
- Sidebar: OpenAI API key, Google Maps API key inputs
- Main UI: Destination, number of days, budget, start date, preferences
- Quick preference multiselect: 12 predefined options
- Generate button triggers `run_travel_planner()`
- Download button for ICS calendar file

#### MCP Implementation Details:
- **MCP Servers Connected**:
  - `@openbnb/mcp-server-airbnb` - Airbnb listings
  - `@gongrzhe/server-travelplanner-mcp` - Travel planning
- **Transport**: stdio via npx commands
- **Connection Management**: `await mcp_tools.connect()` / `await mcp_tools.close()`
- **Session Management**: Single session per generation request
- **Tool Calling**: Agent framework handles tool dispatch via `MultiMCPTools`
- **Resources**: Not explicitly exposed; tools only
- **Prompts**: System prompt embedded in Agent constructor

#### Error Handling:
- Try/finally for MCP cleanup
- Streamlit error display with `st.error()`
- Fallback message if MCP connection fails

#### Configuration Management:
- API keys via Streamlit sidebar inputs
- Google Maps key passed as environment variable
- OpenAI key passed directly to OpenAIChat

#### Memory Patterns:
- Streamlit session state for itinerary persistence
- No database or vector store

#### Planning Patterns:
- Single-step: Generate complete itinerary in one response
- No multi-step orchestration

#### Agent Orchestration:
- Single agent with multiple tools
- No agent-to-agent communication

### requirements.txt:
```
streamlit
agno>=2.2.10
openai
icalendar
google-search-results
```

### README.md Summary:
- Streamlit-based travel planner using MCP
- Airbnb MCP for real accommodation data
- Google Maps MCP for distance calculations
- Google Search for current information
- Calendar export functionality

---

## Project 2: browser_mcp_agent

### Files:
- main.py
- mcp_agent.config.yaml
- mcp_agent.secrets.yaml.example
- README.md
- requirements.txt

### main.py Analysis

#### Imports:
- `asyncio` - Event loop management
- `os` - Environment/file checks
- `streamlit` - UI framework
- `textwrap.dedent` - String formatting
- `mcp_agent.app.MCPApp` - MCP application framework
- `mcp_agent.agents.agent.Agent` - Agent definition
- `mcp_agent.workflows.llm.augmented_llm_openai.OpenAIAugmentedLLM` - OpenAI LLM integration
- `mcp_agent.workflows.llm.augmented_llm.RequestParams` - Request configuration

#### Session State:
- `initialized` - Boolean flag for one-time setup
- `mcp_app` - MCPApp instance
- `mcp_context` - Async context manager
- `mcp_agent_app` - MCP agent application
- `browser_agent` - Agent instance
- `llm` - LLM instance
- `loop` - Asyncio event loop
- `is_processing` - Processing flag
- `last_result` - Result storage

#### Functions:

1. `async setup_agent()`
   - Creates MCPApp with name `streamlit_mcp_agent`
   - Enters context manager via `__aenter__`
   - Creates Agent:
     - Name: `browser`
     - Instruction: Web browsing assistant with Playwright
     - Server names: `["playwright"]`
   - Initializes agent and attaches `OpenAIAugmentedLLM`
   - Lists available tools

2. `async run_mcp_agent(message)`
   - Checks for OpenAI API key (env or secrets file)
   - Calls `setup_agent()` if not initialized
   - Generates response via `llm.generate_str()`
   - RequestParams: `use_history=True, maxTokens=10000`

3. `start_run()` - Sets processing flag

#### Streamlit UI:
- Text area for browsing commands
- Run Command button with processing state
- Spinner during processing
- Response display in markdown

#### MCP Implementation Details:
- **MCP Server**: Playwright
  - Command: `npx`
  - Args: `["@playwright/mcp@latest"]`
- **Transport**: stdio via npx
- **Connection Management**: Context manager pattern with `__aenter__`/`__aexit__`
- **Session Management**: Persistent across Streamlit reruns via session state
- **Tool Calling**: Via augmented LLM with tool definitions from MCP server
- **Resources**: Playwright browser automation tools
- **Prompts**: System instruction for web browsing capabilities

#### Error Handling:
- Try/except in setup and run functions
- Fallback error messages

#### Configuration Management:
- `mcp_agent.config.yaml` for server and model config
- `mcp_agent.secrets.yaml` for API keys (gitignored)
- Environment variable fallback for OpenAI key

#### Memory Patterns:
- Streamlit session state for agent persistence
- `use_history=True` for conversation context

#### Planning Patterns:
- Single agent with Playwright tools
- No multi-step planning

#### Agent Orchestration:
- Single browser agent
- No agent routing

### mcp_agent.config.yaml:
```yaml
execution_engine: asyncio
logger:
  transports: [console, file]
  level: debug
mcp:
  servers:
    playwright:
      command: "npx"
      args: ["@playwright/mcp@latest"]
openai:
  default_model: "gpt-4o-mini"
```

### mcp_agent.secrets.yaml.example:
```yaml
openai:
  api_key: YOUR_OPENAI_API_KEY
```

### requirements.txt:
```
streamlit>=1.28.0
mcp-agent>=0.0.14
openai>=1.0.0
```

### README.md Summary:
- Streamlit app for web browsing via MCP
- Playwright integration for browser automation
- Natural language commands for navigation
- Supports OpenAI and local Ollama models

---

## Project 3: github_mcp_agent

### Files:
- github_agent.py
- README.md
- requirements.txt

### github_agent.py Analysis

#### Imports:
- `asyncio` - Async operations
- `os` - Environment variables
- `streamlit` - UI framework
- `textwrap.dedent` - String formatting
- `agno.agent.Agent` - Agent framework
- `agno.run.agent.RunOutput` - Agent output
- `agno.tools.mcp.MCPTools` - Single MCP server tools
- `mcp.StdioServerParameters` - MCP server configuration

#### Functions:

1. `async run_github_agent(message)`
   - Validates GITHUB_TOKEN and OPENAI_API_KEY
   - Creates StdioServerParameters:
     - Command: `docker`
     - Args: `["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "-e", "GITHUB_TOOLSETS", "ghcr.io/github/github-mcp-server"]`
     - Environment: `GITHUB_PERSONAL_ACCESS_TOKEN`, `GITHUB_TOOLSETS=repos,issues,pull_requests`
   - Uses `async with MCPTools(server_params)` context manager
   - Creates Agent with MCP tools
   - Agent instructions: GitHub assistant with markdown formatting
   - Calls `agent.arun(message)` with 120s timeout
   - Returns response content

#### Streamlit UI:
- Sidebar: OpenAI API key, GitHub token inputs
- Main: Repository input, query type dropdown, query text area
- Query types: Issues, Pull Requests, Repository Activity, Custom
- Run Query button with spinner

#### MCP Implementation Details:
- **MCP Server**: GitHub MCP Server (official)
  - Package: `ghcr.io/github/github-mcp-server` (Docker)
  - Toolsets: repos, issues, pull_requests
- **Transport**: stdio via Docker container
- **Connection Management**: `async with MCPTools(server_params)` context manager
- **Session Management**: Single session per query
- **Tool Calling**: Agent framework dispatches to MCP tools
- **Resources**: GitHub API tools (repos, issues, PRs)
- **Prompts**: System prompt for GitHub assistant

#### Error Handling:
- Timeout handling (120 seconds)
- Exception catch-all with error messages
- Input validation for API keys

#### Configuration Management:
- Environment variables for tokens
- Streamlit sidebar for key input
- Docker-based MCP server

#### Memory Patterns:
- No persistent memory
- Single query-response pattern

#### Planning Patterns:
- Single agent execution
- No multi-step planning

#### Agent Orchestration:
- Single GitHub agent
- No routing

### requirements.txt:
```
streamlit>=1.28.0
agno>=2.2.10
mcp>=0.1.0
openai>=1.0.0
```

### README.md Summary:
- Streamlit app for GitHub exploration via MCP
- Uses official GitHub MCP server via Docker
- Natural language queries for issues, PRs, repo activity
- Requires Docker, OpenAI key, GitHub token

---

## Project 4: multi_mcp_agent_router

### Files:
- agent_forge.py
- README.md
- requirements.txt

### agent_forge.py Analysis

#### Imports:
- `asyncio` - Async operations
- `json` - JSON handling
- `os` - Environment variables
- `contextlib.AsyncExitStack` - Async context management
- `dataclasses.dataclass, field` - Data structures
- `streamlit` - UI framework
- `anthropic.Anthropic` - Anthropic API client
- `mcp.ClientSession, StdioServerParameters` - MCP client
- `mcp.client.stdio.stdio_client` - Stdio transport

#### Dataclass:

1. `Agent` - Specialized agent definition
   - Fields: `name`, `description`, `system_prompt`, `icon`, `mcp_servers`
   - `mcp_servers`: List of dicts with `name`, `command`, `args`, optional `env`

#### Agent Definitions (AGENTS dict):

1. **code_reviewer**:
   - MCP Servers: `@modelcontextprotocol/server-github`, `@modelcontextprotocol/server-filesystem`
   - Focus: Code review, bugs, anti-patterns

2. **security_auditor**:
   - MCP Servers: `@modelcontextprotocol/server-github`, `@modelcontextprotocol/server-fetch`
   - Focus: OWASP Top 10, injection, XSS, secrets

3. **researcher**:
   - MCP Servers: `@modelcontextprotocol/server-fetch`, `@modelcontextprotocol/server-filesystem`
   - Focus: Web research, synthesis, citations

4. **bim_engineer**:
   - MCP Servers: `@modelcontextprotocol/server-filesystem`
   - Focus: BIM, Revit, construction data

#### Functions:

1. `classify_query(query: str) -> str`
   - Keyword-based routing to agents
   - Security keywords → security_auditor
   - Code keywords → code_reviewer
   - BIM keywords → bim_engineer
   - Default → researcher

2. `mcp_tool_to_anthropic(tool) -> dict`
   - Converts MCP tool definition to Anthropic format
   - Maps: name, description, input_schema

3. `async connect_mcp_servers(agent: Agent) -> tuple[AsyncExitStack, list[dict], dict[str, ClientSession]]`
   - Creates AsyncExitStack
   - For each MCP server config:
     - Creates StdioServerParameters
     - Enters stdio_client context
     - Creates ClientSession
     - Initializes session
     - Lists tools and maps to session
   - Returns stack, tools list, session map

4. `async run_agent_async(client: Anthropic, agent: Agent, query: str, history: list) -> str`
   - If no MCP servers, calls Anthropic directly
   - Otherwise, connects MCP servers
   - Agentic loop:
     - Sends messages to Claude with tools
     - If stop_reason == "tool_use":
       - Extracts tool_use blocks
       - Calls tools via session_map
       - Appends results to messages
       - Continues loop
     - Returns final text response

5. `run_agent(...)` - Sync wrapper with new event loop

6. `main()` - Streamlit app
   - Sidebar: Anthropic API key, agent info
   - Agent selection: Auto-Route or Manual
   - Chat history per agent
   - Chat input with routing

#### MCP Implementation Details:
- **MCP Servers Connected** (per agent):
  - `@modelcontextprotocol/server-github` - GitHub API
  - `@modelcontextprotocol/server-filesystem` - Filesystem access
  - `@modelcontextprotocol/server-fetch` - Web fetching
- **Transport**: stdio via npx commands
- **Connection Management**: AsyncExitStack for lifecycle
- **Session Management**: Per-agent, per-request sessions
- **Tool Calling**: Manual dispatch via session_map
- **Resources**: Filesystem, GitHub, web content
- **Prompts**: System prompts per agent specialization

#### Error Handling:
- Tool call exceptions caught and returned as error results
- Stack cleanup in finally block

#### Configuration Management:
- Anthropic API key via Streamlit sidebar
- MCP server configs in agent definitions

#### Memory Patterns:
- Per-agent conversation history in session state
- No persistent storage

#### Planning Patterns:
- Query classification for routing
- Agentic loop for tool use

#### Agent Orchestration:
- Router pattern with keyword classification
- Manual or automatic agent selection
- Isolated tool access per agent

### requirements.txt:
```
streamlit>=1.28.0
anthropic>=0.40.0
mcp>=0.1.0
pydantic>=2.0.0
```

### README.md Summary:
- Multi-agent system with MCP tool routing
- 4 specialized agents with different MCP servers
- Auto-route or manual selection
- Conversation memory per agent

---

## Project 5: multi_mcp_agent

### Files:
- multi_mcp_agent.py
- README.md
- requirements.txt

### multi_mcp_agent.py Analysis

#### Imports:
- `asyncio` - Async operations
- `os` - Environment variables
- `uuid` - Session/user ID generation
- `textwrap.dedent` - String formatting
- `agno.agent.Agent` - Agent framework
- `agno.models.openai.OpenAIChat` - OpenAI model
- `agno.tools.mcp.MultiMCPTools` - Multiple MCP tools
- `agno.db.sqlite.SqliteDb` - SQLite database
- `dotenv.load_dotenv` - Environment loading

#### Functions:

1. `async main()`
   - Validates environment variables: GITHUB_PERSONAL_ACCESS_TOKEN, OPENAI_API_KEY, PERPLEXITY_API_KEY
   - Generates unique user_id and session_id
   - Sets up environment for MCP servers
   - MCP servers list:
     - `npx -y @modelcontextprotocol/server-github`
     - `npx -y @chatmcp/server-perplexity-ask`
     - `npx @gongrzhe/server-calendar-autoauth-mcp`
     - `npx @gongrzhe/server-gmail-autoauth-mcp`
   - Creates SQLiteDb for memory
   - Uses `async with MultiMCPTools(mcp_servers, env=env)` context manager
   - Creates Agent with:
     - Model: `gpt-4o`
     - Tools: mcp_tools
     - Database: SQLiteDb
     - Memory: `enable_user_memories=True`
     - History: `add_history_to_context=True, num_history_runs=10`
     - Retries: 3
   - Starts interactive CLI via `agent.acli_app()`

#### MCP Implementation Details:
- **MCP Servers Connected**:
  - `@modelcontextprotocol/server-github` - GitHub API
  - `@chatmcp/server-perplexity-ask` - Perplexity search
  - `@gongrzhe/server-calendar-autoauth-mcp` - Calendar
  - `@gongrzhe/server-gmail-autoauth-mcp` - Gmail
- **Transport**: stdio via npx commands
- **Connection Management**: `async with MultiMCPTools` context manager
- **Session Management**: Unique user_id/session_id per run
- **Tool Calling**: Agent framework handles tool dispatch
- **Resources**: GitHub, Perplexity, Calendar, Gmail
- **Prompts**: Detailed system prompt with 7 capability sections

#### Error Handling:
- Environment variable validation
- Retry mechanism (3 retries)
- Graceful exit handling

#### Configuration Management:
- `.env` file via python-dotenv
- Environment variables for all API keys

#### Memory Patterns:
- SQLite database for persistent memory
- User memories enabled
- Conversation history (last 10 runs)

#### Planning Patterns:
- Single agent with multiple tools
- Tool chaining capabilities mentioned in instructions

#### Agent Orchestration:
- Single multi-tool agent
- No agent routing

### requirements.txt:
```
agno>=2.2.10
openai
mcp
python-dotenv
sqlalchemy
```

### README.md Summary:
- Multi-MCP assistant with GitHub, Perplexity, Calendar, Gmail
- Interactive CLI with streaming
- Conversation memory and context retention
- Cross-platform workflow automation

---

## Project 6: notion_mcp_agent

### Files:
- notion_mcp_agent.py
- README.md
- requirements.txt

### notion_mcp_agent.py Analysis

#### Imports:
- `asyncio` - Async operations
- `json` - JSON encoding
- `os` - Environment variables
- `sys` - Command-line arguments
- `uuid` - Session/user ID generation
- `textwrap.dedent` - String formatting
- `agno.agent.Agent` - Agent framework
- `agno.models.openai.OpenAIChat` - OpenAI model
- `agno.tools.mcp.MCPTools` - Single MCP tools
- `agno.db.sqlite.SqliteDb` - SQLite database
- `mcp.StdioServerParameters` - MCP server config
- `dotenv.load_dotenv` - Environment loading

#### Functions:

1. `async main()`
   - Loads environment variables
   - Gets NOTION_API_KEY and OPENAI_API_KEY
   - Accepts page_id from command line or user input
   - Generates unique user_id and session_id
   - Creates StdioServerParameters:
     - Command: `npx`
     - Args: `["-y", "@notionhq/notion-mcp-server"]`
     - Environment: `OPENAPI_MCP_HEADERS` with Authorization and Notion-Version
   - Uses `async with MCPTools(server_params)` context manager
   - Creates SQLiteDb for memory
   - Creates Agent with:
     - Model: `gpt-4o`
     - Tools: mcp_tools
     - Database: SQLiteDb
     - Memory: `enable_user_memories=True`
     - History: `add_history_to_context=True, num_history_runs=5`
     - Retries: 3
   - Starts interactive CLI via `agent.acli_app()`

#### MCP Implementation Details:
- **MCP Server**: Notion MCP Server
  - Package: `@notionhq/notion-mcp-server`
  - Authentication: Bearer token in OPENAPI_MCP_HEADERS
  - Notion-Version: 2022-06-28
- **Transport**: stdio via npx
- **Connection Management**: `async with MCPTools` context manager
- **Session Management**: Unique user_id/session_id per run
- **Tool Calling**: Agent framework dispatches to Notion tools
- **Resources**: Notion pages, blocks, comments
- **Prompts**: System prompt with page_id context

#### Error Handling:
- Input validation for page_id
- Retry mechanism (3 retries)
- Graceful exit handling

#### Configuration Management:
- `.env` file via python-dotenv
- Environment variables for API keys
- Command-line argument for page_id

#### Memory Patterns:
- SQLite database for persistent memory
- User memories enabled
- Conversation history (last 5 runs)

#### Planning Patterns:
- Single agent with Notion tools
- No multi-step planning

#### Agent Orchestration:
- Single Notion agent
- No routing

### requirements.txt:
```
agno>=2.2.10
python-dotenv
mcp
openai
sqlalchemy
```

### README.md Summary:
- Terminal-based Notion agent via MCP
- Read, update, search Notion pages
- Session management with memory
- Requires Notion integration token

---

## Cross-Cutting Analysis

### MCP Server Packages Used:
1. `@openbnb/mcp-server-airbnb` - Airbnb listings
2. `@gongrzhe/server-travelplanner-mcp` - Travel planning
3. `@playwright/mcp@latest` - Browser automation
4. `ghcr.io/github/github-mcp-server` - GitHub API (Docker)
5. `@modelcontextprotocol/server-github` - GitHub API (npm)
6. `@modelcontextprotocol/server-filesystem` - Filesystem access
7. `@modelcontextprotocol/server-fetch` - Web fetching
8. `@chatmcp/server-perplexity-ask` - Perplexity search
9. `@gongrzhe/server-calendar-autoauth-mcp` - Calendar
10. `@gongrzhe/server-gmail-autoauth-mcp` - Gmail
11. `@notionhq/notion-mcp-server` - Notion API

### Transport Mechanisms:
- **stdio**: All projects use stdio transport via npx or Docker
- **HTTP/SSE/WebSocket**: None used

### Frameworks Used:
- **Agno**: Projects 1, 3, 5, 6 (agent framework with MCP integration)
- **MCP-Agent**: Project 2 (lastmile-ai framework)
- **Raw MCP SDK**: Project 4 (direct ClientSession usage)

### Memory Patterns:
- **Streamlit session state**: Projects 1, 2, 3, 4
- **SQLite database**: Projects 5, 6
- **No memory**: Project 3 (single query)

### UI Patterns:
- **Streamlit**: All projects except Project 5 (CLI)
- **CLI**: Project 5

### API Key Management:
- **Streamlit sidebar**: Projects 1, 2, 3, 4
- **Environment variables**: Projects 5, 6
- **Secrets files**: Project 2 (mcp_agent.secrets.yaml)

### Error Handling:
- **Try/except with user messages**: All projects
- **Retry mechanisms**: Projects 5, 6 (3 retries)
- **Timeouts**: Project 3 (120s), Project 1 (60s MCP timeout)

### Planning Patterns:
- **Single agent**: Projects 1, 2, 3, 5, 6
- **Multi-agent routing**: Project 4 (keyword classification)
- **Agentic loop**: Project 4 (tool use loop)

### Agent Orchestration:
- **Single agent**: Most projects
- **Router pattern**: Project 4 (4 specialized agents)
- **No inter-agent communication**: All projects
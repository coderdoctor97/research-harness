# Comprehensive Implementation Plan: Local LLM Research Assistant Harness

---

## 1. High-Level System Architecture

### Component Overview

The system consists of six primary components that interact through a central orchestration loop:

1. **Local LLM Core** — The locally running language model (e.g., llama.cpp server, Ollama, vLLM, or any OpenAI-compatible local endpoint) that processes prompts and generates responses, including structured tool-call requests.

2. **Orchestration Loop (Agent Controller)** — The central runtime that mediates between the user, the LLM, and the tools. It parses LLM output for tool invocations, dispatches them, injects results back into the prompt, and decides when to terminate the loop and present a final answer.

3. **Tool Registry** — A dynamic registry of callable tools, each with a declared schema (name, description, parameters, output format). The registry is populated at startup from default tool definitions and user-configured custom endpoints.

4. **Retrieval Layer** — The collection of concrete tool implementations that perform external I/O: web search, URL fetching, content extraction, and summarization. These implementations read connection details from the Configuration Interface.

5. **Memory & Context Manager** — Manages conversation history, retrieved document caches, and context-window budgeting. Responsible for compressing, summarizing, or evicting old context to stay within token limits.

6. **User Configuration Interface** — A config file (YAML/JSON), environment variables, and optionally a lightweight web UI that allows users to register API keys, custom endpoints, headers, and rate limits without writing code.

### System Flowchart

```
┌────────────────────────────────────────────────────────────────────────┐
│                             USER INTERFACE                             │
│                    (CLI / Web Chat / API Endpoint)                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ user query
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATION LOOP                           │
│                                                                        │
│   ┌──────────┐        ┌──────────────┐     ┌────────────────────────┐  │
│   │ Context  │◄──────►│  LLM Core    │────►│  Tool Call Parser      │  │
│ ┌►│ Manager  │        │ (local model)│     │ (extracts tool calls   │  │
│ │ └──────────┘        └──────────────┘     │  from LLM output)      │  │
│ │                                          └─────────┬──────────────┘  │
│ │                                                    │ tool request    │
│ │                       ┌────────────────────────────▼─────┐           │
│ │                       │          TOOL REGISTRY           │           │
│ │                       │  ┌────────────┐ ┌────────────┐   │           │
│ │                       │  │ web_search │ │ fetch_url  │   │           │
│ │                       │  └──────┬─────┘ └──────┬─────┘   │           │
│ │                       └────────┼───────────────┼──────────┘          │
│ │                                │              │                      │
│ │                    ┌───────────▼──────────────▼───────────┐          │
│ │                    │           RETRIEVAL LAYER            │          │
│ │                    │  (HTTP clients, scrapers, parsers)   │          │
│ │                    │   reads config from the User         │          │
│ │                    │   Configuration Interface (below)    │          │
│ │                    └─────────────────┬────────────────────┘          │
│ │                                      │ tool result                   │
│ └──────────────────────────────────────┘                               │
│                                                                        │
│  Final answer (with citations & links) ──► returned to USER            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ loads endpoints, keys, settings
                                    ▼
        ┌───────────────────────────┬────────────────────────────┐
        │              USER CONFIGURATION INTERFACE              │
        │     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │     │ config.yaml  │  │  .env file   │  │   Web UI     │
        │     │ (endpoints,  │  │  (API keys)  │  │  (optional)  │
        │     │  schemas)    │                                   │
        │     └──────────────┘  └──────────────┘  └──────────────┘
        └────────────────────────────────────────────────────────┘
```

### Data Flow Summary

1. User submits a query.
2. Orchestration Loop injects system prompt + conversation history + tool schemas → sends to LLM Core.
3. LLM Core responds with either a final answer or one or more tool-call requests.
4. Tool Call Parser extracts structured tool calls from the LLM output.
5. Tool Registry resolves each tool call to a concrete implementation.
6. Retrieval Layer executes the call using configuration (endpoint URLs, API keys, headers) from the User Configuration Interface.
7. Results are injected back into the context; the loop repeats (up to a configurable max iteration count).
8. When the LLM produces a final answer (no more tool calls), the Orchestration Loop formats it with citations and hyperlinks and returns it to the user.
9. The Memory & Context Manager persists the turn and manages token budgets.

---

## 2. Configuration Schema Design

### Design Principles

- **Separation of secrets from structure**: API keys live in environment variables or an encrypted local vault; the config file references them by variable name.
- **Declarative endpoint definitions**: Each endpoint is described as a template — URL, method, headers, body template with placeholders, and a response-parsing rule.
- **Hot-reloadable**: The harness should watch the config file for changes and reload without restart.

### Example YAML Schema: `config.yaml`

```yaml
# ============================================================
# HARNESS CONFIGURATION
# ============================================================

harness:
  # --- Local LLM Connection ---
  llm:
    provider: "openai_compatible"          # openai_compatible | ollama | custom
    base_url: "http://localhost:8080"       # Local model server URL
    model_name: "mistral-7b-instruct"
    api_key_env: "LOCAL_LLM_API_KEY"       # env var name (can be "none" if no auth)
    max_tokens: 4096
    temperature: 0.3
    context_window: 32768                  # Total token budget for this model
    supports_tool_calling: true            # If true, use native tool-call format
    tool_call_format: "openai"             # openai | anthropic | react | custom_regex

  # --- Orchestration ---
  orchestration:
    max_tool_iterations: 8                 # Max tool-call loops before forcing final answer
    parallel_tool_calls: true              # Allow multiple tools in one iteration
    max_parallel: 3
    tool_call_timeout_seconds: 30
    fallback_to_training_knowledge: true   # If all tools fail, answer from training data
    thinking_budget: 2048                  # Reserved tokens for model's internal reasoning

  # --- Memory ---
  memory:
    conversation_history_max_turns: 50
    context_budget_percentage: 0.75        # % of context_window for history+docs
    summarization_strategy: "rolling"      # rolling | hierarchical | none
    document_cache_dir: "./cache/docs"
    document_cache_ttl_minutes: 60

  # --- Response Formatting ---
  response:
    citation_style: "inline_numbered"      # inline_numbered | footnote | parenthetical
    link_format: "markdown"                # markdown | html | plain
    include_source_list: true              # Append a "Sources" section at the end
    max_sources_per_response: 10

# ============================================================
# ENDPOINT REGISTRY (User-Configurable)
# ============================================================

endpoints:
  # --- Web Search ---
  web_search:
    enabled: true
    provider: "serper"                     # Label for logging/UI
    url: "https://google.serper.dev/search"
    method: "POST"
    headers:
      X-API-KEY: "${SERPER_API_KEY}"       # Resolved from env var
      Content-Type: "application/json"
    body_template: |
      {
        "q": "{{query}}",
        "num": {{num_results|default:5}},
        "gl": "{{country_code|default:us}}"
      }
    response_parsing:
      results_path: "organic"             # JSONPath or dot-notation to results array
      fields:
        title: "title"
        url: "link"
        snippet: "snippet"
        date: "date"
    rate_limit:
      requests_per_minute: 60
      requests_per_day: 2500
    retry:
      max_retries: 3
      backoff_seconds: [1, 3, 10]

  # --- Alternative Search (Brave) ---
  web_search_brave:
    enabled: false
    provider: "brave"
    url: "https://api.search.brave.com/res/v1/web/search"
    method: "GET"
    headers:
      X-Subscription-Token: "${BRAVE_API_KEY}"
      Accept: "application/json"
    query_params_template:
      q: "{{query}}"
      count: "{{num_results|default:5}}"
    response_parsing:
      results_path: "web.results"
      fields:
        title: "title"
        url: "url"
        snippet: "description"
    rate_limit:
      requests_per_minute: 15
      requests_per_day: 2000

  # --- URL Fetching / Scraping ---
  fetch_url:
    enabled: true
    provider: "jina_reader"
    url: "https://r.jina.ai/{{target_url}}"
    method: "GET"
    headers:
      Authorization: "Bearer ${JINA_API_KEY}"
      Accept: "application/json"
      X-Return-Format: "markdown"
    response_parsing:
      content_path: "data.content"
      title_path: "data.title"
      fallback_content_path: "data.text"
    rate_limit:
      requests_per_minute: 20

  # --- Alternative Fetcher (self-hosted) ---
  fetch_url_local:
    enabled: false
    provider: "local_scraper"
    url: "http://localhost:3001/scrape"
    method: "POST"
    headers:
      Content-Type: "application/json"
    body_template: |
      {
        "url": "{{target_url}}",
        "format": "markdown",
        "include_links": true
      }
    response_parsing:
      content_path: "content"
      title_path: "title"
      links_path: "links"

  # --- Academic Search ---
  arxiv_search:
    enabled: true
    provider: "arxiv"
    url: "http://export.arxiv.org/api/query"
    method: "GET"
    query_params_template:
      search_query: "all:{{query}}"
      start: "0"
      max_results: "{{num_results|default:5}}"
    response_parsing:
      format: "xml"                       # xml | json
      results_path: "feed.entry"
      fields:
        title: "title"
        url: "id"
        snippet: "summary"
        authors: "author[*].name"
        published: "published"
    rate_limit:
      requests_per_minute: 10

  # --- News Search ---
  news_search:
    enabled: false
    provider: "newsapi"
    url: "https://newsapi.org/v2/everything"
    method: "GET"
    query_params_template:
      q: "{{query}}"
      pageSize: "{{num_results|default:5}}"
      sortBy: "publishedAt"
      apiKey: "${NEWSAPI_KEY}"
    response_parsing:
      results_path: "articles"
      fields:
        title: "title"
        url: "url"
        snippet: "description"
        date: "publishedAt"
        source_name: "source.name"

# ============================================================
# CUSTOM ENDPOINTS (User adds their own here)
# ============================================================

custom_endpoints:
  # Example: a custom internal knowledge base
  # internal_kb:
  #   enabled: true
  #   provider: "my_company_kb"
  #   url: "https://kb.internal.company.com/api/search"
  #   method: "POST"
  #   headers:
  #     Authorization: "Bearer ${INTERNAL_KB_KEY}"
  #     Content-Type: "application/json"
  #   body_template: |
  #     {
  #       "query": "{{query}}",
  #       "top_k": {{num_results|default:3}}
  #     }
  #   response_parsing:
  #     results_path: "results"
  #     fields:
  #       title: "document_title"
  #       url: "document_url"
  #       snippet: "relevant_passage"
  #   tool_mapping: "knowledge_base_search"   # Maps to a tool the LLM can call
  #   tool_description: "Search the internal company knowledge base for policy documents and procedures."
```

### Environment Variables File: `.env`

```bash
# API Keys — never committed to version control
LOCAL_LLM_API_KEY=none
SERPER_API_KEY=your_serper_key_here
BRAVE_API_KEY=your_brave_key_here
JINA_API_KEY=your_jina_key_here
NEWSAPI_KEY=your_newsapi_key_here
INTERNAL_KB_KEY=your_internal_key_here
```

### Configuration Resolution Rules

1. All `${VAR_NAME}` references are resolved from environment variables at startup.
2. All `{{placeholder}}` references in templates are resolved at call-time from tool parameters.
3. `|default:value` syntax provides fallback values.
4. If an endpoint is `enabled: false`, its corresponding tool is not registered.
5. If multiple endpoints map to the same tool type (e.g., `web_search` and `web_search_brave`), the first enabled one is primary; others are fallbacks.

---

## 3. Tool Registry Design

### Default Tools

The harness ships with the following default tool definitions. Each tool maps to one or more configured endpoints.

---

#### 3.1 `web_search`

**Purpose:** Perform a web search and return structured results.

**Input Parameters:**
```json
{
  "query": {
    "type": "string",
    "description": "The search query",
    "required": true
  },
  "num_results": {
    "type": "integer",
    "description": "Number of results to return (1-10)",
    "default": 5
  },
  "country_code": {
    "type": "string",
    "description": "Two-letter country code for regional results",
    "default": "us"
  }
}
```

**Output Format:**
```json
{
  "results": [
    {
      "title": "Page Title",
      "url": "https://example.com/page",
      "snippet": "Brief description or excerpt...",
      "date": "2025-01-15"
    }
  ],
  "query_used": "the actual query sent",
  "result_count": 5
}
```

**Endpoint Mapping:** Uses the first enabled endpoint with tool type `web_search` from the `endpoints` section. Fills `{{query}}`, `{{num_results}}`, `{{country_code}}` into the body/query template.

---

#### 3.2 `fetch_url`

**Purpose:** Retrieve and extract the textual content of a web page.

**Input Parameters:**
```json
{
  "url": {
    "type": "string",
    "description": "The URL to fetch and extract content from",
    "required": true
  },
  "extract_links": {
    "type": "boolean",
    "description": "Whether to also extract hyperlinks from the page",
    "default": false
  }
}
```

**Output Format:**
```json
{
  "title": "Page Title",
  "url": "https://example.com/page",
  "content": "Markdown-formatted page content (truncated to max_content_tokens)...",
  "links": [
    {"text": "Link text", "url": "https://..."}
  ],
  "fetch_timestamp": "2025-01-15T10:30:00Z",
  "content_truncated": false
}
```

**Content Truncation:** The retrieval layer truncates page content to a configurable maximum (e.g., 3000 tokens) to prevent context overflow. The `content_truncated` flag indicates if truncation occurred.

**Endpoint Mapping:** Uses the `fetch_url` endpoint. The `{{target_url}}` placeholder is filled with the URL parameter.

---

#### 3.3 `extract_links`

**Purpose:** Extract all hyperlinks from a given URL (without full page content). Useful for navigation and discovery.

**Input Parameters:**
```json
{
  "url": {
    "type": "string",
    "description": "The URL to extract links from",
    "required": true
  },
  "filter_pattern": {
    "type": "string",
    "description": "Optional regex pattern to filter links (e.g., '.*\\.pdf$')",
    "default": null
  }
}
```

**Output Format:**
```json
{
  "source_url": "https://example.com",
  "links": [
    {"text": "Link text", "url": "https://...", "type": "internal|external"}
  ],
  "link_count": 42
}
```

**Implementation:** This is a specialized invocation of `fetch_url` with post-processing that parses only the links from the content. Can be implemented as a wrapper around `fetch_url` with `extract_links: true` and content discarded.

---

#### 3.4 `summarize_page`

**Purpose:** Fetch a URL and produce a concise summary. This is a compound tool: it calls `fetch_url` internally, then passes the content through the LLM for summarization.

**Input Parameters:**
```json
{
  "url": {
    "type": "string",
    "description": "The URL to fetch and summarize",
    "required": true
  },
  "focus": {
    "type": "string",
    "description": "Optional focus topic — summarize with emphasis on this aspect",
    "default": null
  },
  "max_length": {
    "type": "string",
    "description": "Desired summary length: 'brief' (1-2 sentences), 'medium' (1 paragraph), 'detailed' (3-5 paragraphs)",
    "default": "medium"
  }
}
```

**Output Format:**
```json
{
  "title": "Page Title",
  "url": "https://example.com/page",
  "summary": "Concise summary of the page content...",
  "key_points": ["Point 1", "Point 2"],
  "fetch_timestamp": "2025-01-15T10:30:00Z"
}
```

**Implementation:** This tool triggers a secondary LLM call (using a summarization system prompt) within the retrieval layer. The summarization call is separate from the main orchestration loop to keep the agent context clean.

---

#### 3.5 `academic_search`

**Purpose:** Search academic databases (arXiv, Semantic Scholar, etc.) for papers.

**Input Parameters:**
```json
{
  "query": {
    "type": "string",
    "description": "Academic search query (keywords, paper title, author name)",
    "required": true
  },
  "num_results": {
    "type": "integer",
    "default": 5
  }
}
```

**Output Format:**
```json
{
  "papers": [
    {
      "title": "Paper Title",
      "url": "https://arxiv.org/abs/2401.xxxxx",
      "authors": ["Author A", "Author B"],
      "abstract": "Paper abstract...",
      "published": "2025-01-10",
      "source": "arxiv"
    }
  ]
}
```

**Endpoint Mapping:** Uses `arxiv_search` or any custom academic endpoint.

---

#### 3.6 `news_search`

**Purpose:** Search recent news articles on a topic.

**Input Parameters:**
```json
{
  "query": {
    "type": "string",
    "required": true
  },
  "num_results": {
    "type": "integer",
    "default": 5
  },
  "recency": {
    "type": "string",
    "description": "Time range: 'today', 'this_week', 'this_month', 'any'",
    "default": "this_week"
  }
}
```

**Output Format:**
```json
{
  "articles": [
    {
      "title": "Article Title",
      "url": "https://...",
      "snippet": "Description...",
      "source_name": "Reuters",
      "published": "2025-01-15"
    }
  ]
}
```

---

#### 3.7 `compute` (Optional Utility Tool)

**Purpose:** Evaluate mathematical expressions or perform date/time calculations.

**Input Parameters:**
```json
{
  "expression": {
    "type": "string",
    "description": "Mathematical expression or date calculation to evaluate",
    "required": true
  }
}
```

**Output Format:**
```json
{
  "expression": "2^10 * 3",
  "result": "3072"
}
```

**Implementation:** Uses a safe local expression evaluator (sandboxed). No external endpoint needed.

---

#### 3.8 `custom_endpoint` (Dynamic / User-Defined)

**Purpose:** A generic tool generated from any entry in the `custom_endpoints` config section.

For each custom endpoint, the harness auto-generates a tool with:
- **Name:** The key from `custom_endpoints` (e.g., `internal_kb`)
- **Description:** From `tool_description` field in config
- **Input Parameters:** Inferred from `{{placeholder}}` variables in the body/query template
- **Output Format:** Determined by `response_parsing` config

This is how users add arbitrary endpoints without code — they just add a YAML block and the harness creates a callable tool from it.

---

### Tool Schema Generation for LLM

At startup, the Tool Registry generates a tool schema document in the format expected by the local LLM's tool-calling convention (OpenAI function-calling format, Anthropic tool-use format, or a ReAct-style text description). Example for OpenAI format:

```json
{
  "type": "function",
  "function": {
    "name": "web_search",
    "description": "Search the web for current information on any topic. Returns titles, URLs, and snippets.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {"type": "string", "description": "The search query"},
        "num_results": {"type": "integer", "description": "Number of results (1-10)", "default": 5}
      },
      "required": ["query"]
    }
  }
}
```

---

## 4. Orchestration Loop Logic

### Overview

The orchestration loop implements an **agentic ReAct-style cycle**: Reason → Act → Observe → Repeat (or Finish). It is the beating heart of the harness.

### Step-by-Step Decision Flow

```
START: User submits query
│
▼
[Step 1] CONTEXT ASSEMBLY
│  • Retrieve conversation history from Memory Manager
│  • Load system prompt (with tool schemas, citation instructions)
│  • Calculate available token budget:
│      budget = context_window - thinking_budget - max_output_tokens
│  • If history exceeds budget, trigger summarization/eviction
│  • Assemble full prompt: system + history + tools + current query
│
▼
[Step 2] LLM INFERENCE
│  • Send assembled prompt to Local LLM Core
│  • Receive response (text, or structured tool-call objects)
│
▼
[Step 3] RESPONSE CLASSIFICATION
│  • Parse LLM output to determine response type:
│    ├─ FINAL_ANSWER: Model produced a direct answer (no tool calls)
│    ├─ TOOL_CALL: Model requested one or more tool invocations
│    └─ MALFORMED: Model output doesn't match expected format
│
├── If FINAL_ANSWER ──────────────────────────────────────────────┐
│                                                                 │
│   [Step 7] POST-PROCESSING                                      │
│   • Validate citations reference real retrieved sources         │
│   • Format hyperlinks per config (markdown/HTML)                │
│   • Append source list if configured                            │
│   • Store turn in Memory Manager                                │
│   • Return response to user                                     │
│   ──► END                                                       │
│                                                                 │
├── If TOOL_CALL ─────────────────────────────────────────────────┤
│                                                                 │
│   [Step 4] TOOL DISPATCH                                        │
│   • For each tool call in the response:                         │
│     ├─ Validate tool name exists in registry                    │
│     ├─ Validate parameters against tool schema                  │
│     ├─ Check rate limits for the associated endpoint            │
│     └─ If validation fails: create error result                 │
│   • Execute valid tool calls:                                   │
│     ├─ If parallel_tool_calls enabled: dispatch concurrently    │
│     │   (up to max_parallel, with individual timeouts)          │
│     └─ If sequential: execute one by one                        │
│   • For each execution:                                         │
│     ├─ Fill endpoint template with parameters                   │
│     ├─ Make HTTP request                                        │
│     ├─ Parse response using response_parsing rules              │
│     ├─ Handle errors (timeout, HTTP errors, parse failures)     │
│     └─ Format result into standardized tool output              │
│                                                                 │
│   [Step 5] RESULT INJECTION                                     │
│   • Append tool results to conversation as "tool" role msgs     │
│   • Store retrieved content in document cache (for reuse)       │
│   • Assign source IDs to each retrieved item (e.g., [1],[2])    │
│   • Recalculate token budget                                    │
│   • If budget exceeded: summarize/truncate tool results         │
│                                                                 │
│   [Step 6] ITERATION CHECK                                      │
│   • iteration_count += 1                                        │
│   • If iteration_count >= max_tool_iterations:                  │
│     ├─ Inject "force_final_answer" system message               │
│     └─ Go to Step 2 (one last LLM call)                         │
│   • Else: Go to Step 2                                          │
│                                                                 │
├── If MALFORMED ─────────────────────────────────────────────────┤
│                                                                 │
│   • malformed_count += 1                                        │
│   • If malformed_count >= 3:                                    │
│     ├─ Inject corrective system message:                        │
│     │   "Your previous output was not valid. Please respond     │
│     │    with either a final answer or a properly formatted     │
│     │    tool call."                                            │
│     └─ Go to Step 2                                             │
│   • If malformed_count >= 5:                                    │
│     ├─ Abandon tool-calling; ask LLM to answer directly         │
│     └─ Go to Step 2 with tools disabled                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-Tool Call Strategy

When the model requests multiple tools in one turn:

1. **Dependency Analysis:** If tool B's input depends on tool A's output (e.g., `web_search` then `fetch_url` on a result), the harness should detect this and execute sequentially. In practice, if the model requests both in a single turn with the URL already specified, they can be parallel.

2. **Parallel Execution:** Independent calls (e.g., two different `web_search` queries) execute concurrently with `asyncio.gather()` or equivalent, each with its own timeout.

3. **Partial Failure:** If 2 of 3 parallel calls succeed, inject the successful results plus an error message for the failed one. Let the model decide whether to retry.

### Error Handling During Tool Execution

| Error Type | Handling |
|---|---|
| **HTTP 4xx** (client error) | Return error message to model: "Tool returned error 403: Forbidden. The endpoint may require different authentication." |
| **HTTP 5xx** (server error) | Retry per retry config. After max retries, return error to model. |
| **Timeout** | Return: "Tool call timed out after N seconds. Consider simplifying the request or trying a different approach." |
| **Malformed response** | Attempt best-effort parsing. If completely unparseable, return raw response truncated to 500 chars with error note. |
| **Rate limit exceeded** | If a secondary endpoint is configured for the same tool type, failover. Otherwise return: "Rate limit reached. Try again in N seconds." |
| **Endpoint not configured** | Return: "This tool is not currently configured. Please answer using your training knowledge." |

---

## 5. Response Formatting & Hyperlink Integration

### Strategy

The harness enforces citation and link behavior through a combination of:
1. **System prompt instructions** that tell the model exactly how to cite
2. **Post-processing** that validates and cleans citations
3. **Source injection** that provides source metadata in a structured format the model can reference

### System Prompt Snippet

````markdown
## System Prompt for Research Assistant Mode

You are a research assistant with access to live web tools. Your responses must be accurate, well-sourced, and include proper citations.

### Citation Rules (MANDATORY):

1. **Every factual claim derived from a tool result MUST include an inline citation** using the format `[n]` where `n` is the source number assigned to the tool result.

2. **Citations link to sources.** When you write `[1]`, it refers to the first source in the retrieved results. You will see source assignments like:
   ```
   [Source 1] Title: "Example Article" | URL: https://example.com/article
   [Source 2] Title: "Another Source" | URL: https://another.com/page
   ```

3. **Include hyperlinks naturally in your text** using Markdown format:
   - When mentioning a source by name: `[Article Title](https://url)`
   - When providing a direct link: `[Read more](https://url)`
   - When citing: `according to [Source Name](https://url) [1]`

4. **At the end of your response**, include a "Sources" section:
   ```
   ---
   **Sources:**
   1. [Title](URL)
   2. [Title](URL)
   ```

5. **Do NOT fabricate URLs.** Only use URLs that appear in tool results. If you need to reference general knowledge from your training data, say "Based on my training knowledge" without a citation number.

6. **Do NOT include raw API keys, authentication tokens, or internal system details in your response.**

### Response Quality Rules:

- Synthesize information from multiple sources when available
- Note when sources conflict or when information may be outdated
- Prefer recent sources over older ones for time-sensitive topics
- If the tools return insufficient information, say so honestly and supplement with training knowledge (clearly labeled)

### Tool Usage Guidelines:

- Use `web_search` for current events, recent information, or facts you're unsure about
- Use `fetch_url` to get detailed content from a specific page found in search results
- Use `academic_search` for scientific papers, research, and scholarly topics
- Use `news_search` specifically for recent news stories
- You may chain tools: search first, then fetch specific URLs for deeper information
- Do NOT call tools unnecessarily — if you can confidently answer from prior tool results or clear training knowledge, do so
````

### Post-Processing Rules

After the model generates its final answer, the harness applies these transformations:

1. **Citation Validation:** Check that every `[n]` reference maps to an actual retrieved source. Remove orphaned citations. Log warnings for citations to non-existent sources.

2. **URL Validation:** Verify that all URLs in the response text were actually present in tool results. Strip any URLs that appear fabricated (not in the retrieved source registry).

3. **Markdown Link Assembly:** If the model outputs bare URLs, wrap them: `https://example.com` → `[example.com](https://example.com)`.

4. **Source List Generation:** If `include_source_list: true`, and the model didn't include one, auto-append a Sources section based on all sources actually cited in the text.

5. **Key Scrubbing:** Regex scan for patterns resembling API keys (long alphanumeric strings, bearer tokens) and redact them.

### Example Output

```markdown
## Current State of Quantum Computing in 2025

Quantum computing has seen significant advances in early 2025. IBM announced
its Heron processor achieving over 5,000 qubits [1], while Google's Willow
chip demonstrated quantum error correction below the threshold needed for
practical computation [according to [Google AI Blog](https://blog.google/technology/ai/quantum-willow) [2]].

Meanwhile, startups like PsiQuantum are pursuing photonic approaches that
could scale more easily, as [reported by MIT Technology Review](https://www.technologyreview.com/2025/01/10/psiquantum-update) [3].

However, experts caution that fault-tolerant quantum computing for practical
applications remains several years away [4].

---
**Sources:**
1. [IBM Quantum Roadmap 2025](https://www.ibm.com/quantum/roadmap)
2. [Google AI Blog: Willow Processor](https://blog.google/technology/ai/quantum-willow)
3. [MIT Technology Review: PsiQuantum Update](https://www.technologyreview.com/2025/01/10/psiquantum-update)
4. [Nature: Quantum Computing Timeline](https://www.nature.com/articles/d41586-025-00100-1)
```

---

## 6. Memory & Context Management

### Architecture

The Memory & Context Manager operates at three levels:

```
┌──────────────────────────────────────────────────────────┐
│  Level 1: WORKING CONTEXT (in-prompt)                    │
│  Active conversation turns + current tool results        │
│  Lives inside the prompt sent to the LLM                 │
│  Budget: context_budget_percentage × context_window      │
├──────────────────────────────────────────────────────────┤
│  Level 2: SESSION CACHE (in-memory)                      │
│  Full conversation history for current session           │
│  Retrieved document cache (full text)                    │
│  Used for context reconstruction after eviction          │
├──────────────────────────────────────────────────────────┤
│  Level 3: PERSISTENT STORE (on-disk)                     │
│  Conversation logs (SQLite or JSON files)                │
│  Document cache with TTL (filesystem)                    │
│  Session summaries for cross-session continuity          │
└──────────────────────────────────────────────────────────┘
```

### Token Budget Management

**Budget Calculation (each turn):**
```
total_context_window = 32768  (from config)
reserved_for_output  = 4096   (max_tokens)
reserved_for_thinking= 2048   (thinking_budget)
available_for_input  = 32768 - 4096 - 2048 = 26624 tokens

system_prompt_tokens = ~1500  (measured once at startup)
tool_schemas_tokens  = ~800   (measured once at startup)
remaining_for_history_and_docs = 26624 - 1500 - 800 = 24324 tokens
```

### Context Eviction Strategy

When the assembled context exceeds `remaining_for_history_and_docs`:

1. **First Pass — Document Truncation:**
   - Truncate retrieved document content to essential excerpts (first 500 tokens each).
   - Keep metadata (title, URL, snippet) intact for citation purposes.

2. **Second Pass — Rolling Summarization:**
   - Take the oldest N turns of conversation.
   - Send them to the LLM with a summarization prompt: "Summarize the following conversation turns, preserving key facts, decisions, and source references."
   - Replace those N turns with the summary (typically 3-5x compression).
   - The summary is marked with a header: `[Summary of turns 1-8]`

3. **Third Pass — Aggressive Eviction:**
   - If still over budget after summarization, remove tool result details from older turns, keeping only the model's synthesized answers.
   - As a last resort, keep only: system prompt + latest summary + last 3 turns.

### Document Cache

- Retrieved documents are stored in Level 2 (in-memory dict keyed by URL) and Level 3 (filesystem, keyed by URL hash).
- Each cached document has a TTL (default 60 minutes from config).
- When the model calls `fetch_url` for a URL that's already cached and not expired, the cached version is returned instantly (no HTTP call).
- Cache entries store: URL, title, content, links, fetch timestamp, token count.

### Cross-Turn Source Registry

A running `source_registry` object maintains all sources encountered in the session:

```python
# Pseudo-code structure
source_registry = {
    1: {"title": "...", "url": "...", "snippet": "...", "turn_introduced": 3},
    2: {"title": "...", "url": "...", "snippet": "...", "turn_introduced": 3},
    # ...
}
next_source_id = 3
```

When new sources are retrieved, they're assigned the next available ID. When the model references `[1]` in turn 5, the harness can verify this refers to a source from turn 3. This registry persists across turns and is included in the system prompt as a reference table.

### Multi-Session Continuity (Optional)

For users who want to resume research across sessions:
- At session end (or periodically), generate a session summary including key findings, sources, and unresolved questions.
- Store in Level 3 with a session ID.
- At session start, if a session ID is provided, load the summary into the system prompt as prior context.

---

## 7. Implementation Roadmap

### Phase 1: Bare-Bones LLM Wrapper
**Deliverable:** A CLI application that accepts user input, sends it to a local LLM server, and prints the response.

**Tasks:**
- Set up project structure (Python with async support)
- Implement LLM client supporting OpenAI-compatible API format
- Basic CLI input/output loop
- Load minimal config (LLM endpoint URL, model name)

**Testing Criteria:**
- Can connect to a running Ollama/llama.cpp/vLLM instance
- Sends a message and receives a coherent response
- Handles connection errors gracefully

**Estimated Effort:** 1-2 days

---

### Phase 2: Configuration System
**Deliverable:** Full config file parsing with environment variable resolution, validation, and hot-reload.

**Tasks:**
- Implement YAML config parser
- Implement `${ENV_VAR}` resolution from `.env` file and system env
- Implement `{{placeholder}}` template engine for request bodies
- Add config validation (required fields, type checking, URL format)
- Add file watcher for hot-reload

**Testing Criteria:**
- Config loads and validates without errors
- Missing required fields produce clear error messages
- Environment variables are resolved correctly
- Malformed YAML produces helpful error (not a stack trace)
- Config changes are detected and reloaded within 5 seconds

**Estimated Effort:** 2-3 days

---

### Phase 3: Tool Registry & Basic Tool Execution
**Deliverable:** A tool registry that generates tool schemas from config and can execute HTTP-based tools.

**Tasks:**
- Implement Tool base class with schema generation
- Build registry that auto-discovers tools from config endpoints
- Implement generic HTTP tool executor (template filling → HTTP call → response parsing)
- Support both JSON and XML response parsing
- Implement the `web_search` tool against a real search API (e.g., Serper)
- Implement the `fetch_url` tool against a reader API (e.g., Jina Reader)

**Testing Criteria:**
- Tool schemas are correctly generated in OpenAI function-calling format
- `web_search("latest AI news")` returns parsed, structured results
- `fetch_url("https://example.com")` returns markdown content
- HTTP errors return structured error objects, not crashes
- Rate limiting is respected

**Estimated Effort:** 3-4 days

---

### Phase 4: Orchestration Loop (Core Agent)
**Deliverable:** The full agent loop — model reasons, calls tools, observes results, and produces final answers.

**Tasks:**
- Implement the orchestration loop (Steps 1-7 from Section 4)
- Implement tool-call parsing from LLM output (support OpenAI format and ReAct text format)
- Implement multi-tool parallel execution
- Implement iteration counting and force-final-answer logic
- Implement malformed-output recovery
- Build the system prompt with tool schemas and citation instructions

**Testing Criteria:**
- Ask "What happened in tech news today?" → model calls `web_search`, produces answer with citations
- Ask a multi-step question → model chains `web_search` + `fetch_url` across iterations
- Model stops after `max_tool_iterations` even if it keeps wanting to search
- Malformed tool calls are caught and the model is prompted to retry
- Questions answerable from training data don't trigger unnecessary tool calls

**Estimated Effort:** 4-5 days

---

### Phase 5: Response Formatting & Citation Engine
**Deliverable:** Post-processing pipeline that ensures all responses have proper citations, hyperlinks, and source lists.

**Tasks:**
- Implement source registry (cross-turn source tracking)
- Implement citation validation (verify `[n]` references)
- Implement URL validation (ensure cited URLs came from tools)
- Implement markdown link formatter
- Implement auto-generated Sources section
- Implement API key scrubbing regex
- Build the system prompt refinements for citation quality

**Testing Criteria:**
- Responses consistently contain `[n]` inline citations
- Source list at bottom matches inline citations
- Fabricated URLs are stripped
- Bare URLs are wrapped in markdown links
- No API keys appear in any response

**Estimated Effort:** 2-3 days

---

### Phase 6: Memory & Context Manager
**Deliverable:** Conversation memory system with summarization, document caching, and token budget enforcement.

**Tasks:**
- Implement token counting (using tiktoken or model-specific tokenizer)
- Implement token budget calculator
- Implement rolling summarization strategy
- Implement document cache (in-memory + filesystem with TTL)
- Implement context assembly with budget-aware truncation
- Implement cross-turn source registry persistence

**Testing Criteria:**
- A 20-turn conversation stays within context window limits
- Summarized turns preserve key facts and source references
- Cached URLs are served instantly on re-fetch
- Cache entries expire correctly after TTL
- Model can reference sources from earlier turns accurately

**Estimated Effort:** 3-4 days

---

### Phase 7: Custom Endpoint & Dynamic Tool Generation
**Deliverable:** Users can add arbitrary endpoints in `custom_endpoints` config and they automatically become callable tools.

**Tasks:**
- Implement dynamic tool generation from config entries
- Auto-infer parameter schemas from template placeholders
- Implement `tool_mapping` and `tool_description` config fields
- Implement endpoint fallback chains (primary → secondary)
- Add validation for custom endpoint configs

**Testing Criteria:**
- Add a custom endpoint in config → tool appears in model's tool list
- Model successfully calls custom tool and receives parsed results
- Remove/disable custom endpoint → tool disappears from registry
- Malformed custom endpoint config produces clear error
- Fallback from failed primary endpoint to secondary works

**Estimated Effort:** 2-3 days

---

### Phase 8: Additional Default Tools
**Deliverable:** Full suite of built-in tools: `academic_search`, `news_search`, `extract_links`, `summarize_page`, `compute`.

**Tasks:**
- Implement `academic_search` with arXiv API (XML parsing)
- Implement `news_search` with NewsAPI or equivalent
- Implement `extract_links` as a post-processor on fetch results
- Implement `summarize_page` as a compound tool (fetch + LLM summarization call)
- Implement `compute` with sandboxed expression evaluation

**Testing Criteria:**
- `academic_search("transformer architecture")` returns arXiv papers
- `news_search("climate change")` returns recent articles with dates
- `extract_links` on a Wikipedia page returns valid links
- `summarize_page` produces a coherent summary with focus topic
- `compute("2^32")` returns correct result, and `compute("import os")` is safely rejected

**Estimated Effort:** 3-4 days

---

### Phase 9: Web UI Configuration Panel (Optional)
**Deliverable:** A lightweight local web interface for managing endpoints, viewing logs, and testing tools.

**Tasks:**
- Build simple web UI (e.g., Gradio, Streamlit, or custom FastAPI + minimal HTML)
- Endpoint management: add/edit/disable/test endpoints
- API key management: set/update keys (stored in env, shown as masked)
- Live chat interface for testing
- Tool execution logs with timing and result previews
- Config export/import

**Testing Criteria:**
- Can add a new endpoint through the UI and immediately use it in chat
- API keys are masked in the UI (show only last 4 chars)
- Can test a tool independently (fill params, see raw result)
- Chat interface produces same quality as CLI

**Estimated Effort:** 3-5 days

---

### Phase 10: Hardening, Optimization & Polish
**Deliverable:** Production-ready harness with all edge cases handled, performance optimized, and documentation complete.

**Tasks:**
- Comprehensive error handling audit
- Performance optimization (async I/O, connection pooling)
- Streaming response support (token-by-token output)
- Request deduplication (don't search the same query twice in one session)
- Model-specific prompt tuning (test with Mistral, Llama 3, Qwen, Phi, etc.)
- Write user documentation (setup guide, config reference, troubleshooting)
- Write developer documentation (architecture, extension points)
- Package as installable (pip package or Docker container)

**Testing Criteria:**
- All test scenarios from Section 10 pass
- Works with at least 3 different local model backends
- Handles 50+ turn conversations without degradation
- Streams responses for better UX
- Documentation enables a new user to set up in < 30 minutes

**Estimated Effort:** 4-6 days

---

### Total Estimated Effort: 27-39 days (for a single developer)

---

## 8. Edge Cases & Fallback Strategy

### Endpoint Failures

| Scenario | Response |
|---|---|
| **Endpoint returns HTTP 403/401** | Log auth error. If alternate endpoint configured for same tool type, retry with alternate. If not, return tool error to model with message: "Authentication failed for [tool]. This may require reconfiguring the API key." |
| **Endpoint returns HTTP 429 (rate limited)** | Respect `Retry-After` header if present. If not, apply exponential backoff per retry config. If all retries exhausted, try alternate endpoint. If none available, return rate limit error to model. |
| **Endpoint returns HTTP 500+** | Retry per config. Log each attempt. After exhaustion, return server error to model. |
| **DNS resolution failure / Connection refused** | Immediately return error to model: "Could not reach [endpoint]. The service may be down or the URL may be misconfigured." No retries for DNS failures (likely config issue). |
| **Request timeout** | Per `tool_call_timeout_seconds` config. Return timeout error to model. Model may choose to retry with simpler query or proceed with existing information. |

### Malformed Responses

| Scenario | Response |
|---|---|
| **Response is valid HTTP but not valid JSON/XML** | Attempt to extract useful text content. If HTML, attempt basic text extraction. Return whatever was extracted with a warning: "Response was not in expected format. Extracted text: [truncated content]" |
| **JSON is valid but `results_path` doesn't exist** | Log the actual response structure (sanitized). Return: "Response structure did not match expected schema. Raw keys found: [list top-level keys]" |
| **Response is empty (200 OK, empty body)** | Return: "Endpoint returned an empty response for query: [query]." |
| **Response is valid but contains 0 results** | Return normally with empty results array. Model interprets no results and may rephrase query or try different tool. |

### Endpoint Completely Unavailable

If **no endpoint** is configured or enabled for a tool the model tries to call:
1. Return a tool error: "The tool `[tool_name]` is not currently configured. No endpoint is available."
2. The model should then fall back to its training knowledge.
3. If `fallback_to_training_knowledge` is `true` (config), the system prompt includes: "If a tool is unavailable or fails, clearly state this and provide the best answer you can from your training knowledge, noting that the information may not be current."

### Model Refuses to Use Tools

Some models may ignore tool schemas and answer directly even when tools would be beneficial. Mitigation:
- Detect when the model answers a clearly time-sensitive question without calling tools
- Inject a follow-up system message: "Your answer may contain outdated information. Consider using web_search to verify current facts."
- This is a soft nudge, not a forced retry (to avoid infinite loops)

### Circular Tool Calls

If the model keeps calling the same tool with the same parameters:
- Track (tool_name, parameters_hash) pairs per session
- If the same call is made 2+ times in the same orchestration run, return the cached result immediately and add a note: "This query was already executed. Returning cached result."

### Context Window Overflow

If tool results are so large they blow the context budget:
1. Truncate tool result content (keeping metadata + first N tokens)
2. If still over budget, summarize the tool result before injection
3. If still over budget, inject only metadata: "Fetched [URL], [word_count] words. Key topics: [auto-extracted topic list]"

---

## 9. Security & Key Management

### Key Storage Hierarchy (Recommended)

```
Priority 1: System Keychain / Encrypted Vault
├── macOS: Keychain Access
├── Linux: libsecret / GNOME Keyring / KWallet
├── Windows: Windows Credential Manager
├── Cross-platform: HashiCorp Vault, age-encrypted file
│
Priority 2: Environment Variables
├── Set in shell profile (.bashrc, .zshrc)
├── Set in systemd service file
├── Set in Docker environment
│
Priority 3: Local .env File
├── MUST be in .gitignore
├── MUST have restricted file permissions (chmod 600)
├── SHOULD be documented as "development only"
│
NEVER: Directly in config.yaml or committed to version control
```

### Key Reference System

The config file never contains raw keys. It uses `${ENV_VAR_NAME}` references. The harness resolves these at startup in this order:
1. Check system keychain/vault (if integration is configured)
2. Check environment variables
3. Check `.env` file
4. If not found: log a clear warning and disable the affected endpoint

### Preventing Key Leakage in Model Responses

**Multi-layer defense:**

1. **System Prompt Instruction:**
   ```
   CRITICAL: Never include API keys, tokens, authentication credentials,
   or internal system configuration in your responses. If you encounter
   such values in tool results, omit them.
   ```

2. **Output Scrubbing (Post-Processing):**
   - Maintain a set of all resolved key values (in memory only)
   - Before returning any response to the user, scan the text for exact matches of any key value
   - Replace matches with `[REDACTED]`
   - Also scan for common patterns:
     - `Bearer [A-Za-z0-9_-]{20,}`
     - `sk-[A-Za-z0-9]{32,}`
     - `key-[A-Za-z0-9]{16,}`
     - Any string matching a known key format for configured providers

3. **Input Scrubbing (Before Injection to Model):**
   - When tool results are injected into the prompt, strip any headers or metadata that contain key values
   - The model should never see the raw HTTP request/response headers — only the parsed content

4. **Tool Result Sanitization:**
   - The retrieval layer strips response headers before passing results to the orchestrator
   - If a tool response body contains the API key (some APIs echo it), the parser removes it

### Configuration File Security

- The config file (`config.yaml`) should be readable only by the user running the harness (`chmod 600`)
- If a web UI is used, it should bind to `localhost` only by default (not `0.0.0.0`)
- The web UI should not expose a raw config editor that shows resolved key values — only masked versions

### Audit Logging

- Log all tool calls with timestamps, endpoint URLs, and parameter summaries (but never log request headers containing keys)
- Log all key resolution events (which keys were found, which were missing) at startup (log key names, never values)

---

## 10. Testing & Validation Checklist

### Test Scenarios

---

**Test 1: Simple Factual Question (No Tools Needed)**
- **Input:** "What is the capital of France?"
- **Expected Behavior:** Model answers directly from training knowledge ("Paris") without calling any tools. No citations section (no sources retrieved). Response should note it's from training knowledge if configured to do so.
- **Validates:** Tool-call avoidance for simple queries, basic response formatting.

---

**Test 2: Current Events Query**
- **Input:** "What are the major news stories today?"
- **Expected Behavior:** Model calls `web_search` or `news_search` with an appropriate query. Returns a summary of current headlines with inline citations `[1]`, `[2]`, etc. Each cited item has a working hyperlink. Sources section appears at the bottom.
- **Validates:** Tool invocation, search API integration, citation formatting.

---

**Test 3: Deep Dive with URL Fetching**
- **Input:** "Summarize the latest blog post on the OpenAI blog."
- **Expected Behavior:** Model calls `web_search("latest OpenAI blog post")` → gets URL → calls `fetch_url(url)` or `summarize_page(url)` → produces summary with citation to the actual blog post URL.
- **Validates:** Multi-step tool chaining, `fetch_url` integration, summarization quality.

---

**Test 4: Academic Research Query**
- **Input:** "Find recent papers on diffusion models for video generation."
- **Expected Behavior:** Model calls `academic_search` → returns papers with titles, authors, arXiv links. Response includes hyperlinks to each paper. Citations reference the arXiv entries.
- **Validates:** `academic_search` tool, XML parsing (arXiv API), academic citation formatting.

---

**Test 5: Multi-Turn Conversation with Context Retention**
- **Input (Turn 1):** "Search for information about SpaceX's Starship program."
- **Input (Turn 2):** "What was the second source you found? Tell me more about that."
- **Input (Turn 3):** "Compare what source [1] says with source [3]."
- **Expected Behavior:** Turn 1 performs search and presents sources. Turn 2 correctly identifies the second source from turn 1 and fetches it for more detail. Turn 3 references and compares content from two previously retrieved sources.
- **Validates:** Cross-turn memory, source registry persistence, context manager.

---

**Test 6: Endpoint Failure / Graceful Degradation**
- **Setup:** Disable or misconfigure the `web_search` endpoint (wrong API key).
- **Input:** "What's the current price of Bitcoin?"
- **Expected Behavior:** Model calls `web_search`. Tool returns an authentication error. Model acknowledges the tool failure and either: (a) tries an alternative endpoint if configured, or (b) falls back to training knowledge with a disclaimer: "I was unable to fetch live data. Based on my training knowledge..."
- **Validates:** Error handling, fallback behavior, graceful degradation.

---

**Test 7: Rate Limit Handling**
- **Setup:** Set `requests_per_minute: 2` for the search endpoint.
- **Input:** Rapid series of questions requiring search.
- **Expected Behavior:** First 2 requests work. Third request triggers rate limiting. Harness either waits and retries, falls back to alternate endpoint, or informs the model. No crash or hang.
- **Validates:** Rate limiter, retry logic, backoff strategy.

---

**Test 8: Custom Endpoint Integration**
- **Setup:** Add a custom endpoint to `custom_endpoints` config (e.g., a mock server or a real API like a weather service).
- **Input:** A query that should trigger the custom tool.
- **Expected Behavior:** The custom tool appears in the model's tool list. Model correctly calls it with inferred parameters. Results are parsed according to custom `response_parsing` rules. Response cites the custom source.
- **Validates:** Dynamic tool generation from config, custom endpoint execution, plug-and-play capability.

---

**Test 9: API Key Scrubbing**
- **Setup:** Intentionally craft a scenario where a tool result includes an API key (mock a response that echoes the key).
- **Input:** Any query that triggers the mocked tool.
- **Expected Behavior:** The API key does NOT appear in the model's response. Post-processing scrubbing catches and redacts it.
- **Validates:** Output sanitization, key leak prevention.

---

**Test 10: Context Window Stress Test**
- **Input:** Ask 30+ questions in a single session, each requiring web search and URL fetching.
- **Expected Behavior:** System never crashes due to context overflow. Rolling summarization kicks in. Later responses may reference summarized earlier context. Token budget warnings appear in logs but never in user-facing output.
- **Validates:** Context manager, summarization, token budgeting.

---

**Test 11: Malformed Model Output Recovery**
- **Setup:** Use a smaller/weaker model that may produce improperly formatted tool calls.
- **Input:** "Search for the latest developments in quantum computing."
- **Expected Behavior:** If model produces malformed tool call JSON, the harness detects it, sends a correction prompt, and the model retries. After max retries, falls back to direct answer.
- **Validates:** Malformed output detection, correction prompts, retry limits.

---

**Test 12: URL with Special Characters**
- **Input:** "Fetch this page: https://en.wikipedia.org/wiki/São_Paulo"
- **Expected Behavior:** URL is properly encoded and fetched. Content is returned. No encoding errors.
- **Validates:** URL encoding, international character handling.

---

**Test 13: No-Tool-Available Fallback**
- **Setup:** Disable ALL endpoints.
- **Input:** "What is the latest news about AI?"
- **Expected Behavior:** Model detects no tools are available (or all tool calls fail). Responds with training knowledge and explicitly states: "I don't have access to live web search at the moment. Based on my training data..."
- **Validates:** Complete fallback mode, honest capability reporting.

---

**Test 14: Parallel Tool Execution**
- **Input:** "Compare the current weather in Tokyo and New York." (Assuming a weather endpoint is configured.)
- **Expected Behavior:** Model requests two tool calls (one for each city). They execute in parallel (visible in timing logs — both complete in ~1 request time, not 2x). Results are combined in the response.
- **Validates:** Parallel dispatch, result aggregation, concurrent HTTP handling.

---

**Test 15: Hot Reload of Configuration**
- **Setup:** Start the harness. While it's running, add a new custom endpoint to `config.yaml` and save.
- **Input:** Ask a question that would trigger the new tool.
- **Expected Behavior:** Within the reload interval, the new tool becomes available. The model can call it without restarting the harness.
- **Validates:** Hot reload, dynamic tool registration, file watcher.

---

### Validation Metrics

For each test, record:
- ✅/❌ Pass/Fail
- Response time (end-to-end)
- Number of tool calls made
- Token count of final context
- Any errors in logs
- Citation accuracy (do links work? do `[n]` references match?)

---

## Summary of Key Design Decisions

| Decision | Rationale |
|---|---|
| YAML config over code | Users can add endpoints without programming knowledge |
| Environment variables for keys | Standard security practice; supported by all deployment environments |
| OpenAI-compatible tool format as default | Most local model servers support this format |
| Post-processing citation validation | Models are unreliable at self-enforcing formatting rules; the harness must verify |
| Rolling summarization for memory | Best balance of context preservation and token efficiency |
| Parallel tool execution | Dramatically reduces latency for multi-source queries |
| Multiple endpoint fallbacks | Resilience against any single API being down |
| Generic HTTP executor | Any REST API can be integrated without custom code |
| Output scrubbing for keys | Defense-in-depth; prompt instructions alone are insufficient |

This blueprint provides a complete, actionable specification. A developer or AI agent following these 10 sections can build a fully functional, Luminary-like research assistant harness around any locally running language model, with plug-and-play endpoint configuration requiring zero custom code from the end user.

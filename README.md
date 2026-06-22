# PDF Summary Assistant

An AI-powered PDF summarization agent built with DeepSeek Function Calling.

## Experiment Requirements

| Requirement | Implementation |
|-------------|---------------|
| Tool Use / Skills (>= 2 tools) | 4 tools: read_pdf, search_pdf, get_pdf_info, list_pdf_files |
| Context Integration (MCP or similar) | DeepSeek Chat API Function Calling (OpenAI-compatible) |
| "Vibe Coding" | 100% AI-generated boilerplate (Claude Code) |

## Quick Start

```bash
pip install -r requirements.txt
# Edit .env with your DeepSeek API key
python main.py
# Or: python main.py "Summarize the file sample_ai.pdf"
```

## Project Structure

```
pdf-summary-agent/
  main.py                         # CLI entry point
  pdf_summary_agent/
    __init__.py                   # Package init
    config.py                     # Environment configuration
    tools.py                      # Tool implementations + schemas
    agent.py                      # Agent orchestration loop
  .env.example
  requirements.txt
```

## Tools

- read_pdf: Extract text from PDF pages
- search_pdf: Search keywords in PDF
- get_pdf_info: Get PDF metadata
- list_pdf_files: List PDFs in directory

## Configuration

Edit `.env` to set your DeepSeek API key:

```
API_KEY=sk-your-deepseek-api-key
API_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

## Agent Workflow

User Query -> LLM (analyze, decide tools) -> Function Calling -> Tool Execution -> Results -> LLM (synthesize) -> Final Summary

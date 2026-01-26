# Sahiloan Customer Support Agent

Multi-agent customer support system built with LangChain and LangGraph for Sahiloan loan application.

## Architecture

### Agents
- **FAQ Agent**: Handles 80% of common questions using ingested knowledge base
- **Application Agent**: Guides customers through new loan applications
- **Tracking Agent**: Provides loan status updates and tracking information
- **Financial Advisory Agent**: Offers EMI optimization and financial advice
- **Document Intelligence Agent**: Analyzes documents using vision capabilities
- **Escalation Agent**: Routes complex cases to human support

### Technology Stack
- **LangChain**: LLM orchestration and prompt management
- **LangGraph**: Multi-agent workflow building
- **Vector Store**: Knowledge base for FAQ retrieval

## Project Structure

```
sahiloan-csx/
├── src/
│   ├── agents/          # Individual agent implementations
│   ├── workflows/       # LangGraph workflow orchestration
│   ├── llm/            # LLM client and prompts
│   ├── knowledge/      # Knowledge base and retrieval
│   ├── utils/          # Utility functions
│   └── config/         # Configuration files
├── data/
│   ├── faqs/           # FAQ documents for ingestion
│   └── documents/      # Document storage
├── tests/              # Unit tests
├── logs/               # Application logs
└── main.py             # Application entry point
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the application:
```bash
python main.py
```

## Development

- Add FAQ documents to `data/faqs/`
- Configure agents in `src/config/agent_config.py`
- Customize prompts in `src/llm/prompts.py`
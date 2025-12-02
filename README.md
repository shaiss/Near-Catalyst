# NEAR Catalyst Framework - Multi-Agent Partnership Discovery System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![OpenAI API](https://img.shields.io/badge/OpenAI-GPT--4o%20%7C%20o4--mini-green.svg)](https://openai.com/)
[![NEAR Protocol](https://img.shields.io/badge/NEAR-Protocol-00D4FF.svg)](https://near.org)
[![Web3](https://img.shields.io/badge/Web3-3.0-black.svg)](https://web3.foundation/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 🚀 **AI-powered system for discovering hackathon co-creation partners that create "1 + 1 = 3" value propositions and unlock developer potential during NEAR hackathons and developer events.**

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [System Architecture](#️-system-architecture)
- [Configuration](#-configuration)
- [API Cost Management](#-api-cost-management)
- [Web Dashboard](#-web-dashboard)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🤖 **8-Agent Multi-Agent System**
- **Research Agent**: Web search + NEAR catalog data extraction (OpenAI native or DDGS)
- **Deep Research Agent**: o4-mini deep research (optional, ~$2/project)
- **6x Question Agents**: Parallel analysis using configurable reasoning models
- **Summary Agent**: Synthesis and final recommendations

### ⚡ **Dual Provider Support**
- **OpenAI Provider**: Native web search, GPT-4o + o4-mini reasoning models
- **Local Provider**: LM Studio integration with DDGS web search, free inference
- **Unified API**: LiteLLM abstraction enables seamless provider switching

### 🎯 **Hackathon-Focused Analysis**
- **6 Diagnostic Questions**: Gap-Filler, Proof-Points, Clear Story, Dev-Friendly, Aligned Incentives, Ecosystem Fit
- **Partnership Scoring**: -6 to +6 scale with actionable recommendations
- **Time-Optimized**: Built for hackathon partnership discovery (not general research)

### 💰 **Advanced Cost Management**
- **Real-time API tracking**: Token usage, costs, and model performance
- **Usage analytics**: Session summaries and cost optimization insights
- **Deep research controls**: Cost limits, timeouts, and caching

### 🎨 **Glass UI Dashboard**
- **Modern glassmorphism design** with responsive layout
- **Real-time filtering** and search capabilities
- **Detailed project modals** with comprehensive analysis views
- **Export functionality** for partnership reports

### ⚡ **Performance & Reliability**
- **Parallel execution**: 6x speed improvement with concurrent question analysis
- **Smart caching**: 24-hour freshness with project-specific cache keys
- **Database persistence**: SQLite with WAL mode for concurrent access
- **Graceful failure handling**: Timeout protection and retry logic

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Clone repository
git clone <repository-url>
cd near-catalyst-framework

# 2. Set up environment
echo "OPENAI_API_KEY=your_api_key_here" > .env

# 3. Start with Docker Compose
docker-compose up

# 4. Open dashboard at http://localhost:5000
# 5. Run analysis: docker-compose run --rm near-catalyst-analysis
```

### Option 2: Local Development

```bash
# 1. Clone and setup environment
git clone <repository-url>
cd near-catalyst-framework
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure OpenAI API (get key from https://platform.openai.com/api-keys)
echo "OPENAI_API_KEY=your_api_key_here" > .env

# 4. Run analysis with OpenAI models (requires API key)
python analyze_projects_multi_agent_v2.py --limit 5

# Alternative: Use local models via LM Studio (free, requires setup)
# python analyze_projects_multi_agent_v2.py --provider local --limit 5

# 5. Start web dashboard
python server.py
# Open http://localhost:5000
```

## 🛠️ Installation

### Prerequisites
- **Docker & Docker Compose** (recommended) OR **Python 3.8+**
- **Either**:
  - **OpenAI API key** with GPT-4.1 access (for OpenAI provider)
  - **LM Studio** with compatible models (for local provider - free)
- **For deep research**: Access to o4-mini models (~$2/project)

### Option 1: Docker Installation (Recommended)

#### Quick Setup
```bash
# 1. Clone repository
git clone <repository-url>
cd near-catalyst-framework

# 2. Set up environment (for OpenAI provider)
echo "OPENAI_API_KEY=sk-your-openai-api-key-here" > .env
# Skip this step if using --provider local

# 3. Start services
docker-compose up -d

# 4. Verify installation
docker-compose logs near-catalyst
```

#### Docker Commands
```bash
# Start web dashboard only
docker-compose up near-catalyst

# Run analysis (separate container)
docker-compose run --rm near-catalyst-analysis

# Run custom analysis
docker-compose run --rm near-catalyst-analysis python analyze_projects_multi_agent_v2.py --limit 3 --deep-research

# View logs
docker-compose logs -f near-catalyst

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up --build
```

#### Volume Mounts
- `./data` → `/app/data` - Database persistence
- `./config` → `/app/config` - Benchmark configuration
- `./.env` → `/app/.env` - Environment variables (read-only)

### Option 2: Local Python Installation

#### Environment Setup
1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # OR
   venv\Scripts\activate     # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   # Create .env file with your OpenAI API key
   echo "OPENAI_API_KEY=sk-your-openai-api-key-here" > .env
   ```

### Verify Installation

#### Docker Verification
```bash
# Check container health
docker-compose ps

# Test database functionality
docker-compose exec near-catalyst python server.py --check-db

# Test analysis (requires valid API key)
docker-compose run --rm near-catalyst-analysis python analyze_projects_multi_agent_v2.py --limit 1
```

#### Local Verification
```bash
# Test the system with 1 project
python analyze_projects_multi_agent_v2.py --limit 1

# Check if database was created
ls -la project_analyses_multi_agent.db

# Start dashboard to verify frontend
python server.py --check-db
```

## 🎮 Usage

### Basic Analysis Commands

```bash
# Analyze 5 projects with OpenAI models (default)
python analyze_projects_multi_agent_v2.py --limit 5

# Use local LM Studio models instead of OpenAI
python analyze_projects_multi_agent_v2.py --provider local --limit 5

# High-throughput analysis with custom concurrency
python analyze_projects_multi_agent_v2.py --threads 8 --limit 50

# Force refresh all cached data
python analyze_projects_multi_agent_v2.py --force-refresh --limit 10
```

### Deep Research (Advanced Analysis)

⚠️ **Cost Warning**: Deep research uses OpenAI's o4-mini model at ~$2 per project

```bash
# Option 1: Enable via command line flag (recommended for testing)
python analyze_projects_multi_agent_v2.py --deep-research --limit 1

# Option 2: Enable in config permanently
# Edit config/config.py: DEEP_RESEARCH_CONFIG['enabled'] = True
python analyze_projects_multi_agent_v2.py --limit 3

# Deep research with only general research (skip question analysis)
python analyze_projects_multi_agent_v2.py --deep-research --research-only --limit 1

# Use deep research with local models (if supported)
python analyze_projects_multi_agent_v2.py --provider local --deep-research --limit 1
```

### Database Management

```bash
# List all analyzed projects
python analyze_projects_multi_agent_v2.py --list

# Clear specific projects
python analyze_projects_multi_agent_v2.py --clear project1 project2

# Clear all projects (with confirmation)
python analyze_projects_multi_agent_v2.py --clear all

# Clear cache and re-analyze fresh
python analyze_projects_multi_agent_v2.py --clear all --limit 5
```

### Partial Analysis Options

```bash
# Research only (skip question analysis and summary)
python analyze_projects_multi_agent_v2.py --research-only --limit 5

# Questions only (skip summary generation)
python analyze_projects_multi_agent_v2.py --questions-only --limit 5
```

### Benchmark Management

#### Getting Started with Benchmarks

Before running analysis, set up your partnership evaluation benchmarks:

```bash
# 1. Copy the example template to create your benchmark file
cp config/partnership_benchmarks.example.json config/partnership_benchmarks.json

# 2. Edit the benchmark file with your real partnership evaluations
# WARNING: Never commit real partnership data - keep it in the gitignored file
nano config/partnership_benchmarks.json
```

The example file (`partnership_benchmarks.example.json`) provides:
- **Template structure** for complementary vs competitive examples
- **Scoring guidance** (+4 to +6 strong, 0 to +3 mixed, <0 decline)
- **Framework principles** (gap-filler signs, competitive red flags)
- **Anonymized examples** you can replace with real partnership data

#### Format Management

The system supports both JSON and CSV formats with automatic synchronization:

```bash
# Convert JSON benchmarks to CSV for editing (creates 3 files)
python config/benchmark_converter.py json-to-csv

# Edit CSV files in Excel/Google Sheets, system auto-syncs back to JSON
# - partnership_benchmarks_examples.csv    # Partnership examples
# - partnership_benchmarks_principles.csv  # Framework principles
# - partnership_benchmarks_scoring.csv     # Scoring guidance

# Force specific format usage
python analyze_projects_multi_agent_v2.py --benchmark-format csv --limit 5
python analyze_projects_multi_agent_v2.py --benchmark-format json --limit 5
```

#### Benchmark File Structure

Your benchmark file should contain:

```json
{
  "framework_benchmarks": {
    "complementary_examples": [
      {
        "partner": "NEAR + YourPartner",
        "score": 6,
        "type": "technology category",
        "description": "why it works well"
      }
    ],
    "competitive_examples": [
      {
        "partner": "NEAR + Competitor", 
        "score": -3,
        "type": "conflict type",
        "description": "why it's problematic"
      }
    ]
  },
  "framework_principles": {
    "complementary_signs": ["Gap filler", "Clear value story", ...],
    "competitive_red_flags": ["Direct overlap", "Either/or choice", ...]
  },
  "scoring_guidance": {
    "strong_candidate": {"range": "+4 to +6", "action": "explore MoU"},
    "mixed_fit": {"range": "0 to +3", "action": "negotiate scope"},
    "decline": {"range": "< 0", "action": "decline or redesign"}
  }
}
```

### Complete CLI Reference

```bash
python analyze_projects_multi_agent_v2.py [OPTIONS]

Core Options:
  --provider PROVIDER    AI provider: 'openai' (default) or 'local' (LM Studio)
  --limit N              Process N projects (0 for unlimited, default: all)
  --threads N            Concurrent projects (default: 5, max: 10)
  --force-refresh        Ignore cache, refresh all data

Analysis Control:
  --research-only        Only run research agents (skip questions & summary)
  --questions-only       Only run question agents (skip summary)
  --deep-research        Enable deep research (~$2/project, overrides config)

Database Management:
  --list                 List all projects in database
  --clear [PROJECTS]     Clear projects (specific names or 'all')

Format Control:
  --benchmark-format     Force 'json' or 'csv' benchmark format

Examples:
  # Quick test with OpenAI models
  python analyze_projects_multi_agent_v2.py --limit 3 --threads 1
  
  # Use local models via LM Studio
  python analyze_projects_multi_agent_v2.py --provider local --limit 5
  
  # High-volume batch processing with OpenAI
  python analyze_projects_multi_agent_v2.py --threads 8 --limit 100
  
  # Deep research with local models
  python analyze_projects_multi_agent_v2.py --provider local --deep-research --limit 3
  
  # Database cleanup and fresh analysis
  python analyze_projects_multi_agent_v2.py --clear all --limit 10
```

## 🏗️ System Architecture

### Multi-Agent Pipeline
```
📡 NEAR Catalog API → 🔍 Research Agent → 🔬 Deep Research (Optional) → 
🤖 6x Question Agents (Parallel) → 📊 Summary Agent → 💾 Database →
🌐 Flask API → 🎨 Glass UI Dashboard
```

### Core Components

#### 🤖 **Analysis Agents** (`agents/`)
- **ResearchAgent** ([research_agent.py](agents/research_agent.py)): Web search + NEAR catalog data
- **DeepResearchAgent** ([deep_research_agent.py](agents/deep_research_agent.py)): o4-mini deep research (optional)
- **QuestionAgent** ([question_agent.py](agents/question_agent.py)): 6x parallel analysis using provider-specific reasoning models
- **SummaryAgent** ([summary_agent.py](agents/summary_agent.py)): Final synthesis and recommendations

#### 🎯 **6 Diagnostic Questions Framework**
1. **Gap-Filler?** - Strategic technology gaps NEAR lacks
2. **New Proof-Points?** - Novel use cases unlocked by combination  
3. **Clear Story?** - Simple "Better Together" value proposition
4. **Shared Audience, Different Function?** - Complementary vs competitive
5. **Low-Friction Integration?** - Hackathon-ready developer experience
6. **Hands-On Support?** - Mentors, bounties, technical assistance

#### 💾 **Data Layer** (`database/`)
- **DatabaseManager** ([database_manager.py](database/database_manager.py)): SQLite operations with WAL mode
- **APIUsageTracker** ([usage_tracker.py](database/usage_tracker.py)): Real-time cost tracking and optimization

#### 🎨 **Glass UI Frontend** (`frontend/`)
- **Glassmorphism design** with modern translucent effects
- **Responsive modals** with independent scrolling sections
- **Real-time search/filtering** across all project data
- **Export controls** for partnership reports

#### ⚙️ **Configuration** (`config/`)
- **Centralized config** ([config.py](config/config.py)): All system constants
- **Benchmark management**: JSON/CSV auto-sync for partnership criteria
- **Provider selection**: OpenAI with native web search or local models via LM Studio

### Project Structure
```
near-catalyst-framework/
├── agents/                              # 8-agent multi-agent system
│   ├── research_agent.py               # Agent 1: General research + web search
│   ├── deep_research_agent.py          # Agent 1.5: Optional deep research (o4-mini)
│   ├── question_agent.py               # Agents 2-7: Parallel diagnostic analysis  
│   ├── summary_agent.py                # Agent 8: Final synthesis
│   └── __init__.py                     # Agent exports
├── config/                             # Configuration management
│   ├── config.py                       # Core system configuration
│   ├── benchmark_converter.py          # JSON/CSV format management
│   ├── partnership_benchmarks.json    # Partnership evaluation criteria
│   └── partnership_benchmarks_*.csv   # Auto-synced CSV files
├── database/                           # Data persistence layer
│   ├── database_manager.py             # SQLite operations (WAL mode)
│   ├── usage_tracker.py               # API cost tracking & optimization
│   └── __init__.py                     # Database exports
├── frontend/                           # Glass UI web dashboard
│   ├── index.html                      # Dashboard structure  
│   ├── styles.css                      # Glassmorphism styling
│   └── app.js                          # Interactive functionality
├── docs/                               # Documentation
│   ├── agentic-data-flow.md           # System architecture details
│   ├── partnership-benchmarks.md      # Scoring framework docs
│   └── roadmap.md                      # Development roadmap
├── analyze_projects_multi_agent_v2.py # Main orchestrator & CLI
├── server.py                           # Flask API backend
├── debug_data_flow.py                  # Database debugging utility
├── prompt.md                           # LLM system prompt framework
├── requirements.txt                    # Python dependencies
├── .env                               # Environment variables (not in repo)
└── README.md                          # This file
```

## ⚙️ Configuration

### Environment Variables (`.env`)
```bash
# Required for OpenAI provider: OpenAI API key with GPT-4.1 access
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Database location (defaults to project_analyses_multi_agent.db)
DATABASE_PATH=./data/analyses.db
```

### Local Model Setup (LM Studio)

The system supports local models via LM Studio as an alternative to OpenAI:

#### Prerequisites for Local Models
- **LM Studio** installed and running on default port (1234)
- **Required models downloaded** in LM Studio:
  - `qwen2.5-72b-instruct` or `qwen2.5-coder-32b` (research)
  - `deepseek-r1-distill-qwen-32b` (reasoning)

#### Setup Steps
1. **Install LM Studio** from [https://lmstudio.ai](https://lmstudio.ai)
2. **Download models** via LM Studio's model manager
3. **Start LM Studio server** (port 1234 by default)
4. **Use local provider**:
   ```bash
   python analyze_projects_multi_agent_v2.py --provider local --limit 5
   ```

#### Model Selection Strategy
- **OpenAI Provider**: Uses native web search, consistent performance, costs apply
- **Local Provider**: Uses DDGS web search, free inference, requires powerful hardware

See [docs/lm-studio-setup.md](docs/lm-studio-setup.md) for detailed setup instructions.

### Key Configuration Settings (`config/config.py`)

```python
# Deep Research (o4-mini model, ~$2/project)
DEEP_RESEARCH_CONFIG = {
    'enabled': False,  # Set True to enable by default
    'model': 'o4-mini',        # Standard LiteLLM model name
    'priming_model': 'gpt-4.1', # Model for context priming
    'cost_per_input': 2.00
}

# Question Agent Provider-Specific Configuration  
QUESTION_AGENT_CONFIG = {
    # OpenAI Provider (with native web search)
    'openai': {
        'research_model': {
            'production': 'gpt-4o-search-preview',
            'development': 'gpt-4o-search-preview'
        },
        'reasoning_model': {
            'production': 'o4-mini',
            'development': 'o4-mini'
        }
    },
    # Local Provider (LM Studio + DDGS web search)
    'local': {
        'research_model': {
            'production': 'qwen2.5-72b-instruct',
            'development': 'qwen2.5-coder-32b'
        },
        'reasoning_model': {
            'production': 'deepseek-r1-distill-qwen-32b',
            'development': 'qwen2.5-coder-32b'
        }
    }
}

# Batch Processing
BATCH_PROCESSING_CONFIG = {
    'default_batch_size': 5,  # Concurrent projects
    'max_batch_size': 10      # API rate limit protection
}
```

## 🐳 Docker Usage

### Container Architecture

The application provides two Docker containers:
- **`near-catalyst`**: Web dashboard service (always running)
- **`near-catalyst-analysis`**: Analysis runner service (on-demand)

### Basic Docker Commands

```bash
# Start web dashboard
docker-compose up near-catalyst

# Run analysis in separate container
docker-compose run --rm near-catalyst-analysis

# Both services with auto-restart
docker-compose up -d

# View real-time logs
docker-compose logs -f near-catalyst

# Stop all services
docker-compose down
```

### Running Analysis with Docker

#### Option 1: Docker Compose Analysis Service (Recommended)

```bash
# Run analysis with default settings (5 projects)
docker-compose run --rm near-catalyst-analysis

# Custom analysis parameters
docker-compose run --rm near-catalyst-analysis \
  python analyze_projects_multi_agent_v2.py --limit 10 --threads 3

# Deep research analysis (~$2 per project)
docker-compose run --rm near-catalyst-analysis \
  python analyze_projects_multi_agent_v2.py --deep-research --limit 3

# Force refresh cached data
docker-compose run --rm near-catalyst-analysis \
  python analyze_projects_multi_agent_v2.py --force-refresh --limit 5

# Research only (skip question analysis)
docker-compose run --rm near-catalyst-analysis \
  python analyze_projects_multi_agent_v2.py --research-only --limit 10

# Database management
docker-compose run --rm near-catalyst-analysis \
  python analyze_projects_multi_agent_v2.py --list

docker-compose run --rm near-catalyst-analysis \
  python analyze_projects_multi_agent_v2.py --clear all
```

#### Option 2: Execute in Running Web Container

```bash
# If web service is already running
docker-compose exec near-catalyst python analyze_projects_multi_agent_v2.py --limit 5

# Interactive shell access
docker-compose exec near-catalyst bash
```

#### Option 3: Direct Docker Run

```bash
# One-off analysis
docker run --rm \
  --env-file .env \
  -v "${PWD}/data:/app/data" \
  -v "${PWD}/config:/app/config" \
  near-catalyst-framework python analyze_projects_multi_agent_v2.py --limit 5

# Background analysis job
docker run -d \
  --name analysis-job \
  --env-file .env \
  -v "${PWD}/data:/app/data" \
  -v "${PWD}/config:/app/config" \
  near-catalyst-framework python analyze_projects_multi_agent_v2.py --limit 20

# Check background job
docker logs -f analysis-job
docker wait analysis-job  # Wait for completion
docker rm analysis-job    # Clean up
```

### Development Workflow

```bash
# Build and test locally
docker build -t near-catalyst-framework .

# Run with custom command
docker run --rm -p 5001:5000 \
  -e OPENAI_API_KEY=your_key \
  -v "${PWD}/data:/app/data" \
  near-catalyst-framework python analyze_projects_multi_agent_v2.py --limit 1

# Debug container
docker run -it --rm near-catalyst-framework bash

# Rebuild after code changes
docker-compose up --build
```

### Production Deployment

```bash
# Production with custom host/port
docker run -d \
  --name near-catalyst-prod \
  -p 80:5000 \
  -e OPENAI_API_KEY=your_production_key \
  -v /opt/near-catalyst/data:/app/data \
  -v /opt/near-catalyst/config:/app/config \
  --restart unless-stopped \
  near-catalyst-framework

# Health check
curl http://localhost/api/health

# View production logs
docker logs -f near-catalyst-prod
```

### Docker Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `DATABASE_PATH` | Database file location | `/app/data/project_analyses_multi_agent.db` |
| `FLASK_HOST` | Flask server host | `0.0.0.0` |
| `FLASK_PORT` | Flask server port | `5000` |
| `FLASK_DEBUG` | Enable debug mode | `false` |

### Data Persistence

All analysis data persists in Docker volumes:

```bash
# Data directory structure
./data/
├── project_analyses_multi_agent.db    # SQLite database
└── multi_agent_analyses_*.json        # Export files

# Configuration directory  
./config/
├── partnership_benchmarks.json        # Your benchmark data
├── partnership_benchmarks.example.json # Template
└── *.csv                              # Auto-generated CSV files
```

### Troubleshooting Docker

```bash
# Container won't start
docker-compose logs near-catalyst

# Database permissions
docker-compose exec near-catalyst ls -la /app/data/

# Reset everything
docker-compose down -v
docker-compose up --build

# Check container health
docker-compose ps
docker inspect near-catalyst-framework

# Performance issues
docker stats near-catalyst-framework
```

## 💰 API Cost Management

### Real-Time Usage Tracking

The system tracks all OpenAI API calls with detailed cost analysis:

```bash
# View usage statistics during analysis
python analyze_projects_multi_agent_v2.py --limit 5
# Output shows: tokens used, costs, model performance

# Access detailed usage data
python -c "
from database.usage_tracker import APIUsageTracker
tracker = APIUsageTracker()
tracker.print_session_summary()
"
```

### Cost Optimization Features

- **Input caching**: Reduces duplicate API calls  
- **Context truncation**: Optimizes token usage for reasoning models
- **Model selection**: Provider-specific models optimized for each task
- **Timeout controls**: Prevents runaway costs
- **Deep research limits**: 50 tool calls maximum per analysis

### Budget Management

```python
# Estimated costs (as of January 2025):
# - Standard analysis (GPT-4.1): ~$0.05 per project
# - With reasoning models (o4-mini): ~$0.20 per project  
# - Deep research (o4-mini): ~$2.00 per project
# - Local models: Free (requires LM Studio setup)

# Monitor costs in dashboard:
# - Real-time token counters
# - Cost estimates vs actual
# - Model performance metrics
```

## 🎨 Web Dashboard

### Features

- **🔍 Real-time search**: Filter by name, score, technology, recommendation
- **📊 Multiple views**: Card grid and detailed table layouts  
- **📋 Project details**: Comprehensive modal with research, analysis, and sources
- **📈 Score visualization**: Color-coded partnership recommendations
- **💾 Export controls**: Download filtered results as JSON
- **💰 Cost tracking**: API usage and performance metrics

### Score System & Recommendations

| Score Range | Color | Recommendation | Action |
|-------------|-------|----------------|---------|
| **+4 to +6** | 🟢 Green | **Strong candidate** | Explore MoU/co-marketing |
| **0 to +3** | 🟡 Yellow | **Mixed fit** | Negotiate scope carefully |
| **-1 to -6** | 🔴 Red | **Likely misaligned** | Proceed with caution |

### Dashboard Access

```bash
# Start server
python server.py

# Custom host/port
python server.py --host 0.0.0.0 --port 8080

# Check database before starting
python server.py --check-db

# Debug mode
python server.py --debug
```

## 🛠️ Development

### Adding New Diagnostic Questions

1. **Update configuration**:
   ```python
   # In config/config.py, add to DIAGNOSTIC_QUESTIONS:
   {
       "id": 7,
       "key": "new_question",
       "question": "Your Question?",
       "description": "Detailed description...",
       "search_focus": "keywords for web search..."
   }
   ```

2. **Update frontend scoring** (if needed):
   ```javascript
   // In frontend/app.js, update score calculation
   ```

3. **Test with sample project**:
   ```bash
   python analyze_projects_multi_agent_v2.py --limit 1 --force-refresh
   ```

### Adding New Agents

Follow the established agent pattern:

```python
# agents/your_new_agent.py
class YourNewAgent:
    def __init__(self, client, db_manager=None, usage_tracker=None):
        self.client = client
        self.db_manager = db_manager  
        self.usage_tracker = usage_tracker
    
    def analyze(self, project_name, context):
        # Your agent logic here
        pass
```

### Database Schema

The system uses SQLite with these main tables:

- **project_research**: General research data and sources
- **question_analyses**: Question-specific analysis and scores  
- **final_summaries**: Partnership recommendations and totals
- **api_usage_tracking**: Cost and performance monitoring

### Testing

```bash
# Test core functionality
python analyze_projects_multi_agent_v2.py --limit 1

# Test database operations
python debug_data_flow.py --summary

# Test frontend
python server.py --check-db

# Test deep research (costs money!)
python analyze_projects_multi_agent_v2.py --deep-research --limit 1
```

## 🔍 Troubleshooting

### Common Issues

#### OpenAI API Errors
```bash
# Check API key
echo $OPENAI_API_KEY  # Should show your key

# Test API access
python -c "
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model='gpt-4.1',
    messages=[{'role': 'user', 'content': 'test'}]
)
print('API works!')
"
```

#### Database Issues
```bash
# Check database exists and has data
python server.py --check-db

# Debug database problems
python debug_data_flow.py --summary

# Clear corrupted data
python analyze_projects_multi_agent_v2.py --clear all
```

#### Performance Issues
```bash
# Reduce concurrency
python analyze_projects_multi_agent_v2.py --threads 1 --limit 5

# Disable deep research
# Edit config/config.py: DEEP_RESEARCH_CONFIG['enabled'] = False

# Clear old cache
python analyze_projects_multi_agent_v2.py --force-refresh --limit 5
```

### Error Codes

| Error | Cause | Solution |
|-------|-------|----------|
| `OPENAI_API_KEY not found` | Missing .env file | Create `.env` with API key |
| `Database connection error` | File permissions | Check SQLite file permissions |
| `API rate limit exceeded` | Too many concurrent requests | Reduce `--threads` |
| `Deep research timeout` | Model taking too long | Increase timeout in config |

## 🤝 Contributing

### Development Setup

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/near-catalyst-framework.git
   cd near-catalyst-framework
   ```
3. **Create development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Set up pre-commit hooks** (if available):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Contribution Guidelines

- **Focus**: Improvements to hackathon partnership discovery
- **Code style**: Follow existing patterns, use type hints
- **Testing**: Test with `--limit 1` before submitting PRs
- **Documentation**: Update README for new features
- **Cost awareness**: Consider API costs in new features

### Reporting Issues

Please include:
- Python version and OS
- Full error message  
- Steps to reproduce
- Expected vs actual behavior
- Relevant log output

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🚀 About NEAR Protocol

Built for [NEAR Protocol](https://near.org) hackathon catalyst discovery. NEAR is a carbon-neutral, scalable blockchain platform designed to enable the next generation of decentralized applications.

---

**🎯 Mission**: *Identifying technical collaborators that create exponential value for NEAR developers during hackathons and co-creation events.* 
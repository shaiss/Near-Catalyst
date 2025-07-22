# NEAR Catalyst Framework - Multi-Agent System

A sophisticated AI-powered system for discovering hackathon co-creation partners within the NEAR ecosystem. Uses a multi-agent architecture to identify collaborators that create "1 + 1 = 3" value propositions and unlock developer potential during hackathons and developer events.

## 🚀 Quick Start

```bash
# 1. Setup environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure OpenAI API
echo "openai_key=your_api_key_here" > .env

# 3. Run analysis
python analyze_projects_multi_agent_v2.py --limit 5

# 4. View results
python server.py
# Open http://localhost:5000
```

## Usage

### Basic Analysis
```bash
# Analyze all projects (default: 5 concurrent)
python analyze_projects_multi_agent_v2.py

# Analyze with custom concurrency
python analyze_projects_multi_agent_v2.py --threads 8 --limit 50

# Force refresh all data
python analyze_projects_multi_agent_v2.py --force-refresh --limit 10
```

### Deep Research (Advanced)

The system supports OpenAI's deep research models for comprehensive, analyst-level partnership evaluation. This feature performs extensive web research and analysis but comes with significant costs.

**⚠️ IMPORTANT: Deep research costs ~$2 per project**

#### Setup Deep Research
1. **Option A: Enable via Command Line Flag (Recommended for testing)**:
   ```bash
   # Test deep research without modifying config files
   python analyze_projects_multi_agent_v2.py --deep-research --limit 1
   ```

2. **Option B: Enable in Configuration (For permanent use)**:
   ```python
   # In config/config.py, set:
   DEEP_RESEARCH_CONFIG = {
       'enabled': True,  # Change from False to True
       # ... other settings remain the same
   }
   ```

#### Deep Research Usage
```bash
# Enable deep research via flag (overrides config setting)
python analyze_projects_multi_agent_v2.py --deep-research --limit 3

# Deep research with only general research (no question analysis)
python analyze_projects_multi_agent_v2.py --deep-research --research-only --limit 1

# View deep research status in project list
python analyze_projects_multi_agent_v2.py --list
```

#### What Deep Research Provides
- **Comprehensive Analysis**: Uses o4-mini-deep-research-2025-06-26 model
- **Enhanced Context**: GPT-4.1 primes the deep research with optimized prompts
- **Extensive Sources**: Hundreds of sources analyzed and synthesized
- **Detailed Reports**: Research analyst-level partnership evaluation
- **Better Question Analysis**: Deep research data feeds into question agents for higher quality scoring

#### Cost Management
- **Background Mode**: Long-running analyses use background processing
- **Cached Input**: Reduces costs through input caching when possible
- **Tool Call Limits**: Limited to 50 tool calls per analysis to control costs
- **Database Tracking**: All deep research results stored with cost and performance metrics

### Benchmark Format Management
```bash
# Default behavior: JSON with auto-sync from newer CSV files
python analyze_projects_multi_agent_v2.py

# Force JSON format (still auto-syncs from newer CSV)
python analyze_projects_multi_agent_v2.py --benchmark-format json --limit 5

# Force CSV format (bypasses auto-sync, uses CSV directly)
python analyze_projects_multi_agent_v2.py --benchmark-format csv --limit 5

# Convert JSON benchmarks to CSV for editing
python config/benchmark_converter.py json-to-csv

# Manual conversion of CSV back to JSON (usually not needed due to auto-sync)
python config/benchmark_converter.py csv-to-json

# Check which format is currently preferred
python config/benchmark_converter.py detect
```

### Database Management
```bash
# List all projects in database
python analyze_projects_multi_agent_v2.py --list

# Clear specific projects (by name or slug)
python analyze_projects_multi_agent_v2.py --clear project1 project2 slug3

# Clear all projects (with confirmation)
python analyze_projects_multi_agent_v2.py --clear all
# or
python analyze_projects_multi_agent_v2.py --clear
```

### Partial Analysis
```bash
# Research only (skip question analysis)
python analyze_projects_multi_agent_v2.py --research-only --limit 5

# Questions only (skip summary generation)
python analyze_projects_multi_agent_v2.py --questions-only --limit 5
```

## 📊 Hackathon Catalyst Benchmark Management

The system supports both JSON and CSV formats for hackathon catalyst benchmarks, with automatic format detection and prioritization.

### 🎯 Benchmark Framework

The catalyst evaluation framework uses these benchmark files:

```
config/
├── partnership_benchmarks.json          # Complete catalyst benchmark data
├── partnership_benchmarks.example.json  # Example template
└── partnership_benchmarks_*.csv         # Auto-synced CSV files:
    ├── partnership_benchmarks_examples.csv    # Catalyst examples
    ├── partnership_benchmarks_principles.csv  # Framework principles  
    └── partnership_benchmarks_scoring.csv     # Scoring guidance
```

### Format Priority Logic

1. **JSON Default**: System always uses JSON format (preferred by technical users)
2. **Auto-Sync**: If CSV files are newer than JSON, automatically converts CSV to JSON
3. **Tech User Priority**: If JSON is newer than CSV files, CSV edits are ignored
4. **Manual Override**: Use `--benchmark-format csv` to force CSV usage without auto-sync

### Editing Workflow

#### Option 1: Non-Technical Users (CSV Editing - Recommended)
```bash
# 1. Convert existing JSON to CSV for editing
python config/benchmark_converter.py json-to-csv

# 2. Edit CSV files in Excel, Google Sheets, or any text editor
# - partnership_benchmarks_examples.csv: Add/edit partnership examples
# - partnership_benchmarks_principles.csv: Modify framework principles
# - partnership_benchmarks_scoring.csv: Update scoring guidance

# 3. System automatically detects newer CSV files and syncs to JSON
python analyze_projects_multi_agent_v2.py
# Output: 📝 CSV files are newer than JSON - auto-syncing to JSON...

# No manual conversion needed! CSV changes automatically update JSON
```

#### Option 2: Technical Users (JSON Editing - Direct)
```bash
# Edit the JSON file directly
nano config/partnership_benchmarks.json

# System uses JSON directly (CSV files ignored if JSON is newer)
python analyze_projects_multi_agent_v2.py --benchmark-format json
```

#### Option 3: Force CSV Mode (Override Auto-Sync)
```bash
# Use CSV files without auto-sync to JSON
python analyze_projects_multi_agent_v2.py --benchmark-format csv
```

### CSV File Structure

> **💡 Auto-Sync Note**: When you edit CSV files, the system automatically detects newer timestamps and converts them to JSON. No manual conversion needed!

#### Examples File (`partnership_benchmarks_examples.csv`)
| category | partner | score | type | description | evidence |
|----------|---------|-------|------|-------------|----------|
| complementary | NEAR + Phala | 6 | TEE/confidential computing | perfect complementary partner | [detailed evidence] |
| competitive | NEAR + Solana | -1 | competing L1 | integration showcases tech but competes | [detailed evidence] |

#### Principles File (`partnership_benchmarks_principles.csv`)
| principle_type | principle_text |
|----------------|----------------|
| complementary_signs | Fills a strategic gap rather than overlap NEAR's core |
| competitive_red_flags | Direct product overlap with NEAR's core functionality |

#### Scoring File (`partnership_benchmarks_scoring.csv`)
| category | range | action | examples |
|----------|-------|--------|----------|
| strong_candidate | +4 to +6 | Strong candidate; explore MoU/co-marketing | Phala (+6), Filecoin (+6) |
| mixed_fit | 0 to +3 | Mixed; negotiate scope | Chainlink (+3), ElizaOS (+3) |

## 🏗️ System Architecture

### Multi-Agent Pipeline
```
📡 NEAR Catalog API → 🤖 Research Agent → 🔍 6x Question Agents (Parallel) → 📊 Summary Agent → 💾 Database
                                                        ↓
📈 Glass UI Dashboard ← 🌐 Flask API ← 📋 Comprehensive Export
```

### Core Components

#### 🎯 **Analysis Agents**
- **Research Agent**: Gathers comprehensive project information via web search
- **Question Agents (6x)**: Parallel analysis of diagnostic questions:
  - Q1: Gap-Filler? (Technology gaps NEAR lacks)
  - Q2: New Proof-Points? (Novel use cases/demos)
  - Q3: One-Sentence Story? (Clear value proposition)
  - Q4: Developer-Friendly? (Integration ease)
  - Q5: Aligned Incentives? (Mutual benefit)
  - Q6: Ecosystem Fit? (Target audience match)
- **Summary Agent**: Synthesizes results into final recommendations

#### 💾 **Data Layer**
- **SQLite Database**: WAL mode for concurrent access
- **Project-Specific Caching**: Prevents data poisoning
- **24-Hour Freshness**: Automatic cache invalidation
- **Full Traceability**: Sources, analyses, and scores

#### 🎨 **Glass UI Frontend**
- **Glassmorphism Design**: Modern translucent interface
- **Responsive Layout**: Adapts to all screen sizes
- **Real-Time Filtering**: Search and filter capabilities
- **Detailed Modals**: Comprehensive project analysis views

## 📁 Project Structure

```
json to csv/
├── agents/                              # AI agent modules
│   ├── __init__.py                     # Agent package exports  
│   ├── research_agent.py               # Agent 1: General project research
│   ├── question_agent.py               # Agents 2-7: Question-specific analysis
│   └── summary_agent.py                # Agent 8: Final synthesis
├── config/                             # Configuration package
│   ├── __init__.py                     # Config package exports
│   ├── config.py                       # Main configuration constants
│   ├── partnership_benchmarks.json    # Partnership evaluation benchmarks
│   └── partnership_benchmarks.example.json # Example benchmarks
├── database/                           # Database management
│   ├── __init__.py                     # Database package exports
│   └── database_manager.py             # SQLite operations and exports
├── frontend/                           # Web dashboard (Glass UI)
│   ├── index.html                      # Dashboard structure
│   ├── styles.css                      # Glassmorphism styling
│   └── app.js                          # Frontend logic
├── docs/                               # Documentation
│   ├── agentic-data-flow.md           # System architecture
│   └── partnership-benchmarks.md      # Benchmark documentation
├── analyze_projects_multi_agent_v2.py # Main orchestrator and CLI
├── server.py                          # Flask backend API
├── prompt.md                          # LLM system prompt framework
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

## 🚀 Performance Features

### ⚡ **Parallel Execution**
- **6x Speed Improvement**: Question agents run simultaneously
- **ThreadPoolExecutor**: Optimal resource utilization
- **Timeout Protection**: Graceful failure handling

### 🧠 **Smart Caching**
- **Project-Specific Keys**: Prevents data contamination
- **Freshness Checks**: 24-hour automatic invalidation
- **Thread-Safe Operations**: WAL mode with retry logic

### 🎯 **Comprehensive Analysis**
- **Web Search Integration**: OpenAI's latest search capabilities
- **Full Traceability**: Every source and decision tracked
- **Structured Export**: JSON with complete analysis pipeline

## 🔧 Configuration

### Environment Variables (`.env`)
```bash
openai_key=your_openai_api_key_here
```

### Command Line Options
```bash
python analyze_projects_multi_agent_v2.py [OPTIONS]

Options:
  --limit N             Process only N projects (0 for unlimited)
  --research-only       Only run general research agent
  --questions-only      Only run question agents (skip summary)
  --force-refresh       Ignore cache and refresh all data
```

## 📊 Output

### Database Tables
- **project_research**: General research with sources
- **question_analyses**: Detailed question-by-question analysis
- **final_summaries**: Partnership recommendations and scores

### Export Format
```json
{
  "project_name": "Example Project",
  "total_score": 4,
  "recommendation": "Green-light partnership",
  "general_research": "...",
  "question_analyses": [...],
  "final_summary": "...",
  "created_at": "2024-01-15T10:30:00"
}
```

## 🎨 Glass UI Dashboard

### Features
- **Real-Time Search**: Filter projects by name, score, or recommendation
- **Multiple Views**: Card grid and table layouts
- **Detailed Modals**: Two-column responsive design with independent scrolling
- **Score Visualization**: Color-coded partnership recommendations
- **Export Controls**: Download filtered results

### Score System
- **🟢 Green (4-6)**: Strong partnership candidate
- **🟡 Yellow (0-3)**: Mid-tier fit, worth pursuing
- **🔴 Red (<0)**: Likely misaligned, proceed with caution

## 🔄 Development Workflow

### Adding New Diagnostic Questions
1. Update `config/config.py` → `DIAGNOSTIC_QUESTIONS`
2. Restart analysis for fresh evaluation
3. Update frontend scoring logic if needed

### Modifying Analysis Logic
1. Edit respective agent in `agents/` directory
2. Maintain stateless design patterns
3. Test parallel execution scenarios

### Enhancing Frontend
1. Follow Glass UI patterns in `frontend/styles.css`
2. Ensure Safari compatibility with `-webkit-` prefixes
3. Test responsive design across devices

## 🛠️ Dependencies

### Required Packages
```bash
pip install openai requests flask flask-cors python-dotenv
```

### API Requirements
- **OpenAI API**: GPT-4.1 model with web search capabilities
- **NEAR Catalog API**: Public API for project data

## 🎯 Scoring Framework

Each hackathon catalyst candidate is evaluated on 6 diagnostic questions, with scores ranging from -1 (weak) to +1 (strong):

1. **Gap-Filler**: Does it fill technology gaps NEAR lacks?
2. **New Proof-Points**: Does it enable novel use cases/demos?
3. **Clear Story**: Is there a compelling value proposition?
4. **Developer-Friendly**: How easy is integration?
5. **Aligned Incentives**: Is it mutually beneficial?
6. **Ecosystem Fit**: Does it match NEAR's audience?

**Total Score Interpretation**:
- **4-6**: 🟢 Green-light catalyst partnership (hackathon co-creation)
- **0-3**: 🟡 Mid-tier fit (worth pursuing with support)
- **<0**: 🔴 Likely misaligned (proceed with caution)

## 🔍 Troubleshooting

### SQLite Threading Errors
- Each thread creates its own database connection
- Use WAL mode for concurrent access
- Implement retry logic with exponential backoff

### API Rate Limits
- Built-in timeouts and delays between requests
- Graceful failure handling for individual agents
- Comprehensive error logging

### Frontend Issues
- Ensure `-webkit-backdrop-filter` for Safari
- Test glassmorphism effects across browsers
- Verify responsive modal behavior

## 📈 Future Enhancements

- **Machine Learning Models**: Predictive partnership success scoring
- **Integration APIs**: Direct connections to partner platforms
- **Advanced Visualizations**: Network graphs and trend analysis
- **Automated Reporting**: Scheduled analysis and notifications

---

**Built for NEAR Protocol Hackathon Catalyst Discovery**  
*Identifying technical collaborators that create exponential value* 🚀 
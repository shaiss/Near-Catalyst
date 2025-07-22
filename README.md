# NEAR Partnership Analysis - Multi-Agent System

A sophisticated AI-powered system for analyzing potential technical partners for NEAR Protocol hackathons and developer events. Uses a multi-agent architecture to evaluate partnerships that create "1 + 1 = 3" value propositions.

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
📦 NEAR Partnership Analysis
├── 🎯 analyze_projects_multi_agent_v2.py  # Main orchestrator
├── 🏗️ agents/                            # AI agent modules
│   ├── config.py                         # Configuration constants
│   ├── research_agent.py                 # General research
│   ├── question_agent.py                 # Question-specific analysis
│   └── summary_agent.py                  # Final synthesis
├── 💾 database/                          # Database management
│   └── database_manager.py               # SQLite operations
├── 🎨 frontend/                          # Glass UI dashboard
│   ├── index.html                        # Dashboard structure
│   ├── styles.css                        # Glassmorphism styling
│   └── app.js                            # Frontend logic
├── 🌐 server.py                          # Flask backend API
├── 📋 prompt.md                          # LLM framework
├── 🔧 .env                               # API keys
└── 📚 archive/                           # Legacy files
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
1. Update `agents/config.py` → `DIAGNOSTIC_QUESTIONS`
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

Each partnership candidate is evaluated on 6 diagnostic questions, with scores ranging from -1 (weak) to +1 (strong):

1. **Gap-Filler**: Does it fill technology gaps NEAR lacks?
2. **New Proof-Points**: Does it enable novel use cases/demos?
3. **Clear Story**: Is there a compelling value proposition?
4. **Developer-Friendly**: How easy is integration?
5. **Aligned Incentives**: Is it mutually beneficial?
6. **Ecosystem Fit**: Does it match NEAR's audience?

**Total Score Interpretation**:
- **4-6**: 🟢 Green-light partnership (strategic collaboration)
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

**Built for NEAR Protocol Partnership Development**  
*Identifying technical collaborators that create exponential value* 🚀 
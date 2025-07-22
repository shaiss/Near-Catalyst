# NEAR Protocol Partnership Analysis

A sophisticated multi-agent system for analyzing potential partnerships between NEAR Protocol and ecosystem projects using AI-powered research and evaluation.

## 🚀 Overview

This project implements an 8-agent architecture that comprehensively evaluates partnership opportunities using the "Framework for Choosing Complementary Technical Partners." Each partnership is scored across 6 diagnostic questions to identify "1 + 1 = 3" value propositions.

## 🏗️ Architecture

### Multi-Agent System

1. **Research Agent** - Conducts comprehensive project research using web search
2. **Gap-Filler Agent** (Q1) - Analyzes technology gaps NEAR lacks
3. **Proof-Points Agent** (Q2) - Evaluates new use cases and demos
4. **Clear Story Agent** (Q3) - Assesses value proposition clarity
5. **Developer-Friendly Agent** (Q4) - Reviews integration ease and learning curve
6. **Aligned Incentives Agent** (Q5) - Examines mutual benefits and competition
7. **Ecosystem Fit Agent** (Q6) - Matches target audience alignment
8. **Summary Agent** - Synthesizes findings into final recommendations

### Scoring Framework

Each question receives a score:
- **+1**: Strong/Yes
- **0**: Neutral/Unsure  
- **-1**: Weak/No

**Final Recommendations:**
- **+4 to +6**: Green-light partnership (Strong strategic collaboration candidate)
- **0 to +3**: Mid-tier fit (Worth pursuing with integration support)
- **< 0**: Likely misaligned (Proceed with caution)

## 📊 Features

- **Web Search Integration**: Real-time research using OpenAI's web search capabilities
- **Glass UI Dashboard**: Beautiful, modern interface with glassmorphism design
- **Interactive Filtering**: Filter by score range, search by project name
- **Detailed Project Views**: Modal popups with full analysis breakdown
- **Project-Specific Caching**: Prevents data poisoning between analyses
- **Full Traceability**: Every conclusion linked to sources and evidence
- **Confidence Scoring**: Each agent provides confidence levels
- **Comprehensive Export**: JSON exports with complete audit trails
- **Flexible Execution**: Research-only, questions-only, or full analysis modes

## 🛠️ Setup

### Prerequisites

- Python 3.8+
- OpenAI API key with GPT-4.1 access

### Installation

1. Clone and navigate to the project:
```bash
git clone <repository-url>
cd json-to-csv
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file with your OpenAI key:
```bash
echo "openai_key=your_openai_api_key_here" > .env
```

## 📖 Usage

### Multi-Agent Analysis

```bash
# Test with 3 projects (recommended for first run)
python analyze_projects_multi_agent.py --limit 3

# Research phase only (faster, cheaper)
python analyze_projects_multi_agent.py --limit 5 --research-only

# Question analysis only (skip summary)
python analyze_projects_multi_agent.py --limit 5 --questions-only

# Force refresh cached data
python analyze_projects_multi_agent.py --limit 3 --force-refresh

# Process all projects (use with caution - expensive)
python analyze_projects_multi_agent.py --limit 0
```

### Glass UI Dashboard

After running the analysis, start the beautiful web dashboard:

```bash
# Start the dashboard server
python server.py

# Custom host/port
python server.py --host 0.0.0.0 --port 8080

# Debug mode
python server.py --debug

# Check database status
python server.py --check-db
```

Then open your browser to `http://localhost:5000` to view the interactive dashboard.

### Command Line Options

- `--limit N`: Process N projects (0 = no limit)
- `--research-only`: Only conduct general research
- `--questions-only`: Skip final summary generation
- `--force-refresh`: Ignore cache and refresh all data

## 📁 Project Structure

```
.
├── analyze_projects_multi_agent.py    # Main multi-agent script
├── server.py                          # Flask dashboard server
├── frontend/                          # Glass UI dashboard
│   ├── index.html                     # Main dashboard page
│   ├── styles.css                     # Glass UI styling
│   └── app.js                         # Dashboard JavaScript
├── prompt.md                          # Partnership evaluation framework
├── project_analyses_multi_agent.db    # SQLite database with full traceability
├── multi_agent_analyses_*.json        # Exported analysis results
├── archive/                           # Legacy files and scripts
├── venv/                              # Python virtual environment
├── README.md                          # This file
└── .env                              # Environment variables (not in git)
```

## 🗄️ Database Schema

### Tables

1. **project_research**: General project information and web search results
2. **question_analyses**: Question-specific research and scoring (with caching)
3. **final_summaries**: Comprehensive partnership recommendations

### Caching Strategy

- Project-specific cache keys prevent data contamination
- 24-hour cache expiration for fresh analysis
- Granular caching per question for efficiency

## 📈 Output Format

### JSON Export Structure

```json
{
  "project_name": "Example Project",
  "slug": "example-project",
  "total_score": 4,
  "recommendation": "Green-light partnership...",
  "general_research": "Comprehensive project overview...",
  "general_sources": [{"url": "...", "title": "..."}],
  "question_analyses": [
    {
      "question_id": 1,
      "question_key": "gap_filler",
      "analysis": "Detailed analysis...",
      "score": 1,
      "confidence": "High",
      "sources": [...]
    }
  ],
  "final_summary": "Partnership analysis summary...",
  "created_at": "2025-01-07T19:41:58"
}
```

## 💰 Cost Considerations

- **Research Agent**: ~$0.01-0.05 per project (web search + GPT-4.1)
- **Question Agents**: ~$0.005-0.02 per question (6 total)
- **Summary Agent**: ~$0.01 per project
- **Total**: ~$0.08-0.18 per project

**Cost Optimization:**
- Use `--research-only` for initial exploration
- Leverage caching for repeated analyses
- Set appropriate `--limit` for budget control

## 🔧 Configuration

### OpenAI Models Used

- **Web Search**: GPT-4.1 with web search preview
- **Analysis**: GPT-4.1 for consistency and quality
- **Fallback**: Basic project info if web search fails

### Rate Limiting

- 1-second delay between question agents
- 2-second delay between projects
- 3-second delay after complete analysis

## 🐛 Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   ```bash
   ERROR: OpenAI key not found in .env file
   ```
   - Ensure `.env` file exists with `openai_key=your_key`

2. **Database Lock Error**
   - Close any open database connections
   - Restart the script

3. **Rate Limit Errors**
   - Increase delays in the script
   - Use smaller `--limit` values

### Debug Mode

Enable verbose logging by modifying the script:
```python
# Add at the top of main()
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Submit a pull request with detailed description

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Projects

- [NEAR Protocol](https://near.org/) - The blockchain platform
- [NEAR Catalog](https://nearcatalog.org/) - Project discovery platform
- [OpenAI API](https://openai.com/api/) - AI capabilities

## 📞 Support

For questions or issues:
1. Check the troubleshooting section above
2. Review the `archive/` folder for legacy implementations
3. Open an issue with detailed error messages and steps to reproduce

---

**Built with ❤️ for the NEAR Protocol ecosystem** 
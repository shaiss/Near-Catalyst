# NEAR Catalyst Framework: Question Analysis Storage Bug Fix

## 🎯 **ISSUE SUMMARY**
The NEAR Catalyst multi-agent system has a critical storage bug in the QuestionAgent that prevents question analysis data from being saved to the database. While the analysis logic works correctly, the results are not persisted, leading to:
- Empty question_analyses arrays in exports
- 0/6 scores instead of real scores  
- Missing detailed analysis data
- Data integrity issues

## 🚨 **SPECIFIC ERROR MESSAGES**
```
⚠️ Cache storage failed: unrecognized token: "{"
❌ Analysis failed for Q1: QuestionAgent._store_cache() missing 1 required positional argument: 'result_data'
❌ Analysis failed for Q2: QuestionAgent._store_cache() missing 1 required positional argument: 'result_data'
[... repeated for all 6 questions]
```

## 📁 **KEY FILES TO EXAMINE**

### **Primary File (Contains the Bug):**
- `agents/question_agent.py` - QuestionAgent class with broken `_store_cache()` method

### **Supporting Files:**
- `database/database_manager.py` - Database operations and table schemas
- `analyze_projects_multi_agent_v2.py` - Main orchestrator (for context)
- `config/config.py` - Configuration settings (for context)

## 🔍 **TECHNICAL DETAILS**

### **What's Working:**
- ✅ Multi-agent workflow (ResearchAgent → 6x QuestionAgent → SummaryAgent)
- ✅ OpenAI provider with web search (`gpt-4o-search-preview`)
- ✅ Question analysis generation (logic works)
- ✅ Final summary generation
- ✅ General research storage
- ✅ Cost tracking via LiteLLM

### **What's Broken:**
- ❌ `QuestionAgent._store_cache()` method signature/implementation
- ❌ Question analysis results not stored in `question_analysis` table
- ❌ JSON serialization issues ("unrecognized token" error)
- ❌ Cache key-based storage mechanism

### **Expected Database Schema:**
```sql
CREATE TABLE question_analysis (
    cache_key TEXT PRIMARY KEY,
    result_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### **Expected Question Analysis Data Structure:**
```json
{
  "question_id": 1,
  "question": "Gap-Filler?",
  "analysis": "Detailed analysis text...",
  "score": 1,  // +1, 0, or -1
  "confidence": "High",  // High, Medium, Low
  "research_data": "Question-specific research...",
  "sources": ["url1", "url2"],
  "cached": false,
  "cost": 0.0038
}
```

## 🎯 **SPECIFIC FIX NEEDED**

### **Primary Issue:**
The `_store_cache()` method in `agents/question_agent.py` has incorrect parameters or implementation that's causing:
1. **Missing required argument error** - method signature doesn't match call sites
2. **JSON serialization failure** - "unrecognized token" suggests malformed JSON
3. **Data not persisting** - question analyses aren't reaching the database

### **Investigation Focus:**
1. **Method Signature**: Check `_store_cache()` method definition vs. how it's being called
2. **JSON Handling**: Ensure proper JSON serialization before database storage  
3. **Cache Key Generation**: Verify cache keys are being generated correctly
4. **Database Interaction**: Confirm database_manager methods are working

### **Success Criteria:**
- ✅ Question analyses stored in `question_analysis` table
- ✅ No cache storage error messages
- ✅ Exported JSON contains populated `question_analyses` arrays
- ✅ Final scores reflect actual question analysis results (not 0/6)

## 🧪 **TEST COMMAND**
After fixing, test with:
```bash
# Clear database and test
sqlite3 project_analyses_multi_agent.db "DELETE FROM question_analysis; DELETE FROM final_summaries; DELETE FROM project_research;"
source venv/bin/activate && python3 analyze_projects_multi_agent_v2.py --provider openai --limit 1

# Verify fix
sqlite3 project_analyses_multi_agent.db "SELECT COUNT(*) FROM question_analysis;"
# Should return 6 (one for each question)
```

## 🗂️ **SYSTEM CONTEXT**
- **Framework**: NEAR Partnership Analysis multi-agent system
- **Architecture**: 8-agent swarm (1 Research + 6 Questions + 1 Summary)
- **Database**: SQLite with WAL mode
- **Models**: OpenAI (gpt-4o-search-preview, o4-mini) + Local LM Studio support
- **Caching**: MD5-based cache keys for project-specific data isolation

## 🚀 **EXPECTED OUTCOME**
After the fix, running the analysis should:
1. Generate question analyses (already working)
2. Store them in the database (currently broken)
3. Include them in final exports (currently empty)
4. Show proper scores in summaries (currently 0/6)
5. Enable proper framework compliance validation

The multi-agent flow and web search integration are working correctly - this is purely a data persistence issue in the QuestionAgent caching mechanism. 
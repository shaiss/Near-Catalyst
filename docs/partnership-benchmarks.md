# Partnership Framework Benchmarks

## Overview

The NEAR Partnership Analysis system uses external benchmark examples to evaluate potential partners against proven complementary and competitive cases. **Real partnership evaluations are treated as sensitive internal data** and kept in gitignored files, similar to environment variables.

## ⚠️ **Important: Sensitive Data Handling**

- **Real partnership examples are PRIVATE** - never commit actual evaluations to git
- Use **generic placeholder examples** in committed code
- Store **actual evaluations** in the gitignored `partnership_benchmarks.json` file
- Think of this like `.env` files - the structure is public, the data is private

## File Structure

```
agents/
├── partnership_benchmarks.json          # Private evaluations (gitignored - like .env)
├── partnership_benchmarks.example.json  # Generic template (committed)
└── config.py                           # Loader functions
```

## Configuration

### 1. Setup Private Benchmark File

Copy the example file and replace with your **real, private evaluations**:

```bash
cp agents/partnership_benchmarks.example.json agents/partnership_benchmarks.json
# Edit partnership_benchmarks.json with REAL evaluations (this file is gitignored)
```

### 2. Add Your Actual Partnership Evaluations

Edit `agents/partnership_benchmarks.json` with your **real internal assessments**:

```json
{
  "framework_benchmarks": {
    "complementary_examples": [
      {
        "partner": "NEAR + [Actual Partner Name]",
        "score": 6,
        "type": "actual partnership type",
        "description": "your real evaluation"
      }
    ],
    "competitive_examples": [
      {
        "partner": "NEAR + [Actual Competitor]", 
        "score": -4,
        "type": "actual competition type",
        "description": "why it failed/was misaligned"
      }
    ]
  }
}
```

### 3. Framework Principles (Based on 3-1_framework.md)

Update principles based on the "1+1=3" framework:

```json
{
  "framework_principles": {
    "complementary_signs": [
      "Fills a strategic gap rather than overlap NEAR's core",
      "Unlocks use-cases that neither side can deliver alone",
      "Clear 'Better Together' story (one sentence, no diagrams)",
      "Same developers, different workflow functions",
      "Low-friction integration (wire together in hours)",
      "Hands-on support (mentors, bounties, tooling)"
    ],
    "competitive_red_flags": [
      "Direct product overlap with NEAR's core functionality",
      "Creates 'either/or' dilemma for developers",
      "'Logo on a slide' partnerships (purely transactional)",
      "Conflicting technical standards or integration friction"
    ]
  }
}
```

## Usage in Prompts

The system automatically loads your private benchmarks and formats them for prompts:

```python
from agents.config import format_benchmark_examples_for_prompt, get_framework_principles

# In analysis prompts - uses your private evaluations
benchmark_examples = format_benchmark_examples_for_prompt()
framework_principles = get_framework_principles()
```

## Benefits

- ✅ **Privacy Protection**: Real evaluations never committed to git
- ✅ **Clean Prompts**: No hardcoded examples cluttering agent code
- ✅ **Easy Updates**: Modify private evaluations without touching code  
- ✅ **Consistent Framework**: All agents use same evaluation examples
- ✅ **Fallback Protection**: Generic examples if private file is missing

## Framework Alignment

Based on the "1+1=3" Partnership Framework, the system evaluates:

### **Ideal Complementary Partners (Force Multipliers)**
- **Synergistic Technology**: Fills strategic gaps, unlocks new use cases
- **Aligned Developer Ecosystem**: Same audience, different workflow functions  
- **Clear Immediate Value**: Plug-and-play integration, hands-on support

### **Competitive/Misaligned Partners (Red Flags)**
- **Direct Product Overlap**: Either/or choices, competing functionality
- **Conflicting Standards**: Integration friction, technical misalignment
- **Vague Value**: "Logo on slide" partnerships with no substance

## Updating Your Private Benchmarks

As you evaluate new partnerships:

1. **Add successful partnerships** to `complementary_examples` in your private file
2. **Add problematic partnerships** to `competitive_examples` with lessons learned
3. **Update framework principles** based on real-world experience
4. **Keep examples current** - remove outdated evaluations

## Security Notes

- ✅ `partnership_benchmarks.json` is gitignored (like `.env` files)
- ✅ Generic examples in committed code protect sensitive evaluations
- ✅ Private file created automatically with fallback data if missing
- ⚠️ **Never commit real partnership names or scores** to version control

This approach keeps your competitive intelligence private while maintaining a functional, framework-aligned analysis system. 
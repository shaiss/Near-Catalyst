# NEAR Catalyst Framework - Agentic Data Flow

## 🎯 System Overview

Our system implements an **8-agent swarm** that collaboratively discovers hackathon catalyst opportunities. Each agent has a specialized role and operates with specific data inputs/outputs to identify co-creation partners that unlock developer potential during NEAR hackathons and developer events.

## 🔄 High-Level Data Flow

```mermaid
graph TD
    A[Project Name: 'ref-finance'] --> B[Fetch Project Details]
    B --> C[Extract Display Name: 'Rhea Finance']
    C --> D[Check Cache & Freshness]
    D -->|Fresh Data Exists| E[Skip Analysis]
    D -->|Stale/No Data| F[Initialize Agent Swarm]
    
    F --> G[Agent 1: Research Agent]
    G --> H[Agents 2-7: Parallel Question Analysis]
    H --> I[Agent 8: Summary Agent]
    I --> J[Store Results & Export]
    
    E --> K[Dashboard Display]
    J --> K
```

## 📊 Detailed Agentic Flow

### Phase 1: Project Initialization & Data Extraction

```mermaid
sequenceDiagram
    participant Main as Main Orchestrator
    participant API as NEAR Catalog API
    participant DB as Database Manager
    participant Cache as Cache System

    Main->>API: GET /project?pid=ref-finance
    API-->>Main: Project JSON with profile data
    
    Note over Main: Extract name: "Rhea Finance"<br/>from profile.name field
    
    Main->>DB: Check existing analysis
    DB->>Cache: Query final_summaries table
    Cache-->>DB: Return analysis timestamp
    DB-->>Main: Analysis age: 12 hours (fresh)
    
    alt Analysis is fresh (< 24h)
        Main->>Main: Skip analysis, return cached
    else Analysis is stale or missing
        Main->>Main: Proceed to agent swarm
    end
```

### Phase 2: Multi-Agent Swarm Initialization

```mermaid
graph LR
    subgraph "Agent Swarm Initialization"
        A[Project Data] --> B[Research Agent]
        A --> C[Question Agent Pool]
        A --> D[Summary Agent]
        
        B --> E[OpenAI Client + Web Search]
        C --> F[6x Parallel Workers]
        D --> G[Synthesis Engine]
    end
    
    subgraph "Resource Allocation"
        H[ThreadPoolExecutor<br/>max_workers=6] --> F
        I[Database Connections<br/>Per Thread] --> F
        J[Cache Keys<br/>Project-Specific] --> F
    end
```

### Phase 3: Agent 1 - Research Agent Deep Dive

```mermaid
sequenceDiagram
    participant Orch as Main Orchestrator
    participant RA as Research Agent
    participant OpenAI as OpenAI API
    participant DB as Database

    Orch->>RA: analyze("Rhea Finance", project_data)
    
    Note over RA: Construct comprehensive<br/>research prompt with known data:<br/>- Tagline: "DeFi platform"<br/>- Tags: ["DeFi", "Trading"]<br/>- Phase: "Mainnet"
    
    RA->>OpenAI: responses.create() with web_search_preview
    OpenAI-->>RA: Research content + URL sources
    
    Note over RA: Extract sources from annotations:<br/>- URLs, titles, indices<br/>- Comprehensive project overview
    
    RA->>DB: Store general research + sources
    RA-->>Orch: Return research_result{<br/>content, sources, success<br/>}
```

### Phase 4: Agents 2-7 - Parallel Question Analysis Swarm

```mermaid
graph TD
    subgraph "Parallel Question Agent Execution"
        A[Research Result] --> B[ThreadPoolExecutor]
        
        B --> C1[Q1: Gap-Filler Agent]
        B --> C2[Q2: Proof-Points Agent]
        B --> C3[Q3: Clear Story Agent]
        B --> C4[Q4: Developer-Friendly Agent]
        B --> C5[Q5: Aligned Incentives Agent]
        B --> C6[Q6: Ecosystem Fit Agent]
        
        C1 --> D1[Thread 1: DB Connection]
        C2 --> D2[Thread 2: DB Connection]
        C3 --> D3[Thread 3: DB Connection]
        C4 --> D4[Thread 4: DB Connection]
        C5 --> D5[Thread 5: DB Connection]
        C6 --> D6[Thread 6: DB Connection]
        
        D1 --> E1[Cache Check + Analysis]
        D2 --> E2[Cache Check + Analysis]
        D3 --> E3[Cache Check + Analysis]
        D4 --> E4[Cache Check + Analysis]
        D5 --> E5[Cache Check + Analysis]
        D6 --> E6[Cache Check + Analysis]
        
        E1 --> F[Results Collection]
        E2 --> F
        E3 --> F
        E4 --> F
        E5 --> F
        E6 --> F
    end
```

#### Individual Question Agent Flow

```mermaid
sequenceDiagram
    participant Pool as ThreadPoolExecutor
    participant QA as Question Agent (Q1)
    participant DB as Thread DB Connection
    participant OpenAI as OpenAI API
    participant Cache as Project Cache

    Pool->>QA: analyze(project, research, Q1_config, db_path)
    
    QA->>DB: Connect with WAL mode
    QA->>Cache: Check cache_key: md5("rhea finance_gap_filler")
    Cache-->>QA: No cached analysis found
    
    Note over QA: Construct Q1-specific prompt:<br/>"Does Rhea Finance fill gaps NEAR lacks?"<br/>Focus: DeFi capabilities, trading infrastructure
    
    QA->>OpenAI: responses.create() with targeted web search
    OpenAI-->>QA: Q1-specific research + sources
    
    QA->>OpenAI: chat.completions.create() for analysis
    OpenAI-->>QA: Analysis with SCORE: +1, CONFIDENCE: High
    
    QA->>DB: Cache results with retry logic
    QA->>DB: Commit transaction
    QA->>DB: Close connection
    
    QA-->>Pool: Return Q1 result{<br/>question_id: 1,<br/>score: +1,<br/>confidence: "High",<br/>analysis: "...",<br/>sources: [...]<br/>}
```

### Phase 5: Parallel Execution Coordination

```mermaid
gantt
    title Question Agent Execution Timeline
    dateFormat X
    axisFormat %s
    
    section Agent Execution
    Q1 Gap-Filler      :active, q1, 0, 35s
    Q2 Proof-Points    :active, q2, 0, 32s
    Q3 Clear Story     :active, q3, 0, 28s
    Q4 Developer-Friendly :active, q4, 0, 40s
    Q5 Aligned Incentives :active, q5, 0, 30s
    Q6 Ecosystem Fit   :active, q6, 0, 38s
    
    section Results Collection
    Sort by Question ID :milestone, 42s, 0s
    Validation Complete :milestone, 43s, 0s
```

### Phase 6: Agent 8 - Summary Agent Synthesis

```mermaid
sequenceDiagram
    participant Orch as Main Orchestrator
    participant SA as Summary Agent
    participant OpenAI as OpenAI API
    participant Config as Score Thresholds

    Orch->>SA: analyze(project, research, question_results, prompt)
    
    Note over SA: Aggregate scores:<br/>Q1: +1, Q2: +1, Q3: 0<br/>Q4: +1, Q5: +1, Q6: +1<br/>Total: 5/6
    
    SA->>Config: Check score against thresholds
    Config-->>SA: Score 5 >= 4 → "Green-light catalyst partnership"
    
    Note over SA: Construct synthesis prompt with:<br/>- General research context<br/>- All question analyses<br/>- Score breakdown<br/>- Recommendation framework
    
    SA->>OpenAI: chat.completions.create() with system prompt
    OpenAI-->>SA: Comprehensive hackathon catalyst summary
    
    SA-->>Orch: Return summary_result{<br/>summary: "...",<br/>total_score: 5,<br/>recommendation: "Green-light catalyst partnership. Strong candidate for hackathon co-creation.",<br/>success: true<br/>}
```

### Phase 7: Data Persistence & Export Pipeline

```mermaid
graph TD
    subgraph "Database Storage"
        A[Summary Result] --> B[final_summaries table]
        C[Question Results] --> D[question_analyses table]
        E[Research Data] --> F[project_research table]
    end
    
    subgraph "Export Generation"
        B --> G[Comprehensive Query]
        D --> G
        F --> G
        G --> H[JSON Export with Full Traceability]
    end
    
    subgraph "Frontend API"
        H --> I[Flask Server]
        I --> J[Glass UI Dashboard]
        J --> K[Real-time Filtering & Search]
    end
```

## 🔄 Cache Management & Data Poisoning Prevention

```mermaid
graph LR
    subgraph "Project-Specific Caching"
        A[Project: "Rhea Finance"] --> B[Question: "gap_filler"]
        B --> C[Generate Cache Key]
        C --> D[MD5: "rhea finance_gap_filler"]
        D --> E[Unique Cache Entry]
    end
    
    subgraph "Different Project"
        F[Project: "NEAR Intents"] --> G[Question: "gap_filler"]
        G --> H[Generate Cache Key]
        H --> I[MD5: "near intents_gap_filler"]
        I --> J[Separate Cache Entry]
    end
    
    E -.-> K[No Data Contamination]
    J -.-> K
```

## ⚡ Performance Optimizations

### Thread-Safe Database Operations

```mermaid
sequenceDiagram
    participant T1 as Thread 1 (Q1)
    participant T2 as Thread 2 (Q2)
    participant WAL as SQLite WAL Mode
    participant DB as Database File

    par Concurrent Writes
        T1->>WAL: Write Q1 analysis
        T2->>WAL: Write Q2 analysis
    end
    
    WAL->>DB: Atomic commit of both writes
    
    Note over WAL: WAL mode enables:<br/>- Multiple concurrent readers<br/>- One writer at a time<br/>- No blocking between threads
```

### Error Handling & Retry Logic

```mermaid
graph TD
    A[Question Agent Execution] --> B{Database Write}
    B -->|Success| C[Return Result]
    B -->|Database Locked| D[Retry Logic]
    
    D --> E[Attempt 1: 0.1s delay]
    E -->|Fail| F[Attempt 2: 0.2s delay]
    F -->|Fail| G[Attempt 3: 0.3s delay]
    G -->|Success| C
    G -->|Final Fail| H[Log Error & Continue]
    
    H --> I[Return Error Result]
    I --> J[Graceful Degradation]
```

## 📊 Data Structures & Interfaces

### Question Agent Result Format

```json
{
  "question_id": 1,
  "research_data": "Comprehensive research about DeFi gaps...",
  "sources": [
    {
      "url": "https://rhea.finance/docs",
      "title": "Rhea Finance Documentation",
      "index": 1
    }
  ],
  "analysis": "ANALYSIS: Rhea Finance provides sophisticated DeFi trading tools that NEAR currently lacks...\nSCORE: +1 (Strong Yes)\nCONFIDENCE: High",
  "score": 1,
  "confidence": "High",
  "cached": false
}
```

### Final Summary Export Format

```json
{
  "project_name": "Rhea Finance",
  "slug": "ref-finance",
  "total_score": 5,
  "recommendation": "Green-light catalyst partnership. Strong candidate for hackathon co-creation.",
  "general_research": "Comprehensive overview...",
  "general_sources": [...],
  "question_analyses": [
    {
      "question_id": 1,
      "question_key": "gap_filler",
      "analysis": "...",
      "score": 1,
      "confidence": "High",
      "sources": [...]
    }
  ],
  "final_summary": "Hackathon catalyst discovery summary...",
  "created_at": "2024-01-15T10:30:00"
}
```

## 🎯 Agent Communication Patterns

### Stateless Agent Design

```mermaid
graph LR
    subgraph "Agent Independence"
        A[Input Data] --> B[Agent Processing]
        B --> C[Output Data]
        
        D[No Shared State]
        E[No Agent-to-Agent Communication]
        F[Pure Functions]
    end
    
    subgraph "Orchestrator Coordination"
        G[Main Orchestrator] --> H[Agent 1]
        G --> I[Agents 2-7 Parallel]
        G --> J[Agent 8]
        
        H --> K[Results Collection]
        I --> K
        J --> L[Final Output]
    end
```

### Error Propagation & Graceful Degradation

```mermaid
graph TD
    A[Agent Execution] --> B{Success?}
    B -->|Yes| C[Normal Result]
    B -->|Timeout| D[Timeout Result]
    B -->|Error| E[Error Result]
    
    C --> F[Results Array]
    D --> F
    E --> F
    
    F --> G[Summary Agent]
    G --> H[Handles Partial Data]
    H --> I[Generates Report with Caveats]
```

This agentic swarm architecture ensures **fault tolerance**, **performance optimization**, and **comprehensive analysis** while maintaining **data integrity** and **traceability** throughout the entire pipeline.

---

**Key Innovation**: The system transforms a single complex analysis task into a coordinated swarm of specialized agents, each optimized for specific aspects of partnership evaluation, resulting in more thorough, faster, and more reliable assessments. 
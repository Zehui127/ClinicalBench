# Project Principles

## Core Problems: Tools Definition + Evaluation Criteria

### 1. Build Better User Persona
- Remove unrelated user info from task definitions — only include medically relevant patient details
- Better mapping from disease to symptom using existing databases (e.g., PrimeKG, clinical knowledge graphs)

### 2. Improve Tools and Evaluation Quality
- Better classification of agent actions into: **suggestions**, **diagnosis**, **treatment**
- For each category, define:
  - Which tool sets are available
  - Which evaluation criteria should be used

### 3. Data Sources
- Directly from clinical data (real medical dialogues, case records)
- Knowledge graphs (PrimeKG, disease-symptom mappings)

## General Advice
- Explore more data sources to increase coverage and diversity
- More conversational turns with use of tools, combined with evaluation on more explicit criteria, is more helpful for benchmarking

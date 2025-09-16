# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered web crawler system designed to automatically explore supplier websites and extract architecture material product information. The system uses AI to intelligently navigate websites, build structural maps with link series detection, and generate data extraction schemas.

## Environment Setup

### Python Environment
- Python 3.13.5 is used
- Virtual environment is located in `venv/` directory
- Dependencies are managed via `requirements.txt` (currently empty)

### Environment Configuration
- Copy `.env.example` to `.env` and configure:
  - `CLAUDE_API_KEY`: Required for AI agent functionality
  - `OUTPUT_DIR`: Directory for storing exploration artifacts (default: output)
  - `LOG_LEVEL`: Logging verbosity (default: INFO)

### Basic Commands
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies (when requirements.txt is populated)
pip install -r requirements.txt

# Run Python scripts
python <script_name>.py
```

## Architecture

### Three-Phase System Design

The system is architected around three distinct phases as outlined in the technical documentation:

1. **EXPLORE PHASE**: AI agent explores websites to build structural tree
   - Starts from homepage and uses AI tools to analyze page structure
   - Detects link series patterns to avoid redundant exploration
   - Builds hierarchical website structure with confidence scoring
   - Implements smart navigation with priority-based exploration

2. **SCHEMA PHASE**: Generate crawling schemas from exploration data
   - Analyzes exploration tree to identify product page patterns
   - Creates extraction rules for product information fields
   - Generates URL patterns for systematic crawling

3. **EXECUTE PHASE**: Use schemas to extract product data
   - Applies generated schemas to crawl product information
   - May not require AI for execution phase

### Key Architectural Concepts

#### Link Series Detection
The system intelligently handles repetitive link patterns (e.g., pagination, category listings) by:
- Detecting groups of similar URLs using pattern matching
- Selecting representative samples (3-5) instead of exploring all links
- Creating series metadata to represent entire link groups efficiently

#### Planned Directory Structure
Based on the technical plan, the system will be organized as:
- `src/models/`: Core data structures (WebsiteNode, LinkSeries, ExplorationState)
- `src/explorer/`: Website exploration engine and algorithms
- `src/schema/`: Schema generation from exploration data
- `src/config/`: Configuration parameters and settings
- `src/utils/`: HTTP client and utility functions

### Documentation Workflow

The project uses a structured approach to feature development:

#### Planning Templates (in docs/features/commands/)
- `@plan_feature.md`: Create technical plans for new features
- `@create_brief.md`: Generate product briefs and context
- `@code_review.md`: Review completed implementations
- `@write_docs.md`: Create comprehensive documentation

#### Usage Pattern
```
@plan_feature.md
[Feature description for AI web crawler enhancement]
```

Plans are saved as `docs/features/NNNN_PLAN.md` with incremental numbering.

## Current Status

This is an early-stage project with comprehensive planning documentation but minimal implementation. The codebase currently contains:
- Basic environment setup (venv, .env configuration)
- Detailed technical plans in `docs/features/`
- Planning workflow templates for feature development

When implementing features, refer to the detailed technical specifications in `docs/features/0001_PLAN.md` for the complete system architecture and implementation approach.
import os
from pathlib import Path

DOCS_STRUCTURE = {
    "index.md": """# Karhuno Analysis System

Welcome to Karhuno Analysis System documentation.

## Quick Start

- [System Overview](overview/index.md)
- [Developer Guide](developer/index.md)
- [Best Practices](best-practices/index.md)
""",
    
    "overview/": {
        "index.md": """# System Overview

- [Introduction](introduction.md)
- [Architecture](architecture.md)
- [Data Pipeline](data-pipeline.md)
""",
        "introduction.md": """# Introduction

- [System Purpose](purpose.md)
- [Signal Intelligence Concept](signal-intelligence.md)
- [Key Features](features.md)
- [Target Audience](audience.md)
""",
        "architecture.md": "# System Architecture",
        "data-pipeline.md": "# Data Pipeline",
    },
    
    "business-processes/": {
        "index.md": """# Business Processes

- [Client Request Workflow](client-request.md)
- [Search Configuration](search-config.md)
- [Analysis Process](analysis-process.md)
""",
        "client-request.md": "# Client Request Workflow",
        "search-config.md": "# Search Configuration",
        "analysis-process.md": "# Analysis Process",
    },
    
    "developer/": {
        "index.md": """# Developer Guide

- [Getting Started](getting-started.md)
- [Core Functionality](core-functionality.md)
- [Extending System](extending.md)
""",
        "getting-started.md": "# Getting Started",
        "core-functionality.md": "# Core Functionality",
        "extending.md": "# Extending the System",
    },
    
    "prompts/": {
        "index.md": """# Prompts and Analysis

- [Prompt Structure](structure.md)
- [LLM Integration](llm.md)
- [Results Processing](results.md)
""",
        "structure.md": "# Prompt Structure",
        "llm.md": "# Working with LLM",
        "results.md": "# Results Processing",
    },
    
    "best-practices/": {
        "index.md": """# Best Practices

- [Development](development.md)
- [Data Handling](data-handling.md)
- [Optimization](optimization.md)
""",
        "development.md": "# Development Practices",
        "data-handling.md": "# Data Handling",
        "optimization.md": "# Optimization",
    },
    
    "troubleshooting/": {
        "index.md": """# Troubleshooting

- [Common Issues](common-issues.md)
- [Specific Cases](specific-cases.md)
- [Support](support.md)
""",
        "common-issues.md": "# Common Issues",
        "specific-cases.md": "# Specific Cases",
        "support.md": "# Support",
    }
}

def create_structure(base_path: Path, structure: dict):
    for name, content in structure.items():
        path = base_path / name
        
        if isinstance(content, dict):
            path.mkdir(exist_ok=True)
            create_structure(path, content)
        else:
            path.parent.mkdir(exist_ok=True, parents=True)
            path.write_text(content)

def create_mkdocs_config():
    config = """site_name: Karhuno Analysis System
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - search.suggest
    - search.highlight
    
markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.superfences
  - admonition
  - pymdownx.details
  - pymdownx.tabbed:
      alternate_style: true
  - attr_list
  - def_list
  - footnotes

nav:
  - Home: index.md
  - Overview:
    - overview/index.md
    - Introduction: overview/introduction.md
    - Architecture: overview/architecture.md
    - Data Pipeline: overview/data-pipeline.md
  - Business Processes:
    - business-processes/index.md
    - Client Request: business-processes/client-request.md
    - Search Configuration: business-processes/search-config.md
    - Analysis Process: business-processes/analysis-process.md
  - Developer Guide:
    - developer/index.md
    - Getting Started: developer/getting-started.md
    - Core Functionality: developer/core-functionality.md
    - Extending System: developer/extending.md
  - Prompts and Analysis:
    - prompts/index.md
    - Prompt Structure: prompts/structure.md
    - LLM Integration: prompts/llm.md
    - Results Processing: prompts/results.md
  - Best Practices:
    - best-practices/index.md
    - Development: best-practices/development.md
    - Data Handling: best-practices/data-handling.md
    - Optimization: best-practices/optimization.md
  - Troubleshooting:
    - troubleshooting/index.md
    - Common Issues: troubleshooting/common-issues.md
    - Specific Cases: troubleshooting/specific-cases.md
    - Support: troubleshooting/support.md
"""
    Path("mkdocs.yml").write_text(config)

if __name__ == "__main__":
    docs_path = Path("docs")
    create_structure(docs_path, DOCS_STRUCTURE)
    create_mkdocs_config()
    print("Documentation structure created successfully!") 